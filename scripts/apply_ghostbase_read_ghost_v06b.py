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

old_apply = '''    } else if index.id.peerId.namespace == Namespaces.Peer.CloudUser || index.id.peerId.namespace == Namespaces.Peer.CloudGroup || index.id.peerId.namespace == Namespaces.Peer.CloudChannel {
        stateManager.notifyAppliedIncomingReadMessages([index.id])
    }
'''

new_apply = '''    } else if index.id.peerId.namespace == Namespaces.Peer.CloudUser || index.id.peerId.namespace == Namespaces.Peer.CloudGroup || index.id.peerId.namespace == Namespaces.Peer.CloudChannel {
        // MARK: GhostBase v0.6B Read Ghost local read without remote notify
        let ghostBaseReadGhost = (UserDefaults.standard.object(forKey: "GhostBase.GhostMode.ReadMessages") as? Bool) ?? false
        if !ghostBaseReadGhost {
            stateManager.notifyAppliedIncomingReadMessages([index.id])
        }
    }
'''

apply_s = must_replace(apply_s, old_apply, new_apply, "ApplyMaxReadIndexInteractively read notify")
apply_p.write_text(apply_s)
print("patched", apply_p)

function_marker = "private func pushPeerReadState(network: Network, postbox: Postbox, stateManager: AccountStateManager, peerId: PeerId, readState: PeerReadState) -> Signal<PeerReadState, PeerReadStateValidationError> {\n"

guard_block = '''    // MARK: GhostBase v0.6B Read Ghost remote readHistory guard
    let ghostBaseReadGhost = (UserDefaults.standard.object(forKey: "GhostBase.GhostMode.ReadMessages") as? Bool) ?? false
    if ghostBaseReadGhost && peerId.namespace != Namespaces.Peer.SecretChat {
        return .single(readState)
    }

'''

if function_marker not in sync_s:
    raise SystemExit("missing replacement point: pushPeerReadState function")

if "GhostBase v0.6B Read Ghost remote readHistory guard" not in sync_s:
    sync_s = sync_s.replace(function_marker, function_marker + guard_block, 1)

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
