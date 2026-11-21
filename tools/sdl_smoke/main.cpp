#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>

#include <SDL3/SDL.h>
#include <SDL3/SDL_vulkan.h>
#include <vulkan/vulkan.h>

#include <algorithm>
#include <atomic>
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <string>
#include <vector>

namespace {

constexpr uint32_t kMaxFramesInFlight = 2;

struct AudioContext {
    std::atomic<uint64_t> bytesRequested{0};
};

void SDLCALL AudioCallback(void* userdata, SDL_AudioStream* stream, int additional_amount, int /*total_amount*/) {
    if (!userdata || !stream || additional_amount <= 0) {
        return;
    }
    auto* ctx = static_cast<AudioContext*>(userdata);
    ctx->bytesRequested.fetch_add(static_cast<uint64_t>(additional_amount), std::memory_order_relaxed);

    static constexpr uint8_t kSilence[4096]{};
    int remaining = additional_amount;
    while (remaining > 0) {
        int chunk = (remaining < static_cast<int>(sizeof(kSilence))) ? remaining : static_cast<int>(sizeof(kSilence));
        SDL_PutAudioStreamData(stream, kSilence, chunk);
        remaining -= chunk;
    }
}

const char* PhysicalDeviceTypeStr(VkPhysicalDeviceType type) {
    switch (type) {
    case VK_PHYSICAL_DEVICE_TYPE_DISCRETE_GPU:   return "discrete";
    case VK_PHYSICAL_DEVICE_TYPE_INTEGRATED_GPU: return "integrated";
    case VK_PHYSICAL_DEVICE_TYPE_VIRTUAL_GPU:    return "virtual";
    case VK_PHYSICAL_DEVICE_TYPE_CPU:            return "cpu";
    default:                                     return "other";
    }
}

int Fail(const std::string& reason) {
    std::printf("[sdl] RESULT FAIL %s\n", reason.c_str());
    std::fflush(stdout);
    return 1;
}

struct SmokeApp {
    SDL_Window* window = nullptr;
    SDL_Gamepad* gamepad = nullptr;
    SDL_JoystickID gamepadId = 0;
    bool prevButtons[SDL_GAMEPAD_BUTTON_COUNT]{};

    SDL_AudioStream* audioStream = nullptr;
    AudioContext audioCtx{};

    VkInstance instance = VK_NULL_HANDLE;
    VkSurfaceKHR surface = VK_NULL_HANDLE;
    VkPhysicalDevice physicalDevice = VK_NULL_HANDLE;
    uint32_t queueFamily = UINT32_MAX;
    VkDevice device = VK_NULL_HANDLE;
    VkQueue queue = VK_NULL_HANDLE;

    VkSwapchainKHR swapchain = VK_NULL_HANDLE;
    VkFormat swapchainFormat = VK_FORMAT_B8G8R8A8_UNORM;
    VkExtent2D swapchainExtent{0, 0};
    std::vector<VkImage> swapchainImages;
    std::vector<VkImageView> swapchainImageViews;
    std::vector<VkSemaphore> renderFinishedSemaphores;

    VkCommandPool commandPool = VK_NULL_HANDLE;
    std::vector<VkCommandBuffer> commandBuffers;
    std::vector<VkSemaphore> imageAvailableSemaphores;
    std::vector<VkFence> inFlightFences;

    bool framebufferResized = false;

    void DestroySwapchain() {
        for (VkSemaphore sem : renderFinishedSemaphores) {
            if (sem != VK_NULL_HANDLE) vkDestroySemaphore(device, sem, nullptr);
        }
        renderFinishedSemaphores.clear();

        for (VkImageView view : swapchainImageViews) {
            if (view != VK_NULL_HANDLE) vkDestroyImageView(device, view, nullptr);
        }
        swapchainImageViews.clear();
        swapchainImages.clear();

        if (swapchain != VK_NULL_HANDLE) {
            vkDestroySwapchainKHR(device, swapchain, nullptr);
            swapchain = VK_NULL_HANDLE;
        }
    }

