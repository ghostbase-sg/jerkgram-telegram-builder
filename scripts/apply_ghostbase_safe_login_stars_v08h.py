from pathlib import Path
import runpy

VERSION = "v0.8H"

def find_base() -> Path:
    cwd = Path.cwd()
    for c in [cwd / "work/swiftgram-src", cwd, cwd.parent / "swiftgram-src"]:
        if (c / "submodules/AuthorizationUI/Sources/AuthorizationSequencePhoneEntryControllerNode.swift").exists():
            return c
    raise SystemExit(f"[{VERSION}] ERROR: cannot find source base from cwd={cwd}")

def clean(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.splitlines()) + "\n"

def fail(label: str) -> None:
    raise SystemExit(f"[{VERSION}] ERROR: required anchor not found: {label}")

def replace_once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        print(f"[{VERSION}] already patched: {label}")
        return text
    if old not in text:
        fail(label)
    return text.replace(old, new, 1)

def insert_after_line_contains(text: str, contains: str, insertion: str, label: str) -> str:
    if insertion.strip() in text:
        print(f"[{VERSION}] already patched: {label}")
        return text
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if contains in line:
            lines[i + 1:i + 1] = insertion.rstrip("\n").splitlines()
            return "\n".join(lines) + "\n"
    fail(label)

def insert_before_line_contains(text: str, contains: str, insertion: str, label: str) -> str:
    if insertion.strip() in text:
        print(f"[{VERSION}] already patched: {label}")
        return text
    lines = text.splitlines()
    for i, line in enumerate(lines):
        if contains in line:
            lines[i:i] = insertion.rstrip("\n").splitlines()
            return "\n".join(lines) + "\n"
    fail(label)

def insert_args_before_state_init_close(text: str, insertion: str, label: str) -> str:
    if insertion.strip() in text:
        print(f"[{VERSION}] already patched: {label}")
        return text
    start = text.find("return GhostBaseSettingsState(")
    if start < 0:
        fail(label + " init start")
    depth = 0
    close = -1
    for i in range(start, len(text)):
        if text[i] == "(":
            depth += 1
        elif text[i] == ")":
            depth -= 1
            if depth == 0:
                close = i
                break
    if close < 0:
        fail(label + " init close")
    before = text[:close]
    after = text[close:]
    if before.rstrip() and not before.rstrip().endswith(","):
        before = before.rstrip() + ",\n"
    return before + insertion.rstrip("\n") + "\n" + after

