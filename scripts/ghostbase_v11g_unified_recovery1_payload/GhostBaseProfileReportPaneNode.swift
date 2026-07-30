import Foundation
import UIKit
import AsyncDisplayKit
import Display
import SwiftSignalKit
import TelegramCore
import TelegramPresentationData
import AccountContext
import PeerInfoPaneNode

// MARK: GhostBase v1.1G PROFILEHISTORYBOUNDED1
private struct GhostBaseObservedProfileSnapshotV11G: Codable, Equatable {
    let observedAt: Int64
    let displayName: String
    let username: String?
    let about: String?
    let avatarResourceId: String?
    let emojiStatus: String

    func hasSameContent(as other: GhostBaseObservedProfileSnapshotV11G) -> Bool {
        return self.displayName == other.displayName
            && self.username == other.username
            && self.about == other.about
            && self.avatarResourceId == other.avatarResourceId
            && self.emojiStatus == other.emojiStatus
    }
}

private struct GhostBaseObservedProfileHistoryV11G: Codable {
    var current: GhostBaseObservedProfileSnapshotV11G
    var events: [GhostBaseObservedProfileSnapshotV11G]
}

private struct GhostBasePersonalChannelObservationV11G: Codable, Equatable {
    let observedAt: Int64
    let channelPeerId: Int64?
    let title: String?
    let username: String?
    let link: String?
    let subscriberCount: Int?
    let topMessageId: Int32?

    func hasSameContent(as other: GhostBasePersonalChannelObservationV11G) -> Bool {
        return self.channelPeerId == other.channelPeerId
            && self.title == other.title
            && self.username == other.username
            && self.link == other.link
            && self.subscriberCount == other.subscriberCount
            && self.topMessageId == other.topMessageId
    }
}

private struct GhostBasePersonalChannelHistoryV11G: Codable {
    var current: GhostBasePersonalChannelObservationV11G
    var events: [GhostBasePersonalChannelObservationV11G]
}

private enum GhostBaseProfileReportStoreV11G {
    static let queue = DispatchQueue(
        label: "GhostBase.ProfileReportStore.V11G",
        qos: .utility
    )
    static let maximumEvents = 200

    // Queue-confined caches ensure repeated PeerInfoScreen data updates do not
    // decode and rewrite the same history over and over.
    private static var profileHistories: [String: GhostBaseObservedProfileHistoryV11G] = [:]
    private static var loadedProfileKeys: Set<String> = []
    private static var personalChannelHistories: [String: GhostBasePersonalChannelHistoryV11G] = [:]
    private static var loadedPersonalChannelKeys: Set<String> = []

    static func profileKey(accountPeerId: Int64, peerId: Int64) -> String {
        return "GhostBase.ProfileHistory.V11G.\(accountPeerId).\(peerId)"
    }

    static func personalChannelKey(accountPeerId: Int64, peerId: Int64) -> String {
        // Reuse the established PROFILEINTEL3 key so old observations survive.
        return "GhostBase.ProfileIntel3.PersonalChannel.\(accountPeerId).\(peerId)"
    }

    static func recordProfile(
        accountPeerId: Int64,
        peerId: Int64,
        snapshot: GhostBaseObservedProfileSnapshotV11G
    ) {
        self.queue.async {
            let defaults = UserDefaults.standard
            let key = self.profileKey(
                accountPeerId: accountPeerId,
                peerId: peerId
            )
            var history: GhostBaseObservedProfileHistoryV11G
            if self.loadedProfileKeys.contains(key) {
                history = self.profileHistories[key] ?? GhostBaseObservedProfileHistoryV11G(
                    current: snapshot,
                    events: []
                )
            } else {
                self.loadedProfileKeys.insert(key)
                if let data = defaults.data(forKey: key),
                   let value = try? JSONDecoder().decode(
                    GhostBaseObservedProfileHistoryV11G.self,
                    from: data
                   ) {
                    history = value
                } else {
                    history = GhostBaseObservedProfileHistoryV11G(
                        current: snapshot,
                        events: []
                    )
                }
                self.profileHistories[key] = history
            }

            if !history.events.isEmpty,
               history.current.hasSameContent(as: snapshot) {
                return
            }

            history.events.append(snapshot)
            if history.events.count > self.maximumEvents {
                history.events.removeFirst(
                    history.events.count - self.maximumEvents
                )
            }
            history.current = snapshot
            self.profileHistories[key] = history

            if let data = try? JSONEncoder().encode(history) {
                defaults.set(data, forKey: key)
            }
        }
    }

