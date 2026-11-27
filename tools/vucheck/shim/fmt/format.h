// Minimal shim: the recompiler uses fmt::format; map it onto std::format (fmt is not available offline).
#pragma once
#include <format>
namespace fmt {
using std::format;
}