def insert_before_func_end(text: str, func_marker: str, insertion: str, label: str) -> str:
    if insertion.strip() in text:
        print(f"[{VERSION}] already patched: {label}")
        return text
    start = text.find(func_marker)
    if start < 0:
        fail(label + " func start")
    brace = text.find("{", start)
    if brace < 0:
        fail(label + " func brace")
    depth = 0
    close = -1
    for i in range(brace, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                close = i
                break
    if close < 0:
        fail(label + " func close")
    return text[:close] + insertion.rstrip("\n") + "\n" + text[close:]

BASE = find_base()

v08g_p = Path(__file__).with_name("apply_ghostbase_onetime_media_v08g.py")
if not v08g_p.exists():
    raise SystemExit(f"[{VERSION}] ERROR: missing prerequisite {v08g_p}")

settings_p = BASE / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
auth_p = BASE / "submodules/AuthorizationUI/Sources/AuthorizationSequencePhoneEntryControllerNode.swift"

settings_existing = settings_p.read_text(errors="ignore") if settings_p.exists() else ""
if "Version: v0.8H" in settings_existing and "GhostBase.Stars.LocalBalance.Enabled" in settings_existing:
    print(f"[{VERSION}] v0.8H already applied; skip prerequisite replay")
elif "Version: v0.8G" in settings_existing and "GhostBase.ProtectedContent.OneTimeSave" in settings_existing:
    print(f"[{VERSION}] v0.8G chain already applied; skip prerequisite replay")
else:
    runpy.run_path(str(v08g_p))

settings = settings_p.read_text()
auth = auth_p.read_text()

# MARK: GhostBase v0.8H Stars Settings Phase 1
import re

settings = settings.replace("Version: v0.8G", "Version: v0.8H")

settings = insert_after_line_contains(
    settings,
    'static let oneTimeSave = "GhostBase.ProtectedContent.OneTimeSave"',
    '''    static let localStarsEnabled = "GhostBase.Stars.LocalBalance.Enabled"
    static let localStarsAmount = "GhostBase.Stars.LocalBalance.Amount"
''',
    "stars keys"
)

settings = insert_after_line_contains(
    settings,
    "private func ghostBaseBool",
    '''private func ghostBaseString(_ key: String, defaultValue: String) -> String {
    if let value = UserDefaults.standard.object(forKey: key) as? String {
        return value
    }
    return defaultValue
}

private func ghostBaseSanitizeStarsAmount(_ text: String) -> String {
    var result = ""
    for ch in text {
        if ch == "-" && result.isEmpty {
            result.append(ch)
        } else if ch >= "0" && ch <= "9" {
            result.append(ch)
        }
    }
    if result.count > 20 {
        result = String(result.prefix(20))
    }
    return result
}

''',
    "stars string/sanitize helpers"
)

settings = insert_before_line_contains(
    settings,
    "static func load()",
    '''    var localStarsEnabled: Bool
    var localStarsAmount: String

''',
    "stars state vars"
)

settings = insert_args_before_state_init_close(
    settings,
    '''            localStarsEnabled: ghostBaseBool(GhostBaseKey.localStarsEnabled, defaultValue: false),
            localStarsAmount: ghostBaseString(GhostBaseKey.localStarsAmount, defaultValue: "0")''',
    "stars load"
)

settings = insert_before_func_end(
    settings,
    "func save()",
    '''        UserDefaults.standard.set(self.localStarsEnabled, forKey: GhostBaseKey.localStarsEnabled)
        UserDefaults.standard.set(self.localStarsAmount, forKey: GhostBaseKey.localStarsAmount)
''',
    "stars save"
)

settings = settings.replace(
    "    case protectedContent\n    case debug",
    "    case protectedContent\n    case stars\n    case debug"
)

settings = settings.replace(
    "    case toggle(Int32, Int32, String, String, Bool)\n    case info",
    "    case toggle(Int32, Int32, String, String, Bool)\n    case input(Int32, Int32, String, String, String)\n    case info"
)

settings = settings.replace(
    '''        case let .toggle(section, _, _, _, _):
            return section
        case let .info(section, _):''',
    '''        case let .toggle(section, _, _, _, _):
            return section
        case let .input(section, _, _, _, _):
            return section
        case let .info(section, _):'''
)

settings = settings.replace(
    '''        case let .toggle(section, index, _, _, _):
            return section * 1000 + index
        case let .info(section, _):''',
    '''        case let .toggle(section, index, _, _, _):
            return section * 1000 + index
        case let .input(section, index, _, _, _):
            return section * 1000 + index
        case let .info(section, _):'''
)

settings = settings.replace(
    '''        case let .toggle(ls, li, lk, lt, lv):
            if case let .toggle(rs, ri, rk, rt, rv) = rhs {
                return ls == rs && li == ri && lk == rk && lt == rt && lv == rv
            } else {
                return false
            }
        case let .info(ls, lt):''',
    '''        case let .toggle(ls, li, lk, lt, lv):
            if case let .toggle(rs, ri, rk, rt, rv) = rhs {
                return ls == rs && li == ri && lk == rk && lt == rt && lv == rv
            } else {
                return false
            }
        case let .input(ls, li, lk, lt, lv):
            if case let .input(rs, ri, rk, rt, rv) = rhs {
                return ls == rs && li == ri && lk == rk && lt == rt && lv == rv
            } else {
                return false
            }
        case let .info(ls, lt):'''
)

settings = settings.replace(
    '''        case let .toggle(_, _, key, title, value):
            return ItemListSwitchItem(''',
    '''        case let .input(_, _, key, title, text):
            return ItemListSingleLineInputItem(
                presentationData: presentationData,
                title: NSAttributedString(string: title, textColor: presentationData.theme.list.itemPrimaryTextColor),
                text: text,
                placeholder: "0",
                type: .regular(capitalization: false, autocorrection: false),
                clearType: .onFocus,
                maxLength: 20,
                sectionId: self.section,
                textUpdated: { updatedText in
                    UserDefaults.standard.set(ghostBaseSanitizeStarsAmount(updatedText), forKey: key)
                },
                shouldUpdateText: { updatedText in
                    return ghostBaseSanitizeStarsAmount(updatedText) == updatedText
                },
                action: {}
            )

        case let .toggle(_, _, key, title, value):
            return ItemListSwitchItem('''
)

settings = insert_after_line_contains(
    settings,
    "let protected = GhostBaseSettingsSection.protectedContent.rawValue",
    "    let stars = GhostBaseSettingsSection.stars.rawValue",
    "stars section var"
)

settings = insert_before_line_contains(
    settings,
    "    let telegramId = String(context.account.peerId.id._internalGetInt64Value())",
    '''    entries.append(.header(stars, "Stars"))
    entries.append(.toggle(stars, 1, GhostBaseKey.localStarsEnabled, "Enable Local Stars Balance", state.localStarsEnabled))
    entries.append(.input(stars, 2, GhostBaseKey.localStarsAmount, "Stars Amount", state.localStarsAmount))
    entries.append(.info(stars, "Local Stars Balance is visual only. It does not change your real Telegram balance or payments. Negative values are allowed for local display experiments."))

''',
    "stars entries"
)

settings = insert_after_line_contains(
    settings,
    "case GhostBaseKey.oneTimeSave:",
    '''            case GhostBaseKey.localStarsEnabled:
                updated.localStarsEnabled = value
''',
    "stars update case"
)

# MARK: GhostBase v0.8H final write/check

# MARK: GhostBase v0.8H Safe Login Ghost button

auth = insert_before_line_contains(
    auth,
    'final class AuthorizationSequencePhoneEntryControllerNode: ASDisplayNode',
    '''private let ghostBaseSafeLoginEnabledKey = "GhostBase.SafeLogin.GhostModeEnabled"

private let ghostBaseSafeLoginGhostModeKeys: [String] = [
    "GhostBase.GhostMode.ReadMessages",
    "GhostBase.GhostMode.TypingActions",
    "GhostBase.GhostMode.RecordingActions",
    "GhostBase.GhostMode.UploadingActions",
    "GhostBase.GhostMode.StickerActivity",
    "GhostBase.GhostMode.GameActivity",
    "GhostBase.GhostMode.EmojiActivity",
    "GhostBase.GhostMode.Presence"
]

private func ghostBaseSafeLoginInitialEnabled() -> Bool {
    if let value = UserDefaults.standard.object(forKey: ghostBaseSafeLoginEnabledKey) as? Bool {
        return value
    }
    return true
}

private func ghostBaseSafeLoginApply(enabled: Bool) {
    UserDefaults.standard.set(enabled, forKey: ghostBaseSafeLoginEnabledKey)
    for key in ghostBaseSafeLoginGhostModeKeys {
        UserDefaults.standard.set(enabled, forKey: key)
    }
}

private func ghostBaseSafeLoginButtonTitle(_ enabled: Bool) -> String {
    return enabled ? "👻 Ghost Mode: ON" : "👻 Ghost Mode: OFF"
}

''',
    "safe login helpers"
)

auth = insert_after_line_contains(
    auth,
    'proceedNode: SolidRoundedButtonNode',
    '''    private let ghostBaseSafeLoginInfoNode: ImmediateTextNode
    private let ghostBaseSafeLoginNode: SolidRoundedButtonNode
    private var ghostBaseSafeLoginEnabled: Bool
''',
    "safe login properties"
)

auth = replace_once(
    auth,
    '''        self.proceedNode = SolidRoundedButtonNode(title: self.strings.Login_Continue, theme: SolidRoundedButtonTheme(theme: self.theme), glass: false, height: 50.0, cornerRadius: 50 * 0.5)
        self.proceedNode.progressType = .embedded
        self.proceedNode.isEnabled = false
        self.proceedNode.accessibilityIdentifier = "Auth.PhoneEntry.ContinueButton"''',
    '''        self.proceedNode = SolidRoundedButtonNode(title: self.strings.Login_Continue, theme: SolidRoundedButtonTheme(theme: self.theme), glass: false, height: 50.0, cornerRadius: 50 * 0.5)
        self.proceedNode.progressType = .embedded
        self.proceedNode.isEnabled = false
        self.proceedNode.accessibilityIdentifier = "Auth.PhoneEntry.ContinueButton"

        // MARK: GhostBase v0.8H Safe Login init
        let ghostBaseInitialSafeLoginEnabled = ghostBaseSafeLoginInitialEnabled()
        self.ghostBaseSafeLoginEnabled = ghostBaseInitialSafeLoginEnabled
        ghostBaseSafeLoginApply(enabled: ghostBaseInitialSafeLoginEnabled)

        self.ghostBaseSafeLoginInfoNode = ImmediateTextNode()
        self.ghostBaseSafeLoginInfoNode.maximumNumberOfLines = 2
        self.ghostBaseSafeLoginInfoNode.textAlignment = .center
        self.ghostBaseSafeLoginInfoNode.attributedText = NSAttributedString(string: "Enable before login to stay invisible from the first session.", font: Font.regular(13.0), textColor: self.theme.list.itemPrimaryTextColor.withAlphaComponent(0.65))

        self.ghostBaseSafeLoginNode = SolidRoundedButtonNode(title: ghostBaseSafeLoginButtonTitle(ghostBaseInitialSafeLoginEnabled), theme: SolidRoundedButtonTheme(theme: self.theme), glass: false, height: 50.0, cornerRadius: 50.0 * 0.5)
        self.ghostBaseSafeLoginNode.accessibilityIdentifier = "Auth.PhoneEntry.GhostModeButton"''',
    "safe login init nodes"
)

auth = replace_once(
    auth,
    '''        self.addSubnode(self.contactSyncNode)
        self.addSubnode(self.proceedNode)
        self.addSubnode(self.animationNode)''',
    '''        self.addSubnode(self.contactSyncNode)
        self.addSubnode(self.proceedNode)
        self.addSubnode(self.ghostBaseSafeLoginInfoNode)
        self.addSubnode(self.ghostBaseSafeLoginNode)
        self.addSubnode(self.animationNode)''',
    "safe login add subnodes"
)

auth = replace_once(
    auth,
    '''        self.proceedNode.pressed = { [weak self] in
            self?.checkPhone?()
        }''',
    '''        self.proceedNode.pressed = { [weak self] in
            self?.checkPhone?()
        }

        self.ghostBaseSafeLoginNode.pressed = { [weak self] in
            guard let strongSelf = self else {
                return
            }
            strongSelf.ghostBaseSafeLoginEnabled = !strongSelf.ghostBaseSafeLoginEnabled
            ghostBaseSafeLoginApply(enabled: strongSelf.ghostBaseSafeLoginEnabled)
            strongSelf.ghostBaseSafeLoginNode.animateTitle(to: ghostBaseSafeLoginButtonTitle(strongSelf.ghostBaseSafeLoginEnabled))
        }''',
    "safe login pressed"
)

auth = replace_once(
    auth,
    '''        let additionalBottomInset: CGFloat = layout.size.width > 320.0 ? 80.0 : 10.0''',
    '''        let ghostBaseSafeLoginExtraBottomInset: CGFloat = layout.size.width > 320.0 ? 88.0 : 0.0
        let additionalBottomInset: CGFloat = (layout.size.width > 320.0 ? 80.0 : 10.0) + ghostBaseSafeLoginExtraBottomInset''',
    "safe login extra bottom inset"
)

auth = replace_once(
    auth,
    '''        let proceedHeight = self.proceedNode.updateLayout(width: maximumWidth - inset * 2.0, transition: transition)
        let proceedSize = CGSize(width: maximumWidth - inset * 2.0, height: proceedHeight)''',
    '''        let proceedHeight = self.proceedNode.updateLayout(width: maximumWidth - inset * 2.0, transition: transition)
        let proceedSize = CGSize(width: maximumWidth - inset * 2.0, height: proceedHeight)
        let ghostBaseSafeLoginInfoSize = self.ghostBaseSafeLoginInfoNode.updateLayout(CGSize(width: proceedSize.width, height: CGFloat.greatestFiniteMagnitude))
        let ghostBaseSafeLoginHeight = self.ghostBaseSafeLoginNode.updateLayout(width: proceedSize.width, transition: transition)''',
    "safe login layout sizes"
)

auth = replace_once(
    auth,
    '''        transition.updateFrame(node: self.proceedNode, frame: buttonFrame)''',
    '''        transition.updateFrame(node: self.proceedNode, frame: buttonFrame)

        // MARK: GhostBase v0.8H Safe Login layout
        let ghostBaseSafeLoginButtonFrame = CGRect(origin: CGPoint(x: buttonFrame.minX, y: buttonFrame.minY - 10.0 - ghostBaseSafeLoginHeight), size: CGSize(width: proceedSize.width, height: ghostBaseSafeLoginHeight))
        let ghostBaseSafeLoginInfoFrame = CGRect(origin: CGPoint(x: buttonFrame.minX, y: ghostBaseSafeLoginButtonFrame.minY - 6.0 - ghostBaseSafeLoginInfoSize.height), size: ghostBaseSafeLoginInfoSize)
        transition.updateFrame(node: self.ghostBaseSafeLoginNode, frame: ghostBaseSafeLoginButtonFrame)
        transition.updateFrame(node: self.ghostBaseSafeLoginInfoNode, frame: ghostBaseSafeLoginInfoFrame)
        self.ghostBaseSafeLoginNode.isHidden = self.proceedNode.isHidden
        self.ghostBaseSafeLoginInfoNode.isHidden = self.proceedNode.isHidden''',
    "safe login layout frames"
)

auth_checks = [
    ("safe login helpers", "ghostBaseSafeLoginApply" in auth and "GhostBase.GhostMode.Presence" in auth),
    ("safe login node", "ghostBaseSafeLoginInfoNode" in auth and "ghostBaseSafeLoginNode" in auth),
    ("safe login default on", "return true" in auth and "ghostBaseInitialSafeLoginEnabled" in auth),
    ("safe login button title", "👻 Ghost Mode: ON" in auth and "👻 Ghost Mode: OFF" in auth),
    ("safe login animate title", "animateTitle(to:" in auth),
    ("safe login layout", "GhostBase v0.8H Safe Login layout" in auth),
]

bad_auth = [name for name, ok in auth_checks if not ok]
if bad_auth:
    print(f"[{VERSION}] FAILED Safe Login:")
    for name in bad_auth:
        print("-", name)
    raise SystemExit(1)


# MARK: GhostBase v0.8H hard normalize Settings before write

# 1) Deduplicate generated .input item case blocks.
input_marker = "        case let .input(_, _, key, title, text):"
while settings.count(input_marker) > 1:
    first = settings.find(input_marker)
    second = settings.find(input_marker, first + 1)
    next_case = settings.find("\n        case let .toggle", second)
    if second < 0 or next_case < 0:
        fail("hard normalize duplicate input item")
    settings = settings[:second] + settings[next_case + 1:]

# 2) Ensure Equatable has .input comparison before .info.
if "case let .input(ls, li, lk, lt, lv):" not in settings:
    eq_anchor = """        case let .info(ls, lt):
            if case let .info(rs, rt) = rhs {"""
    eq_insert = """        case let .input(ls, li, lk, lt, lv):
            if case let .input(rs, ri, rk, rt, rv) = rhs {
                return ls == rs && li == ri && lk == rk && lt == rt && lv == rv
            } else {
                return false
            }
        case let .info(ls, lt):
            if case let .info(rs, rt) = rhs {"""
    if eq_anchor not in settings:
        fail("hard normalize input equality")
    settings = settings.replace(eq_anchor, eq_insert, 1)

# 3) Fix malformed oneTimeSave/localStarsEnabled update cases.
broken_update = """            case GhostBaseKey.oneTimeSave:
            case GhostBaseKey.localStarsEnabled:
                updated.localStarsEnabled = value
                updated.oneTimeSave = value
            case GhostBaseKey.readMessages:"""

fixed_update = """            case GhostBaseKey.oneTimeSave:
                updated.oneTimeSave = value
            case GhostBaseKey.localStarsEnabled:
                updated.localStarsEnabled = value
            case GhostBaseKey.readMessages:"""

if broken_update in settings:
    settings = settings.replace(broken_update, fixed_update, 1)

if "case GhostBaseKey.oneTimeSave:\n            case GhostBaseKey.localStarsEnabled:" in settings:
    fail("hard normalize malformed stars update cases")


settings_p.write_text(clean(settings))
auth_p.write_text(clean(auth))

settings = settings_p.read_text()
auth = auth_p.read_text()

checks = [
    ("settings version", "Version: v0.8H" in settings),
    ("stars keys", "GhostBase.Stars.LocalBalance.Enabled" in settings and "GhostBase.Stars.LocalBalance.Amount" in settings),
    ("stars state", "var localStarsEnabled: Bool" in settings and "var localStarsAmount: String" in settings),
    ("stars input", "ItemListSingleLineInputItem" in settings and "Stars Amount" in settings),
    ("stars negative sanitize", "ghostBaseSanitizeStarsAmount" in settings and 'ch == "-"' in settings),
    ("stars section", "case stars" in settings and 'entries.append(.header(stars, "Stars"))' in settings),
    ("stars input item not duplicated", settings.count("case let .input(_, _, key, title, text):") == 1),
    ("stars input equality", "case let .input(ls, li, lk, lt, lv):" in settings),
    ("stars update cases sane", "case GhostBaseKey.oneTimeSave:\n                updated.oneTimeSave = value\n            case GhostBaseKey.localStarsEnabled:\n                updated.localStarsEnabled = value" in settings),
    ("v0.8G preserved", "Allow One-Time Screenshots" in settings and "Allow One-Time Save" in settings),
]

bad = [name for name, ok in checks if not ok]
if bad:
    print(f"[{VERSION}] FAILED:")
    for name in bad:
        print("-", name)
    raise SystemExit(1)

print("GhostBase Safe Login + Stars v0.8H patch OK")
