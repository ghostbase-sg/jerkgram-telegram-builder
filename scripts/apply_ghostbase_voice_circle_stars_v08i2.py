from pathlib import Path
import runpy

VERSION = "v0.8I.2"

def find_base() -> Path:
    cwd = Path.cwd()
    for c in [cwd / "work/swiftgram-src", cwd, cwd.parent / "swiftgram-src"]:
        if (c / "submodules/TelegramCore/Sources/TelegramEngine/Messages/MarkMessageContentAsConsumedInteractively.swift").exists():
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
    print(f"[{VERSION}] patch {label}")
    return text.replace(old, new, 1)

def replace_exact_count(text: str, old: str, new: str, expected_count: int, label: str) -> str:
    if new in text and old not in text:
        print(f"[{VERSION}] already patched: {label}")
        return text
    count = text.count(old)
    if count != expected_count:
        raise SystemExit(f"[{VERSION}] ERROR: {label}: expected {expected_count} replacement(s), found {count}")
    print(f"[{VERSION}] patch {label}: {count} replacement(s)")
    return text.replace(old, new)

BASE = find_base()

prev = Path(__file__).with_name("apply_ghostbase_onetime_timed_save_repair_v08i1.py")
if not prev.exists():
    raise SystemExit(f"[{VERSION}] ERROR: missing prerequisite {prev}")

settings_p = BASE / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
consume_p = BASE / "submodules/TelegramCore/Sources/TelegramEngine/Messages/MarkMessageContentAsConsumedInteractively.swift"
stars_balance_p = BASE / "submodules/TelegramUI/Components/Stars/StarsTransactionsScreen/Sources/StarsBalanceComponent.swift"
stars_screen_p = BASE / "submodules/TelegramUI/Components/Stars/StarsTransactionsScreen/Sources/StarsTransactionsScreen.swift"
secret_p = BASE / "submodules/GalleryUI/Sources/SecretMediaPreviewController.swift"

settings_existing = settings_p.read_text(errors="ignore") if settings_p.exists() else ""
if "Version: v0.8I.2" in settings_existing:
    print(f"[{VERSION}] v0.8I.2 already applied; skip prerequisite replay")
elif "Version: v0.8I.1" in settings_existing:
    print(f"[{VERSION}] v0.8I.1 chain already applied; skip prerequisite replay")
else:
    runpy.run_path(str(prev))

settings = settings_p.read_text()
consume = consume_p.read_text()
stars_balance = stars_balance_p.read_text()
stars_screen = stars_screen_p.read_text()
secret = secret_p.read_text()

# MARK: version
while "Version: v0.8I.2.2" in settings or "Version: v0.8I.2.1" in settings:
    settings = settings.replace("Version: v0.8I.2.2", "Version: v0.8I.2").replace("Version: v0.8I.2.1", "Version: v0.8I.2")
if "Version: v0.8I.2" not in settings:
    settings = settings.replace("Version: v0.8I.1", "Version: v0.8I.2")

# MARK: Voice/Circle local keep
old_voice_circle = '''} else if let file = updatedMedia[i] as? TelegramMediaFile {
                                    if file.isInstantVideo {
                                        updatedMedia[i] = TelegramMediaExpiredContent(data: .videoMessage)
                                    } else if file.isVoice {
                                        updatedMedia[i] = TelegramMediaExpiredContent(data: .voiceMessage)
                                    } else {
                                        updatedMedia[i] = TelegramMediaExpiredContent(data: .file)
                                    }
                                }'''

new_voice_circle = '''} else if let file = updatedMedia[i] as? TelegramMediaFile {
                                    // MARK: GhostBase v0.8I.2 voice/circle local keep
                                    let ghostBaseKeepVoiceCircleLocal = (((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.Enabled") as? Bool) ?? true) && ((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.OneTimeSave") as? Bool) ?? false) && message.id.peerId.namespace != Namespaces.Peer.SecretChat && (file.isInstantVideo || file.isVoice))
                                    if file.isInstantVideo {
                                        if !ghostBaseKeepVoiceCircleLocal {
                                            updatedMedia[i] = TelegramMediaExpiredContent(data: .videoMessage)
                                        }
                                    } else if file.isVoice {
                                        if !ghostBaseKeepVoiceCircleLocal {
                                            updatedMedia[i] = TelegramMediaExpiredContent(data: .voiceMessage)
                                        }
                                    } else {
                                        updatedMedia[i] = TelegramMediaExpiredContent(data: .file)
                                    }
                                }'''

consume = replace_exact_count(
    consume,
    old_voice_circle,
    new_voice_circle,
    2,
    "voice/circle expired-media local keep"
)

# MARK: Stars helper in StarsBalanceComponent
stars_balance_helper = '''private func ghostBaseLocalStarsAmountForDisplay() -> StarsAmount? {
    guard ((UserDefaults.standard.object(forKey: "GhostBase.Stars.LocalBalance.Enabled") as? Bool) ?? false) else {
        return nil
    }
    guard let rawValue = UserDefaults.standard.object(forKey: "GhostBase.Stars.LocalBalance.Amount") as? String else {
        return nil
    }
    let value = rawValue.trimmingCharacters(in: .whitespacesAndNewlines)
    guard let intValue = Int64(value) else {
        return nil
    }
    return StarsAmount(value: intValue, nanos: 0)
}

'''

