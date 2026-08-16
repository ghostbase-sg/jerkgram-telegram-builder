#!/usr/bin/env python3
from __future__ import annotations

import os
import re
from pathlib import Path

ROOT = Path(os.environ.get(
    "GHOSTBASE_SOURCE_ROOT",
    "/root/gb_builder/work/swiftgram-src",
)).resolve()

PATHS = {
    "bg": ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/GhostBaseProfileFullscreenBackground.swift",
    "groups": ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/Panes/PeerInfoGroupsInCommonPaneNode.swift",
    "music_controls": ROOT / "submodules/TelegramUI/Sources/OverlayAudioPlayerControlsNode.swift",
    "music_controller": ROOT / "submodules/TelegramUI/Sources/OverlayAudioPlayerControllerNode.swift",
    "enqueue": ROOT / "submodules/TelegramCore/Sources/PendingMessages/EnqueueMessage.swift",
    "state": ROOT / "submodules/TelegramCore/Sources/State/AccountStateManagementUtils.swift",
    "delete": ROOT / "submodules/TelegramCore/Sources/TelegramEngine/Messages/DeleteMessagesInteractively.swift",
    "settings": ROOT / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift",
}

MARKER = "GhostBase v1.1T BUILD105_FULL1"

for name, path in PATHS.items():
    if not path.is_file():
        raise RuntimeError(f"[V11T] missing required source {name}: {path}")

sources = {
    name: path.read_text(encoding="utf-8")
    for name, path in PATHS.items()
}

if MARKER in sources["enqueue"]:
    print("[V11T] BUILD105_FULL1 already materialized")
    raise SystemExit(0)

for name, required in {
    "bg": "GhostBase v1.1S RUNTIME_RECOVERY1",
    "groups": "GhostBase v1.1S COMMON_GROUPS_TRANSLUCENT1",
    "music_controls": "GhostBase v1.1S MUSIC_TRANSLUCENT_SHEET1",
    "music_controller": "GhostBase v1.1S MUSIC_HEADER_TRANSLUCENT1",
    "settings": "GhostBase v1.1R RAM_SETTING1",
}.items():
    if required not in sources[name]:
        raise RuntimeError(
            f"[V11T] missing prerequisite in {name}: {required}"
        )

backups = dict(sources)


def once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(
            f"[V11T] {label}: expected exactly one anchor, found {count}"
        )
    return text.replace(old, new, 1)


def balanced_region(
    text: str,
    token: str,
    *,
    start_at: int = 0,
    label: str,
) -> tuple[int, int]:
    start = text.find(token, start_at)
    if start < 0:
        raise RuntimeError(f"[V11T] {label}: start token not found")
    brace = text.find("{", start + len(token))
    if brace < 0:
        raise RuntimeError(f"[V11T] {label}: opening brace not found")

    depth = 0
    in_string = False
    escaped = False
    i = brace
    while i < len(text):
        ch = text[i]
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            i += 1
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

    raise RuntimeError(f"[V11T] {label}: closing brace not found")


def replace_region(
    text: str,
    start_token: str,
    end_token: str,
    replacement: str,
    label: str,
) -> str:
    start = text.find(start_token)
    if start < 0:
        raise RuntimeError(f"[V11T] {label}: start token missing")
    end = text.find(end_token, start)
    if end < 0:
        raise RuntimeError(f"[V11T] {label}: end token missing")
    return text[:start] + replacement + text[end:]


