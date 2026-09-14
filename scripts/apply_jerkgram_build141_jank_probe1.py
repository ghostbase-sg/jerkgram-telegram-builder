#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path
import os


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
ACCOUNT = ROOT / "submodules/TelegramCore/Sources/Account/Account.swift"
APP_DELEGATE = ROOT / "submodules/TelegramUI/Sources/AppDelegate.swift"
SETTINGS = ROOT / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"
CHAT_INPUT = ROOT / "submodules/TelegramUI/Components/Chat/ChatTextInputPanelNode/Sources/ChatTextInputPanelNode.swift"
PROFILE_BG = ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/GhostBaseProfileFullscreenBackground.swift"

CORE_MARKER = "// MARK: Jerkgram Build141 JANK_PROBE_CORE1"
DISPLAY_MARKER = "// MARK: Jerkgram Build141 JANK_DISPLAY_LINK1"
SETTINGS_MARKER = "// MARK: Jerkgram Build141 JANK_SETTINGS1"
CHAT_MARKER = "// MARK: Jerkgram Build141 JANK_CHAT_INPUT1"
PROFILE_MARKER = "// MARK: Jerkgram Build141 JANK_PROFILE1"
PROFILE_PIPELINE_MARKER = "GhostBase v1.1T BUILD97_STATIC_AVATAR_PIPELINE1"


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build141 jank probe] " + message)


def block_bounds(text: str, signature: str) -> tuple[int, int]:
    start = text.find(signature)
    require(start >= 0, "owner missing: " + signature)
    opening = text.find("{", start)
    require(opening >= 0, "opening brace missing: " + signature)
    depth = 0
    in_string = False
    escaped = False
    line_comment = False
    block_comment = 0
    i = opening
    while i < len(text):
        ch = text[i]
        nxt = text[i + 1] if i + 1 < len(text) else ""
        if line_comment:
            if ch == "\n":
                line_comment = False
            i += 1
            continue
        if block_comment:
            if ch == "/" and nxt == "*":
                block_comment += 1
                i += 2
                continue
            if ch == "*" and nxt == "/":
                block_comment -= 1
                i += 2
                continue
            i += 1
            continue
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            i += 1
            continue
        if ch == "/" and nxt == "/":
            line_comment = True
            i += 2
            continue
        if ch == "/" and nxt == "*":
            block_comment = 1
            i += 2
            continue
        if ch == '"':
            in_string = True
        elif ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return start, i + 1
        i += 1
    raise RuntimeError("[Build141 jank probe] unbalanced owner: " + signature)


def instrument_function(text: str, signature: str, marker: str, lines: list[str]) -> str:
    start, end = block_bounds(text, signature)
    block = text[start:end]
    if marker in block:
        return text
    opening = block.find("{")
    require(opening >= 0, "instrument opening missing: " + signature)
    payload = "\n" + "\n".join(lines) + "\n"
    block = block[:opening + 1] + payload + block[opening + 1:]
    return text[:start] + block + text[end:]


