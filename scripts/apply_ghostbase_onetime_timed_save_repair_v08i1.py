from pathlib import Path
import runpy

VERSION = "v0.8I.1"

def find_base() -> Path:
    cwd = Path.cwd()
    for c in [cwd / "work/swiftgram-src", cwd, cwd.parent / "swiftgram-src"]:
        if (c / "submodules/TelegramUI/Sources/ChatInterfaceStateContextMenus.swift").exists():
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

def insert_after_function(text: str, function_name: str, insertion: str, label: str) -> str:
    if insertion.strip() in text:
        print(f"[{VERSION}] already patched: {label}")
        return text

    start = text.find(f"private func {function_name}")
    if start < 0:
        fail(label + " function start")

    brace = text.find("{", start)
    if brace < 0:
        fail(label + " opening brace")

    depth = 0
    for i in range(brace, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                return text[:i + 1] + "\n\n" + insertion.rstrip("\n") + text[i + 1:]

    fail(label + " closing brace")

BASE = find_base()

prev = Path(__file__).with_name("apply_ghostbase_onetime_timed_save_v08i.py")
if not prev.exists():
    raise SystemExit(f"[{VERSION}] ERROR: missing prerequisite {prev}")

settings_p = BASE / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
ctx_p = BASE / "submodules/TelegramUI/Sources/ChatInterfaceStateContextMenus.swift"
secret_p = BASE / "submodules/GalleryUI/Sources/SecretMediaPreviewController.swift"
media_p = BASE / "submodules/TelegramUI/Components/Chat/ChatMessageInteractiveMediaNode/Sources/ChatMessageInteractiveMediaNode.swift"

settings_existing = settings_p.read_text(errors="ignore") if settings_p.exists() else ""
if "Version: v0.8I.1" in settings_existing:
    print(f"[{VERSION}] v0.8I.1 already applied; skip prerequisite replay")
elif "Version: v0.8I" in settings_existing:
    print(f"[{VERSION}] v0.8I chain already applied; skip prerequisite replay")
else:
    runpy.run_path(str(prev))

settings = settings_p.read_text()
ctx = ctx_p.read_text()
secret = secret_p.read_text()
media = media_p.read_text()

# MARK: version
while "Version: v0.8I.1.1" in settings:
    settings = settings.replace("Version: v0.8I.1.1", "Version: v0.8I.1")
if "Version: v0.8I.1" not in settings:
    settings = settings.replace("Version: v0.8I", "Version: v0.8I.1")

# MARK: Stars sidecar: base amount + transaction preview
settings = replace_once(
    settings,
    '''    static let localStarsAmount = "GhostBase.Stars.LocalBalance.Amount"''',
    '''    static let localStarsAmount = "GhostBase.Stars.LocalBalance.Amount"
    static let localStarsBaseAmount = "GhostBase.Stars.LocalBalance.BaseAmount"''',
    "stars base key"
)

settings = insert_after_function(
    settings,
    "ghostBaseSanitizeStarsAmount",
    '''private func ghostBaseStarsInt64(_ text: String) -> Int64 {
    return Int64(ghostBaseSanitizeStarsAmount(text)) ?? 0
}

private func ghostBaseStarsTransactionPreview(baseAmount: String, targetAmount: String) -> String {
    let base = ghostBaseStarsInt64(baseAmount)
    let target = ghostBaseStarsInt64(targetAmount)
    let delta = target - base
    let sign = delta >= 0 ? "+" : ""
    return "Transaction Preview: GhostBase \\(sign)\\(delta)"
}''',
    "stars transaction preview helpers"
)

settings = replace_once(
    settings,
    '''    var localStarsAmount: String''',
    '''    var localStarsAmount: String
    var localStarsBaseAmount: String''',
    "stars base state var"
)

settings = replace_once(
    settings,
    '''            localStarsAmount: ghostBaseString(GhostBaseKey.localStarsAmount, defaultValue: "0")''',
    '''            localStarsAmount: ghostBaseString(GhostBaseKey.localStarsAmount, defaultValue: "0"),
            localStarsBaseAmount: ghostBaseString(GhostBaseKey.localStarsBaseAmount, defaultValue: "0")''',
    "stars base load"
)

settings = replace_once(
    settings,
    '''        UserDefaults.standard.set(self.localStarsAmount, forKey: GhostBaseKey.localStarsAmount)''',
    '''        UserDefaults.standard.set(self.localStarsAmount, forKey: GhostBaseKey.localStarsAmount)
        UserDefaults.standard.set(self.localStarsBaseAmount, forKey: GhostBaseKey.localStarsBaseAmount)''',
    "stars base save"
)

settings = replace_once(
    settings,
    '''    entries.append(.input(stars, 2, GhostBaseKey.localStarsAmount, "Stars Amount", state.localStarsAmount))
    entries.append(.info(stars, "Local Stars Balance is visual only. It does not change your real Telegram balance or payments. Negative values are allowed for local display experiments."))''',
    '''    entries.append(.input(stars, 2, GhostBaseKey.localStarsAmount, "Stars Amount", state.localStarsAmount))
    entries.append(.input(stars, 3, GhostBaseKey.localStarsBaseAmount, "Stars Base Amount", state.localStarsBaseAmount))
    entries.append(.info(stars, ghostBaseStarsTransactionPreview(baseAmount: state.localStarsBaseAmount, targetAmount: state.localStarsAmount) + "\\nLocal Stars Balance is visual only. It does not change your real Telegram balance or payments. Negative values are allowed for local display experiments."))''',
    "stars base input and transaction preview"
)

# MARK: long press photo save repair
ctx = replace_once(
    ctx,
    '''        let ghostBaseTimedMediaSave = (((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.Enabled") as? Bool) ?? true) && ((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.OneTimeSave") as? Bool) ?? false) && message.id.peerId.namespace != Namespaces.Peer.SecretChat && message.paidContent == nil && message.minAutoremoveOrClearTimeout != nil)

        if resourceAvailable, (!message.containsSecretMedia || ghostBaseTimedMediaSave) && (!isCopyProtected || ghostBaseProtectedChatSave || ghostBaseTimedMediaSave) {''',
    '''        let ghostBaseTimedMediaSave = (((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.Enabled") as? Bool) ?? true) && ((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.OneTimeSave") as? Bool) ?? false) && message.id.peerId.namespace != Namespaces.Peer.SecretChat && message.paidContent == nil && message.minAutoremoveOrClearTimeout != nil)

        // MARK: GhostBase v0.8I.1 timed image long-press resource bypass
        let ghostBaseTimedImageMediaSave = ghostBaseTimedMediaSave && message.media.contains(where: { $0 is TelegramMediaImage })

        if (resourceAvailable || ghostBaseTimedImageMediaSave), (!message.containsSecretMedia || ghostBaseTimedMediaSave) && (!isCopyProtected || ghostBaseProtectedChatSave || ghostBaseTimedMediaSave) {''',
    "long press photo resource bypass"
)

# MARK: timed visual parity
media = replace_once(
    media,
    '''&& message.minAutoremoveOrClearTimeout == viewOnceTimeout && message.id.peerId.namespace != Namespaces.Peer.SecretChat)''',
    '''&& message.minAutoremoveOrClearTimeout != nil && message.id.peerId.namespace != Namespaces.Peer.SecretChat)''',
    "timed visual bypass parity"
)

# MARK: timed local keep parity
secret = replace_once(
    secret,
    '''let ghostBaseKeepOneTimeLocal = (((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.Enabled") as? Bool) ?? true) && ((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.OneTimeSave") as? Bool) ?? false) && self.currentNodeMessageIsViewOnce && message.id.peerId.namespace != Namespaces.Peer.SecretChat)''',
    '''let ghostBaseKeepOneTimeLocal = (((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.Enabled") as? Bool) ?? true) && ((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.OneTimeSave") as? Bool) ?? false) && message.minAutoremoveOrClearTimeout != nil && message.id.peerId.namespace != Namespaces.Peer.SecretChat)''',
    "timed local keep parity"
)

# MARK: SecretMediaPreview direct Save button
secret = replace_once(
    secret,
    '''import TelegramNotices''',
    '''import TelegramNotices
import SaveToCameraRoll''',
    "secret preview SaveToCameraRoll import"
)

secret = replace_once(
    secret,
    '''        if let message = message {
            if self.currentNodeMessageId != message.id {''',
    '''        if let message = message {
            // MARK: GhostBase v0.8I.1 secret preview save button
            let ghostBaseTimedPreviewSave = (((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.Enabled") as? Bool) ?? true) && ((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.OneTimeSave") as? Bool) ?? false) && message.id.peerId.namespace != Namespaces.Peer.SecretChat && message.paidContent == nil && message.minAutoremoveOrClearTimeout != nil)
            if ghostBaseTimedPreviewSave, let media = mediaForMessage(message: message) {
                let saveTitle = media is TelegramMediaFile ? self.presentationData.strings.Gallery_SaveVideo : self.presentationData.strings.Gallery_SaveImage
                self.navigationItem.rightBarButtonItem = UIBarButtonItem(title: saveTitle, style: .plain, target: self, action: #selector(self.ghostBaseSaveCurrentTimedMedia))
            } else {
                self.navigationItem.rightBarButtonItem = nil
            }

            if self.currentNodeMessageId != message.id {''',
    "secret preview save button apply"
)

secret = replace_once(
    secret,
    '''        } else {
            if !self.didSetReady {''',
    '''        } else {
            self.navigationItem.rightBarButtonItem = nil
            if !self.didSetReady {''',
    "secret preview clear save button"
)

secret = replace_once(
    secret,
    '''    private func dismiss(forceAway: Bool) {''',
    '''    // MARK: GhostBase v0.8I.1 secret preview save action
    @objc private func ghostBaseSaveCurrentTimedMedia() {
        guard let message = self.messageView?.message else {
            return
        }

        let ghostBaseTimedPreviewSave = (((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.Enabled") as? Bool) ?? true) && ((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.OneTimeSave") as? Bool) ?? false) && message.id.peerId.namespace != Namespaces.Peer.SecretChat && message.paidContent == nil && message.minAutoremoveOrClearTimeout != nil)
        guard ghostBaseTimedPreviewSave, let media = mediaForMessage(message: message) else {
            return
        }

        let mediaReference: AnyMediaReference
        if let image = media as? TelegramMediaImage {
            mediaReference = ImageMediaReference.message(message: MessageReference(message), media: image).abstract
        } else if let file = media as? TelegramMediaFile {
            mediaReference = FileMediaReference.message(message: MessageReference(message), media: file).abstract
        } else {
            return
        }

        let _ = (saveToCameraRoll(context: self.context, postbox: self.context.account.postbox, userLocation: .peer(message.id.peerId), mediaReference: mediaReference)
        |> deliverOnMainQueue).startStandalone()
    }

    private func dismiss(forceAway: Bool) {''',
    "secret preview save action"
)

# MARK: final write/check
settings_p.write_text(clean(settings))
ctx_p.write_text(clean(ctx))
secret_p.write_text(clean(secret))
media_p.write_text(clean(media))

settings = settings_p.read_text()
ctx = ctx_p.read_text()
secret = secret_p.read_text()
media = media_p.read_text()

checks = [
    ("version", "Version: v0.8I.1" in settings and "Version: v0.8I.1.1" not in settings),
    ("stars base key", "localStarsBaseAmount" in settings and "Stars Base Amount" in settings),
    ("stars transaction preview", "Transaction Preview: GhostBase" in settings),
    ("no unsupported keyboard arg", "dismissKeyboardOnEnter" not in settings),
    ("long press image bypass", "ghostBaseTimedImageMediaSave" in ctx and "(resourceAvailable || ghostBaseTimedImageMediaSave)" in ctx),
    ("timed visual parity", "message.minAutoremoveOrClearTimeout != nil && message.id.peerId.namespace != Namespaces.Peer.SecretChat)" in media),
    ("timed local keep", "message.minAutoremoveOrClearTimeout != nil && message.id.peerId.namespace != Namespaces.Peer.SecretChat)" in secret),
    ("secret preview save import", "import SaveToCameraRoll" in secret),
    ("secret preview save button", "ghostBaseSaveCurrentTimedMedia" in secret and "rightBarButtonItem" in secret),
]

for generated_text, generated_label in [
    (ctx, "context menu"),
    (secret, "secret preview"),
    (media, "interactive media"),
]:
    for line in generated_text.splitlines():
        if (
            "ghostBaseTimedImageMediaSave =" in line
            or "ghostBaseTimedPreviewSave =" in line
            or "ghostBaseKeepOneTimeLocal =" in line
            or "ghostBaseOneTimeVisualBypass =" in line
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

print("GhostBase One-Time Timed Save Repair v0.8I.1 patch OK")
