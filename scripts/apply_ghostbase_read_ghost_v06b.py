from pathlib import Path
import runpy

runpy.run_path(str(Path(__file__).with_name("apply_ghostbase_hide_online_v06a.py")))

def find_base() -> Path:
    cwd = Path.cwd()
    for c in [cwd / "work/swiftgram-src", cwd, cwd.parent / "swiftgram-src"]:
        if (c / "submodules/TelegramCore/Sources/TelegramEngine/Messages/ApplyMaxReadIndexInteractively.swift").exists():
            return c
    raise SystemExit(f"cannot find source base from cwd={cwd}")

def must_replace(s: str, old: str, new: str, name: str) -> str:
    if old not in s:
        raise SystemExit(f"missing replacement point: {name}")
    return s.replace(old, new, 1)

BASE = find_base()

apply_p = BASE / "submodules/TelegramCore/Sources/TelegramEngine/Messages/ApplyMaxReadIndexInteractively.swift"
sync_p = BASE / "submodules/TelegramCore/Sources/State/SynchronizePeerReadState.swift"
controller_p = BASE / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"

apply_s = apply_p.read_text()
sync_s = sync_p.read_text()
controller = controller_p.read_text()

controller = controller.replace("Version: v0.6A", "Version: v0.6B")
controller = controller.replace(
    "Hide Online is active in v0.6A.",
    "Hide Online is active in v0.6A. Read Ghost is active in v0.6B."
)

controller_p.write_text(controller)
print("patched", controller_p)

def ensure_foundation_import(text: str) -> str:
    head = "\n".join(text.splitlines()[:20])
    if "import Foundation" not in head:
        return "import Foundation\n" + text
    return text

# MARK: GhostBase v0.6B robust ApplyMaxReadIndexInteractively patch
if "GhostBase v0.6B Read Ghost local read without remote notify" not in apply_s:
    needle = "stateManager.notifyAppliedIncomingReadMessages([index.id])"
    if needle not in apply_s:
        raise SystemExit("missing replacement point: notifyAppliedIncomingReadMessages call")

    lines = apply_s.splitlines(True)
    out = []
    replaced = False

    for line in lines:
        if not replaced and needle in line:
            indent = line[:len(line) - len(line.lstrip())]
            out.append(f"{indent}// MARK: GhostBase v0.6B Read Ghost local read without remote notify\n")
            out.append(f"{indent}let ghostBaseReadGhost = (UserDefaults.standard.object(forKey: \"GhostBase.GhostMode.ReadMessages\") as? Bool) ?? false\n")
            out.append(f"{indent}if !ghostBaseReadGhost {{\n")
            out.append(f"{indent}    {needle}\n")
            out.append(f"{indent}}}\n")
            replaced = True
        else:
            out.append(line)

    if not replaced:
        raise SystemExit("failed to patch notifyAppliedIncomingReadMessages call")

    apply_s = "".join(out)

apply_s = ensure_foundation_import(apply_s)
apply_p.write_text(apply_s)
print("patched", apply_p)

# MARK: GhostBase v0.6B robust SynchronizePeerReadState patch
if "GhostBase v0.6B Read Ghost remote readHistory guard" not in sync_s:
    lines = sync_s.splitlines(True)
    out = []
    function_seen = False
    inserted = False

    for line in lines:
        out.append(line)

        if not function_seen and "private func pushPeerReadState(" in line:
            function_seen = True

        if function_seen and not inserted and "{" in line:
            indent = "    "
            out.append(f"{indent}// MARK: GhostBase v0.6B Read Ghost remote readHistory guard\n")
            out.append(f"{indent}let ghostBaseReadGhost = (UserDefaults.standard.object(forKey: \"GhostBase.GhostMode.ReadMessages\") as? Bool) ?? false\n")
            out.append(f"{indent}if ghostBaseReadGhost && peerId.namespace != Namespaces.Peer.SecretChat {{\n")
            out.append(f"{indent}    return .single(readState)\n")
            out.append(f"{indent}}}\n\n")
            inserted = True

    if not function_seen:
        raise SystemExit("missing replacement point: pushPeerReadState function")
    if not inserted:
        raise SystemExit("failed to insert pushPeerReadState guard")

    sync_s = "".join(out)

sync_s = ensure_foundation_import(sync_s)
sync_p.write_text(sync_s)
print("patched", sync_p)

apply_s = apply_p.read_text()
sync_s = sync_p.read_text()
controller = controller_p.read_text()

checks = [
    ("version", "Version: v0.6B" in controller),
    ("settings note", "Read Ghost is active in v0.6B" in controller),
    ("apply marker", "GhostBase v0.6B Read Ghost local read without remote notify" in apply_s),
    ("apply key", "GhostBase.GhostMode.ReadMessages" in apply_s),
    ("apply notify guarded", "if !ghostBaseReadGhost" in apply_s),
    ("sync marker", "GhostBase v0.6B Read Ghost remote readHistory guard" in sync_s),
    ("sync key", "GhostBase.GhostMode.ReadMessages" in sync_s),
    ("sync return", "return .single(readState)" in sync_s),
    ("readHistory still present", "readHistory" in sync_s),
    ("readMessageContents untouched", "readMessageContents" not in apply_s),
]

bad = [name for name, ok in checks if not ok]
if bad:
    print("FAILED:")
    for x in bad:
        print("-", x)
    raise SystemExit(1)

print("GhostBase Read Ghost v0.6B patch OK")