CORE_RUNTIME = r'''
// MARK: Jerkgram Build141 JANK_PROBE_CORE1
public enum JerkgramJankContext: UInt8 {
    case other = 0
    case settings = 1
    case chat = 2
}

public enum JerkgramJankRegion: UInt8, CaseIterable {
    case settingsUpdate = 0
    case profileBackground = 1
    case avatarRequest = 2
    case chatTextInput = 3
    case typingPolicy = 4
}

public struct JerkgramJankRegionToken {
    fileprivate let region: JerkgramJankRegion
    fileprivate let startedAt: TimeInterval
    fileprivate let context: JerkgramJankContext
}

private struct JerkgramJankHitchSample {
    let timestamp: TimeInterval
    let durationMs: Double
    let severity: UInt8
    let context: JerkgramJankContext
    let scrolling: Bool
    let typing: Bool
    let animatedAvatar: Bool
    let activeRegionMask: UInt32
}

private struct JerkgramJankRegionSample {
    let region: JerkgramJankRegion
    let durationMs: Double
    let context: JerkgramJankContext
}

public final class JerkgramJankProbe {
    public static let shared = JerkgramJankProbe()

    public static let hitchCapacity = 64
    public static let regionCapacity = 256

    private let lock = NSLock()
    private var context: JerkgramJankContext = .other
    private var scrolling = false
    private var typingUntil: TimeInterval = 0.0
    private var animatedAvatarUntil: TimeInterval = 0.0

    private var hitchStorage = [JerkgramJankHitchSample?](repeating: nil, count: JerkgramJankProbe.hitchCapacity)
    private var hitchWriteIndex = 0
    private var hitchTotal: UInt64 = 0

    private var regionStorage = [JerkgramJankRegionSample?](repeating: nil, count: JerkgramJankProbe.regionCapacity)
    private var regionWriteIndex = 0
    private var regionTotal: UInt64 = 0
    private var regionDepth = [UInt16](repeating: 0, count: JerkgramJankRegion.allCases.count)
    private var regionCallCount = [UInt64](repeating: 0, count: JerkgramJankRegion.allCases.count)
    private var regionTotalMs = [Double](repeating: 0.0, count: JerkgramJankRegion.allCases.count)
    private var regionMaxMs = [Double](repeating: 0.0, count: JerkgramJankRegion.allCases.count)

    private init() {}

    @inline(__always)
    private func now() -> TimeInterval {
        return ProcessInfo.processInfo.systemUptime
    }

    public func setContext(_ context: JerkgramJankContext) {
        self.lock.lock()
        self.context = context
        self.lock.unlock()
    }

    public func noteScrolling(_ active: Bool) {
        self.lock.lock()
        self.scrolling = active
        self.lock.unlock()
    }

    public func noteTyping(_ active: Bool) {
        let now = self.now()
        self.lock.lock()
        self.typingUntil = active ? now + 1.0 : 0.0
        self.lock.unlock()
    }

    public func noteAnimatedAvatar(_ active: Bool) {
        let now = self.now()
        self.lock.lock()
        self.animatedAvatarUntil = active ? now + 2.0 : 0.0
        self.lock.unlock()
    }

    public func begin(_ region: JerkgramJankRegion) -> JerkgramJankRegionToken {
        let startedAt = self.now()
        self.lock.lock()
        let context = self.context
        let index = Int(region.rawValue)
        if index < self.regionDepth.count && self.regionDepth[index] < UInt16.max {
            self.regionDepth[index] += 1
        }
        self.lock.unlock()
        return JerkgramJankRegionToken(region: region, startedAt: startedAt, context: context)
    }

    public func end(_ token: JerkgramJankRegionToken) {
        let durationMs = max(0.0, (self.now() - token.startedAt) * 1000.0)
        let index = Int(token.region.rawValue)
        self.lock.lock()
        if index < self.regionDepth.count && self.regionDepth[index] > 0 {
            self.regionDepth[index] -= 1
        }
        if index < self.regionCallCount.count {
            self.regionCallCount[index] &+= 1
            self.regionTotalMs[index] += durationMs
            self.regionMaxMs[index] = max(self.regionMaxMs[index], durationMs)
        }
        self.regionStorage[self.regionWriteIndex] = JerkgramJankRegionSample(region: token.region, durationMs: durationMs, context: token.context)
        self.regionWriteIndex = (self.regionWriteIndex + 1) % JerkgramJankProbe.regionCapacity
        self.regionTotal &+= 1
        self.lock.unlock()
    }

    public func recordFrameGap(timestamp: TimeInterval, durationMs: Double, severity: UInt8) {
        guard durationMs >= 33.0 else {
            return
        }
        let now = self.now()
        self.lock.lock()
        var activeRegionMask: UInt32 = 0
        for index in 0 ..< min(self.regionDepth.count, 32) where self.regionDepth[index] > 0 {
            activeRegionMask |= UInt32(1) << UInt32(index)
        }
        self.hitchStorage[self.hitchWriteIndex] = JerkgramJankHitchSample(
            timestamp: timestamp,
            durationMs: durationMs,
            severity: severity,
            context: self.context,
            scrolling: self.scrolling,
            typing: now <= self.typingUntil,
            animatedAvatar: now <= self.animatedAvatarUntil,
            activeRegionMask: activeRegionMask
        )
        self.hitchWriteIndex = (self.hitchWriteIndex + 1) % JerkgramJankProbe.hitchCapacity
        self.hitchTotal &+= 1
        self.lock.unlock()
    }

    public func makeTextReport() -> String {
        self.lock.lock()
        let hitches = self.hitchStorage.compactMap { $0 }
        let regionCalls = self.regionCallCount
        let regionTotals = self.regionTotalMs
        let regionMax = self.regionMaxMs
        let hitchTotal = self.hitchTotal
        let regionTotal = self.regionTotal
        self.lock.unlock()

        let severe = hitches.filter { $0.severity >= 2 }.count
        let critical = hitches.filter { $0.severity >= 3 }.count
        let maxGap = hitches.map { $0.durationMs }.max() ?? 0.0
        var lines: [String] = [
            "Jerkgram Jank Probe / Build141",
            "hitches.total=\(hitchTotal) retained=\(hitches.count) severe=\(severe) critical=\(critical) maxMs=\(String(format: \"%.1f\", maxGap))",
            "regions.total=\(regionTotal) retained<=\(JerkgramJankProbe.regionCapacity)"
        ]
        for region in JerkgramJankRegion.allCases {
            let i = Int(region.rawValue)
            let count = i < regionCalls.count ? regionCalls[i] : 0
            let total = i < regionTotals.count ? regionTotals[i] : 0.0
            let maximum = i < regionMax.count ? regionMax[i] : 0.0
            if count != 0 {
                lines.append("region.\(region)=count:\(count) totalMs:\(String(format: \"%.1f\", total)) maxMs:\(String(format: \"%.1f\", maximum))")
            }
        }
        lines.append("recentHitches:")
        for hitch in hitches.suffix(20) {
            lines.append(
                "gapMs=\(String(format: \"%.1f\", hitch.durationMs)) severity=\(hitch.severity) context=\(hitch.context) scroll=\(hitch.scrolling ? 1 : 0) typing=\(hitch.typing ? 1 : 0) animatedAvatar=\(hitch.animatedAvatar ? 1 : 0) regions=0x\(String(hitch.activeRegionMask, radix: 16))"
            )
        }
        return lines.joined(separator: "\n")
    }
}
'''


