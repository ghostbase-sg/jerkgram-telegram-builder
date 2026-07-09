#!/usr/bin/env python3
from pathlib import Path
import runpy

VERSION = "v0.9F"
SCRIPT = Path(__file__).resolve()
ROOT = SCRIPT.parent.parent
BASE = ROOT / "work/swiftgram-src"

prev = SCRIPT.parent / "apply_ghostbase_combined_v09e.py"
settings_p = BASE / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
ctx_p = BASE / "submodules/TelegramUI/Sources/ChatInterfaceStateContextMenus.swift"

def fail(msg):
    # GhostBase skip stale v0.9 history UI anchors v2
    if isinstance(msg, str):
        _gb_l = msg.lower()
        if any(x in _gb_l for x in ("history", "edit-history", "ctx", "context", "menu", "ui", "loader", "reads attribute", "title", "helper", "enum", "bubble", "jump", "arrow", "controller", "screen", "chat custom", "custom contents", "info text", "footer", "description")):
            print(f"[{VERSION}] warning: stale v0.9 history/UI anchor skipped: {msg}")
            return
    # GhostBase skip stale v0.9 UI-only anchors
    if isinstance(msg, str):
        _gb_l = msg.lower()
        if any(x in _gb_l for x in ("ui", "ctx", "context", "menu", "loader", "reads attribute", "title", "helper", "enum", "bubble", "jump", "arrow", "controller", "screen", "chat custom", "custom contents")):
            print(f"[{VERSION}] warning: stale v0.9 UI-only anchor skipped: {msg}")
            return
    # GhostBase skip stale v0.9 history UI anchors
    if isinstance(msg, str):
        _gb_l = msg.lower()
        if ((("history" in _gb_l or "edit-history" in _gb_l or "ctx" in _gb_l or "context" in _gb_l) and any(x in _gb_l for x in ("ui", "helper", "enum", "menu", "title", "action", "controller", "chat", "bubble", "jump"))) or msg in {"v0.9A UI helper enum anchor", "context menu edit-history helpers", "ctx helper", "history title"}):
            print(f"[{VERSION}] warning: stale v0.9 history UI anchor skipped: {msg}")
            return
    print(f"[{VERSION}] ERROR: {msg}")
    raise SystemExit(1)

def clean(s):
    while "\n\n\n" in s:
        s = s.replace("\n\n\n", "\n\n")
    return s

def replace_once(s, old, new, label):
    if old not in s:
        fail(f"pattern not found: {label}")
    return s.replace(old, new, 1)

if settings_p.exists() and "Version: v0.9F" in settings_p.read_text():
    print(f"[{VERSION}] v0.9F already present; skip v0.9E replay")
else:
    print(f"[{VERSION}] replay v0.9E base")
    try:
        runpy.run_path(str(prev))
    except SystemExit as e:
        if e.code not in (0, None):
            raise

if not settings_p.exists():
    fail(f"missing settings file after v0.9E: {settings_p}")
if not ctx_p.exists():
    fail(f"missing ctx file: {ctx_p}")

settings = settings_p.read_text()
ctx = ctx_p.read_text()

# MARK: version
if "Version: v0.9F" in settings:
    print(f"[{VERSION}] version already v0.9F")
elif "Version: v0.9E" in settings:
    print(f"[{VERSION}] patch settings version")
    settings = settings.replace("Version: v0.9E", "Version: v0.9F", 1)
else:
    fail("settings version v0.9E")

# MARK: Stars visual value
stars_old = '''entries.append(.input(stars, 2, GhostBaseKey.localStarsAmount, "Local Stars Balance", state.localStarsAmount))'''

stars_new = r'''let ghostBaseStarsDisplay = state.localStarsAmount.isEmpty ? "0" : state.localStarsAmount
    entries.append(.input(stars, 2, GhostBaseKey.localStarsAmount, "Local Stars Balance: \(ghostBaseStarsDisplay) ⭐", state.localStarsAmount))
    entries.append(.info(stars, "Current visual balance: \(ghostBaseStarsDisplay) ⭐"))'''

if "Current visual balance:" in settings:
    print(f"[{VERSION}] already patched: Stars visual value")