    bool CreateSwapchain(std::string& err) {
        int w = 0, h = 0;
        SDL_GetWindowSizeInPixels(window, &w, &h);
        if (w <= 0 || h <= 0) {
            swapchainExtent = {0, 0};
            return true;
        }

        VkSurfaceCapabilitiesKHR caps{};
        if (vkGetPhysicalDeviceSurfaceCapabilitiesKHR(physicalDevice, surface, &caps) != VK_SUCCESS) {
            err = "vkGetPhysicalDeviceSurfaceCapabilitiesKHR failed";
            return false;
        }

        uint32_t fmtCount = 0;
        vkGetPhysicalDeviceSurfaceFormatsKHR(physicalDevice, surface, &fmtCount, nullptr);
        std::vector<VkSurfaceFormatKHR> formats(fmtCount);
        if (fmtCount > 0) {
            vkGetPhysicalDeviceSurfaceFormatsKHR(physicalDevice, surface, &fmtCount, formats.data());
        }
        if (formats.empty()) {
            err = "no surface formats available";
            return false;
        }

        VkSurfaceFormatKHR chosenFormat = formats[0];
        for (const auto& f : formats) {
            if (f.format == VK_FORMAT_B8G8R8A8_UNORM && f.colorSpace == VK_COLOR_SPACE_SRGB_NONLINEAR_KHR) {
                chosenFormat = f;
                break;
            }
            if (f.format == VK_FORMAT_B8G8R8A8_SRGB && f.colorSpace == VK_COLOR_SPACE_SRGB_NONLINEAR_KHR) {
                chosenFormat = f;
            }
        }

        VkExtent2D extent{};
        if (caps.currentExtent.width != UINT32_MAX) {
            extent = caps.currentExtent;
        } else {
            extent.width = std::clamp(static_cast<uint32_t>(w), caps.minImageExtent.width, caps.maxImageExtent.width);
            extent.height = std::clamp(static_cast<uint32_t>(h), caps.minImageExtent.height, caps.maxImageExtent.height);
        }

        uint32_t imageCount = std::max(3u, caps.minImageCount);
        if (caps.maxImageCount > 0 && imageCount > caps.maxImageCount) {
            imageCount = caps.maxImageCount;
        }

        VkSwapchainCreateInfoKHR sci{};
        sci.sType = VK_STRUCTURE_TYPE_SWAPCHAIN_CREATE_INFO_KHR;
        sci.surface = surface;
        sci.minImageCount = imageCount;
        sci.imageFormat = chosenFormat.format;
        sci.imageColorSpace = chosenFormat.colorSpace;
        sci.imageExtent = extent;
        sci.imageArrayLayers = 1;
        sci.imageUsage = VK_IMAGE_USAGE_COLOR_ATTACHMENT_BIT;
        sci.imageSharingMode = VK_SHARING_MODE_EXCLUSIVE;
        sci.preTransform = caps.currentTransform;
        sci.compositeAlpha = VK_COMPOSITE_ALPHA_OPAQUE_BIT_KHR;
        sci.presentMode = VK_PRESENT_MODE_FIFO_KHR;
        sci.clipped = VK_TRUE;
        sci.oldSwapchain = VK_NULL_HANDLE;

        if (vkCreateSwapchainKHR(device, &sci, nullptr, &swapchain) != VK_SUCCESS) {
            err = "vkCreateSwapchainKHR failed";
            return false;
        }

        swapchainFormat = chosenFormat.format;
        swapchainExtent = extent;

        uint32_t actualCount = 0;
        vkGetSwapchainImagesKHR(device, swapchain, &actualCount, nullptr);
        swapchainImages.resize(actualCount);
        vkGetSwapchainImagesKHR(device, swapchain, &actualCount, swapchainImages.data());

        swapchainImageViews.resize(actualCount, VK_NULL_HANDLE);
        for (uint32_t i = 0; i < actualCount; ++i) {
            VkImageViewCreateInfo ivci{};
            ivci.sType = VK_STRUCTURE_TYPE_IMAGE_VIEW_CREATE_INFO;
            ivci.image = swapchainImages[i];
            ivci.viewType = VK_IMAGE_VIEW_TYPE_2D;
            ivci.format = swapchainFormat;
            ivci.subresourceRange.aspectMask = VK_IMAGE_ASPECT_COLOR_BIT;
            ivci.subresourceRange.levelCount = 1;
            ivci.subresourceRange.layerCount = 1;
            if (vkCreateImageView(device, &ivci, nullptr, &swapchainImageViews[i]) != VK_SUCCESS) {
                err = "vkCreateImageView failed";
                return false;
            }
        }

        renderFinishedSemaphores.resize(actualCount, VK_NULL_HANDLE);
        VkSemaphoreCreateInfo semInfo{};
        semInfo.sType = VK_STRUCTURE_TYPE_SEMAPHORE_CREATE_INFO;
        for (uint32_t i = 0; i < actualCount; ++i) {
            if (vkCreateSemaphore(device, &semInfo, nullptr, &renderFinishedSemaphores[i]) != VK_SUCCESS) {
                err = "vkCreateSemaphore (renderFinished) failed";
                return false;
            }
        }
        return true;
    }