DISPLAY_RUNTIME = r'''
// MARK: Jerkgram Build141 JANK_DISPLAY_LINK1
private final class JerkgramJankDisplayLink: NSObject {
    static let shared = JerkgramJankDisplayLink()

    private var displayLink: CADisplayLink?
    private var previousTimestamp: CFTimeInterval?

    func start() {
        guard self.displayLink == nil else {
            return
        }
        let displayLink = CADisplayLink(target: self, selector: #selector(self.tick(_:)))
        displayLink.add(to: .main, forMode: .common)
        self.displayLink = displayLink
    }

    @objc private func tick(_ displayLink: CADisplayLink) {
        guard UIApplication.shared.applicationState == .active else {
            self.previousTimestamp = nil
            return
        }
        guard let previousTimestamp = self.previousTimestamp else {
            self.previousTimestamp = displayLink.timestamp
            return
        }
        self.previousTimestamp = displayLink.timestamp
        let durationMs = (displayLink.timestamp - previousTimestamp) * 1000.0
        guard durationMs >= 33.0, durationMs < 2000.0 else {
            return
        }
        let severity: UInt8
        if durationMs >= 250.0 {
            severity = 3
        } else if durationMs >= 100.0 {
            severity = 2
        } else {
            severity = 1
        }
        JerkgramJankProbe.shared.recordFrameGap(timestamp: displayLink.timestamp, durationMs: durationMs, severity: severity)
    }
}
'''


def patch_account(text: str) -> str:
    if CORE_MARKER in text:
        require(text.count(CORE_MARKER) == 1, "core marker count")
        return text
    anchor = "public final class Account"
    require(text.count(anchor) == 1, "Account anchor count")
    return text.replace(anchor, CORE_RUNTIME.strip() + "\n\n" + anchor, 1)


def patch_app_delegate(text: str) -> str:
    if DISPLAY_MARKER not in text:
        anchor = "@objc(AppDelegate)"
        require(text.count(anchor) == 1, "AppDelegate class anchor count")
        text = text.replace(anchor, DISPLAY_RUNTIME.strip() + "\n\n" + anchor, 1)
    launch_signature = "func application(_ application: UIApplication, didFinishLaunchingWithOptions"
    text = instrument_function(
        text,
        launch_signature,
        "JerkgramJankDisplayLink.shared.start()",
        ["        JerkgramJankDisplayLink.shared.start()"],
    )
    require(text.count("CADisplayLink(target:") == 1, "must materialize exactly one probe display link")
    return text