    static func recordPersonalChannel(
        accountPeerId: Int64,
        peerId: Int64,
        observation: GhostBasePersonalChannelObservationV11G
    ) {
        self.queue.async {
            let defaults = UserDefaults.standard
            let key = self.personalChannelKey(
                accountPeerId: accountPeerId,
                peerId: peerId
            )
            var history: GhostBasePersonalChannelHistoryV11G
            if self.loadedPersonalChannelKeys.contains(key) {
                history = self.personalChannelHistories[key] ?? GhostBasePersonalChannelHistoryV11G(
                    current: observation,
                    events: []
                )
            } else {
                self.loadedPersonalChannelKeys.insert(key)
                if let data = defaults.data(forKey: key),
                   let value = try? JSONDecoder().decode(
                    GhostBasePersonalChannelHistoryV11G.self,
                    from: data
                   ) {
                    history = value
                } else {
                    history = GhostBasePersonalChannelHistoryV11G(
                        current: observation,
                        events: []
                    )
                }
                self.personalChannelHistories[key] = history
            }

            if !history.events.isEmpty,
               history.current.hasSameContent(as: observation) {
                return
            }

            history.events.append(observation)
            if history.events.count > self.maximumEvents {
                history.events.removeFirst(
                    history.events.count - self.maximumEvents
                )
            }
            history.current = observation
            self.personalChannelHistories[key] = history

            if let data = try? JSONEncoder().encode(history) {
                defaults.set(data, forKey: key)
            }
        }
    }

    static func profileReport(accountPeerId: Int64, peerId: Int64) -> String? {
        let defaults = UserDefaults.standard
        let key = self.profileKey(
            accountPeerId: accountPeerId,
            peerId: peerId
        )
        var sections: [String] = []

        if let data = defaults.data(forKey: key),
           let history = try? JSONDecoder().decode(
            GhostBaseObservedProfileHistoryV11G.self,
            from: data
           ) {
            let formatter = DateFormatter()
            formatter.locale = Locale(identifier: "ru_RU")
            formatter.dateFormat = "dd.MM.yyyy HH:mm"
            var lines = ["Наблюдаемая история профиля: \(history.events.count)"]
            for event in history.events.reversed() {
                lines.append(
                    "\(formatter.string(from: Date(timeIntervalSince1970: TimeInterval(event.observedAt)))) · имя=\(event.displayName) · username=\(event.username ?? "nil") · BIO=\(event.about ?? "nil") · avatar=\(event.avatarResourceId ?? "nil") · emoji=\(event.emojiStatus)"
                )
            }
            sections.append(lines.joined(separator: "\n"))
        }

        let oldBase = "GhostBase.ProfileIntel2.\(accountPeerId).\(peerId)."
        if let oldHistory = defaults.string(forKey: oldBase + "History"),
           !oldHistory.isEmpty {
            sections.append("PROFILEINTEL2\n" + oldHistory)
        }

        return sections.isEmpty ? nil : sections.joined(separator: "\n\n")
    }

    static func personalChannelReport(
        accountPeerId: Int64,
        peerId: Int64
    ) -> String? {
        let key = self.personalChannelKey(
            accountPeerId: accountPeerId,
            peerId: peerId
        )
        guard let data = UserDefaults.standard.data(forKey: key),
              let history = try? JSONDecoder().decode(
                GhostBasePersonalChannelHistoryV11G.self,
                from: data
              ) else {
            return nil
        }

        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "ru_RU")
        formatter.dateFormat = "dd.MM.yyyy HH:mm"
        var lines = ["История прикреплённого канала: \(history.events.count)"]
        for event in history.events.reversed() {
            let date = formatter.string(
                from: Date(timeIntervalSince1970: TimeInterval(event.observedAt))
            )
            if let channelPeerId = event.channelPeerId {
                lines.append(
                    "\(date) · id=\(channelPeerId) · title=\(event.title ?? "nil") · username=\(event.username ?? "nil") · link=\(event.link ?? "nil") · subscribers=\(event.subscriberCount.map(String.init) ?? "nil") · topMessageId=\(event.topMessageId.map(String.init) ?? "nil")"
                )
            } else {
                lines.append("\(date) · канал откреплён")
            }
        }
        return lines.joined(separator: "\n")
    }
}