    bool RecreateSwapchain(std::string& err) {
        int w = 0, h = 0;
        SDL_GetWindowSizeInPixels(window, &w, &h);
        if (w <= 0 || h <= 0) {
            return true;
        }
        vkDeviceWaitIdle(device);
        DestroySwapchain();
        return CreateSwapchain(err);
    }

    void OpenFirstGamepad() {
        int count = 0;
        SDL_JoystickID* ids = SDL_GetGamepads(&count);
        if (!ids) {
            return;
        }
        if (count > 0 && !gamepad) {
            gamepad = SDL_OpenGamepad(ids[0]);
            if (gamepad) {
                gamepadId = ids[0];
                std::memset(prevButtons, 0, sizeof(prevButtons));
                const char* name = SDL_GetGamepadName(gamepad);
                std::printf("[sdl] gamepad=%s\n", name ? name : "unknown");
            }
        }
        SDL_free(ids);
    }

    void Cleanup() {
        if (device != VK_NULL_HANDLE) {
            vkDeviceWaitIdle(device);
        }

        DestroySwapchain();

        for (VkFence fence : inFlightFences) {
            if (fence != VK_NULL_HANDLE) vkDestroyFence(device, fence, nullptr);
        }
        inFlightFences.clear();

        for (VkSemaphore sem : imageAvailableSemaphores) {
            if (sem != VK_NULL_HANDLE) vkDestroySemaphore(device, sem, nullptr);
        }
        imageAvailableSemaphores.clear();

        if (commandPool != VK_NULL_HANDLE) {
            vkDestroyCommandPool(device, commandPool, nullptr);
            commandPool = VK_NULL_HANDLE;
        }

        if (device != VK_NULL_HANDLE) {
            vkDestroyDevice(device, nullptr);
            device = VK_NULL_HANDLE;
        }

        if (surface != VK_NULL_HANDLE && instance != VK_NULL_HANDLE) {
            SDL_Vulkan_DestroySurface(instance, surface, nullptr);
            surface = VK_NULL_HANDLE;
        }

        if (instance != VK_NULL_HANDLE) {
            vkDestroyInstance(instance, nullptr);
            instance = VK_NULL_HANDLE;
        }

        if (audioStream) {
            SDL_DestroyAudioStream(audioStream);
            audioStream = nullptr;
        }

        if (gamepad) {
            SDL_CloseGamepad(gamepad);
            gamepad = nullptr;
        }

        if (window) {
            SDL_DestroyWindow(window);
            window = nullptr;
        }

        SDL_Quit();
    }
};

bool InitVulkan(SmokeApp& app, std::string& err) {
    Uint32 extCount = 0;
    char const* const* sdlExts = SDL_Vulkan_GetInstanceExtensions(&extCount);
    if (!sdlExts || extCount == 0) {
        err = std::string("SDL_Vulkan_GetInstanceExtensions failed: ") + SDL_GetError();
        return false;
    }

    VkApplicationInfo appInfo{};
    appInfo.sType = VK_STRUCTURE_TYPE_APPLICATION_INFO;
    appInfo.pApplicationName = "sdl_smoke";
    appInfo.applicationVersion = VK_MAKE_VERSION(1, 0, 0);
    appInfo.pEngineName = "sdl_smoke";
    appInfo.engineVersion = VK_MAKE_VERSION(1, 0, 0);
    appInfo.apiVersion = VK_API_VERSION_1_3;

    VkInstanceCreateInfo ici{};
    ici.sType = VK_STRUCTURE_TYPE_INSTANCE_CREATE_INFO;
    ici.pApplicationInfo = &appInfo;
    ici.enabledExtensionCount = extCount;
    ici.ppEnabledExtensionNames = sdlExts;

    if (vkCreateInstance(&ici, nullptr, &app.instance) != VK_SUCCESS) {
        err = "vkCreateInstance failed";
        return false;
    }

    if (!SDL_Vulkan_CreateSurface(app.window, app.instance, nullptr, &app.surface)) {
        err = std::string("SDL_Vulkan_CreateSurface failed: ") + SDL_GetError();
        return false;
    }

    uint32_t pdCount = 0;
    vkEnumeratePhysicalDevices(app.instance, &pdCount, nullptr);
    if (pdCount == 0) {
        err = "no Vulkan physical devices found";
        return false;
    }
    std::vector<VkPhysicalDevice> pds(pdCount);
    vkEnumeratePhysicalDevices(app.instance, &pdCount, pds.data());

    int bestScore = -1;
    VkPhysicalDeviceProperties bestProps{};
    for (VkPhysicalDevice pd : pds) {
        VkPhysicalDeviceProperties props{};
        vkGetPhysicalDeviceProperties(pd, &props);
        if (props.apiVersion < VK_API_VERSION_1_3) {
            continue;
        }

        uint32_t qfCount = 0;
        vkGetPhysicalDeviceQueueFamilyProperties(pd, &qfCount, nullptr);
        std::vector<VkQueueFamilyProperties> qfs(qfCount);
        vkGetPhysicalDeviceQueueFamilyProperties(pd, &qfCount, qfs.data());

        uint32_t chosenQf = UINT32_MAX;
        for (uint32_t i = 0; i < qfCount; ++i) {
            if ((qfs[i].queueFlags & VK_QUEUE_GRAPHICS_BIT) == 0) continue;
            VkBool32 presentSupport = VK_FALSE;
            vkGetPhysicalDeviceSurfaceSupportKHR(pd, i, app.surface, &presentSupport);
            if (presentSupport == VK_TRUE) {
                chosenQf = i;
                break;
            }
        }
        if (chosenQf == UINT32_MAX) continue;

        uint32_t devExtCount = 0;
        vkEnumerateDeviceExtensionProperties(pd, nullptr, &devExtCount, nullptr);
        std::vector<VkExtensionProperties> devExts(devExtCount);
        vkEnumerateDeviceExtensionProperties(pd, nullptr, &devExtCount, devExts.data());
        bool hasSwapchain = false;
        for (const auto& e : devExts) {
            if (std::strcmp(e.extensionName, VK_KHR_SWAPCHAIN_EXTENSION_NAME) == 0) {
                hasSwapchain = true;
                break;
            }
        }
        if (!hasSwapchain) continue;

        int score = (props.deviceType == VK_PHYSICAL_DEVICE_TYPE_DISCRETE_GPU) ? 100 : 10;
        if (score > bestScore) {
            bestScore = score;
            app.physicalDevice = pd;
            app.queueFamily = chosenQf;
            bestProps = props;
        }
    }

    if (app.physicalDevice == VK_NULL_HANDLE) {
        err = "no suitable Vulkan 1.3 physical device with graphics+present+swapchain";
        return false;
    }

    std::printf("[sdl] gpu=%s type=%s queueFamily=%u\n",
                bestProps.deviceName,
                PhysicalDeviceTypeStr(bestProps.deviceType),
                app.queueFamily);

    float queuePriority = 1.0f;
    VkDeviceQueueCreateInfo qci{};
    qci.sType = VK_STRUCTURE_TYPE_DEVICE_QUEUE_CREATE_INFO;
    qci.queueFamilyIndex = app.queueFamily;
    qci.queueCount = 1;
    qci.pQueuePriorities = &queuePriority;

    VkPhysicalDeviceVulkan13Features v13{};
    v13.sType = VK_STRUCTURE_TYPE_PHYSICAL_DEVICE_VULKAN_1_3_FEATURES;
    v13.dynamicRendering = VK_TRUE;
    v13.synchronization2 = VK_TRUE;

    const char* deviceExts[] = { VK_KHR_SWAPCHAIN_EXTENSION_NAME };
    VkDeviceCreateInfo dci{};
    dci.sType = VK_STRUCTURE_TYPE_DEVICE_CREATE_INFO;
    dci.pNext = &v13;
    dci.queueCreateInfoCount = 1;
    dci.pQueueCreateInfos = &qci;
    dci.enabledExtensionCount = 1;
    dci.ppEnabledExtensionNames = deviceExts;

    if (vkCreateDevice(app.physicalDevice, &dci, nullptr, &app.device) != VK_SUCCESS) {
        err = "vkCreateDevice failed";
        return false;
    }
    vkGetDeviceQueue(app.device, app.queueFamily, 0, &app.queue);

    VkCommandPoolCreateInfo cpci{};
    cpci.sType = VK_STRUCTURE_TYPE_COMMAND_POOL_CREATE_INFO;
    cpci.flags = VK_COMMAND_POOL_CREATE_RESET_COMMAND_BUFFER_BIT;
    cpci.queueFamilyIndex = app.queueFamily;
    if (vkCreateCommandPool(app.device, &cpci, nullptr, &app.commandPool) != VK_SUCCESS) {
        err = "vkCreateCommandPool failed";
        return false;
    }

    app.commandBuffers.resize(kMaxFramesInFlight);
    VkCommandBufferAllocateInfo cbai{};
    cbai.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_ALLOCATE_INFO;
    cbai.commandPool = app.commandPool;
    cbai.level = VK_COMMAND_BUFFER_LEVEL_PRIMARY;
    cbai.commandBufferCount = kMaxFramesInFlight;
    if (vkAllocateCommandBuffers(app.device, &cbai, app.commandBuffers.data()) != VK_SUCCESS) {
        err = "vkAllocateCommandBuffers failed";
        return false;
    }

    app.imageAvailableSemaphores.resize(kMaxFramesInFlight, VK_NULL_HANDLE);
    app.inFlightFences.resize(kMaxFramesInFlight, VK_NULL_HANDLE);
    VkSemaphoreCreateInfo sci{};
    sci.sType = VK_STRUCTURE_TYPE_SEMAPHORE_CREATE_INFO;
    VkFenceCreateInfo fci{};
    fci.sType = VK_STRUCTURE_TYPE_FENCE_CREATE_INFO;
    fci.flags = VK_FENCE_CREATE_SIGNALED_BIT;
    for (uint32_t i = 0; i < kMaxFramesInFlight; ++i) {
        if (vkCreateSemaphore(app.device, &sci, nullptr, &app.imageAvailableSemaphores[i]) != VK_SUCCESS ||
            vkCreateFence(app.device, &fci, nullptr, &app.inFlightFences[i]) != VK_SUCCESS) {
            err = "failed to create per-frame sync objects";
            return false;
        }
    }

    return app.CreateSwapchain(err);
}

void RecordFrame(SmokeApp& app, VkCommandBuffer cmd, uint32_t imageIndex, float elapsedSec) {
    VkCommandBufferBeginInfo bi{};
    bi.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_BEGIN_INFO;
    vkBeginCommandBuffer(cmd, &bi);

    VkImageMemoryBarrier2 toColor{};
    toColor.sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER_2;
    toColor.srcStageMask = VK_PIPELINE_STAGE_2_TOP_OF_PIPE_BIT;
    toColor.srcAccessMask = 0;
    toColor.dstStageMask = VK_PIPELINE_STAGE_2_COLOR_ATTACHMENT_OUTPUT_BIT;
    toColor.dstAccessMask = VK_ACCESS_2_COLOR_ATTACHMENT_WRITE_BIT;
    toColor.oldLayout = VK_IMAGE_LAYOUT_UNDEFINED;
    toColor.newLayout = VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL;
    toColor.image = app.swapchainImages[imageIndex];
    toColor.subresourceRange = { VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1 };

    VkDependencyInfo depToColor{};
    depToColor.sType = VK_STRUCTURE_TYPE_DEPENDENCY_INFO;
    depToColor.imageMemoryBarrierCount = 1;
    depToColor.pImageMemoryBarriers = &toColor;
    vkCmdPipelineBarrier2(cmd, &depToColor);

    VkRenderingAttachmentInfo colorAtt{};
    colorAtt.sType = VK_STRUCTURE_TYPE_RENDERING_ATTACHMENT_INFO;
    colorAtt.imageView = app.swapchainImageViews[imageIndex];
    colorAtt.imageLayout = VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL;
    colorAtt.loadOp = VK_ATTACHMENT_LOAD_OP_CLEAR;
    colorAtt.storeOp = VK_ATTACHMENT_STORE_OP_STORE;
    colorAtt.clearValue.color.float32[0] = 0.5f + 0.5f * std::sinf(elapsedSec * 1.3f);
    colorAtt.clearValue.color.float32[1] = 0.5f + 0.5f * std::sinf(elapsedSec * 1.7f + 2.094f);
    colorAtt.clearValue.color.float32[2] = 0.5f + 0.5f * std::sinf(elapsedSec * 2.1f + 4.188f);
    colorAtt.clearValue.color.float32[3] = 1.0f;

    VkRenderingInfo ri{};
    ri.sType = VK_STRUCTURE_TYPE_RENDERING_INFO;
    ri.renderArea = { {0, 0}, app.swapchainExtent };
    ri.layerCount = 1;
    ri.colorAttachmentCount = 1;
    ri.pColorAttachments = &colorAtt;

    vkCmdBeginRendering(cmd, &ri);
    vkCmdEndRendering(cmd);

    VkImageMemoryBarrier2 toPresent{};
    toPresent.sType = VK_STRUCTURE_TYPE_IMAGE_MEMORY_BARRIER_2;
    toPresent.srcStageMask = VK_PIPELINE_STAGE_2_COLOR_ATTACHMENT_OUTPUT_BIT;
    toPresent.srcAccessMask = VK_ACCESS_2_COLOR_ATTACHMENT_WRITE_BIT;
    toPresent.dstStageMask = VK_PIPELINE_STAGE_2_BOTTOM_OF_PIPE_BIT;
    toPresent.dstAccessMask = 0;
    toPresent.oldLayout = VK_IMAGE_LAYOUT_COLOR_ATTACHMENT_OPTIMAL;
    toPresent.newLayout = VK_IMAGE_LAYOUT_PRESENT_SRC_KHR;
    toPresent.image = app.swapchainImages[imageIndex];
    toPresent.subresourceRange = { VK_IMAGE_ASPECT_COLOR_BIT, 0, 1, 0, 1 };

    VkDependencyInfo depToPresent{};
    depToPresent.sType = VK_STRUCTURE_TYPE_DEPENDENCY_INFO;
    depToPresent.imageMemoryBarrierCount = 1;
    depToPresent.pImageMemoryBarriers = &toPresent;
    vkCmdPipelineBarrier2(cmd, &depToPresent);

    vkEndCommandBuffer(cmd);
}

} // namespace

