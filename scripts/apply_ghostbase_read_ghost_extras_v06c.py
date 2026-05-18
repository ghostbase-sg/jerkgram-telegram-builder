from pathlib import Path
import runpy

runpy.run_path(str(Path(__file__).with_name("apply_ghostbase_read_ghost_v06b.py")))

def find_base() -> Path:
    cwd = Path.cwd()
    for c in [cwd / "work/swiftgram-src", cwd, cwd.parent / "swiftgram-src"]:
        if (c / "submodules/TelegramCore/Sources/TelegramEngine/Messages/MarkMessageContentAsConsumedInteractively.swift").exists():
            return c
    raise SystemExit(f"cannot find source base from cwd={cwd}")

def ensure_foundation_import(text: str) -> str:
    head = "\n".join(text.splitlines()[:20])
    if "import Foundation" not in head:
        return "import Foundation\n" + text
    return text

def insert_after_function_open(text: str, function_substring: str, guard_block: str, marker: str, name: str) -> str:
    if marker in text:
        return text

    lines = text.splitlines(True)
    out = []
    seen = False
    inserted = False

    for line in lines:
        out.append(line)

        if not seen and function_substring in line:
            seen = True

        if seen and not inserted and "{" in line:
            out.append(guard_block)
            inserted = True

    if not seen:
        raise SystemExit(f"missing replacement point: {name}")
    if not inserted:
        raise SystemExit(f"failed to insert guard: {name}")

    return "".join(out)

BASE = find_base()

mark_p = BASE / "submodules/TelegramCore/Sources/TelegramEngine/Messages/MarkMessageContentAsConsumedInteractively.swift"
consume_p = BASE / "submodules/TelegramCore/Sources/State/ManagedSynchronizeConsumeMessageContentsOperations.swift"
stories_p = BASE / "submodules/TelegramCore/Sources/TelegramEngine/Messages/Stories.swift"
view_stories_p = BASE / "submodules/TelegramCore/Sources/State/ManagedSynchronizeViewStoriesOperations.swift"
controller_p = BASE / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"

mark_s = mark_p.read_text()
consume_s = consume_p.read_text()
stories_s = stories_p.read_text()
view_stories_s = view_stories_p.read_text()
controller = controller_p.read_text()

# Version / footer
controller = controller.replace("Version: v0.6B", "Version: v0.6C")
controller = controller.replace(
    "Read Ghost is active in v0.6B.",
    "Read Ghost is active in v0.6B. Read Ghost Extras are active in v0.6C."
)
controller_p.write_text(controller)
print("patched", controller_p)

# Voice/circle consumed-content: do not create remote sync operation
marker_mark = "GhostBase v0.6C Read Ghost Extras skip consumed-content sync operation"
if marker_mark not in mark_s:
    needle = "addSynchronizeConsumeMessageContentsOperation(transaction: transaction, messageIds: [message.id])"
    if needle not in mark_s:
        raise SystemExit("missing replacement point: addSynchronizeConsumeMessageContentsOperation")

    lines = mark_s.splitlines(True)
    out = []
    replaced = False

    for line in lines:
        if not replaced and needle in line:
            indent = line[:len(line) - len(line.lstrip())]
            out.append(f"{indent}// MARK: {marker_mark}\n")
            out.append(f"{indent}let ghostBaseReadGhostExtras = (UserDefaults.standard.object(forKey: \"GhostBase.GhostMode.ReadMessages\") as? Bool) ?? false\n")
            out.append(f"{indent}let ghostBaseShouldSuppressConsumedSync = ghostBaseReadGhostExtras && message.id.peerId.namespace != Namespaces.Peer.SecretChat\n")
            out.append(f"{indent}if !ghostBaseShouldSuppressConsumedSync {{\n")
            out.append(f"{indent}    {needle}\n")
            out.append(f"{indent}}}\n")
            replaced = True
        else:
            out.append(line)

    if not replaced:
        raise SystemExit("failed to patch consumed-content sync operation")

    mark_s = "".join(out)