func ghostBaseRecordObservedProfileV11G(
    accountPeerId: EnginePeer.Id,
    peer: EnginePeer,
    cachedData: CachedPeerData?
) {
    let about = (cachedData as? CachedUserData)?.about
    let snapshot = GhostBaseObservedProfileSnapshotV11G(
        observedAt: Int64(Date().timeIntervalSince1970),
        displayName: peer.compactDisplayTitle,
        username: peer.addressName,
        about: about,
        avatarResourceId: peer.profileImageRepresentations.last?.resource.id.stringRepresentation,
        emojiStatus: String(describing: peer.emojiStatus)
    )
    GhostBaseProfileReportStoreV11G.recordProfile(
        accountPeerId: accountPeerId.toInt64(),
        peerId: peer.id.toInt64(),
        snapshot: snapshot
    )
}

func ghostBaseRecordPersonalChannelObservationV11G(
    accountPeerId: EnginePeer.Id,
    targetPeerId: EnginePeer.Id,
    personalChannel: PeerInfoPersonalChannelData?
) {
    let channelPeer = personalChannel?.peer.peer
    let username = channelPeer?.addressName
    let observation = GhostBasePersonalChannelObservationV11G(
        observedAt: Int64(Date().timeIntervalSince1970),
        channelPeerId: channelPeer?.id.toInt64(),
        title: channelPeer?.compactDisplayTitle,
        username: username,
        link: username.map { "https://t.me/\($0)" },
        subscriberCount: personalChannel?.subscriberCount,
        topMessageId: personalChannel?.topMessages.first?.id.id
    )
    GhostBaseProfileReportStoreV11G.recordPersonalChannel(
        accountPeerId: accountPeerId.toInt64(),
        peerId: targetPeerId.toInt64(),
        observation: observation
    )
}

// MARK: GhostBase v1.1G NATIVEPANES1
final class GhostBaseProfileReportPaneNode: ASDisplayNode, PeerInfoPaneNode, UIScrollViewDelegate {
    enum Kind {
        case profileHistory
        case presence
        case giftHistory
        case personalChannel
    }

    weak var parentController: ViewController?

    private let accountPeerId: EnginePeer.Id
    private let peerId: EnginePeer.Id
    private let kind: Kind
    private let personalChannel: PeerInfoPersonalChannelData?

    private let scrollNode = ASScrollNode()
    private let textNode = ImmediateTextNode()
    private let readyPromise = ValuePromise<Bool>(true, ignoreRepeated: true)
    private let statusPromise = Promise<PeerInfoStatusData?>(nil)

    private var currentPresentationData: PresentationData?
    private var currentSize: CGSize?
    private var reportText: String?
    private var didStartLoading = false

    var isReady: Signal<Bool, NoError> {
        return self.readyPromise.get()
    }

    var status: Signal<PeerInfoStatusData?, NoError> {
        return self.statusPromise.get()
    }

    var tabBarOffsetUpdated: ((ContainedViewLayoutTransition) -> Void)?

    var tabBarOffset: CGFloat {
        return max(0.0, self.scrollNode.view.contentOffset.y)
    }

    init(
        context: AccountContext,
        peerId: EnginePeer.Id,
        kind: Kind,
        personalChannel: PeerInfoPersonalChannelData?
    ) {
        self.accountPeerId = context.account.peerId
        self.peerId = peerId
        self.kind = kind
        self.personalChannel = personalChannel

        super.init()

        self.backgroundColor = .clear
        self.scrollNode.backgroundColor = .clear
        self.textNode.displaysAsynchronously = false

        self.addSubnode(self.scrollNode)
        self.scrollNode.addSubnode(self.textNode)
    }

    override func didLoad() {
        super.didLoad()
        self.scrollNode.view.backgroundColor = .clear
        self.scrollNode.view.contentInsetAdjustmentBehavior = .never
        self.scrollNode.view.alwaysBounceVertical = true
        self.scrollNode.view.scrollsToTop = false
        self.scrollNode.view.delegate = self
    }

    private func startLoadingIfNeeded() {
        guard !self.didStartLoading else {
            return
        }
        self.didStartLoading = true

        let accountPeerId = self.accountPeerId
        let peerId = self.peerId
        let kind = self.kind
        let personalChannel = self.personalChannel

        DispatchQueue.global(qos: .utility).async { [weak self] in
            let text = Self.loadReport(
                accountPeerId: accountPeerId,
                peerId: peerId,
                kind: kind,
                personalChannel: personalChannel
            )
            DispatchQueue.main.async {
                guard let self else {
                    return
                }
                self.reportText = text
                self.updateTextLayout(transition: .immediate)
            }
        }
    }

