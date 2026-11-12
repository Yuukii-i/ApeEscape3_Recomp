"""Merge the VU1 block dumps (logs/vublk2_u1_<image>*.txt) into one record file whose timing hashes do NOT contain the XGKICK-active token.

The runtime hash (VU1Interpreter blkStateScan) is H = 0x1234ABCD; for each token: H = mix(H ^ mix(tokenvalue)), the "x" (transfer active) token last. The dump
stores every record's entry / exit token text, so each hash is recomputed from the tokens (and checked against the recorded one), then recomputed again with the
x token dropped. With the transfer-aware dispatcher (hash ignores the transfer) these are the keys the runtime looks up.
Usage: python tools/vu1gen/hotgen_norm.py <out.txt> <dump1.txt> [<dump2.txt> ...]   (the first dump wins on equal (pc, x-less sig))"""
import re
import sys

M = (1 << 64) - 1


def mix(x):
    x = (x + 0x9E3779B97F4A7C15) & M
    x = ((x ^ (x >> 30)) * 0xBF58476D1CE4E5B9) & M
    x = ((x ^ (x >> 27)) * 0x94D049BB133111EB) & M
    return x ^ (x >> 31)


def tok_hash(tokens):
    h = 0x1234ABCD
    for t in tokens:
        m = re.match(r"([a-z])(\d+)\.(\d+)\.(-?\d+)$", t)
        tag, a, b, rel = m.group(1), int(m.group(2)), int(m.group(3)), int(m.group(4))
        val = ((ord(tag) << 56) ^ (a << 40) ^ (b << 32) ^ (rel & M)) & M
        h = mix(h ^ mix(val))
    return h


def parse(path):
    recs, cur = [], None
    for ln in open(path, encoding="utf-8", errors="replace"):
        if ln.startswith("B "):
            kv = dict(t.split("=", 1) for t in ln.split()[1:])
            cur = dict(kv=kv, lines=[], entry=[], exit=[])
            recs.append(cur)
        elif cur is not None:
            s = ln.strip()
            cur["lines"].append(ln.rstrip("\n"))
            if s.startswith("entry:"):
                cur["entry"] = s[6:].split()
            elif s.startswith("exit:"):
                cur["exit"] = s[5:].split()
    return recs


def main():
    out = sys.argv[1]
    seen, merged = {}, []
    bad = 0
    stats = dict(total=0, entry_x=0, exit_x=0, dup=0, hash_ok=0)
    for path in sys.argv[2:]:
        for r in parse(path):
            stats["total"] += 1
            kv = r["kv"]
            sig, exitsig = int(kv["sig"], 16), int(kv["exitsig"], 16)
            if tok_hash(r["entry"]) != sig or tok_hash(r["exit"]) != exitsig:
                bad += 1
                continue
            stats["hash_ok"] += 1
            ent = [t for t in r["entry"] if not t.startswith("x")]
            ext = [t for t in r["exit"] if not t.startswith("x")]
            stats["entry_x"] += len(ent) != len(r["entry"])
            stats["exit_x"] += len(ext) != len(r["exit"])
            nsig, nexit = tok_hash(ent), tok_hash(ext)
            key = (int(kv["pc"], 16), nsig)
            if key in seen:
                stats["dup"] += 1
                continue
            seen[key] = True
            kv2 = dict(kv)
            kv2["sig"], kv2["exitsig"], kv2["xg"] = "%016x" % nsig, "%016x" % nexit, "0"
            head = "B " + " ".join("%s=%s" % (k, v) for k, v in kv2.items())
            body = []
            for ln in r["lines"]:
                s = ln.strip()
                if s.startswith("entry:"):
                    body.append("  entry: " + " ".join(ent) + (" " if ent else ""))
                elif s.startswith("exit:"):
                    body.append("  exit: " + " ".join(ext) + (" " if ext else ""))
                else:
                    body.append(ln)
            merged.append((head, body, r["kv"].get("xg", "0")))
    with open(out, "w", newline="\n") as f:
        for head, body, _ in merged:
            f.write(head + "\n")
            for ln in body:
                f.write(ln + "\n")
    print("records %d, hash recompute ok %d (mismatch skipped %d), entry had x: %d, exit had x: %d, duplicates dropped %d -> %d unique -> %s" % (
        stats["total"], stats["hash_ok"], bad, stats["entry_x"], stats["exit_x"], stats["dup"], len(merged), out))


if __name__ == "__main__":
    main()
