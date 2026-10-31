"""Reader for logs/vu1corpus.bin (PROBE-CAPTURE in ps2_vu1_core.cpp). Usage: python tools/vu1gen/corpus.py [file]  -> summary.
Chunks: u32 tag, u32 bytes, payload. HDR {u32 sizeof(VU1State)}, CODE {u64 gen, code}, RUN (see svCaptureRecord)."""
import hashlib
import struct
import sys


def chunks(path):
    data = open(path, "rb").read()
    o = 0
    while o + 8 <= len(data):
        tag, n = struct.unpack_from("<II", data, o)
        if o + 8 + n > len(data):
            break  # truncated tail (process killed mid-write)
        yield data[o:o + 4], data[o + 8:o + 8 + n]
        o += 8 + n


def state(b, o):
    s = {}
    s["vf"] = struct.unpack_from("<128f", b, o)
    s["vi"] = struct.unpack_from("<16i", b, o + 512)
    s["acc"] = struct.unpack_from("<4f", b, o + 576)
    s["q"], s["p"], s["i"] = struct.unpack_from("<3f", b, o + 592)
    s["r"], s["pc"], s["mac"], s["clip"], s["status"] = struct.unpack_from("<5I", b, o + 604)
    s["raw"] = b[o:o + 0]  # placeholder; raw bytes are sliced by the caller when needed
    return s


def runs(path):
    stsize = None
    codes = {}
    for tag, p in chunks(path):
        if tag == b"HDR ":
            stsize = struct.unpack_from("<I", p)[0]
        elif tag == b"CODE":
            gen = struct.unpack_from("<Q", p)[0]
            codes[gen] = p[8:]
        elif tag == b"RUN ":
            o = 0
            startPC, top, itop, maxCycles, wc0, wcA = struct.unpack_from("<6I", p, o); o += 24
            cyc0, cycA, gen = struct.unpack_from("<3Q", p, o); o += 24
            (dsz,) = struct.unpack_from("<I", p, o); o += 4
            s0 = p[o:o + stsize]; o += stsize
            sA = p[o:o + stsize]; o += stsize
            mem0 = p[o:o + dsz]; o += dsz
            (nd,) = struct.unpack_from("<I", p, o); o += 4
            diff = []
            for _ in range(nd):
                (q,) = struct.unpack_from("<I", p, o); o += 4
                diff.append((q, p[o:o + 16])); o += 16
            (gn,) = struct.unpack_from("<I", p, o); o += 4
            gif = p[o:o + gn]
            yield dict(startPC=startPC, top=top, itop=itop, maxCycles=maxCycles, wc0=wc0, wcA=wcA, cyc0=cyc0, cycA=cycA, gen=gen,
                       dsz=dsz, s0=s0, sA=sA, mem0=mem0, diff=diff, gif=gif, code=codes.get(gen))


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "logs/vu1corpus.bin"
    n = 0
    byPc = {}
    gens = {}
    for r in runs(path):
        n += 1
        k = r["startPC"]
        d = byPc.setdefault(k, [0, 0, 0, 0])
        d[0] += 1
        d[1] += r["cycA"] - r["cyc0"]
        d[2] += len(r["diff"])
        d[3] += len(r["gif"])
        h = hashlib.sha1(r["code"] or b"").hexdigest()[:16] if r["code"] else "nocode"
        gens[(r["gen"], h)] = gens.get((r["gen"], h), 0) + 1
    print("records", n)
    for k, v in sorted(byPc.items()):
        print("startPC %04X: runs=%d avgCycles=%.0f avgChangedQw=%.1f avgGifBytes=%.0f" % (k, v[0], v[1] / v[0], v[2] / v[0], v[3] / v[0]))
    for (g, h), c in sorted(gens.items()):
        print("codeGen %d sha1=%s runs=%d" % (g, h, c))