    private static func loadReport(
        accountPeerId: EnginePeer.Id,
        peerId: EnginePeer.Id,
        kind: Kind,
        personalChannel: PeerInfoPersonalChannelData?
    ) -> String {
        switch kind {
        case .presence:
            return ghostBasePresenceHistoryReport(
                accountPeerId: accountPeerId,
                peerId: peerId
            ) ?? "История присутствия пока пуста."

        case .giftHistory:
            let report = ghostBaseGiftHistoryReport(
                accountPeerId: accountPeerId,
                peerId: peerId
            )
            return report.isEmpty ? "История подарков пока пуста." : report

        case .profileHistory:
            return GhostBaseProfileReportStoreV11G.profileReport(
                accountPeerId: accountPeerId.toInt64(),
                peerId: peerId.toInt64()
            ) ?? "История профиля пока пуста."

        case .personalChannel:
            if let report = GhostBaseProfileReportStoreV11G.personalChannelReport(
                accountPeerId: accountPeerId.toInt64(),
                peerId: peerId.toInt64()
            ) {
                return report
            }
            if let personalChannel {
                var lines: [String] = ["Личный канал"]
                if let peer = personalChannel.peer.chatOrMonoforumMainPeer {
                    lines.append("Название: \(peer.compactDisplayTitle)")
                    lines.append("ID: \(peer.id.toInt64())")
                } else {
                    lines.append("ID: \(personalChannel.peer.peerId.toInt64())")
                }
                if let subscriberCount = personalChannel.subscriberCount {
                    lines.append("Подписчики: \(subscriberCount)")
                }
                lines.append("Последние сообщения: \(personalChannel.topMessages.count)")
                return lines.joined(separator: "\n")
            }
            return "Личный канал не найден."
        }
    }

    private func updateTextLayout(transition: ContainedViewLayoutTransition) {
        guard let size = self.currentSize,
              let presentationData = self.currentPresentationData else {
            return
        }

        let text = self.reportText ?? "Загрузка…"
        self.textNode.attributedText = NSAttributedString(
            string: text,
            font: Font.regular(15.0),
            textColor: presentationData.theme.list.itemPrimaryTextColor
        )

        let sideInset: CGFloat = 20.0
        let textSize = self.textNode.updateLayout(
            CGSize(
                width: max(1.0, size.width - sideInset * 2.0),
                height: .greatestFiniteMagnitude
            )
        )
        transition.updateFrame(
            node: self.textNode,
            frame: CGRect(
                origin: CGPoint(x: sideInset, y: 20.0),
                size: textSize
            )
        )
        self.scrollNode.view.contentSize = CGSize(
            width: size.width,
            height: max(size.height + 1.0, textSize.height + 40.0)
        )
    }

    func update(
        size: CGSize,
        topInset: CGFloat,
        sideInset: CGFloat,
        bottomInset: CGFloat,
        deviceMetrics: DeviceMetrics,
        visibleHeight: CGFloat,
        isScrollingLockedAtTop: Bool,
        expandProgress: CGFloat,
        navigationHeight: CGFloat,
        presentationData: PresentationData,
        synchronous: Bool,
        transition: ContainedViewLayoutTransition
    ) {
        self.currentSize = size
        self.currentPresentationData = presentationData

        transition.updateFrame(
            node: self.scrollNode,
            frame: CGRect(origin: .zero, size: size)
        )
        self.scrollNode.view.contentInset = UIEdgeInsets(
            top: topInset,
            left: 0.0,
            bottom: bottomInset,
            right: 0.0
        )
        self.scrollNode.view.scrollIndicatorInsets = self.scrollNode.view.contentInset
        self.updateTextLayout(transition: transition)

        if visibleHeight > 0.0 {
            self.startLoadingIfNeeded()
        }
    }

    func scrollViewDidScroll(_ scrollView: UIScrollView) {
        self.tabBarOffsetUpdated?(.immediate)
    }

    func scrollToTop() -> Bool {
        self.scrollNode.view.setContentOffset(
            CGPoint(x: 0.0, y: -self.scrollNode.view.contentInset.top),
            animated: true
        )
        return true
    }

    func transferVelocity(_ velocity: CGFloat) {
    }

    func cancelPreviewGestures() {
    }

    func findLoadedMessage(id: EngineMessage.Id) -> EngineMessage? {
        return nil
    }

    func transitionNodeForGallery(
        messageId: EngineMessage.Id,
        media: EngineMedia
    ) -> (ASDisplayNode, CGRect, () -> (UIView?, UIView?))? {
        return nil
    }

    func addToTransitionSurface(view: UIView) {
        self.view.addSubview(view)
    }

    func updateHiddenMedia() {
    }

    func updateSelectedMessages(animated: Bool) {
    }

    func ensureMessageIsVisible(id: EngineMessage.Id) {
    }
}