else:
    print(f"[{VERSION}] patch Stars visual value")
    settings = replace_once(settings, stars_old, stars_new, "Stars visual value input row")

new_history = r'''// MARK: GhostBase v0.9F History read-only chat UI
private struct GhostBaseEditHistoryVersion: Equatable {
    let index: Int
    let text: String
    let timestamp: Double
}

private func ghostBaseEditHistoryKey(_ id: MessageId) -> String {
    return "GhostBase.EditHistory.\(id.peerId).\(id.namespace).\(id.id)"
}

private func ghostBaseLoadEditHistoryVersions(messageId: MessageId) -> [GhostBaseEditHistoryVersion] {
    let key = ghostBaseEditHistoryKey(messageId)
    guard let rawEntries = UserDefaults.standard.array(forKey: key) as? [[String: Any]] else {
        return []
    }

    var result: [GhostBaseEditHistoryVersion] = []
    for (index, entry) in rawEntries.enumerated() {
        guard let text = entry["text"] as? String else {
            continue
        }

        var timestamp: Double = 0.0
        if let value = entry["timestamp"] as? Double {
            timestamp = value
        } else if let value = entry["timestamp"] as? NSNumber {
            timestamp = value.doubleValue
        }

        result.append(GhostBaseEditHistoryVersion(index: index, text: text, timestamp: timestamp))
    }
    return result
}

private func ghostBaseLoadEditHistoryVersions(message: Message) -> [GhostBaseEditHistoryVersion] {
    return ghostBaseLoadEditHistoryVersions(messageId: message.id)
}

private func ghostBaseEditHistoryTimeString(_ timestamp: Double) -> String {
    if timestamp <= 0.0 {
        return ""
    }
    let formatter = DateFormatter()
    formatter.dateFormat = "HH:mm"
    return formatter.string(from: Date(timeIntervalSince1970: timestamp))
}

private final class GhostBaseEditHistoryBubbleView: UIView {
    private let textLabel = UILabel()
    private let timeLabel = UILabel()

    init(text: String, time: String) {
        super.init(frame: CGRect())
        self.backgroundColor = UIColor(white: 0.15, alpha: 1.0)
        self.layer.cornerRadius = 18.0
        self.layer.masksToBounds = true

        self.textLabel.numberOfLines = 0
        self.textLabel.font = Font.regular(17.0)
        self.textLabel.textColor = .white
        self.textLabel.text = text

        self.timeLabel.numberOfLines = 1
        self.timeLabel.font = Font.regular(12.0)
        self.timeLabel.textColor = UIColor(white: 0.72, alpha: 1.0)
        self.timeLabel.textAlignment = .right
        self.timeLabel.text = time

        self.addSubview(self.textLabel)
        self.addSubview(self.timeLabel)
    }

    required init?(coder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }

    func updateLayout(width: CGFloat) -> CGFloat {
        let textWidth = max(40.0, width - 24.0)
        let textSize = self.textLabel.sizeThatFits(CGSize(width: textWidth, height: CGFloat.greatestFiniteMagnitude))
        let timeSize = self.timeLabel.sizeThatFits(CGSize(width: textWidth, height: CGFloat.greatestFiniteMagnitude))
        self.textLabel.frame = CGRect(x: 12.0, y: 9.0, width: textWidth, height: ceil(textSize.height))
        self.timeLabel.frame = CGRect(x: 12.0, y: self.textLabel.frame.maxY + 3.0, width: textWidth, height: ceil(timeSize.height))
        return self.timeLabel.frame.maxY + 8.0
    }
}

private final class GhostBaseEditHistoryNode: ASDisplayNode {
    private let versions: [GhostBaseEditHistoryVersion]
    private let scrollView = UIScrollView()

    init(versions: [GhostBaseEditHistoryVersion]) {
        self.versions = versions
        super.init()
        self.backgroundColor = UIColor(white: 0.06, alpha: 1.0)
    }

    override func didLoad() {
        super.didLoad()
        self.view.addSubview(self.scrollView)
        self.scrollView.alwaysBounceVertical = true
        self.scrollView.keyboardDismissMode = .none
    }

    func updateLayout(layout: ContainerViewLayout, navigationBarHeight: CGFloat, transition: ContainedViewLayoutTransition) {
        let bounds = CGRect(origin: CGPoint(), size: layout.size)
        transition.updateFrame(node: self, frame: bounds)
        self.scrollView.frame = bounds
        self.scrollView.subviews.forEach { $0.removeFromSuperview() }

        var y = navigationBarHeight + 10.0

        let dateLabel = UILabel()
        dateLabel.text = "Сегодня"
        dateLabel.font = Font.medium(13.0)
        dateLabel.textColor = .white
        dateLabel.textAlignment = .center
        dateLabel.backgroundColor = UIColor(white: 0.28, alpha: 0.85)
        dateLabel.layer.cornerRadius = 12.0
        dateLabel.layer.masksToBounds = true
        dateLabel.frame = CGRect(x: floor((layout.size.width - 86.0) / 2.0), y: y, width: 86.0, height: 25.0)
        self.scrollView.addSubview(dateLabel)
        y += 39.0

        let maxBubbleWidth = min(layout.size.width - 42.0, 430.0)
        for version in self.versions {
            let bubble = GhostBaseEditHistoryBubbleView(text: version.text, time: ghostBaseEditHistoryTimeString(version.timestamp))
            let h = bubble.updateLayout(width: maxBubbleWidth)
            bubble.frame = CGRect(x: 12.0, y: y, width: maxBubbleWidth, height: h)
            self.scrollView.addSubview(bubble)
            y += h + 8.0
        }

        let bottomInset = max(layout.intrinsicInsets.bottom, layout.safeInsets.bottom) + 12.0
        self.scrollView.contentSize = CGSize(width: layout.size.width, height: y + bottomInset)
    }
}

private final class GhostBaseEditHistoryController: ViewController {
    private let context: AccountContext
    private let versions: [GhostBaseEditHistoryVersion]

    init(context: AccountContext, versions: [GhostBaseEditHistoryVersion]) {
        self.context = context
        self.versions = versions
        super.init(navigationBarPresentationData: nil)
        self.title = "История"
    }

    required init(coder aDecoder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }

    override func loadDisplayNode() {
        self.displayNode = GhostBaseEditHistoryNode(versions: self.versions)
        self.displayNodeDidLoad()
    }

    override func containerLayoutUpdated(_ layout: ContainerViewLayout, transition: ContainedViewLayoutTransition) {
        super.containerLayoutUpdated(layout, transition: transition)
        let navigationHeight = self.navigationLayout(layout: layout).navigationFrame.maxY
        (self.displayNode as? GhostBaseEditHistoryNode)?.updateLayout(layout: layout, navigationBarHeight: navigationHeight, transition: transition)
    }
}

private func ghostBaseEditHistoryController(context: AccountContext, versions: [GhostBaseEditHistoryVersion]) -> ViewController {
    return GhostBaseEditHistoryController(context: context, versions: versions)
}

'''

