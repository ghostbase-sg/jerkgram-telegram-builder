#!/usr/bin/env python3
import os
from pathlib import Path

ROOT = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src"))
PATH = ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoProfileItems.swift"
if not PATH.is_file():
    raise SystemExit(f"[V11A HUB] missing source: {PATH}")
text = PATH.read_text(encoding="utf-8")
if "// MARK: GhostBase v1.1A PROFILEHUB1 Telegram-style sheet" in text:
    print("[V11A] profile hub/channel fix already applied")
    raise SystemExit(0)
for proof in (
    "// MARK: GhostBase v1.0ZG PROFILEINTEL3 personal channel storage",
    "// MARK: GhostBase v1.0ZH PROFILEUI1 integrated profile cards",
    "ghostBaseGiftHistoryReport(",
):
    if proof not in text:
        raise SystemExit(f"[V11A HUB] prerequisite missing: {proof}")

# Remove the ugly Build 86 preview helper only.
marker = "// MARK: GhostBase v1.0ZH PROFILEUI1 integrated profile cards"
start = text.index(marker)
next_marker = text.find("// MARK:", start + len(marker))
func_start = text.find("func infoItems(\n", start)
end_candidates = [v for v in (next_marker, func_start) if v != -1]
if not end_candidates:
    raise SystemExit("[V11A HUB] unable to remove PROFILEUI1 helper")
text = text[:start] + text[min(end_candidates):]

# Correct the personal-channel baseline: an initial confirmed nil is not an
# event, while the first actual channel is a baseline observation.
old = '''    var history: GhostBasePersonalChannelHistory
    if let data = UserDefaults.standard.data(forKey: key),
       let value = try? decoder.decode(GhostBasePersonalChannelHistory.self, from: data) {
        history = value
    } else {
        history = GhostBasePersonalChannelHistory(current: current, events: [])
    }

    let previous = history.current
    let meaningfulChange =
        previous.channelPeerId != current.channelPeerId
        || previous.title != current.title
        || previous.username != current.username

    if history.events.isEmpty || meaningfulChange {
        history.events.append(current)
        if history.events.count > 200 {
            history.events.removeFirst(history.events.count - 200)
        }
    }
    history.current = current
'''
new = '''    var history: GhostBasePersonalChannelHistory
    if let data = UserDefaults.standard.data(forKey: key),
       let value = try? decoder.decode(GhostBasePersonalChannelHistory.self, from: data) {
        history = value
        while history.events.count > 1,
              history.events.first?.channelPeerId == nil {
            history.events.removeFirst()
        }
    } else {
        guard current.channelPeerId != nil else {
            return
        }
        history = GhostBasePersonalChannelHistory(
            current: current,
            events: [current]
        )
    }

    let previous = history.current
    let meaningfulChange =
        previous.channelPeerId != current.channelPeerId
        || previous.title != current.title
        || previous.username != current.username

    if meaningfulChange {
        history.events.append(current)
        if history.events.count > 200 {
            history.events.removeFirst(history.events.count - 200)
        }
    }
    history.current = current
'''
if old not in text:
    raise SystemExit("[V11A HUB] personal-channel baseline anchor missing")
text = text.replace(old, new, 1)

old_call = '''        // MARK: GhostBase v1.0ZG PROFILEINTEL3 observe personal channel
        ghostBaseRecordPersonalChannel(
            accountPeerId: context.account.peerId,
            targetPeerId: user.id,
            personalChannel: data.personalChannel
        )
'''
new_call = '''        // MARK: GhostBase v1.1A PERSONALCHANNEL2 confirmed observation
        if let cachedUserData = data.cachedData as? CachedUserData {
            switch cachedUserData.personalChannel {
            case .unknown:
                break
            case let .known(value):
                if value == nil {
                    ghostBaseRecordPersonalChannel(
                        accountPeerId: context.account.peerId,
                        targetPeerId: user.id,
                        personalChannel: nil
                    )
                } else if let personalChannel = data.personalChannel {
                    ghostBaseRecordPersonalChannel(
                        accountPeerId: context.account.peerId,
                        targetPeerId: user.id,
                        personalChannel: personalChannel
                    )
                }
            }
        }
'''
if old_call not in text:
    raise SystemExit("[V11A HUB] old personal-channel call missing")
text = text.replace(old_call, new_call, 1)

