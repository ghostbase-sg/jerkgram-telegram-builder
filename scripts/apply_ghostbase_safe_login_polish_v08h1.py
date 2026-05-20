from pathlib import Path
import runpy

VERSION = "v0.8H.1"

def find_base() -> Path:
    cwd = Path.cwd()
    for c in [cwd / "work/swiftgram-src", cwd, cwd.parent / "swiftgram-src"]:
        if (c / "submodules/AuthorizationUI/Sources/AuthorizationSequenceSplashController.swift").exists():
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

BASE = find_base()

v08h_p = Path(__file__).with_name("apply_ghostbase_safe_login_stars_v08h.py")
if not v08h_p.exists():
    raise SystemExit(f"[{VERSION}] ERROR: missing prerequisite {v08h_p}")

settings_p = BASE / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
phone_p = BASE / "submodules/AuthorizationUI/Sources/AuthorizationSequencePhoneEntryControllerNode.swift"
splash_p = BASE / "submodules/AuthorizationUI/Sources/AuthorizationSequenceSplashController.swift"
rmintro_p = BASE / "submodules/RMIntro/Sources/platform/ios/RMIntroViewController.m"
secret_preview_p = BASE / "submodules/GalleryUI/Sources/SecretMediaPreviewController.swift"
interactive_media_p = BASE / "submodules/TelegramUI/Components/Chat/ChatMessageInteractiveMediaNode/Sources/ChatMessageInteractiveMediaNode.swift"

settings_existing = settings_p.read_text(errors="ignore") if settings_p.exists() else ""
if "Version: v0.8H.1" in settings_existing:
    print(f"[{VERSION}] v0.8H.1 already applied; skip prerequisite replay")
elif "Version: v0.8H" in settings_existing and "GhostBase.Stars.LocalBalance.Enabled" in settings_existing:
    print(f"[{VERSION}] v0.8H chain already applied; skip prerequisite replay")
else:
    runpy.run_path(str(v08h_p))

settings = settings_p.read_text()
phone = phone_p.read_text()
splash = splash_p.read_text()
rmintro = rmintro_p.read_text()
secret_preview = secret_preview_p.read_text()
interactive_media = interactive_media_p.read_text()

# MARK: GhostBase v0.8H.1 Safe Login polish

while "Version: v0.8H.1.1" in settings:
    settings = settings.replace("Version: v0.8H.1.1", "Version: v0.8H.1")
if "Version: v0.8H.1" not in settings:
    settings = settings.replace("Version: v0.8H", "Version: v0.8H.1")

splash = insert_before_line_contains(
    splash,
    "public final class AuthorizationSequenceSplashController: ViewController",
    '''private let ghostBaseSplashSafeLoginEnabledKey = "GhostBase.SafeLogin.GhostModeEnabled"

private let ghostBaseSplashGhostModeKeys: [String] = [
    "GhostBase.GhostMode.ReadMessages",
    "GhostBase.GhostMode.TypingActions",
    "GhostBase.GhostMode.RecordingActions",
    "GhostBase.GhostMode.UploadingActions",
    "GhostBase.GhostMode.StickerActivity",
    "GhostBase.GhostMode.GameActivity",
    "GhostBase.GhostMode.EmojiActivity",
    "GhostBase.GhostMode.Presence"
]

private func ghostBaseSplashSafeLoginInitialEnabled() -> Bool {
    if let value = UserDefaults.standard.object(forKey: ghostBaseSplashSafeLoginEnabledKey) as? Bool {
        return value
    }
    return true
}

private func ghostBaseSplashSafeLoginApply(enabled: Bool) {
    UserDefaults.standard.set(enabled, forKey: ghostBaseSplashSafeLoginEnabledKey)
    for key in ghostBaseSplashGhostModeKeys {
        UserDefaults.standard.set(enabled, forKey: key)
    }
}

private func ghostBaseSplashSafeLoginButtonTitle(_ enabled: Bool) -> String {
    return enabled ? "👻 Ghost Mode: ON" : "👻 Ghost Mode: OFF"
}

''',
    "splash safe login helpers"
)

splash = insert_after_line_contains(
    splash,
    "private let startButton: SolidRoundedButtonNode",
    '''    private let ghostBaseSafeLoginButton: SolidRoundedButtonNode
    private let ghostBaseSafeLoginContainer: UIView
    private var ghostBaseSafeLoginEnabled: Bool
''',
    "splash safe login properties"
)