mark_s = ensure_foundation_import(mark_s)
mark_p.write_text(mark_s)
print("patched", mark_p)

# Lower-layer readMessageContents guard
marker_consume = "GhostBase v0.6C Read Ghost Extras remote readMessageContents guard"
consume_guard = '''    // MARK: GhostBase v0.6C Read Ghost Extras remote readMessageContents guard
    let ghostBaseReadGhostExtras = (UserDefaults.standard.object(forKey: "GhostBase.GhostMode.ReadMessages") as? Bool) ?? false
    if ghostBaseReadGhostExtras && peerId.namespace != Namespaces.Peer.SecretChat {
        return .complete()
    }

'''
consume_s = insert_after_function_open(
    consume_s,
    "private func synchronizeConsumeMessageContents(",
    consume_guard,
    marker_consume,
    "synchronizeConsumeMessageContents function",
)
consume_s = ensure_foundation_import(consume_s)
consume_p.write_text(consume_s)
print("patched", consume_p)

# Story mark-as-seen upper-layer guard
marker_story = "GhostBase v0.6C Story Read Ghost markStoryAsSeen guard"
story_guard = '''    // MARK: GhostBase v0.6C Story Read Ghost markStoryAsSeen guard
    let ghostBaseReadGhostExtras = (UserDefaults.standard.object(forKey: "GhostBase.GhostMode.ReadMessages") as? Bool) ?? false
    if ghostBaseReadGhostExtras {
        return .complete()
    }

'''
stories_s = insert_after_function_open(
    stories_s,
    "func _internal_markStoryAsSeen(",
    story_guard,
    marker_story,
    "_internal_markStoryAsSeen function",
)
stories_s = ensure_foundation_import(stories_s)
stories_p.write_text(stories_s)
print("patched", stories_p)

# Lower-layer stories.readStories guard
marker_view_story = "GhostBase v0.6C Story Read Ghost remote readStories guard"
view_story_guard = '''    // MARK: GhostBase v0.6C Story Read Ghost remote readStories guard
    let ghostBaseReadGhostExtras = (UserDefaults.standard.object(forKey: "GhostBase.GhostMode.ReadMessages") as? Bool) ?? false
    if ghostBaseReadGhostExtras {
        return .complete()
    }

'''
view_stories_s = insert_after_function_open(
    view_stories_s,
    "private func pushStoriesAreSeen(",
    view_story_guard,
    marker_view_story,
    "pushStoriesAreSeen function",
)
view_stories_s = ensure_foundation_import(view_stories_s)
view_stories_p.write_text(view_stories_s)
print("patched", view_stories_p)

# Self-check
mark_s = mark_p.read_text()
consume_s = consume_p.read_text()
stories_s = stories_p.read_text()
view_stories_s = view_stories_p.read_text()
controller = controller_p.read_text()

checks = [
    ("version", "Version: v0.6C" in controller),
    ("settings note", "Read Ghost Extras are active in v0.6C" in controller),

    ("mark marker", marker_mark in mark_s),
    ("mark key", "GhostBase.GhostMode.ReadMessages" in mark_s),
    ("mark operation guarded", "if !ghostBaseShouldSuppressConsumedSync" in mark_s),
    ("mark secret skip", "message.id.peerId.namespace != Namespaces.Peer.SecretChat" in mark_s),

    ("consume marker", marker_consume in consume_s),
    ("consume key", "GhostBase.GhostMode.ReadMessages" in consume_s),
    ("readMessageContents still present", "readMessageContents" in consume_s),

    ("story marker", marker_story in stories_s),
    ("story key", "GhostBase.GhostMode.ReadMessages" in stories_s),

    ("remote story marker", marker_view_story in view_stories_s),
    ("remote story key", "GhostBase.GhostMode.ReadMessages" in view_stories_s),
    ("readStories still present", "readStories" in view_stories_s),
]

bad = [name for name, ok in checks if not ok]
if bad:
    print("FAILED:")
    for x in bad:
        print("-", x)
    raise SystemExit(1)

print("GhostBase Read Ghost Extras v0.6C patch OK")