int main(int /*argc*/, char** /*argv*/) {
    double smokeSeconds = 6.0;
    if (const char* envSec = std::getenv("PS2X_SMOKE_SECONDS")) {
        double parsed = std::atof(envSec);
        if (parsed > 0.0) smokeSeconds = parsed;
    }

    SmokeApp app;

    if (!SDL_Init(SDL_INIT_VIDEO | SDL_INIT_AUDIO | SDL_INIT_GAMEPAD)) {
        return Fail(std::string("SDL_Init failed: ") + SDL_GetError());
    }

    int ver = SDL_GetVersion();
    const char* rev = SDL_GetRevision();
    const char* drv = SDL_GetCurrentVideoDriver();
    std::printf("[sdl] version=%d.%d.%d (%s)\n",
                SDL_VERSIONNUM_MAJOR(ver), SDL_VERSIONNUM_MINOR(ver), SDL_VERSIONNUM_MICRO(ver),
                rev ? rev : "");
    std::printf("[sdl] video driver=%s\n", drv ? drv : "unknown");

    app.window = SDL_CreateWindow("sdl_smoke", 1280, 720, SDL_WINDOW_VULKAN | SDL_WINDOW_RESIZABLE);
    if (!app.window) {
        app.Cleanup();
        return Fail(std::string("SDL_CreateWindow failed: ") + SDL_GetError());
    }

    std::string vkErr;
    if (!InitVulkan(app, vkErr)) {
        app.Cleanup();
        return Fail(vkErr);
    }

    app.OpenFirstGamepad();

    SDL_AudioSpec audioSpec{};
    audioSpec.format = SDL_AUDIO_F32;
    audioSpec.channels = 2;
    audioSpec.freq = 48000;
    app.audioStream = SDL_OpenAudioDeviceStream(SDL_AUDIO_DEVICE_DEFAULT_PLAYBACK, &audioSpec, AudioCallback, &app.audioCtx);
    if (!app.audioStream) {
        app.Cleanup();
        return Fail(std::string("SDL_OpenAudioDeviceStream failed: ") + SDL_GetError());
    }
    if (!SDL_ResumeAudioStreamDevice(app.audioStream)) {
        app.Cleanup();
        return Fail(std::string("SDL_ResumeAudioStreamDevice failed: ") + SDL_GetError());
    }

    LARGE_INTEGER qpcFreq{}, qpcStart{}, qpcLastPresent{}, qpcLastReport{};
    QueryPerformanceFrequency(&qpcFreq);
    QueryPerformanceCounter(&qpcStart);
    qpcLastPresent = qpcStart;
    qpcLastReport = qpcStart;

    uint32_t frameInFlight = 0;
    uint64_t totalFrames = 0;
    std::vector<double> windowFrameMs;
    bool running = true;

    while (running) {
        LARGE_INTEGER now{};
        QueryPerformanceCounter(&now);
        double totalElapsedSec = static_cast<double>(now.QuadPart - qpcStart.QuadPart) / static_cast<double>(qpcFreq.QuadPart);
        if (totalElapsedSec >= smokeSeconds) {
            break;
        }

        SDL_Event ev{};
        while (SDL_PollEvent(&ev)) {
            switch (ev.type) {
            case SDL_EVENT_QUIT:
                running = false;
                break;
            case SDL_EVENT_WINDOW_RESIZED:
            case SDL_EVENT_WINDOW_PIXEL_SIZE_CHANGED:
                app.framebufferResized = true;
                break;
            case SDL_EVENT_KEY_DOWN:
                std::printf("[sdl] key %s\n", SDL_GetKeyName(ev.key.key));
                break;
            case SDL_EVENT_GAMEPAD_ADDED:
                if (!app.gamepad) {
                    app.gamepad = SDL_OpenGamepad(ev.gdevice.which);
                    if (app.gamepad) {
                        app.gamepadId = ev.gdevice.which;
                        std::memset(app.prevButtons, 0, sizeof(app.prevButtons));
                        const char* name = SDL_GetGamepadName(app.gamepad);
                        std::printf("[sdl] gamepad added=%s\n", name ? name : "unknown");
                    }
                }
                break;
            case SDL_EVENT_GAMEPAD_REMOVED:
                if (app.gamepad && ev.gdevice.which == app.gamepadId) {
                    const char* name = SDL_GetGamepadName(app.gamepad);
                    std::printf("[sdl] gamepad removed=%s\n", name ? name : "unknown");
                    SDL_CloseGamepad(app.gamepad);
                    app.gamepad = nullptr;
                    app.gamepadId = 0;
                    app.OpenFirstGamepad();
                }
                break;
            default:
                break;
            }
        }
        if (!running) break;

        if (app.gamepad) {
            for (int b = 0; b < SDL_GAMEPAD_BUTTON_COUNT; ++b) {
                bool down = SDL_GetGamepadButton(app.gamepad, static_cast<SDL_GamepadButton>(b));
                if (down && !app.prevButtons[b]) {
                    std::printf("[sdl] pad button %d down\n", b);
                }
                app.prevButtons[b] = down;
            }
        }

        if (app.framebufferResized || app.swapchainExtent.width == 0 || app.swapchainExtent.height == 0) {
            app.framebufferResized = false;
            if (!app.RecreateSwapchain(vkErr)) {
                app.Cleanup();
                return Fail(vkErr);
            }
            if (app.swapchainExtent.width == 0 || app.swapchainExtent.height == 0) {
                SDL_Delay(16);
                continue;
            }
        }

        vkWaitForFences(app.device, 1, &app.inFlightFences[frameInFlight], VK_TRUE, UINT64_MAX);

        uint32_t imageIndex = 0;
        VkResult acqRes = vkAcquireNextImageKHR(app.device, app.swapchain, UINT64_MAX,
                                                app.imageAvailableSemaphores[frameInFlight], VK_NULL_HANDLE, &imageIndex);
        if (acqRes == VK_ERROR_OUT_OF_DATE_KHR) {
            app.framebufferResized = true;
            continue;
        }
        if (acqRes != VK_SUCCESS && acqRes != VK_SUBOPTIMAL_KHR) {
            app.Cleanup();
            return Fail("vkAcquireNextImageKHR failed");
        }

        vkResetFences(app.device, 1, &app.inFlightFences[frameInFlight]);
        VkCommandBuffer cmd = app.commandBuffers[frameInFlight];
        vkResetCommandBuffer(cmd, 0);
        RecordFrame(app, cmd, imageIndex, static_cast<float>(totalElapsedSec));

        VkSemaphoreSubmitInfo waitSem{};
        waitSem.sType = VK_STRUCTURE_TYPE_SEMAPHORE_SUBMIT_INFO;
        waitSem.semaphore = app.imageAvailableSemaphores[frameInFlight];
        waitSem.stageMask = VK_PIPELINE_STAGE_2_COLOR_ATTACHMENT_OUTPUT_BIT;

        VkCommandBufferSubmitInfo cmdInfo{};
        cmdInfo.sType = VK_STRUCTURE_TYPE_COMMAND_BUFFER_SUBMIT_INFO;
        cmdInfo.commandBuffer = cmd;

        VkSemaphoreSubmitInfo sigSem{};
        sigSem.sType = VK_STRUCTURE_TYPE_SEMAPHORE_SUBMIT_INFO;
        sigSem.semaphore = app.renderFinishedSemaphores[imageIndex];
        sigSem.stageMask = VK_PIPELINE_STAGE_2_ALL_COMMANDS_BIT;

        VkSubmitInfo2 submitInfo{};
        submitInfo.sType = VK_STRUCTURE_TYPE_SUBMIT_INFO_2;
        submitInfo.waitSemaphoreInfoCount = 1;
        submitInfo.pWaitSemaphoreInfos = &waitSem;
        submitInfo.commandBufferInfoCount = 1;
        submitInfo.pCommandBufferInfos = &cmdInfo;
        submitInfo.signalSemaphoreInfoCount = 1;
        submitInfo.pSignalSemaphoreInfos = &sigSem;

        if (vkQueueSubmit2(app.queue, 1, &submitInfo, app.inFlightFences[frameInFlight]) != VK_SUCCESS) {
            app.Cleanup();
            return Fail("vkQueueSubmit2 failed");
        }

        VkPresentInfoKHR presentInfo{};
        presentInfo.sType = VK_STRUCTURE_TYPE_PRESENT_INFO_KHR;
        presentInfo.waitSemaphoreCount = 1;
        presentInfo.pWaitSemaphores = &app.renderFinishedSemaphores[imageIndex];
        presentInfo.swapchainCount = 1;
        presentInfo.pSwapchains = &app.swapchain;
        presentInfo.pImageIndices = &imageIndex;

        VkResult presRes = vkQueuePresentKHR(app.queue, &presentInfo);
        if (presRes == VK_ERROR_OUT_OF_DATE_KHR || presRes == VK_SUBOPTIMAL_KHR || acqRes == VK_SUBOPTIMAL_KHR) {
            app.framebufferResized = true;
        } else if (presRes != VK_SUCCESS) {
            app.Cleanup();
            return Fail("vkQueuePresentKHR failed");
        }

        LARGE_INTEGER afterPresent{};
        QueryPerformanceCounter(&afterPresent);
        double dtMs = static_cast<double>(afterPresent.QuadPart - qpcLastPresent.QuadPart) * 1000.0 /
                      static_cast<double>(qpcFreq.QuadPart);
        qpcLastPresent = afterPresent;
        windowFrameMs.push_back(dtMs);
        ++totalFrames;

        double reportSec = static_cast<double>(afterPresent.QuadPart - qpcLastReport.QuadPart) /
                           static_cast<double>(qpcFreq.QuadPart);
        if (reportSec >= 1.0 && !windowFrameMs.empty()) {
            std::sort(windowFrameMs.begin(), windowFrameMs.end());
            size_t n = windowFrameMs.size();
            double p50 = windowFrameMs[(n * 50) / 100];
            double p95 = windowFrameMs[std::min(n - 1, (n * 95) / 100)];
            double maxMs = windowFrameMs.back();
            std::printf("[sdl] fps=%zu p50=%.2f p95=%.2f max=%.2f ms\n", n, p50, p95, maxMs);
            std::printf("[sdl] audio requested=%llu\n",
                        static_cast<unsigned long long>(app.audioCtx.bytesRequested.load(std::memory_order_relaxed)));
            std::fflush(stdout);
            windowFrameMs.clear();
            qpcLastReport = afterPresent;
        }

        frameInFlight = (frameInFlight + 1) % kMaxFramesInFlight;
    }

    LARGE_INTEGER qpcEnd{};
    QueryPerformanceCounter(&qpcEnd);
    double totalSec = static_cast<double>(qpcEnd.QuadPart - qpcStart.QuadPart) / static_cast<double>(qpcFreq.QuadPart);
    double avgFps = (totalSec > 0.0) ? (static_cast<double>(totalFrames) / totalSec) : 0.0;

    app.Cleanup();
    std::printf("[sdl] RESULT ok frames=%llu avgfps=%.1f\n",
                static_cast<unsigned long long>(totalFrames), avgFps);
    std::fflush(stdout);
    return 0;
}