def patch_settings(text: str) -> str:
    text = instrument_function(
        text,
        "private func ghostBaseSettingsEntries(",
        SETTINGS_MARKER,
        [
            "    // MARK: Jerkgram Build141 JANK_SETTINGS1",
            "    JerkgramJankProbe.shared.setContext(.settings)",
            "    let jerkgramJankSettingsToken = JerkgramJankProbe.shared.begin(.settingsUpdate)",
            "    defer { JerkgramJankProbe.shared.end(jerkgramJankSettingsToken) }",
        ],
    )
    if "JerkgramJankProbe.shared.makeTextReport()" not in text:
        old_case = "        case let .aboutValue(_, _, title, value):\n"
        new_case = '''        case let .aboutValue(_, index, title, value):
            let jerkgramJankReportAction: (() -> Void)?
            if index == 1 {
                jerkgramJankReportAction = {
                    UIPasteboard.general.string = JerkgramJankProbe.shared.makeTextReport()
                }
            } else {
                jerkgramJankReportAction = nil
            }
'''
        require(text.count(old_case) == 1, "About value item owner changed")
        text = text.replace(old_case, new_case, 1)
        case_start = text.index(new_case)
        next_case = text.find("\n        case ", case_start + len(new_case))
        require(next_case > case_start, "About value case end missing")
        block = text[case_start:next_case]
        require(block.count("action: nil") == 1, "About value action anchor count")
        block = block.replace("action: nil", "action: jerkgramJankReportAction", 1)
        text = text[:case_start] + block + text[next_case:]
    require(text.count("JerkgramJankProbe.shared.makeTextReport()") == 1, "report copy action count")
    return text


def patch_chat_input(text: str) -> str:
    return instrument_function(
        text,
        "@objc public func editableTextNodeDidUpdateText(",
        CHAT_MARKER,
        [
            "        // MARK: Jerkgram Build141 JANK_CHAT_INPUT1",
            "        JerkgramJankProbe.shared.setContext(.chat)",
            "        JerkgramJankProbe.shared.noteTyping(true)",
            "        let jerkgramJankChatToken = JerkgramJankProbe.shared.begin(.chatTextInput)",
            "        defer { JerkgramJankProbe.shared.end(jerkgramJankChatToken) }",
        ],
    )


def patch_profile(text: str) -> str:
    if PROFILE_MARKER in text:
        require(text.count(PROFILE_MARKER) == 1, "profile marker count")
        return text
    marker_index = text.find(PROFILE_PIPELINE_MARKER)
    require(marker_index >= 0, "profile static-avatar pipeline marker missing")
    candidates = [
        text.rfind("\n    private func ", 0, marker_index),
        text.rfind("\n    func ", 0, marker_index),
    ]
    start = max(candidates)
    require(start >= 0, "profile static-avatar owner function missing")
    start += 1
    opening = text.find("{", start, marker_index)
    require(opening >= 0, "profile owner opening brace missing")
    signature = text[start:opening].strip()
    return instrument_function(
        text,
        signature,
        PROFILE_MARKER,
        [
            "        // MARK: Jerkgram Build141 JANK_PROFILE1",
            "        JerkgramJankProbe.shared.noteAnimatedAvatar(true)",
            "        let jerkgramJankProfileToken = JerkgramJankProbe.shared.begin(.profileBackground)",
            "        defer { JerkgramJankProbe.shared.end(jerkgramJankProfileToken) }",
        ],
    )


def main() -> None:
    for path in (ACCOUNT, APP_DELEGATE, SETTINGS, CHAT_INPUT, PROFILE_BG):
        require(path.is_file(), "source owner missing: " + str(path))

    transforms = (
        (ACCOUNT, patch_account),
        (APP_DELEGATE, patch_app_delegate),
        (SETTINGS, patch_settings),
        (CHAT_INPUT, patch_chat_input),
        (PROFILE_BG, patch_profile),
    )
    staged: list[tuple[Path, str]] = []
    for path, transform in transforms:
        source = path.read_text(encoding="utf-8")
        staged.append((path, transform(source)))

    for path, updated in staged:
        path.write_text(updated, encoding="utf-8")

    print("[Build141 jank probe] SOURCE PATCHED")
    print("[Build141 jank probe] bounded 64 hitch / 256 region recorder + one CADisplayLink + Settings/profile/chat hooks")
    print("[Build141 jank probe] tap Jerkgram Version in About to copy the in-memory report")


if __name__ == "__main__":
    main()
