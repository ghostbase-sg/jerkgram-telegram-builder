from pathlib import Path
import re

roots = ["Telegram", "submodules", "third-party", "Tests"]
rule = re.compile(r'(?m)^[A-Za-z_][A-Za-z0-9_.]*\(')
cxx = re.compile(r'(?m)^[ \t]*cxxopts[ \t]*=\s*\[[\s\S]*?\],')
copts = re.compile(r'(?m)^[ \t]*copts[ \t]*=')

def patch(text):
    starts = [m.start() for m in rule.finditer(text)] + [len(text)]
    if not starts:
        return text
    out, last = [], 0
    for a, b in zip(starts, starts[1:]):
        out.append(text[last:a])
        seg = text[a:b]
        if "cxxopts" in seg:
            if copts.search(seg):
                seg = cxx.sub("", seg)
            else:
                seg = re.sub(r'(?m)^([ \t]*)cxxopts([ \t]*=)', r'\1copts\2', seg)
        out.append(seg)
        last = b
    out.append(text[last:])
    return "".join(out)

changed = []
for root in roots:
    rp = Path(root)
    if not rp.exists():
        continue
    files = list(rp.rglob("BUILD")) + list(rp.rglob("BUILD.bazel"))
    for p in files:
        if not p.is_file():
            continue
        old = p.read_text(errors="ignore")
        new = patch(old)
        if new != old:
            p.write_text(new)
            changed.append(str(p))

print("\n".join(changed) if changed else "no cxxopts changes")