try:
    # ==================================================================
    # A. BUILD104 VISUAL/RUNTIME FOLLOW-UP
    # ==================================================================
    bg = sources["bg"]

    disk_cache_anchor = '''    private static let imageCache: NSCache<NSString, GhostBaseProfileBackgroundCacheEntry> = {
        let cache = NSCache<NSString, GhostBaseProfileBackgroundCacheEntry>()
        cache.countLimit = 64
        return cache
    }()
'''

    disk_cache_block = disk_cache_anchor + r'''
    // MARK: GhostBase v1.1T BUILD97_STATIC_AVATAR_CACHE1
    // A bounded persistent cache for the already-decoded 360px avatar
    // presentation. This is intentionally NOT a raw MediaBox decoder.
    private static let ghostBaseAvatarDiskCacheLock = NSLock()
    private static let ghostBaseAvatarDiskCacheLimit = 48

    private static func ghostBaseAvatarDiskCacheRoot() -> URL? {
        guard let caches = FileManager.default.urls(
            for: .cachesDirectory,
            in: .userDomainMask
        ).first else {
            return nil
        }
        return caches.appendingPathComponent(
            "GhostBaseProfileAvatarBackgrounds",
            isDirectory: true
        )
    }

    private static func ghostBaseSafeCacheComponent(_ value: String) -> String {
        let allowed = CharacterSet.alphanumerics.union(
            CharacterSet(charactersIn: "-_.")
        )
        return value.components(separatedBy: allowed.inverted)
            .filter { !$0.isEmpty }
            .joined(separator: "_")
    }

    private static func ghostBaseAvatarDiskCacheURL(
        identity: String
    ) -> URL? {
        guard let root = self.ghostBaseAvatarDiskCacheRoot() else {
            return nil
        }
        let name = self.ghostBaseSafeCacheComponent(identity)
        guard !name.isEmpty else {
            return nil
        }
        return root.appendingPathComponent(name + ".jpg")
    }

    private static func ghostBaseLoadAvatarDiskCache(
        identity: String
    ) -> UIImage? {
        self.ghostBaseAvatarDiskCacheLock.lock()
        defer { self.ghostBaseAvatarDiskCacheLock.unlock() }

        guard let url = self.ghostBaseAvatarDiskCacheURL(identity: identity),
              FileManager.default.fileExists(atPath: url.path),
              let image = UIImage(contentsOfFile: url.path) else {
            return nil
        }
        try? FileManager.default.setAttributes(
            [.modificationDate: Date()],
            ofItemAtPath: url.path
        )
        return image
    }

    private static func ghostBaseStoreAvatarDiskCache(
        _ image: UIImage,
        identity: String
    ) {
        guard let url = self.ghostBaseAvatarDiskCacheURL(identity: identity),
              let data = image.jpegData(compressionQuality: 0.88) else {
            return
        }

        self.ghostBaseAvatarDiskCacheLock.lock()
        defer { self.ghostBaseAvatarDiskCacheLock.unlock() }

        let fm = FileManager.default
        try? fm.createDirectory(
            at: url.deletingLastPathComponent(),
            withIntermediateDirectories: true
        )
        try? data.write(to: url, options: .atomic)

        guard let root = self.ghostBaseAvatarDiskCacheRoot(),
              let urls = try? fm.contentsOfDirectory(
                at: root,
                includingPropertiesForKeys: [.contentModificationDateKey],
                options: [.skipsHiddenFiles]
              ),
              urls.count > self.ghostBaseAvatarDiskCacheLimit else {
            return
        }

        let sorted = urls.sorted { lhs, rhs in
            let ld = (try? lhs.resourceValues(
                forKeys: [.contentModificationDateKey]
            ).contentModificationDate) ?? .distantPast
            let rd = (try? rhs.resourceValues(
                forKeys: [.contentModificationDateKey]
            ).contentModificationDate) ?? .distantPast
            return ld < rd
        }

        for old in sorted.prefix(
            max(0, sorted.count - self.ghostBaseAvatarDiskCacheLimit)
        ) {
            try? fm.removeItem(at: old)
        }
    }
'''

    if "GhostBase v1.1T BUILD97_STATIC_AVATAR_CACHE1" not in bg:
        bg = once(
            bg,
            disk_cache_anchor,
            disk_cache_block,
            "avatar decoded disk cache",
        )

    start = bg.find("    // MARK: GhostBase v1.1S STATIC_AVATAR_PIPELINE3\n")
    end = bg.find("    private func resourceEntrySignal(\n", start)
    if start < 0 or end < 0:
        raise RuntimeError("[V11T] static avatar signal boundaries missing")

    avatar_signal = r'''    // MARK: GhostBase v1.1T BUILD97_STATIC_AVATAR_PIPELINE1
    private func avatarEntrySignal(
        peer: EnginePeer,
        representation: TelegramMediaImageRepresentation,
        identity: String,
        fallback: UIColor
    ) -> Signal<GhostBaseProfileBackgroundCacheEntry?, NoError>? {
        // Exact good V11K/Build97 feed: Telegram owns avatar decoding and
        // produces a 360x360 unclipped presentation. Do not decode the raw
        // MediaBox resource as UIImage and do not request the 720px V11S path.
        guard let signal = peerAvatarImage(
            account: self.context.account,
            peerReference: PeerReference(peer),
            authorOfMessage: nil,
            representation: representation,
            displayDimensions: CGSize(width: 360.0, height: 360.0),
            clipStyle: .none,
            blurred: false,
            inset: 0.0,
            emptyColor: nil,
            synchronousLoad: false
        ) else {
            return nil
        }

        return signal
        |> deliverOn(Queue.concurrentDefaultQueue())
        |> map { versions -> GhostBaseProfileBackgroundCacheEntry? in
            guard let image = versions?.0 else {
                return nil
            }

            let tint = Self.sampledTint(
                from: image,
                fallback: fallback
            )

            Self.ghostBaseStoreAvatarDiskCache(
                image,
                identity: identity
            )

            return GhostBaseProfileBackgroundCacheEntry(
                image: image,
                tint: tint
            )
        }
    }

'''
    bg = bg[:start] + avatar_signal + bg[end:]

    old_static_blur = '''            // Static photos were still over-blurred in Build102. Lower only
            // this presentation layer. Animated avatars keep the proven alpha.
            if animatedSource == nil {
                self.blurView.alpha = reduced ? 0.38 : 0.60
            } else {
                self.blurView.alpha = 1.0
            }
'''
    new_static_blur = '''            // MARK: GhostBase v1.1T BUILD97_STATIC_AVATAR_BLUR1
            // Build104 proved 0.60 is still materially stronger than the
            // readable Build97 look. Lower ONLY the static-photo material.
            // Animated avatars keep the already-stable full-strength path.
            if animatedSource == nil {
                self.blurView.alpha = reduced ? 0.24 : 0.38
            } else {
                self.blurView.alpha = 1.0
            }
'''
    bg = once(
        bg,
        old_static_blur,
        new_static_blur,
        "static avatar blur strength",
    )

    old_cache_branch = '''            // MARK: GhostBase v1.1P AVATAR_REOPEN_CACHE1
            if let cached =
                Self.imageCache.object(
                    forKey: cacheKey
                ) {

                self.imageView.image = cached.image
                self.applyTint(
                    cached.tint,
                    fallback: fallback,
                    isDark: isDark,
                    reduced: reduced
                )
            } else {
                self.imageView.image = nil
            }
'''

    new_cache_branch = '''            // MARK: GhostBase v1.1T AVATAR_REOPEN_NO_GREY1
            // RAM cache first, then the small decoded-avatar disk cache.
            // Only if neither exists do we briefly expose the neutral fallback.
            if let cached = Self.imageCache.object(forKey: cacheKey) {
                self.imageView.image = cached.image
                self.applyTint(
                    cached.tint,
                    fallback: fallback,
                    isDark: isDark,
                    reduced: reduced
                )
            } else if let diskImage = Self.ghostBaseLoadAvatarDiskCache(
                identity: loadKey
            ) {
                let diskTint = Self.sampledTint(
                    from: diskImage,
                    fallback: fallback
                )
                let diskEntry = GhostBaseProfileBackgroundCacheEntry(
                    image: diskImage,
                    tint: diskTint
                )
                Self.imageCache.setObject(diskEntry, forKey: cacheKey)
                self.imageView.image = diskImage
                self.applyTint(
                    diskTint,
                    fallback: fallback,
                    isDark: isDark,
                    reduced: reduced
                )
            } else {
                self.imageView.image = nil
            }
'''

    bg = once(
        bg,
        old_cache_branch,
        new_cache_branch,
        "avatar reopen disk fallback",
    )
    sources["bg"] = bg

    groups = sources["groups"]
    groups = once(
        groups,
        "systemStyle: ghostBaseGlassEnabled ? .glass : .legacy",
        "systemStyle: .legacy",
        "Common Groups row system style",
    )

    old_groups_tint = '''            self.ghostBaseGlassTintView.backgroundColor =
                presentationData.theme.list.itemBlocksBackgroundColor
                    .withAlphaComponent(isDark ? 0.22 : 0.32)
'''
    new_groups_tint = '''            // MARK: GhostBase v1.1T COMMON_GROUPS_NO_BLACK1
            self.ghostBaseGlassTintView.backgroundColor = isDark
                ? UIColor.white.withAlphaComponent(0.055)
                : UIColor.black.withAlphaComponent(0.045)
'''
    groups = once(
        groups,
        old_groups_tint,
        new_groups_tint,
        "Common Groups neutral frost",
    )
    sources["groups"] = groups

    controls = sources["music_controls"]
    helper_start = controls.find(
        "    // MARK: GhostBase v1.1S MUSIC_TRANSLUCENT_SHEET1\n"
    )
    helper_end = controls.find(
        "    func updatePresentationData(_ presentationData: PresentationData) {\n",
        helper_start,
    )
    if helper_start < 0 or helper_end < 0:
        raise RuntimeError("[V11T] music controls helper boundaries missing")

    controls_helper = r'''    // MARK: GhostBase v1.1T MUSIC_READABLE_GLASS1
    private func updateGhostBaseGlassBackground() {
        let isDark = self.presentationData.theme.overallDarkAppearance
        self.backgroundNode.isHidden = self.ghostBaseGlassBackgroundEnabled

        if self.ghostBaseGlassBackgroundEnabled {
            self.ghostBaseGlassIsDark = isDark
            self.ghostBaseGlassEffectView.effect = UIBlurEffect(
                style: isDark
                    ? .systemUltraThinMaterialDark
                    : .systemUltraThinMaterialLight
            )
            self.ghostBaseGlassEffectView.alpha = 0.48
            self.ghostBaseGlassEffectView.isHidden = false
            self.ghostBaseGlassEffectView.backgroundColor = .clear
            self.ghostBaseGlassEffectView.contentView.backgroundColor = .clear
            self.ghostBaseGlassEffectView.layer.borderWidth = UIScreenPixel
            self.ghostBaseGlassEffectView.layer.borderColor = UIColor.white
                .withAlphaComponent(isDark ? 0.13 : 0.18).cgColor
            self.ghostBaseGlassTintView.backgroundColor = isDark
                ? UIColor.white.withAlphaComponent(0.070)
                : UIColor.black.withAlphaComponent(0.040)
        } else {
            self.ghostBaseGlassEffectView.isHidden = true
            self.ghostBaseGlassEffectView.effect = nil
            self.ghostBaseGlassEffectView.alpha = 1.0
            self.ghostBaseGlassEffectView.layer.borderWidth = 0.0
            self.ghostBaseGlassEffectView.layer.borderColor = nil
            self.ghostBaseGlassTintView.backgroundColor = .clear
        }
    }

'''
    controls = (
        controls[:helper_start]
        + controls_helper
        + controls[helper_end:]
    )
    sources["music_controls"] = controls

    controller = sources["music_controller"]
    old_header = '''        // MARK: GhostBase v1.1S MUSIC_HEADER_TRANSLUCENT1
        headerGlassView.effect = nil
        headerGlassView.alpha = 1.0
        headerGlassView.isHidden = false
        headerGlassView.backgroundColor = .clear
        headerGlassView.contentView.backgroundColor = .clear
        headerGlassView.layer.borderWidth = UIScreenPixel
        headerGlassView.layer.borderColor = UIColor.white
            .withAlphaComponent(isDark ? 0.12 : 0.20).cgColor
        headerTintView.backgroundColor =
            self.presentationData.theme.list.itemBlocksBackgroundColor
                .withAlphaComponent(isDark ? 0.22 : 0.34)
'''
    new_header = '''        // MARK: GhostBase v1.1T MUSIC_HEADER_READABLE_GLASS1
        headerGlassView.effect = UIBlurEffect(
            style: isDark
                ? .systemUltraThinMaterialDark
                : .systemUltraThinMaterialLight
        )
        headerGlassView.alpha = 0.46
        headerGlassView.isHidden = false
        headerGlassView.backgroundColor = .clear
        headerGlassView.contentView.backgroundColor = .clear
        headerGlassView.layer.borderWidth = UIScreenPixel
        headerGlassView.layer.borderColor = UIColor.white
            .withAlphaComponent(isDark ? 0.13 : 0.18).cgColor
        headerTintView.backgroundColor = isDark
            ? UIColor.white.withAlphaComponent(0.065)
            : UIColor.black.withAlphaComponent(0.038)
'''
    controller = once(
        controller,
        old_header,
        new_header,
        "music header readable glass",
    )
    sources["music_controller"] = controller

    # ==================================================================
    # B. DELETED PORTABLE REPLY / RECOVERED MEDIA V1
    # ==================================================================
    enqueue = sources["enqueue"]

    resolver_marker = "// MARK: GhostBase v1.1T BUILD105_FULL1"
    if resolver_marker in enqueue:
        raise RuntimeError("[V11T] resolver marker unexpectedly already present")

    insertion_token = "private func opportunisticallyTransformOutgoingMedia("
    insertion_pos = enqueue.find(insertion_token)
    if insertion_pos < 0:
        raise RuntimeError("[V11T] public enqueue integration token missing")

    resolver_swift = r'''// MARK: GhostBase v1.1T BUILD105_FULL1
// Deferred deleted-reply materialization. Composer/reply preview stay stock;
// only the public enqueue boundary converts a locally retained deleted reply.
private let ghostBaseDeletedPortableRepliesKey =
    "GhostBase.Messages.DeletedPortableReplies"
private let ghostBaseSaveDeletedKey =
    "GhostBase.Messages.SaveDeleted"
private let ghostBasePreserveDeletedMediaKey =
    "GhostBase.Messages.PreserveDeletedMedia"
private let ghostBaseDeletedMediaCacheLimitKey =
    "GhostBase.Messages.DeletedMediaCacheLimit"
private let ghostBaseDeletedMediaRetentionDaysKey =
    "GhostBase.Messages.DeletedMediaRetentionDays"

private func ghostBaseDeletedBool(
    _ key: String,
    defaultValue: Bool
) -> Bool {
    if let value = UserDefaults.standard.object(forKey: key) as? Bool {
        return value
    }
    return defaultValue
}

private enum GhostBasePublicPeerNameStore {
    private static let valuesKey = "GhostBase.PublicPeerNames.V11T"
    private static let orderKey = "GhostBase.PublicPeerNamesOrder.V11T"
    private static let maximumCount = 256
    private static let lock = NSLock()

    static func store(
        peerId: PeerId,
        firstName: String,
        lastName: String
    ) {
        let first = firstName.trimmingCharacters(in: .whitespacesAndNewlines)
        let last = lastName.trimmingCharacters(in: .whitespacesAndNewlines)
        let name = [first, last].filter { !$0.isEmpty }.joined(separator: " ")
        guard !name.isEmpty else {
            return
        }

        self.lock.lock()
        defer { self.lock.unlock() }

        let defaults = UserDefaults.standard
        var values = defaults.dictionary(
            forKey: self.valuesKey
        ) as? [String: String] ?? [:]
        var order = defaults.stringArray(forKey: self.orderKey) ?? []
        let key = String(peerId.toInt64())
        values[key] = name
        order.removeAll(where: { $0 == key })
        order.append(key)

        while order.count > self.maximumCount {
            let removed = order.removeFirst()
            values.removeValue(forKey: removed)
        }
        defaults.set(values, forKey: self.valuesKey)
        defaults.set(order, forKey: self.orderKey)
    }

    static func name(peerId: PeerId) -> String? {
        self.lock.lock()
        defer { self.lock.unlock() }
        return (
            UserDefaults.standard.dictionary(forKey: self.valuesKey)
            as? [String: String]
        )?[String(peerId.toInt64())]
    }
}

func ghostBaseStorePublicPeerName(
    peerId: PeerId,
    firstName: String,
    lastName: String
) {
    GhostBasePublicPeerNameStore.store(
        peerId: peerId,
        firstName: firstName,
        lastName: lastName
    )
}

private struct GhostBaseDeletedMediaResourceSpec {
    let resource: MediaResource
    let pathExtension: String?
}

private enum GhostBaseDeletedMediaCache {
    private static let queue = DispatchQueue(
        label: "org.ghostbase.deleted-media-cache",
        qos: .utility
    )
    private static let cleanupLock = NSLock()
    private static var lastCleanupTimestamp: TimeInterval = 0.0

    static func root(mediaBox: MediaBox) -> URL {
        return URL(fileURLWithPath: mediaBox.basePath, isDirectory: true)
            .appendingPathComponent(
                "ghostbase-deleted-media",
                isDirectory: true
            )
    }

    private static func safe(_ value: String) -> String {
        let allowed = CharacterSet.alphanumerics.union(
            CharacterSet(charactersIn: "-_.")
        )
        let result = value.components(separatedBy: allowed.inverted)
            .filter { !$0.isEmpty }
            .joined(separator: "_")
        return result.isEmpty ? "resource" : result
    }

    private static func messageDirectory(
        mediaBox: MediaBox,
        messageId: MessageId
    ) -> URL {
        let folder = "\(messageId.peerId.toInt64())_\(messageId.namespace)_\(messageId.id)"
        return self.root(mediaBox: mediaBox).appendingPathComponent(
            self.safe(folder),
            isDirectory: true
        )
    }

    static func spec(media: Media) -> GhostBaseDeletedMediaResourceSpec? {
        if let image = media as? TelegramMediaImage,
           let largest = largestImageRepresentation(image.representations) {
            return GhostBaseDeletedMediaResourceSpec(
                resource: largest.resource,
                pathExtension: "jpg"
            )
        }

        if let file = media as? TelegramMediaFile {
            var ext: String?
            if let fileName = file.fileName {
                let value = (fileName as NSString).pathExtension
                if !value.isEmpty {
                    ext = value
                }
            }
            if ext == nil {
                switch file.mimeType.lowercased() {
                case "video/mp4":
                    ext = "mp4"
                case "audio/ogg", "audio/opus":
                    ext = "ogg"
                case "audio/mpeg":
                    ext = "mp3"
                case "image/gif":
                    ext = "gif"
                default:
                    break
                }
            }
            return GhostBaseDeletedMediaResourceSpec(
                resource: file.resource,
                pathExtension: ext
            )
        }
        return nil
    }

    private static func fileURL(
        mediaBox: MediaBox,
        messageId: MessageId,
        spec: GhostBaseDeletedMediaResourceSpec
    ) -> URL {
        var name = self.safe(spec.resource.id.stringRepresentation)
        if let ext = spec.pathExtension, !ext.isEmpty {
            name += "." + self.safe(ext)
        } else {
            name += ".bin"
        }
        return self.messageDirectory(
            mediaBox: mediaBox,
            messageId: messageId
        ).appendingPathComponent(name)
    }

    private static func validFile(at url: URL) -> Bool {
        guard let attributes = try? FileManager.default.attributesOfItem(
            atPath: url.path
        ),
        let size = attributes[.size] as? NSNumber else {
            return false
        }
        return size.int64Value > 0
    }

    private static func copyCompleteResource(
        mediaBox: MediaBox,
        messageId: MessageId,
        spec: GhostBaseDeletedMediaResourceSpec
    ) -> String? {
        let destination = self.fileURL(
            mediaBox: mediaBox,
            messageId: messageId,
            spec: spec
        )
        let fm = FileManager.default

        if self.validFile(at: destination) {
            try? fm.setAttributes(
                [.modificationDate: Date()],
                ofItemAtPath: destination.path
            )
            return destination.path
        }

        guard let sourcePath = mediaBox.completedResourcePath(spec.resource),
              self.validFile(at: URL(fileURLWithPath: sourcePath)) else {
            return nil
        }

        do {
            try fm.createDirectory(
                at: destination.deletingLastPathComponent(),
                withIntermediateDirectories: true
            )
            if fm.fileExists(atPath: destination.path) {
                try fm.removeItem(at: destination)
            }
            try fm.copyItem(
                at: URL(fileURLWithPath: sourcePath),
                to: destination
            )
            guard self.validFile(at: destination) else {
                try? fm.removeItem(at: destination)
                return nil
            }
            return destination.path
        } catch {
            return nil
        }
    }

    static func resolvePath(
        mediaBox: MediaBox,
        messageId: MessageId,
        media: Media
    ) -> String? {
        guard let spec = self.spec(media: media) else {
            return nil
        }
        let path = self.copyCompleteResource(
            mediaBox: mediaBox,
            messageId: messageId,
            spec: spec
        )
        self.cleanupIfNeeded(mediaBox: mediaBox)
        return path
    }

    static func preserve(
        mediaBox: MediaBox,
        message: Message
    ) {
        guard ghostBaseDeletedBool(
            ghostBasePreserveDeletedMediaKey,
            defaultValue: true
        ) else {
            return
        }

        let messageId = message.id
        let specs = message.media.compactMap { self.spec(media: $0) }
        guard !specs.isEmpty else {
            return
        }

        self.queue.async {
            for spec in specs {
                _ = self.copyCompleteResource(
                    mediaBox: mediaBox,
                    messageId: messageId,
                    spec: spec
                )
            }
            self.cleanupIfNeeded(mediaBox: mediaBox)
        }
    }

    static func remove(
        mediaBox: MediaBox,
        messageIds: [MessageId]
    ) {
        guard !messageIds.isEmpty else {
            return
        }
        self.queue.async {
            let fm = FileManager.default
            for id in messageIds {
                try? fm.removeItem(
                    at: self.messageDirectory(
                        mediaBox: mediaBox,
                        messageId: id
                    )
                )
            }
        }
    }

    private static func cleanupIfNeeded(mediaBox: MediaBox) {
        let now = Date().timeIntervalSince1970
        self.cleanupLock.lock()
        if now - self.lastCleanupTimestamp < 300.0 {
            self.cleanupLock.unlock()
            return
        }
        self.lastCleanupTimestamp = now
        self.cleanupLock.unlock()

        let defaults = UserDefaults.standard
        let retentionDays = (
            defaults.object(forKey: ghostBaseDeletedMediaRetentionDaysKey)
            as? NSNumber
        )?.intValue ?? 30
        let limitBytes = (
            defaults.object(forKey: ghostBaseDeletedMediaCacheLimitKey)
            as? NSNumber
        )?.int64Value ?? (1024 * 1024 * 1024)

        let root = self.root(mediaBox: mediaBox)
        let fm = FileManager.default
        guard let enumerator = fm.enumerator(
            at: root,
            includingPropertiesForKeys: [
                .isRegularFileKey,
                .fileSizeKey,
                .contentModificationDateKey,
            ],
            options: [.skipsHiddenFiles]
        ) else {
            return
        }

        var files: [(URL, Int64, Date)] = []
        let cutoff: Date? = retentionDays < 0
            ? nil
            : Date(timeIntervalSinceNow: -Double(retentionDays) * 86400.0)

        for case let url as URL in enumerator {
            guard let values = try? url.resourceValues(
                forKeys: [
                    .isRegularFileKey,
                    .fileSizeKey,
                    .contentModificationDateKey,
                ]
            ), values.isRegularFile == true else {
                continue
            }
            let date = values.contentModificationDate ?? .distantPast
            if let cutoff, date < cutoff {
                try? fm.removeItem(at: url)
                continue
            }
            files.append((url, Int64(values.fileSize ?? 0), date))
        }

        if limitBytes >= 0 {
            var total = files.reduce(Int64(0)) { $0 + max(0, $1.1) }
            if total > limitBytes {
                for item in files.sorted(by: { $0.2 < $1.2 }) {
                    if total <= limitBytes {
                        break
                    }
                    try? fm.removeItem(at: item.0)
                    total -= max(0, item.1)
                }
            }
        }
    }
}

func ghostBaseScheduleDeletedMediaPreservation(
    mediaBox: MediaBox,
    message: Message
) {
    GhostBaseDeletedMediaCache.preserve(
        mediaBox: mediaBox,
        message: message
    )
}

func ghostBaseRemoveDeletedMediaCacheEntries(
    mediaBox: MediaBox,
    messageIds: [MessageId]
) {
    GhostBaseDeletedMediaCache.remove(
        mediaBox: mediaBox,
        messageIds: messageIds
    )
}

private struct GhostBaseDeletedReplyPlan {
    let outgoing: EnqueueMessage
    let source: Message?
    let authorName: String?
    let mentionPeerId: PeerId?
}

private struct GhostBaseDeletedQuoteBody {
    let text: String
    let originalTextOffset: Int?
}

private func ghostBaseDeletedMediaLabel(_ message: Message) -> String? {
    if message.groupingKey != nil && !message.media.isEmpty {
        return "Альбом"
    }

    guard let media = message.media.first else {
        return nil
    }
    if media is TelegramMediaPoll {
        return "Опрос"
    }
    if media is TelegramMediaMap {
        return "📍 Геолокация"
    }
    if media is TelegramMediaContact {
        return "👤 Контакт"
    }
    if media is TelegramMediaDice {
        return "🎲 Бросок кубика"
    }
    if media is TelegramMediaTodo {
        return "Список задач"
    }
    if media is TelegramMediaImage {
        return "📷 Фотография"
    }
    if let file = media as? TelegramMediaFile {
        if file.isSticker {
            return "Стикер"
        } else if file.isVoice {
            return "🎙 Голосовое сообщение"
        } else if file.isInstantVideo {
            return "🎥 Видеосообщение"
        } else if file.isAnimated {
            return "GIF"
        } else if file.isVideo {
            return "🎬 Видео"
        } else if file.isMusic {
            return "🎵 Аудиофайл"
        } else if let name = file.fileName, !name.isEmpty {
            return "📎 Файл: \(name)"
        } else {
            return "📎 Файл"
        }
    }
    return "Вложение"
}

private func ghostBaseQuoteBody(
    source: Message,
    recoveredMedia: Bool
) -> GhostBaseDeletedQuoteBody {
    let sourceText = source.text

    if recoveredMedia || source.media.isEmpty {
        return GhostBaseDeletedQuoteBody(
            text: sourceText,
            originalTextOffset: sourceText.isEmpty ? nil : 0
        )
    }

    let label = ghostBaseDeletedMediaLabel(source) ?? "Удалённое сообщение"
    if sourceText.isEmpty {
        return GhostBaseDeletedQuoteBody(
            text: label,
            originalTextOffset: nil
        )
    }
    let offset = (label as NSString).length + 1
    return GhostBaseDeletedQuoteBody(
        text: label + "\n" + sourceText,
        originalTextOffset: offset
    )
}

private func ghostBaseShiftEntities(
    _ entities: [MessageTextEntity],
    by offset: Int
) -> [MessageTextEntity] {
    guard offset != 0 else {
        return entities
    }
    return entities.map { entity in
        return MessageTextEntity(
            range: (entity.range.lowerBound + offset)
                ..< (entity.range.upperBound + offset),
            type: entity.type
        )
    }
}

private func ghostBaseOriginalQuoteableEntities(
    source: Message
) -> [MessageTextEntity] {
    guard !source.text.isEmpty,
          let attribute = source.attributes.first(
            where: { $0 is TextEntitiesMessageAttribute }
          ) as? TextEntitiesMessageAttribute else {
        return []
    }
    let length = (source.text as NSString).length
    guard length > 0 else {
        return []
    }
    return messageTextEntitiesInRange(
        entities: attribute.entities,
        range: NSRange(location: 0, length: length),
        onlyQuoteable: true
    ).filter { entity in
        if case .BlockQuote = entity.type {
            return false
        }
        return true
    }
}

private func ghostBaseBuildPortableDeletedReply(
    outgoing: EnqueueMessage,
    source: Message,
    authorName: String,
    mentionPeerId: PeerId?,
    recoveredMedia: AnyMediaReference?
) -> EnqueueMessage {
    guard case let .message(
        userText,
        requestedAttributes,
        inlineStickers,
        userMediaReference,
        threadId,
        _,
        replyToStoryId,
        localGroupingKey,
        correlationId,
        bubbleUpEmojiOrStickersets
    ) = outgoing else {
        return outgoing
    }

    let effectiveRecoveredMedia: AnyMediaReference? =
        userMediaReference == nil ? recoveredMedia : nil
    let body = ghostBaseQuoteBody(
        source: source,
        recoveredMedia: effectiveRecoveredMedia != nil
    )

    var quoteText = authorName
    let authorLength = (authorName as NSString).length
    var originalTextStart: Int?
    if !body.text.isEmpty {
        quoteText += "\n" + body.text
        if let inner = body.originalTextOffset {
            originalTextStart = authorLength + 1 + inner
        }
    }

    let separator = userText.isEmpty ? "" : "\n\n"
    let finalText = quoteText + separator + userText
    let quoteLength = (quoteText as NSString).length
    let userOffset = ((quoteText + separator) as NSString).length

    var entities: [MessageTextEntity] = []
    if let mentionPeerId, authorLength > 0 {
        entities.append(MessageTextEntity(
            range: 0 ..< authorLength,
            type: .TextMention(peerId: mentionPeerId)
        ))
    }

    let sourceLength = (source.text as NSString).length
    let collapse = sourceLength > 320
        || source.text.components(separatedBy: "\n").count > 4
    if quoteLength > 0 {
        entities.append(MessageTextEntity(
            range: 0 ..< quoteLength,
            type: .BlockQuote(isCollapsed: collapse)
        ))
    }

    if let originalTextStart {
        entities.append(contentsOf: ghostBaseShiftEntities(
            ghostBaseOriginalQuoteableEntities(source: source),
            by: originalTextStart
        ))
    }

    var attributes: [MessageAttribute] = []
    var userEntities: [MessageTextEntity] = []
    for attribute in requestedAttributes {
        if let textAttribute = attribute as? TextEntitiesMessageAttribute {
            userEntities.append(contentsOf: textAttribute.entities)
        } else if attribute is ReplyMessageAttribute {
            continue
        } else {
            attributes.append(attribute)
        }
    }
    entities.append(contentsOf: ghostBaseShiftEntities(
        userEntities,
        by: userOffset
    ))
    if !entities.isEmpty {
        attributes.append(TextEntitiesMessageAttribute(entities: entities))
    }

    return .message(
        text: finalText,
        attributes: attributes,
        inlineStickers: inlineStickers,
        mediaReference: userMediaReference ?? effectiveRecoveredMedia,
        threadId: threadId,
        replyToMessageId: nil,
        replyToStoryId: replyToStoryId,
        localGroupingKey: localGroupingKey,
        correlationId: correlationId,
        bubbleUpEmojiOrStickersets: bubbleUpEmojiOrStickersets
    )
}

private func ghostBaseReconstructedMedia(
    account: Account,
    peerId: PeerId,
    source: Message,
    outgoing: EnqueueMessage
) -> AnyMediaReference? {
    guard ghostBaseDeletedBool(
        ghostBasePreserveDeletedMediaKey,
        defaultValue: true
    ) else {
        return nil
    }

    guard peerId.namespace == Namespaces.Peer.CloudUser
        || peerId.namespace == Namespaces.Peer.CloudGroup
        || peerId.namespace == Namespaces.Peer.CloudChannel else {
        return nil
    }

    guard source.groupingKey == nil,
          source.media.count == 1 else {
        return nil
    }

    guard case let .message(
        _, attributes, _, userMedia, _, _, _, _, _, _
    ) = outgoing,
    userMedia == nil else {
        return nil
    }

    if attributes.contains(where: {
        $0 is OutgoingScheduleInfoMessageAttribute
    }) {
        return nil
    }

    let media = source.media[0]
    if let file = media as? TelegramMediaFile, file.isSticker {
        return nil
    }

    guard let path = GhostBaseDeletedMediaCache.resolvePath(
        mediaBox: account.postbox.mediaBox,
        messageId: source.id,
        media: media
    ) else {
        return nil
    }

    let fm = FileManager.default
    let fileSize = (
        ((try? fm.attributesOfItem(atPath: path))?[.size] as? NSNumber)
    )?.int64Value
    guard (fileSize ?? 0) > 0 else {
        return nil
    }

    let randomId = Int64.random(in: Int64.min ... Int64.max)
    let localResource = LocalFileReferenceMediaResource(
        localFilePath: path,
        randomId: randomId,
        isUniquelyReferencedTemporaryFile: false,
        size: fileSize
    )

    if let file = media as? TelegramMediaFile {
        let localFile = TelegramMediaFile(
            fileId: MediaId(
                namespace: Namespaces.Media.LocalFile,
                id: randomId
            ),
            partialReference: nil,
            resource: localResource,
            previewRepresentations: [],
            videoThumbnails: [],
            videoCover: nil,
            immediateThumbnailData: file.immediateThumbnailData,
            mimeType: file.mimeType,
            size: fileSize,
            attributes: file.attributes,
            alternativeRepresentations: []
        )
        return .standalone(media: localFile)
    }

    if let image = media as? TelegramMediaImage,
       let largest = largestImageRepresentation(image.representations) {
        let localRepresentation = TelegramMediaImageRepresentation(
            dimensions: largest.dimensions,
            resource: localResource,
            progressiveSizes: [],
            immediateThumbnailData: nil,
            hasVideo: false,
            isPersonal: false,
            typeHint: .generic
        )
        let localImage = TelegramMediaImage(
            imageId: MediaId(
                namespace: Namespaces.Media.LocalImage,
                id: randomId
            ),
            representations: [localRepresentation],
            videoRepresentations: [],
            immediateThumbnailData: image.immediateThumbnailData,
            emojiMarkup: nil,
            reference: nil,
            partialReference: nil,
            flags: [],
            video: nil
        )
        return .standalone(media: localImage)
    }

    return nil
}

private func ghostBaseResolveDeletedReplies(
    account: Account,
    peerId: PeerId,
    messages: [EnqueueMessage]
) -> Signal<[EnqueueMessage], NoError> {
    guard ghostBaseDeletedBool(
        ghostBaseSaveDeletedKey,
        defaultValue: true
    ), ghostBaseDeletedBool(
        ghostBaseDeletedPortableRepliesKey,
        defaultValue: true
    ) else {
        return .single(messages)
    }

    let ghostBaseCloudDestination =
        peerId.namespace == Namespaces.Peer.CloudUser
        || peerId.namespace == Namespaces.Peer.CloudGroup
        || peerId.namespace == Namespaces.Peer.CloudChannel

    return account.postbox.transaction { transaction -> [GhostBaseDeletedReplyPlan] in
        return messages.map { outgoing in
            guard case let .message(
                _, _, _, _, _, replySubject, _, _, _, _
            ) = outgoing,
            let replySubject,
            let source = transaction.getMessage(replySubject.messageId),
            let deletedAttribute = source.attributes.first(
                where: { $0 is GhostBaseMessageAttribute }
            ) as? GhostBaseMessageAttribute,
            deletedAttribute.isDeleted else {
                return GhostBaseDeletedReplyPlan(
                    outgoing: outgoing,
                    source: nil,
                    authorName: nil,
                    mentionPeerId: nil
                )
            }

            let authorPeer = source.author
            let authorName: String
            if let authorPeer,
               let stored = GhostBasePublicPeerNameStore.name(
                peerId: authorPeer.id
               ), !stored.isEmpty {
                authorName = stored
            } else if let authorPeer {
                let title = EnginePeer(authorPeer).compactDisplayTitle
                authorName = title.isEmpty ? "Пользователь" : title
            } else {
                authorName = "Пользователь"
            }

            var mentionPeerId: PeerId?
            if ghostBaseCloudDestination,
               let authorPeer,
               authorPeer.id.namespace == Namespaces.Peer.CloudUser,
               apiInputUser(authorPeer) != nil {
                mentionPeerId = authorPeer.id
            }

            return GhostBaseDeletedReplyPlan(
                outgoing: outgoing,
                source: source,
                authorName: authorName,
                mentionPeerId: mentionPeerId
            )
        }
    }
    |> mapToSignal { plans -> Signal<[EnqueueMessage], NoError> in
        return Signal { subscriber in
            DispatchQueue.global(qos: .utility).async {
                var result: [EnqueueMessage] = []
                result.reserveCapacity(plans.count)

                for plan in plans {
                    guard let source = plan.source,
                          let authorName = plan.authorName else {
                        result.append(plan.outgoing)
                        continue
                    }

                    let recovered = ghostBaseReconstructedMedia(
                        account: account,
                        peerId: peerId,
                        source: source,
                        outgoing: plan.outgoing
                    )

                    var candidate = ghostBaseBuildPortableDeletedReply(
                        outgoing: plan.outgoing,
                        source: source,
                        authorName: authorName,
                        mentionPeerId: plan.mentionPeerId,
                        recoveredMedia: recovered
                    )
                    if recovered != nil,
                       case let .message(text, _, _, _, _, _, _, _, _, _) = candidate,
                       (text as NSString).length > 1024 {
                        candidate = ghostBaseBuildPortableDeletedReply(
                            outgoing: plan.outgoing,
                            source: source,
                            authorName: authorName,
                            mentionPeerId: plan.mentionPeerId,
                            recoveredMedia: nil
                        )
                    }
                    result.append(candidate)
                }

                subscriber.putNext(result)
                subscriber.putCompletion()
            }
            return EmptyDisposable
        }
    }
}

'''

    enqueue = enqueue[:insertion_pos] + resolver_swift + enqueue[insertion_pos:]

    public_signature = (
        "public func enqueueMessages(account: Account, peerId: PeerId, "
        "messages: [EnqueueMessage]) -> Signal<[MessageId?], NoError>"
    )
    public_start, public_end = balanced_region(
        enqueue,
        public_signature,
        label="public enqueueMessages",
    )
    original_function = enqueue[public_start:public_end]
    renamed = original_function.replace(
        public_signature,
        "private func ghostBaseEnqueueResolvedMessages(account: Account, peerId: PeerId, messages: [EnqueueMessage]) -> Signal<[MessageId?], NoError>",
        1,
    )
    wrapper = r'''

public func enqueueMessages(
    account: Account,
    peerId: PeerId,
    messages: [EnqueueMessage]
) -> Signal<[MessageId?], NoError> {
    return ghostBaseResolveDeletedReplies(
        account: account,
        peerId: peerId,
        messages: messages
    )
    |> mapToSignal { resolvedMessages in
        return ghostBaseEnqueueResolvedMessages(
            account: account,
            peerId: peerId,
            messages: resolvedMessages
        )
    }
}
'''
    enqueue = (
        enqueue[:public_start]
        + renamed
        + wrapper
        + enqueue[public_end:]
    )
    sources["enqueue"] = enqueue

    # --------------------------------------------------------------
    # B2. Delete hooks: complete media is copied asynchronously into the
    #     dedicated cache before/while the retained local Message is marked
    #     deleted. No forced download and no large transaction copy.
    # --------------------------------------------------------------
    state = sources["state"]

    global_anchor = '''                        transaction.updateMessage(id, update: { currentMessage in
                            var updatedAttributes = currentMessage.attributes
'''
    global_new = '''                        transaction.updateMessage(id, update: { currentMessage in
                            // MARK: GhostBase v1.1T DELETED_MEDIA_PRESERVE_GLOBAL1
                            ghostBaseScheduleDeletedMediaPreservation(
                                mediaBox: mediaBox,
                                message: currentMessage
                            )
                            var updatedAttributes = currentMessage.attributes
'''
    state = once(
        state,
        global_anchor,
        global_new,
        "global deleted-media preservation hook",
    )

    local_anchor = '''                        guard let currentMessage = transaction.getMessage(id) else {
                            continue
                        }
                        var updatedAttributes = currentMessage.attributes
'''
    local_new = '''                        guard let currentMessage = transaction.getMessage(id) else {
                            continue
                        }
                        // MARK: GhostBase v1.1T DELETED_MEDIA_PRESERVE_LOCAL1
                        ghostBaseScheduleDeletedMediaPreservation(
                            mediaBox: mediaBox,
                            message: currentMessage
                        )
                        var updatedAttributes = currentMessage.attributes
'''
    state = once(
        state,
        local_anchor,
        local_new,
        "local deleted-media preservation hook",
    )

    user_name_anchor = '''            case let .updateUserName(updateUserNameData):
                let (userId, usernames) = (updateUserNameData.userId, updateUserNameData.usernames)
'''
    user_name_new = '''            case let .updateUserName(updateUserNameData):
                let (userId, usernames) = (updateUserNameData.userId, updateUserNameData.usernames)
                // MARK: GhostBase v1.1T PUBLIC_NAME_SNAPSHOT1
                // Raw updateUserName carries the self-set public profile name,
                // separate from a local contact alias.
                ghostBaseStorePublicPeerName(
                    peerId: PeerId(
                        namespace: Namespaces.Peer.CloudUser,
                        id: PeerId.Id._internalFromInt64Value(userId)
                    ),
                    firstName: updateUserNameData.firstName,
                    lastName: updateUserNameData.lastName
                )
'''
    state = once(
        state,
        user_name_anchor,
        user_name_new,
        "public-name update snapshot",
    )
    sources["state"] = state

    delete = sources["delete"]
    self_anchor = '''            if isOwnMessage && !isGhostBaseDeleted {
                transaction.updateMessage(messageId, update: { currentMessage in
'''
    self_new = '''            if isOwnMessage && !isGhostBaseDeleted {
                // MARK: GhostBase v1.1T DELETED_MEDIA_PRESERVE_SELF1
                ghostBaseScheduleDeletedMediaPreservation(
                    mediaBox: postbox.mediaBox,
                    message: message
                )
                transaction.updateMessage(messageId, update: { currentMessage in
'''
    delete = once(
        delete,
        self_anchor,
        self_new,
        "self first-stage preservation hook",
    )

    physical_anchor = '''    if !ghostBasePhysicalDeleteMessageIds.isEmpty {
        _internal_deleteMessages(transaction: transaction, mediaBox: postbox.mediaBox, ids: ghostBasePhysicalDeleteMessageIds.map(\\.messageId))
    }
'''
    physical_new = '''    if !ghostBasePhysicalDeleteMessageIds.isEmpty {
        // MARK: GhostBase v1.1T DELETED_MEDIA_FINAL_DELETE1
        let ghostBasePhysicalIds = ghostBasePhysicalDeleteMessageIds.map(\\.messageId)
        ghostBaseRemoveDeletedMediaCacheEntries(
            mediaBox: postbox.mediaBox,
            messageIds: ghostBasePhysicalIds
        )
        _internal_deleteMessages(
            transaction: transaction,
            mediaBox: postbox.mediaBox,
            ids: ghostBasePhysicalIds
        )
    }
'''
    delete = once(
        delete,
        physical_anchor,
        physical_new,
        "second physical delete cache cleanup",
    )
    sources["delete"] = delete

    # --------------------------------------------------------------
    # B3. Feature gates in the final materialized GhostBase Settings.
    # --------------------------------------------------------------
    settings = sources["settings"]

    settings = once(
        settings,
        '    static let showRamUnderClock = "GhostBase.Appearance.ShowRamUnderClock"\n',
        '    // MARK: GhostBase v1.1T DELETED_PORTABLE_SETTINGS1\n'
        '    static let deletedPortableReplies = "GhostBase.Messages.DeletedPortableReplies"\n'
        '    static let preserveDeletedMedia = "GhostBase.Messages.PreserveDeletedMedia"\n'
        '    static let deletedMediaCacheLimit = "GhostBase.Messages.DeletedMediaCacheLimit"\n'
        '    static let deletedMediaRetentionDays = "GhostBase.Messages.DeletedMediaRetentionDays"\n'
        '    static let showRamUnderClock = "GhostBase.Appearance.ShowRamUnderClock"\n',
        "deleted portable settings keys",
    )

    settings = once(
        settings,
        "    var showRamUnderClock: Bool\n",
        "    var deletedPortableReplies: Bool\n"
        "    var preserveDeletedMedia: Bool\n"
        "    var showRamUnderClock: Bool\n",
        "deleted portable settings state",
    )

    load_anchor = re.compile(
        r"(?P<indent>\s*)showRamUnderClock:\s*ghostBaseBool\(\s*GhostBaseKey\.showRamUnderClock,\s*defaultValue:\s*false\s*\),\n"
    )
    m = load_anchor.search(settings)
    if not m:
        raise RuntimeError("[V11T] settings showRamUnderClock load anchor missing")
    indent = m.group("indent")
    load_insert = (
        f"{indent}deletedPortableReplies: ghostBaseBool(\n"
        f"{indent}    GhostBaseKey.deletedPortableReplies,\n"
        f"{indent}    defaultValue: true\n"
        f"{indent}),\n"
        f"{indent}preserveDeletedMedia: ghostBaseBool(\n"
        f"{indent}    GhostBaseKey.preserveDeletedMedia,\n"
        f"{indent}    defaultValue: true\n"
        f"{indent}),\n"
    )
    settings = settings[:m.start()] + load_insert + m.group(0) + settings[m.end():]

    save_anchor = '''        UserDefaults.standard.set(
            self.showRamUnderClock,
            forKey: GhostBaseKey.showRamUnderClock
        )
'''
    save_new = '''        UserDefaults.standard.set(
            self.deletedPortableReplies,
            forKey: GhostBaseKey.deletedPortableReplies
        )
        UserDefaults.standard.set(
            self.preserveDeletedMedia,
            forKey: GhostBaseKey.preserveDeletedMedia
        )
        if UserDefaults.standard.object(
            forKey: GhostBaseKey.deletedMediaCacheLimit
        ) == nil {
            UserDefaults.standard.set(
                Int64(1024 * 1024 * 1024),
                forKey: GhostBaseKey.deletedMediaCacheLimit
            )
        }
        if UserDefaults.standard.object(
            forKey: GhostBaseKey.deletedMediaRetentionDays
        ) == nil {
            UserDefaults.standard.set(
                30,
                forKey: GhostBaseKey.deletedMediaRetentionDays
            )
        }
        UserDefaults.standard.set(
            self.showRamUnderClock,
            forKey: GhostBaseKey.showRamUnderClock
        )
'''
    settings = once(
        settings,
        save_anchor,
        save_new,
        "deleted portable settings save/default policy",
    )

    messages_start = settings.find("    if page == .messages {\n")
    messages_end = settings.find("\n    if page == .protectedContent {\n", messages_start)
    if messages_start < 0 or messages_end < 0:
        raise RuntimeError("[V11T] Settings Messages page region missing")
    messages_region = settings[messages_start:messages_end]
    close_list = messages_region.rfind("        ]")
    if close_list < 0:
        raise RuntimeError("[V11T] Settings Messages return-list boundary missing")
    insertion = '''            .header(4, "Удалённые ответы"),
            .toggle(
                4,
                90,
                GhostBaseKey.deletedPortableReplies,
                "Переносимый ответ на удалённое",
                state.deletedPortableReplies
            ),
            .toggle(
                4,
                91,
                GhostBaseKey.preserveDeletedMedia,
                "Сохранять удалённые медиа",
                state.preserveDeletedMedia
            ),
            .info(
                4,
                "Ответ материализуется только после Send. Медиа хранится только во внутреннем кэше GhostBase: до 1 ГБ, 30 дней; если bytes недоступны, используется текстовый fallback."
            ),
'''
    prefix = messages_region[:close_list]
    stripped = prefix.rstrip()
    if stripped and not stripped.endswith(","):
        prefix = stripped + ",\n"
    messages_region = prefix + insertion + messages_region[close_list:]
    settings = settings[:messages_start] + messages_region + settings[messages_end:]

    switch_anchor = "            case GhostBaseKey.showRamUnderClock:\n"
    switch_insert = '''            case GhostBaseKey.deletedPortableReplies:
                updated.deletedPortableReplies = value
                UserDefaults.standard.set(
                    value,
                    forKey: GhostBaseKey.deletedPortableReplies
                )

            case GhostBaseKey.preserveDeletedMedia:
                updated.preserveDeletedMedia = value
                UserDefaults.standard.set(
                    value,
                    forKey: GhostBaseKey.preserveDeletedMedia
                )

'''
    settings = once(
        settings,
        switch_anchor,
        switch_insert + switch_anchor,
        "deleted portable settings update cases",
    )
    sources["settings"] = settings

    for name, path in PATHS.items():
        path.write_text(sources[name], encoding="utf-8")

except Exception:
    for name, path in PATHS.items():
        try:
            path.write_text(backups[name], encoding="utf-8")
        except Exception:
            pass
    raise

print("[V11T] BUILD105_FULL1 materialized")
print("[V11T] blur: Build97 360px Telegram avatar feed + decoded disk reopen cache + lighter static material")
print("[V11T] Common Groups: legacy transparent rows + neutral frost; black owner removed")
print("[V11T] music: one weak UltraThin glass sheet/header over live PeerInfo")
print("[V11T] deleted reply: deferred send-time TextMention + BlockQuote portable payload")
print("[V11T] recovered media: internal 1 GiB/30d cache; native photo/voice/video/GIF/audio/document re-upload")
print("[V11T] delete hooks: global/local/self preserve complete bytes; second physical delete removes cache entry")
print("[V11T] settings: portable reply + preserve media gates; RAM/Premium/Gifts/Quote/History untouched")
