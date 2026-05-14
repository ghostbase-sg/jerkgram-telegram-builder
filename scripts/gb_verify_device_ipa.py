from pathlib import Path
import zipfile, plistlib, struct, shutil, sys

BUNDLE = "app.pumpkin6584.lion7414"
out = Path("ghostbase-final")
out.mkdir(exist_ok=True)

ipas = sorted(Path("bazel-bin").rglob("Swiftgram.ipa"))
if not ipas:
    print("ERROR: Swiftgram.ipa not found")
    sys.exit(1)

ipa = ipas[0]
print("IPA:", ipa)

with zipfile.ZipFile(ipa) as z:
    names = z.namelist()
    plist_name = next((n for n in names if n.startswith("Payload/") and n.endswith(".app/Info.plist")), None)
    exe_name = next((n for n in names if n.startswith("Payload/") and n.endswith(".app/Swiftgram")), None)
    profile_name = next((n for n in names if n.startswith("Payload/") and n.endswith(".app/embedded.mobileprovision")), None)

    if not plist_name or not exe_name:
        print("ERROR: IPA missing Info.plist or executable")
        sys.exit(1)

    info = plistlib.loads(z.read(plist_name))
    bid = info.get("CFBundleIdentifier")
    name = info.get("CFBundleDisplayName")

    print("CFBundleIdentifier =", bid)
    print("CFBundleDisplayName =", name)

    if bid != BUNDLE:
        print("ERROR: wrong bundle id")
        sys.exit(1)

    if not profile_name:
        print("ERROR: embedded.mobileprovision missing")
        sys.exit(1)

    b = z.read(exe_name)

magic = struct.unpack("<I", b[:4])[0]
if magic != 0xfeedfacf:
    print("ERROR: not 64-bit little-endian Mach-O")
    sys.exit(1)

_, cputype, _, _, ncmds, _, _, _ = struct.unpack("<IiiIIIII", b[:32])
print("cputype =", hex(cputype))

if cputype != 0x0100000c:
    print("ERROR: not arm64")
    sys.exit(1)

off = 32
platform = None
for _ in range(ncmds):
    cmd, cmdsize = struct.unpack("<II", b[off:off+8])
    if cmd == 0x32:
        platform = struct.unpack("<I", b[off+8:off+12])[0]
        print("LC_BUILD_VERSION platform =", platform)
    off += cmdsize

if platform != 2:
    print("ERROR: not iOS device build")
    sys.exit(1)

final_ipa = out / "GhostBase.ipa"
shutil.copy2(ipa, final_ipa)

(out / "info.txt").write_text(
    f"IPA={ipa}\n"
    f"Final={final_ipa}\n"
    f"CFBundleIdentifier={bid}\n"
    f"CFBundleDisplayName={name}\n"
    f"cputype={hex(cputype)}\n"
    f"platform={platform}\n"
)


    bad_needles = [
        b"app.swiftgram.ios",
        b"group.4a348a9b186b700c.10",
        b"group.app.swiftgram.ios",
    ]

    for bad in bad_needles:
        hits = []
        for n in names:
            if n.startswith("Payload/") and not n.endswith("/"):
                try:
                    data = z.read(n)
                except Exception:
                    continue
                if bad in data:
                    hits.append(n)
        if hits:
            print("ERROR: forbidden leftover found:", bad.decode("utf-8", "ignore"))
            for h in hits[:30]:
                print(h)
            sys.exit(1)

    print("No forbidden Swiftgram/AppGroup leftovers")

print("Device IPA verification OK")
print("Final IPA:", final_ipa)