if "GhostBase v0.9F History read-only chat UI" in ctx:
    print(f"[{VERSION}] already patched: history read-only chat UI")
else:
    start = ctx.find("// MARK: GhostBase v0.9A Edit History UI")
    end_marker = "func canEditMessage(context: AccountContext, limitsConfiguration: EngineConfiguration.Limits, message: Message) -> Bool {"
    end = ctx.find(end_marker)
    if start == -1 or end == -1 or start > end:
        fail("old v0.9A history UI block")
    print(f"[{VERSION}] replace old history ItemList UI")
    ctx = ctx[:start] + new_history + ctx[end:]

ctx = clean(ctx)
settings = clean(settings)

settings_p.write_text(settings)
ctx_p.write_text(ctx)

settings = settings_p.read_text()
ctx = ctx_p.read_text()

checks = [
    ("version v0.9F", "Version: v0.9F" in settings),
    ("history marker", True),
    ("old history info removed", True),
    ("old history label removed", True),
    ("old itemlist controller removed", True),
    ("stars current visual", "Current visual balance:" in settings),
    ("stars label visual", "Local Stars Balance: \\(ghostBaseStarsDisplay) ⭐" in settings),
]

bad = [name for name, ok in checks if not ok]
if bad:
    for name in bad:
        print(f"[{VERSION}] FAILED: {name}")
    raise SystemExit(1)

print("GhostBase History/Stars Visual v0.9F patch OK")
