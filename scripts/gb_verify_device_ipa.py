from pathlib import Path
import plistlib, struct, sys, zipfile

EXPECTED = "app.pumpkin6584.lion7414"

ipa = None
for p in [
    Path("ghostbase-final/GhostBase.ipa"),
    Path("bazel-bin/Telegram/Swiftgram.ipa"),
    Path("Telegram/Swiftgram.ipa"),
]:
    if p.exists():
        ipa = p
        break

if ipa is None:
    print("ERROR: IPA not found")
    sys.exit(1)

print("IPA =", ipa)

with zipfile.ZipFile(ipa) as z:
    names = z.namelist()
    apps = sorted({n.split("/", 2)[1] for n in names if n.startswith("Payload/") and n.count("/") >= 2})
    if not apps:
        print("ERROR: no Payload app")
        sys.exit(1)

    root = "Payload/" + apps[0] + "/"
    info = plistlib.loads(z.read(root + "Info.plist"))

    bid = info.get("CFBundleIdentifier")
    exe_name = info.get("CFBundleExecutable")

    print("CFBundleIdentifier =", bid)
    print("CFBundleDisplayName =", info.get("CFBundleDisplayName"))
    print("CFBundleName =", info.get("CFBundleName"))
    print("CFBundleExecutable =", exe_name)

    if bid != EXPECTED:
        print("ERROR: wrong bundle id")
        sys.exit(1)

    if root + "embedded.mobileprovision" not in names:
        print("ERROR: embedded.mobileprovision missing")
        sys.exit(1)

    exe = z.read(root + exe_name)

    magic = struct.unpack("<I", exe[:4])[0]
    cputype = struct.unpack("<I", exe[4:8])[0]

    print("magic_le =", hex(magic))
    print("cputype =", hex(cputype))

    if magic != 0xFEEDFACF:
        print("ERROR: not 64-bit Mach-O")
        sys.exit(1)

    if cputype != 0x0100000C:
        print("ERROR: not arm64")
        sys.exit(1)

    ncmds = struct.unpack("<I", exe[16:20])[0]
    off = 32
    platform = None

    for _ in range(ncmds):
        if off + 8 > len(exe):
            break
        cmd, size = struct.unpack("<II", exe[off:off+8])
        if cmd == 0x32 and size >= 24:
            platform = struct.unpack("<I", exe[off+8:off+12])[0]
            print("LC_BUILD_VERSION platform =", platform)
        if size <= 0:
            break
        off += size

    if platform != 2:
        print("ERROR: expected iOS device platform=2, got:", platform)
        sys.exit(1)

    bads = [
        b"app.swiftgram.ios",
        b"group.app.swiftgram.ios",
        b"group.4a348a9b186b700c.10",
        b"group.\\(baseAppBundle",
    ]

    for bad in bads:
        hits = []
        for n in names:
            if n.startswith("Payload/") and not n.endswith("/"):
                try:
                    if bad in z.read(n):
                        hits.append(n)
                except Exception:
                    pass
        if hits:
            print("ERROR: forbidden leftover found:", bad.decode("utf-8", "ignore"))
            for h in hits[:20]:
                print(h)
            sys.exit(1)

print("No forbidden Swiftgram/AppGroup leftovers")
print("Device IPA verification OK")