# Remove the three old main-profile history/action blocks. Keep unrelated
# private-invite and other features intact.
function_start = text.index("func infoItems(\n")
result_anchor = "    var result: [(AnyHashable, [PeerInfoScreenItem])] = []\n"
result_pos = text.index(result_anchor, function_start)
for old_marker in (
    "    // MARK: GhostBase v1.0ZH PROFILEUI1 integrated profile cards\n",
    "    // MARK: GhostBase v1.0ZG GIFTHISTORY1 profile action\n",
    "    // MARK: GhostBase v1.0ZG PROFILEINTEL3 history action\n",
):
    while True:
        pos = text.find(old_marker, function_start, result_pos)
        if pos == -1:
            break
        next_positions = []
        for candidate in (
            text.find("    // MARK:", pos + len(old_marker), result_pos),
            text.find(result_anchor, pos + len(old_marker)),
        ):
            if candidate != -1:
                next_positions.append(candidate)
        if not next_positions:
            raise SystemExit(f"[V11A HUB] cannot remove block: {old_marker.strip()}")
        block_end = min(next_positions)
        text = text[:pos] + text[block_end:]
        result_pos = text.index(result_anchor, function_start)

hub_marker = "// MARK: GhostBase v1.1A PROFILEHUB1 Telegram-style sheet"
if hub_marker not in text:
    insert_at = text.index("func infoItems(\n")
    helper = r'''// MARK: GhostBase v1.1A PROFILEHUB1 Telegram-style sheet
private struct GhostBaseHistoryHubSection {
    let title: String
    let report: String
}

private final class GhostBaseHistoryHubNode: ASDisplayNode {
    private let presentationData: PresentationData
    private let sections: [GhostBaseHistoryHubSection]
    private let titleLabel = UILabel()
    private let closeButton = UIButton(type: .system)
    private let segmentedControl: UISegmentedControl
    private let scrollView = UIScrollView()
    private let stackView = UIStackView()
    private let emptyLabel = UILabel()
    private var selectedIndex: Int = 0

    var dismiss: (() -> Void)?

    init(
        presentationData: PresentationData,
        sections: [GhostBaseHistoryHubSection]
    ) {
        self.presentationData = presentationData
        self.sections = sections
        self.segmentedControl = UISegmentedControl(
            items: sections.map { $0.title }
        )
        super.init()
        self.backgroundColor = presentationData.theme.list.plainBackgroundColor
    }

    override func didLoad() {
        super.didLoad()
        let theme = self.presentationData.theme

        self.titleLabel.text = "История и сведения"
        self.titleLabel.font = Font.semibold(17.0)
        self.titleLabel.textColor = theme.list.itemPrimaryTextColor
        self.titleLabel.textAlignment = .center

        self.closeButton.setTitle("Готово", for: .normal)
        self.closeButton.setTitleColor(theme.list.itemAccentColor, for: .normal)
        self.closeButton.titleLabel?.font = Font.regular(17.0)
        self.closeButton.addTarget(self, action: #selector(self.closePressed), for: .touchUpInside)

        self.segmentedControl.selectedSegmentIndex = 0
        self.segmentedControl.addTarget(self, action: #selector(self.segmentChanged), for: .valueChanged)

        self.scrollView.alwaysBounceVertical = true
        self.scrollView.showsVerticalScrollIndicator = true
        self.scrollView.backgroundColor = theme.list.plainBackgroundColor

        self.stackView.axis = .vertical
        self.stackView.spacing = 10.0
        self.stackView.alignment = .fill
        self.stackView.translatesAutoresizingMaskIntoConstraints = false

        self.emptyLabel.font = Font.regular(15.0)
        self.emptyLabel.textColor = theme.list.itemSecondaryTextColor
        self.emptyLabel.textAlignment = .center
        self.emptyLabel.numberOfLines = 0

        self.view.addSubview(self.titleLabel)
        self.view.addSubview(self.closeButton)
        self.view.addSubview(self.segmentedControl)
        self.view.addSubview(self.scrollView)
        self.scrollView.addSubview(self.stackView)

        NSLayoutConstraint.activate([
            self.stackView.leadingAnchor.constraint(equalTo: self.scrollView.contentLayoutGuide.leadingAnchor, constant: 16.0),
            self.stackView.trailingAnchor.constraint(equalTo: self.scrollView.contentLayoutGuide.trailingAnchor, constant: -16.0),
            self.stackView.topAnchor.constraint(equalTo: self.scrollView.contentLayoutGuide.topAnchor, constant: 14.0),
            self.stackView.bottomAnchor.constraint(equalTo: self.scrollView.contentLayoutGuide.bottomAnchor, constant: -24.0),
            self.stackView.widthAnchor.constraint(equalTo: self.scrollView.frameLayoutGuide.widthAnchor, constant: -32.0),
        ])

        let leftSwipe = UISwipeGestureRecognizer(target: self, action: #selector(self.swiped(_:)))
        leftSwipe.direction = .left
        self.scrollView.addGestureRecognizer(leftSwipe)
        let rightSwipe = UISwipeGestureRecognizer(target: self, action: #selector(self.swiped(_:)))
        rightSwipe.direction = .right
        self.scrollView.addGestureRecognizer(rightSwipe)

        self.rebuildContent()
    }

    func updateLayout(size: CGSize, topInset: CGFloat, bottomInset: CGFloat) {
        let headerY = max(10.0, topInset + 4.0)
        self.titleLabel.frame = CGRect(x: 72.0, y: headerY, width: size.width - 144.0, height: 44.0)
        self.closeButton.frame = CGRect(x: size.width - 88.0, y: headerY, width: 72.0, height: 44.0)
        self.segmentedControl.frame = CGRect(x: 12.0, y: headerY + 50.0, width: size.width - 24.0, height: 34.0)
        self.scrollView.frame = CGRect(x: 0.0, y: headerY + 94.0, width: size.width, height: max(0.0, size.height - headerY - 94.0 - bottomInset))
    }

    @objc private func closePressed() {
        self.dismiss?()
    }

    @objc private func segmentChanged() {
        self.selectedIndex = max(0, self.segmentedControl.selectedSegmentIndex)
        self.rebuildContent()
    }

    @objc private func swiped(_ recognizer: UISwipeGestureRecognizer) {
        if recognizer.direction == .left {
            self.selectedIndex = min(self.sections.count - 1, self.selectedIndex + 1)
        } else if recognizer.direction == .right {
            self.selectedIndex = max(0, self.selectedIndex - 1)
        }
        self.segmentedControl.selectedSegmentIndex = self.selectedIndex
        self.rebuildContent()
    }

    private func rebuildContent() {
        for view in self.stackView.arrangedSubviews {
            self.stackView.removeArrangedSubview(view)
            view.removeFromSuperview()
        }
        guard self.sections.indices.contains(self.selectedIndex) else {
            return
        }
        let report = self.sections[self.selectedIndex].report
        let lines = report.split(separator: "\n", omittingEmptySubsequences: true).map(String.init)
        let visibleLines = lines.first?.contains(":") == true ? Array(lines.dropFirst()) : lines
        if visibleLines.isEmpty {
            self.emptyLabel.text = "Пока нет сохранённых данных."
            self.stackView.addArrangedSubview(self.emptyLabel)
            return
        }
        for line in visibleLines {
            let card = UIView()
            card.backgroundColor = self.presentationData.theme.list.itemBlocksBackgroundColor
            card.layer.cornerRadius = 12.0

            let parts = line.components(separatedBy: " · ")
                .filter { !$0.hasSuffix("=nil") && !$0.isEmpty }
            let titleParts = Array(parts.prefix(min(2, parts.count)))
            let detailParts = Array(parts.dropFirst(titleParts.count))

            let titleLabel = UILabel()
            titleLabel.font = Font.semibold(15.0)
            titleLabel.textColor = self.presentationData.theme.list.itemPrimaryTextColor
            titleLabel.numberOfLines = 0
            titleLabel.text = titleParts.joined(separator: " · ")

            let detailLabel = UILabel()
            detailLabel.font = Font.regular(13.0)
            detailLabel.textColor = self.presentationData.theme.list.itemSecondaryTextColor
            detailLabel.numberOfLines = 0
            detailLabel.text = detailParts
                .map { value in
                    return value
                        .replacingOccurrences(of: "sender=", with: "Отправитель: ")
                        .replacingOccurrences(of: "username=", with: "Username: ")
                        .replacingOccurrences(of: "text=", with: "Подпись: ")
                        .replacingOccurrences(of: "lastVisible=", with: "Последний раз виден: ")
                        .replacingOccurrences(of: "missingSince=", with: "Исчез: ")
                        .replacingOccurrences(of: "subscribers=", with: "Подписчики: ")
                }
                .joined(separator: "\n")
            detailLabel.isHidden = detailParts.isEmpty

            let content = UIStackView(arrangedSubviews: [titleLabel, detailLabel])
            content.axis = .vertical
            content.spacing = 5.0
            content.translatesAutoresizingMaskIntoConstraints = false
            card.addSubview(content)
            NSLayoutConstraint.activate([
                content.leadingAnchor.constraint(equalTo: card.leadingAnchor, constant: 14.0),
                content.trailingAnchor.constraint(equalTo: card.trailingAnchor, constant: -14.0),
                content.topAnchor.constraint(equalTo: card.topAnchor, constant: 12.0),
                content.bottomAnchor.constraint(equalTo: card.bottomAnchor, constant: -12.0),
            ])
            self.stackView.addArrangedSubview(card)
        }
    }
}

private final class GhostBaseHistoryHubController: ViewController {
    private let presentationData: PresentationData
    private let sections: [GhostBaseHistoryHubSection]

    init(
        presentationData: PresentationData,
        sections: [GhostBaseHistoryHubSection]
    ) {
        self.presentationData = presentationData
        self.sections = sections
        super.init(navigationBarPresentationData: nil)
        self.navigationPresentation = .modal
    }

    required init(coder aDecoder: NSCoder) {
        fatalError("init(coder:) has not been implemented")
    }

    override func loadDisplayNode() {
        let node = GhostBaseHistoryHubNode(
            presentationData: self.presentationData,
            sections: self.sections
        )
        node.dismiss = { [weak self] in
            self?.dismiss()
        }
        self.displayNode = node
        self.displayNodeDidLoad()
    }

    override func containerLayoutUpdated(
        _ layout: ContainerViewLayout,
        transition: ContainedViewLayoutTransition
    ) {
        super.containerLayoutUpdated(layout, transition: transition)
        guard let node = self.displayNode as? GhostBaseHistoryHubNode else {
            return
        }
        node.updateLayout(
            size: layout.size,
            topInset: layout.statusBarHeight ?? 0.0,
            bottomInset: layout.intrinsicInsets.bottom + layout.safeInsets.bottom
        )
    }
}

'''
    text = text[:insert_at] + helper + text[insert_at:]