if "private func ghostBaseLocalStarsAmountForDisplay() -> StarsAmount?" not in stars_balance:
    stars_balance = replace_once(
        stars_balance,
        '''import TelegramCore

final class StarsBalanceComponent: Component {''',
        '''import TelegramCore

''' + stars_balance_helper + '''final class StarsBalanceComponent: Component {''',
        "stars balance helper"
    )
else:
    print(f"[{VERSION}] already patched: stars balance helper")

stars_balance = replace_once(
    stars_balance,
    '''            case .stars:
                formattedLabel = formatStarsAmountText(component.count, dateTimeFormat: component.dateTimeFormat)''',
    '''            case .stars:
                let ghostBaseStarsCount = ghostBaseLocalStarsAmountForDisplay() ?? component.count
                formattedLabel = formatStarsAmountText(ghostBaseStarsCount, dateTimeFormat: component.dateTimeFormat)''',
    "StarsBalanceComponent visual local count"
)

# MARK: Stars helper in StarsTransactionsScreen
stars_screen_helper = '''private func ghostBaseLocalStarsAmountForDisplay() -> StarsAmount? {
    guard ((UserDefaults.standard.object(forKey: "GhostBase.Stars.LocalBalance.Enabled") as? Bool) ?? false) else {
        return nil
    }
    guard let rawValue = UserDefaults.standard.object(forKey: "GhostBase.Stars.LocalBalance.Amount") as? String else {
        return nil
    }
    let value = rawValue.trimmingCharacters(in: .whitespacesAndNewlines)
    guard let intValue = Int64(value) else {
        return nil
    }
    return StarsAmount(value: intValue, nanos: 0)
}

'''

if "private func ghostBaseLocalStarsAmountForDisplay() -> StarsAmount?" not in stars_screen:
    stars_screen = replace_once(
        stars_screen,
        '''import StatisticsUI

private let initialSubscriptionsDisplayedLimit: Int32 = 3''',
        '''import StatisticsUI

''' + stars_screen_helper + '''private let initialSubscriptionsDisplayedLimit: Int32 = 3''',
        "stars transactions helper"
    )
else:
    print(f"[{VERSION}] already patched: stars transactions helper")

stars_screen = replace_once(
    stars_screen,
    '''                formattedBalance = formatStarsAmountText(self.starsState?.balance ?? StarsAmount.zero, dateTimeFormat: environment.dateTimeFormat)''',
    '''                formattedBalance = formatStarsAmountText(ghostBaseLocalStarsAmountForDisplay() ?? self.starsState?.balance ?? StarsAmount.zero, dateTimeFormat: environment.dateTimeFormat)''',
    "stars transactions top balance visual"
)

stars_screen = replace_once(
    stars_screen,
    '''                            count: self.starsState?.balance ?? StarsAmount.zero,''',
    '''                            count: ghostBaseLocalStarsAmountForDisplay() ?? self.starsState?.balance ?? StarsAmount.zero,''',
    "stars transactions main balance visual"
)

# MARK: final write/check
settings_p.write_text(clean(settings))
consume_p.write_text(clean(consume))
stars_balance_p.write_text(clean(stars_balance))
stars_screen_p.write_text(clean(stars_screen))

settings = settings_p.read_text()
consume = consume_p.read_text()
stars_balance = stars_balance_p.read_text()
stars_screen = stars_screen_p.read_text()
secret = secret_p.read_text()

checks = [
    ("version", "Version: v0.8I.2" in settings and "Version: v0.8I.2.1" not in settings and "Version: v0.8I.2.2" not in settings),
    ("voice/circle keep", consume.count("GhostBase v0.8I.2 voice/circle local keep") == 2 and "ghostBaseKeepVoiceCircleLocal" in consume),
    ("stars balance helper", "ghostBaseLocalStarsAmountForDisplay" in stars_balance),
    ("stars balance visual", "let ghostBaseStarsCount = ghostBaseLocalStarsAmountForDisplay() ?? component.count" in stars_balance),
    ("stars screen helper", "ghostBaseLocalStarsAmountForDisplay" in stars_screen),
    ("stars screen top visual", "formatStarsAmountText(ghostBaseLocalStarsAmountForDisplay() ?? self.starsState?.balance ?? StarsAmount.zero" in stars_screen),
    ("stars screen main visual", "count: ghostBaseLocalStarsAmountForDisplay() ?? self.starsState?.balance ?? StarsAmount.zero" in stars_screen),
    ("no invalid SecretMediaPreview save signature", "saveToCameraRoll(context: self.context, postbox:" not in secret),
]

for generated_text, generated_label in [
    (consume, "consume"),
    (stars_balance, "stars balance"),
    (stars_screen, "stars screen"),
]:
    for line in generated_text.splitlines():
        if (
            "ghostBaseKeepVoiceCircleLocal =" in line
            or "ghostBaseLocalStarsAmountForDisplay()" in line
            or "let ghostBaseStarsCount =" in line
        ):
            balance = line.count("(") - line.count(")")
            if balance != 0:
                raise SystemExit(f"[{VERSION}] FAILED: unbalanced generated Swift line in {generated_label}: {line}")

bad = [name for name, ok in checks if not ok]
if bad:
    print(f"[{VERSION}] FAILED:")
    for name in bad:
        print("-", name)
    raise SystemExit(1)

print("GhostBase Voice/Circle Local Keep + Stars Visual v0.8I.2 patch OK")
