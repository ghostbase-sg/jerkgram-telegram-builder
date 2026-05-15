from pathlib import Path
import re

BASE = "app.pumpkin6584.lion7414"
GROUP = "group.4a348a9b186b700c.1"
BAD_GROUP_10 = "group.4a348a9b186b700c.10"

roots = [
    Path("Swiftgram"),
    Path("Telegram"),
    Path("submodules/TelegramUI"),
    Path("submodules/WidgetItems"),
    Path("build-system/example-configuration"),
]
changed = []

def is_text_candidate(p: Path) -> bool:
    return (
        p.name in ["BUILD", "BUILD.bazel"]
        or p.suffix in [".swift", ".bzl", ".plist", ".entitlements", ".json", ".m", ".mm", ".h"]
    )

for root in roots:
    if not root.exists():
        continue

    for p in root.rglob("*"):
        if not p.is_file() or not is_text_candidate(p):
            continue

        s = p.read_text(errors="ignore")
        old = s

        s = s.replace("app.swiftgram.ios", BASE)
        s = s.replace("group.app.swiftgram.ios", GROUP)
        s = s.replace("group.org.telegram.Telegram-iOS", GROUP)
        s = s.replace("org.telegram.Telegram-iOS", BASE)

        s = s.replace(r"group.\(baseAppBundleId)0", GROUP)
        s = s.replace(r"group.\(baseAppBundleId)", GROUP)
        s = s.replace(r"group.\(baseAppBundleIdentifier)0", GROUP)
        s = s.replace(r"group.\(baseAppBundleIdentifier)", GROUP)

        s = s.replace(BAD_GROUP_10, GROUP)

        s = re.sub(
            r'(?m)^(\s*)guard\s+let\s+baseAppBundleId\s*=.*?else\s*\{\s*$',
            rf'\1let baseAppBundleId = "{BASE}"\n\1if false {{',
            s
        )

        s = re.sub(
            r'(?m)^(\s*)guard\s+let\s+baseAppBundleIdentifier\s*=.*?else\s*\{\s*$',
            rf'\1let baseAppBundleIdentifier = "{BASE}"\n\1if false {{',
            s
        )

        s = re.sub(
            r'(?m)^(\s*)let\s+baseAppBundleId\s*=.*$',
            rf'\1let baseAppBundleId = "{BASE}"',
            s
        )

        s = re.sub(
            r'(?m)^(\s*)let\s+baseAppBundleIdentifier\s*=.*$',
            rf'\1let baseAppBundleIdentifier = "{BASE}"',
            s
        )

        s = re.sub(
            r'(?m)^(\s*)let\s+appGroupName\s*=.*$',
            rf'\1let appGroupName = "{GROUP}"',
            s
        )

        # Silence Swift strict no-usage after forced constants.


        # Silence strict Swift no-usage for all lastDotRange guard-let blocks.
        lines = s.splitlines(True)
        out = []
        i = 0
        while i < len(lines):
            out.append(lines[i])

            if 'guard let lastDotRange = appBundleIdentifier.range(of: ".", options: [.backwards]) else {' in lines[i]:
                indent = lines[i].split('g')[0]
                depth = lines[i].count("{") - lines[i].count("}")
                j = i + 1

                while j < len(lines):
                    out.append(lines[j])
                    depth += lines[j].count("{") - lines[j].count("}")
                    if depth <= 0:
                        next_line = lines[j + 1] if j + 1 < len(lines) else ""
                        if "_ = lastDotRange" not in next_line:
                            out.append(indent + "_ = lastDotRange\n")
                        i = j
                        break
                    j += 1

            i += 1

        s = "".join(out)


        # Silence strict Swift no-usage for WidgetItems guard-let.
        s = re.sub(
            r'(?m)^(\s*)guard let lastDotRange = appBundleIdentifier\.range\(of: "\.", options: \[\.backwards\]\) else \{\n(\s*)return WidgetPresentationData\.default\n\1\}\n(?!\1_ = lastDotRange\n)',
            r'\1guard let lastDotRange = appBundleIdentifier.range(of: ".", options: [.backwards]) else {\n\2return WidgetPresentationData.default\n\1}\n\1_ = lastDotRange\n',
            s
        )


        for name in ("baseAppBundleId", "baseAppBundleIdentifier", "appGroupName"):
            s = re.sub(
                rf'(?m)^(\s*)let {name} = "([^"]+)"\n(?!\1_ = {name}\n)',
                rf'\1let {name} = "\2"\n\1_ = {name}\n',
                s
            )

        if s != old:
            p.write_text(s)
            changed.append(str(p))

print("patched swift/config files:", len(changed))
for x in changed:
    print(x)

bad = []
for root in roots:
    if not root.exists():
        continue

    for p in root.rglob("*"):
        if not p.is_file() or not is_text_candidate(p):
            continue

        s = p.read_text(errors="ignore")

        if "guard let baseAppBundle" in s:
            bad.append(str(p))
        if "app.swiftgram.ios" in s:
            bad.append(str(p))
        if BAD_GROUP_10 in s:
            bad.append(str(p))
        if r"group.\(baseAppBundle" in s:
            bad.append(str(p))

if bad:
    print("bad Swift/AppGroup leftovers:")
    for x in sorted(set(bad)):
        print(x)
    raise SystemExit(1)

print("Swift/AppGroup patch OK")