# Insert one compact Telegram-style row before the result is assembled.
function_start = text.index("func infoItems(\n")
result_pos = text.index(result_anchor, function_start)
row_marker = "    // MARK: GhostBase v1.1A PROFILEHUB1 profile row\n"
if row_marker not in text:
    row = r'''    // MARK: GhostBase v1.1A PROFILEHUB1 profile row
    if case let .user(user) = data.peer {
        let giftEntries = ghostBaseGiftHistoryEntries(
            accountPeerId: context.account.peerId,
            peerId: user.id
        )
        let giftReport: String
        if giftEntries.isEmpty {
            giftReport = "Подарки\nПока нет сохранённых подарков."
        } else {
            giftReport = ghostBaseGiftHistoryReport(
                accountPeerId: context.account.peerId,
                peerId: user.id
            )
        }
        let presenceReport = ghostBasePresenceHistoryReport(
            accountPeerId: context.account.peerId,
            peerId: user.id
        ) ?? "Онлайн\nПока нет полученных статусов."
        let channelReport = ghostBasePersonalChannelReport(
            accountPeerId: context.account.peerId,
            targetPeerId: user.id
        ) ?? "Канал\nПрикреплённый канал не наблюдался."
        let historyReport = [giftReport, presenceReport, channelReport]
            .flatMap { $0.split(separator: "\n", omittingEmptySubsequences: true).dropFirst().prefix(2) }
            .map(String.init)
            .joined(separator: "\n")
        let username = user.addressName.map { "@\($0)" } ?? "не указан"
        let infoReport = "Сведения\nPeer ID: \(user.id.toInt64())\nUsername: \(username)"

        items[.peerInfoTrailing]!.append(
            PeerInfoScreenActionItem(
                id: 9911001,
                text: "История и сведения",
                color: .accent,
                icon: nil,
                alignment: .natural,
                action: { [weak interaction] in
                    guard let controller = interaction?.getController() else {
                        return
                    }
                    let sheet = GhostBaseHistoryHubController(
                        presentationData: presentationData,
                        sections: [
                            GhostBaseHistoryHubSection(title: "История", report: "История\n\(historyReport)"),
                            GhostBaseHistoryHubSection(title: "Подарки", report: giftReport),
                            GhostBaseHistoryHubSection(title: "Онлайн", report: presenceReport),
                            GhostBaseHistoryHubSection(title: "Канал", report: channelReport),
                            GhostBaseHistoryHubSection(title: "Сведения", report: infoReport),
                        ]
                    )
                    controller.present(
                        sheet,
                        in: .window(.root),
                        with: ViewControllerPresentationArguments(
                            presentationAnimation: .modalSheet
                        )
                    )
                }
            )
        )
    }

'''
    text = text[:result_pos] + row + text[result_pos:]

PATH.write_text(text, encoding="utf-8")
updated = PATH.read_text(encoding="utf-8")
for proof in (
    "GhostBase v1.1A PERSONALCHANNEL2 confirmed observation",
    "case .unknown:",
    "guard current.channelPeerId != nil",
    "GhostBase v1.1A PROFILEHUB1 Telegram-style sheet",
    'text: "История и сведения"',
    'items: sections.map { $0.title }',
    "presentationAnimation: .modalSheet",
):
    if proof not in updated:
        raise SystemExit(f"[V11A HUB] proof missing: {proof}")
for forbidden in (
    'title: "GhostBase · Подарки"',
    'title: "GhostBase · Прикреплённый канал"',
    'title: "GhostBase · Присутствие"',
):
    if forbidden in updated:
        raise SystemExit(f"[V11A HUB] old expanded UI remains: {forbidden}")
print("[V11A] Telegram-style history sheet installed; personal-channel baseline fixed")
