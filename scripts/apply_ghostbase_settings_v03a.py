from pathlib import Path
import runpy

GROUP = "group.4a348a9b186b700c.1"

runpy.run_path(str(Path(__file__).with_name("apply_ghostbase_settings_v02b.py")))

def find_base() -> Path:
    cwd = Path.cwd()
    candidates = [
        cwd / "work/swiftgram-src",
        cwd,
        cwd.parent / "swiftgram-src",
    ]
    for c in candidates:
        if (c / "submodules/SettingsUI/Sources").exists():
            return c
    raise SystemExit(f"cannot find source base from cwd={cwd}")

BASE = find_base()
settings_dir = BASE / "submodules/SettingsUI/Sources/GhostBase"
settings_dir.mkdir(parents=True, exist_ok=True)

controller_p = settings_dir / "GhostBaseSettingsController.swift"
actions_p = BASE / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoScreenSettingsActions.swift"

swift = f'''import Foundation
import UIKit
import Display
import SwiftSignalKit
import TelegramCore
import TelegramPresentationData
import ItemListUI
import AccountContext

private enum GhostBaseSettingsSection: Int32 {{
    case main
}}

private enum GhostBaseSettingsEntry: ItemListNodeEntry {{
    case info(String)

    var section: ItemListSectionId {{
        return GhostBaseSettingsSection.main.rawValue
    }}

    var stableId: Int32 {{
        return 0
    }}

    static func ==(lhs: GhostBaseSettingsEntry, rhs: GhostBaseSettingsEntry) -> Bool {{
        switch lhs {{
        case let .info(lhsText):
            if case let .info(rhsText) = rhs {{
                return lhsText == rhsText
            }}
            return false
        }}
    }}

    static func <(lhs: GhostBaseSettingsEntry, rhs: GhostBaseSettingsEntry) -> Bool {{
        return lhs.stableId < rhs.stableId
    }}

    func item(presentationData: ItemListPresentationData, arguments: Any) -> ListViewItem {{
        switch self {{
        case let .info(text):
            return ItemListTextItem(presentationData: presentationData, text: .plain(text), sectionId: self.section)
        }}
    }}
}}

public func ghostBaseSettingsController(context: AccountContext) -> ViewController {{
    let signal = context.sharedContext.presentationData
    |> deliverOnMainQueue
    |> map {{ presentationData -> (ItemListControllerState, (ItemListNodeState, Any)) in
        let telegramId = String(context.account.peerId.id._internalGetInt64Value())
        let bundleId = Bundle.main.bundleIdentifier ?? "unknown"

        let text = """
Account
Telegram ID: \\(telegramId)
Bundle ID: \\(bundleId)
AppGroup: {GROUP}

Runtime
Base: Official Telegram 12.7
KeychainFix: sideloadKeychainFix.dylib

Build
Version: v0.3A

GhostBase diagnostics screen. Toggles and runtime modules will be added in later builds.
"""

        let controllerState = ItemListControllerState(
            presentationData: ItemListPresentationData(presentationData),
            title: .text("GhostBase"),
            leftNavigationButton: nil,
            rightNavigationButton: nil,
            backNavigationButton: ItemListBackButton(title: presentationData.strings.Common_Back)
        )

        let listState = ItemListNodeState(
            presentationData: ItemListPresentationData(presentationData),
            entries: [GhostBaseSettingsEntry.info(text)],
            style: .blocks,
            animateChanges: false
        )

        return (controllerState, (listState, NSObject()))
    }}

    return ItemListController(context: context, state: signal)
}}
'''

controller_p.write_text(swift)
print("patched", controller_p)

def replace_case(src: str, name: str, body: str):
    lines = src.splitlines(True)
    start = None

    for i, line in enumerate(lines):
        if line.strip() == f"case .{name}:":
            start = i
            break

    if start is None:
        raise SystemExit(f"case .{name} not found")

    end = len(lines)
    for j in range(start + 1, len(lines)):
        if lines[j].startswith("        case ."):
            end = j
            break

    replacement = [f"        case .{name}:\n"] + body.splitlines(True)
    return "".join(lines[:start] + replacement + lines[end:])

s = actions_p.read_text()
s = replace_case(s, "ghostbase", '''            push(ghostBaseSettingsController(context: self.context))
''')
actions_p.write_text(s)
print("patched", actions_p)

actions = actions_p.read_text()
controller = controller_p.read_text()

checks = [
    ("controller function", "public func ghostBaseSettingsController(context: AccountContext)" in controller),
    ("v0.3A marker", "v0.3A" in controller),
    ("action push", "push(ghostBaseSettingsController(context: self.context))" in actions),
    ("no ghostbase alert action", 'title: "GhostBase", text: text' not in actions),
]

bad = [name for name, ok in checks if not ok]
if bad:
    print("FAILED:")
    for x in bad:
        print("-", x)
    raise SystemExit(1)

print("GhostBase Settings v0.3A patch OK")