splash = replace_once(
    splash,
    '''        self.startButton = SolidRoundedButtonNode(title: "Start Messaging", theme: SolidRoundedButtonTheme(theme: theme), glass: false, height: 50.0, cornerRadius: 50.0 * 0.5, isShimmering: true)
        self.startButton.accessibilityIdentifier = "Auth.Welcome.StartButton"''',
    '''        self.startButton = SolidRoundedButtonNode(title: "Start Messaging", theme: SolidRoundedButtonTheme(theme: theme), glass: false, height: 50.0, cornerRadius: 50.0 * 0.5, isShimmering: true)
        self.startButton.accessibilityIdentifier = "Auth.Welcome.StartButton"

        // MARK: GhostBase v0.8H.1 Splash Safe Login init
        let ghostBaseInitialSafeLoginEnabled = ghostBaseSplashSafeLoginInitialEnabled()
        self.ghostBaseSafeLoginEnabled = ghostBaseInitialSafeLoginEnabled
        ghostBaseSplashSafeLoginApply(enabled: ghostBaseInitialSafeLoginEnabled)
        self.ghostBaseSafeLoginButton = SolidRoundedButtonNode(title: ghostBaseSplashSafeLoginButtonTitle(ghostBaseInitialSafeLoginEnabled), theme: SolidRoundedButtonTheme(theme: theme), glass: false, height: 50.0, cornerRadius: 50.0 * 0.5)
        self.ghostBaseSafeLoginButton.accessibilityIdentifier = "Auth.Welcome.GhostModeButton"
        self.ghostBaseSafeLoginContainer = UIView()
        self.ghostBaseSafeLoginContainer.clipsToBounds = false''',
    "splash safe login init"
)

splash = replace_once(
    splash,
    '''        self.startButton.pressed = { [weak self] in
            self?.activateLocalization("en")
        }''',
    '''        self.startButton.pressed = { [weak self] in
            self?.activateLocalization("en")
        }

        self.ghostBaseSafeLoginButton.pressed = { [weak self] in
            guard let strongSelf = self else {
                return
            }
            strongSelf.ghostBaseSafeLoginEnabled = !strongSelf.ghostBaseSafeLoginEnabled
            ghostBaseSplashSafeLoginApply(enabled: strongSelf.ghostBaseSafeLoginEnabled)
            strongSelf.ghostBaseSafeLoginButton.title = ghostBaseSplashSafeLoginButtonTitle(strongSelf.ghostBaseSafeLoginEnabled)
            strongSelf.ghostBaseSafeLoginButton.isEnabled = true
        }''',
    "splash safe login pressed"
)

splash = replace_once(
    splash,
    '''        self.controller.createStartButton = { [weak self] width in
            let _ = self?.startButton.updateLayout(width: width, transition: .immediate)
            return self?.startButton.view
        }''',
    '''        self.controller.createStartButton = { [weak self] width in
            guard let strongSelf = self else {
                return nil
            }
            let buttonHeight: CGFloat = 50.0
            let spacing: CGFloat = 10.0
            let totalHeight = buttonHeight * 2.0 + spacing

            let _ = strongSelf.ghostBaseSafeLoginButton.updateLayout(width: width, transition: .immediate)
            let _ = strongSelf.startButton.updateLayout(width: width, transition: .immediate)

            if strongSelf.ghostBaseSafeLoginButton.view.superview == nil {
                strongSelf.ghostBaseSafeLoginContainer.addSubview(strongSelf.ghostBaseSafeLoginButton.view)
            }
            if strongSelf.startButton.view.superview == nil {
                strongSelf.ghostBaseSafeLoginContainer.addSubview(strongSelf.startButton.view)
            }

            strongSelf.ghostBaseSafeLoginContainer.frame = CGRect(origin: CGPoint(), size: CGSize(width: width, height: totalHeight))
            strongSelf.ghostBaseSafeLoginButton.view.frame = CGRect(x: 0.0, y: 0.0, width: width, height: buttonHeight)
            strongSelf.startButton.view.frame = CGRect(x: 0.0, y: buttonHeight + spacing, width: width, height: buttonHeight)

            return strongSelf.ghostBaseSafeLoginContainer
        }''',
    "splash safe login createStartButton"
)

phone = phone.replace(
    "let ghostBaseSafeLoginExtraBottomInset: CGFloat = layout.size.width > 320.0 ? 88.0 : 0.0",
    "let ghostBaseSafeLoginExtraBottomInset: CGFloat = 0.0"
)

phone = phone.replace(
    "strongSelf.ghostBaseSafeLoginNode.animateTitle(to: ghostBaseSafeLoginButtonTitle(strongSelf.ghostBaseSafeLoginEnabled))",
    '''strongSelf.ghostBaseSafeLoginNode.title = ghostBaseSafeLoginButtonTitle(strongSelf.ghostBaseSafeLoginEnabled)
            strongSelf.ghostBaseSafeLoginNode.isEnabled = true'''
)

phone = phone.replace(
    '''        self.ghostBaseSafeLoginNode.isHidden = self.proceedNode.isHidden
        self.ghostBaseSafeLoginInfoNode.isHidden = self.proceedNode.isHidden''',
    '''        self.ghostBaseSafeLoginNode.isHidden = true
        self.ghostBaseSafeLoginInfoNode.isHidden = true'''
)

rmintro = replace_once(
    rmintro,
    '''    startButton.frame = CGRectMake(floor((self.view.bounds.size.width - startButtonWidth) / 2.0f), self.view.bounds.size.height - startButtonY - statusBarHeight, startButtonWidth, 50.0f);''',
    '''    startButton.frame = CGRectMake(floor((self.view.bounds.size.width - startButtonWidth) / 2.0f), self.view.bounds.size.height - startButtonY - statusBarHeight - 60.0f, startButtonWidth, 110.0f);''',
    "rmintro taller start button container"
)

# MARK: GhostBase v0.8H.1 Stars UX polish

settings = settings.replace(
    '''                type: .regular(capitalization: false, autocorrection: false),
                clearType: .onFocus,
                maxLength: 20,
                sectionId: self.section,''',
    '''                type: .regular(capitalization: false, autocorrection: false),
                returnKeyType: .done,
                alignment: .right,
                spacing: 16.0,
                clearType: .onFocus,
                maxLength: 20,
                selectAllOnFocus: true,
                sectionId: self.section,'''
)

# MARK: GhostBase v0.8H.1 One-Time visual/local keep candidate

interactive_media = replace_once(
    interactive_media,
    """            let isSecretMedia = message.containsSecretMedia""",
    """            // MARK: GhostBase v0.8H.1 one-time visual bypass
            var isSecretMedia = message.containsSecretMedia
            let ghostBaseOneTimeVisualBypass = (((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.Enabled") as? Bool) ?? true) && ((((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.OneTimeScreenshots") as? Bool) ?? false) || ((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.OneTimeScreenRecording") as? Bool) ?? false) || ((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.OneTimeSave") as? Bool) ?? false))) && message.minAutoremoveOrClearTimeout == viewOnceTimeout && message.id.peerId.namespace != Namespaces.Peer.SecretChat)
            if ghostBaseOneTimeVisualBypass {
                isSecretMedia = false
            }""",
    "one-time visual bypass isSecretMedia"
)

secret_preview = replace_once(
    secret_preview,
    """                self.markMessageAsConsumedDisposable.set(self.context.engine.messages.markMessageContentAsConsumedInteractively(messageId: message.id).start())""",
    """                // MARK: GhostBase v0.8H.1 one-time keep local / no local expire
                let ghostBaseKeepOneTimeLocal = (((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.Enabled") as? Bool) ?? true) && ((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.OneTimeSave") as? Bool) ?? false) && self.currentNodeMessageIsViewOnce && message.id.peerId.namespace != Namespaces.Peer.SecretChat)
                if !ghostBaseKeepOneTimeLocal {
                    self.markMessageAsConsumedDisposable.set(self.context.engine.messages.markMessageContentAsConsumedInteractively(messageId: message.id).start())
                }""",
    "one-time keep local no expire"
)

# MARK: GhostBase v0.8H.1 final write/check

settings_p.write_text(clean(settings))
phone_p.write_text(clean(phone))
splash_p.write_text(clean(splash))
rmintro_p.write_text(clean(rmintro))
secret_preview_p.write_text(clean(secret_preview))
interactive_media_p.write_text(clean(interactive_media))

settings = settings_p.read_text()
phone = phone_p.read_text()
splash = splash_p.read_text()
rmintro = rmintro_p.read_text()
secret_preview = secret_preview_p.read_text()
interactive_media = interactive_media_p.read_text()

checks = [
    ("version", "Version: v0.8H.1" in settings and "Version: v0.8H.1.1" not in settings),
    ("splash ghost button", "Auth.Welcome.GhostModeButton" in splash and "GhostBase v0.8H.1 Splash Safe Login init" in splash),
    ("splash no animateTitle", "ghostBaseSafeLoginButton.animateTitle" not in splash),
    ("splash title assignment", "ghostBaseSafeLoginButton.title = ghostBaseSplashSafeLoginButtonTitle" in splash),
    ("rmintro taller container", "110.0f" in rmintro and "- 60.0f" in rmintro),
    ("phone hidden ghost", "self.ghostBaseSafeLoginNode.isHidden = true" in phone),
    ("phone no animateTitle", "ghostBaseSafeLoginNode.animateTitle" not in phone),
    ("stars right alignment", "alignment: .right" in settings and "spacing: 16.0" in settings and "selectAllOnFocus: true" in settings),
]

bad = [name for name, ok in checks if not ok]
if bad:
    print(f"[{VERSION}] FAILED:")
    for name in bad:
        print("-", name)
    raise SystemExit(1)


# MARK: GhostBase v0.8H.1 generated one-time Swift guard
for generated_text, generated_label in [
    (interactive_media, "interactive_media"),
    (secret_preview, "secret_preview"),
]:
    for line in generated_text.splitlines():
        if "ghostBaseOneTimeVisualBypass =" in line or "ghostBaseKeepOneTimeLocal =" in line:
            balance = line.count("(") - line.count(")")
            if balance != 0:
                raise SystemExit(f"[{VERSION}] FAILED: unbalanced one-time Swift line in {generated_label}: {line}")

print("GhostBase Safe Login Polish v0.8H.1 patch OK")
