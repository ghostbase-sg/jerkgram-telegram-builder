#!/usr/bin/env python3
import os
import re
import atexit
import subprocess
from pathlib import Path

ROOT = Path(os.environ.get('GHOSTBASE_SOURCE_ROOT', '/root/gb_builder/work/swiftgram-src'))
# MARK: GhostBase v1.1P CI_OFFICIAL_MINITREE1
#
# V11P needs exact pristine Telegram 12.9.2 bytes for:
#   - renderer preflight
#   - PeerInfo section restore
#   - OverlayAudioPlayer restore
#
# Do not depend on the Linux-only /root/gb_builder/ports tree.
# Materialize only the required Official files from the immutable
# Telegram commit already enforced by the canonical build probe.
OFFICIAL_COMMIT = (
    "6ad963e5b62d354da79040f388ae2b9132fb17b8"
)

_official_tmp_root = Path(
    os.environ.get(
        "RUNNER_TEMP",
        "/tmp"
    )
) / "ghostbase-v11p-official-12.9.2"

_official_required_files = (
    "submodules/AccountContext/Sources/"
    "UniversalVideoNode.swift",

    "submodules/TelegramUniversalVideoContent/Sources/"
    "NativeVideoContent.swift",

    "submodules/MediaPlayer/Sources/"
    "MediaPlayerNode.swift",

    "submodules/MediaPlayer/Sources/"
    "ChunkMediaPlayerV2.swift",

    "submodules/TelegramUI/Components/PeerInfo/"
    "PeerInfoScreen/Sources/"
    "PeerInfoScreenItemSectionContainerNode.swift",

    "submodules/TelegramUI/Sources/"
    "OverlayAudioPlayerControllerNode.swift",
)

for _rel in _official_required_files:
    _result = subprocess.run(
        [
            "git",
            "-C",
            str(ROOT),
            "show",
            f"{OFFICIAL_COMMIT}:{_rel}",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    if _result.returncode != 0:
        raise RuntimeError(
            "[V11P] cannot materialize Official Telegram "
            f"source {_rel} from {OFFICIAL_COMMIT}: "
            + _result.stderr.decode(
                "utf-8",
                errors="replace"
            )
        )

    _dst = (
        _official_tmp_root
        / _rel
    )

    _dst.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    _dst.write_bytes(
        _result.stdout
    )

OFFICIAL = _official_tmp_root

PEER = ROOT / 'submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources'
PRESENT = ROOT / 'submodules/TelegramPresentationData/Sources/Resources/PresentationResourcesItemList.swift'
SECTION = PEER / 'PeerInfoScreenItemSectionContainerNode.swift'
BG = PEER / 'GhostBaseProfileFullscreenBackground.swift'
SCREEN = PEER / 'PeerInfoScreen.swift'
HEADER = PEER / 'PeerInfoHeaderNode.swift'
HEADER_SINGLE = PEER / 'PeerInfoHeaderSingleLineTextFieldNode.swift'
HEADER_MULTI = PEER / 'PeerInfoHeaderMultiLineTextFieldNode.swift'
COVER = ROOT / 'submodules/TelegramUI/Components/PeerInfo/PeerInfoCoverComponent/Sources/PeerInfoCoverComponent.swift'
MEMBERS = PEER / 'Panes/PeerInfoMembersPane.swift'
GROUPS = PEER / 'Panes/PeerInfoGroupsInCommonPaneNode.swift'
GIFT = ROOT / 'submodules/TelegramUI/Components/Gifts/GiftViewScreen/Sources/GiftViewScreen.swift'
GIFT_PAGER = ROOT / 'submodules/TelegramUI/Components/Gifts/GiftViewScreen/Sources/GiftPagerComponent.swift'
MUSIC = ROOT / 'submodules/TelegramUI/Sources/OverlayAudioPlayerControllerNode.swift'
UNIVERSAL = ROOT / 'submodules/AccountContext/Sources/UniversalVideoNode.swift'
NATIVE = ROOT / 'submodules/TelegramUniversalVideoContent/Sources/NativeVideoContent.swift'
MEDIA_NODE = ROOT / 'submodules/MediaPlayer/Sources/MediaPlayerNode.swift'
CHUNK = ROOT / 'submodules/MediaPlayer/Sources/ChunkMediaPlayerV2.swift'
REPORT = PEER / 'GhostBaseProfileReportPaneNode.swift'

for p in (PRESENT, SECTION, BG, SCREEN, HEADER, HEADER_SINGLE, HEADER_MULTI, COVER, MEMBERS, GROUPS, GIFT, GIFT_PAGER, MUSIC, UNIVERSAL, NATIVE, MEDIA_NODE, CHUNK, REPORT):
    if not p.is_file():
        raise RuntimeError(f'[V11P] missing {p}')

MARK = '// MARK: GhostBase v1.1P FULLCORRECTION1'
if MARK in BG.read_text(encoding='utf-8'):
    already_gates = (
        (PRESENT, 'GhostBase v1.1P GLOBAL_GLASS_CORNERS1'),
        (SECTION, 'GhostBase v1.1P SECTION_OWNER1'),
        (MEDIA_NODE, 'GhostBase v1.1P SECONDARY_RENDER_OUTPUT1'),
        (CHUNK, 'GhostBase v1.1P CHUNK_SECONDARY_RENDER_OUTPUT1'),
        (UNIVERSAL, 'GhostBase v1.1P UNIVERSAL_SECONDARY_OUTPUT1'),
        (COVER, 'GhostBase v1.1P PREMIUM_COMPOSITE1'),
        (HEADER_SINGLE, 'GhostBase v1.1P HEADER_FIELD_GLASS_OWNER1'),
        (HEADER_MULTI, 'GhostBase v1.1P HEADER_FIELD_GLASS_OWNER1'),
        (MUSIC, 'GhostBase v1.1P MUSIC_REAL_PROFILE_GLASS1'),
    )
    missing = [str(path) for path, marker in already_gates if marker not in path.read_text(encoding='utf-8')]
    if missing:
        raise RuntimeError('[V11P] inconsistent partial materialization: ' + ', '.join(missing))
    print('[V11P] already materialized')
    raise SystemExit(0)

for rel in (
    'submodules/AccountContext/Sources/UniversalVideoNode.swift',
    'submodules/TelegramUniversalVideoContent/Sources/NativeVideoContent.swift',
    'submodules/MediaPlayer/Sources/MediaPlayerNode.swift',
    'submodules/MediaPlayer/Sources/ChunkMediaPlayerV2.swift',
):
    current_path = ROOT / rel
    official_path = OFFICIAL / rel
    if not official_path.is_file():
        raise RuntimeError(f'[V11P] missing audited Official renderer source: {official_path}')
    if current_path.read_bytes() != official_path.read_bytes():
        raise RuntimeError(f'[V11P] renderer preflight mismatch against Official: {rel}')

_original_bytes = {p: p.read_bytes() for p in (PRESENT, SECTION, BG, SCREEN, HEADER, HEADER_SINGLE, HEADER_MULTI, COVER, MEMBERS, GROUPS, GIFT, GIFT_PAGER, MUSIC, UNIVERSAL, NATIVE, MEDIA_NODE, CHUNK)}
_committed = False

def _rollback_uncommitted() -> None:
    if not _committed:
        for path, data in _original_bytes.items():
            path.write_bytes(data)

atexit.register(_rollback_uncommitted)

def one(text: str, old: str, new: str, label: str) -> str:
    c = text.count(old)
    if c != 1:
        raise RuntimeError(f'[V11P] {label}: expected 1, found {c}')
    return text.replace(old, new, 1)

def regex_one(text: str, pattern: str, repl: str, label: str, flags=re.S) -> str:
    updated, count = re.subn(pattern, repl, text, count=1, flags=flags)
    if count != 1:
        raise RuntimeError(f'[V11P] {label}: expected 1, found {count}')
    return updated

present = PRESENT.read_text(encoding='utf-8')
present = one(
    present,
    '    public static func cornersImage(_ theme: PresentationTheme, top: Bool, bottom: Bool, glass: Bool = false) -> UIImage? {\n        if !top && !bottom {\n            return nil\n        }\n',
    '''    // MARK: GhostBase v1.1P GLOBAL_GLASS_CORNERS1
    private static let ghostBaseGlassCornerSuppressionKey =
        "GhostBase.PresentationResourcesItemList.SuppressGlassCornerFiller"

    public static func withGhostBaseGlassCornerFillerSuppressed<T>(
        _ body: () -> T
    ) -> T {
        let dictionary = Thread.current.threadDictionary
        let key = self.ghostBaseGlassCornerSuppressionKey
        let previous = dictionary[key]
        dictionary[key] = true
        defer {
            if let previous {
                dictionary[key] = previous
            } else {
                dictionary.removeObject(forKey: key)
            }
        }
        return body()
    }

    public static func cornersImage(_ theme: PresentationTheme, top: Bool, bottom: Bool, glass: Bool = false) -> UIImage? {
        if glass,
           (Thread.current.threadDictionary[self.ghostBaseGlassCornerSuppressionKey] as? Bool) == true {
            return nil
        }
        if !top && !bottom {
            return nil
        }
''',
    'global glass corner gate'
)
PRESENT.write_text(present, encoding='utf-8')

off_section_path = OFFICIAL / 'submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoScreenItemSectionContainerNode.swift'
if not off_section_path.is_file():
    raise RuntimeError(f'[V11P] missing official section {off_section_path}')

section = off_section_path.read_text(encoding='utf-8')

section = one(
    section,
    'final class PeerInfoScreenItemSectionContainerNode: ASDisplayNode {\n',
    'final class PeerInfoScreenItemSectionContainerNode: ASDisplayNode {\n    // MARK: GhostBase v1.1P SECTION_OWNER1\n    private let ghostBaseGlassEnabled: Bool\n',
    'section glass property'
)

section = one(
    section,
    '    override init() {\n        self.backgroundNode = ASDisplayNode()\n',
    '    init(ghostBaseGlassEnabled: Bool = false) {\n        self.ghostBaseGlassEnabled = ghostBaseGlassEnabled\n        self.backgroundNode = ASDisplayNode()\n',
    'section init'
)

section = one(
    section,
    '        self.backgroundNode.backgroundColor = presentationData.theme.list.itemBlocksBackgroundColor\n        self.topSeparatorNode.backgroundColor = presentationData.theme.list.itemBlocksSeparatorColor\n        self.bottomSeparatorNode.backgroundColor = presentationData.theme.list.itemBlocksSeparatorColor\n',
    '''        if self.ghostBaseGlassEnabled {\n            let isDark = presentationData.theme.overallDarkAppearance\n            self.backgroundNode.backgroundColor = UIColor(\n                white: isDark ? 0.0 : 1.0,\n                alpha: isDark ? 0.13 : 0.16\n            )\n            self.itemContainerNode.backgroundColor = .clear\n            self.topSeparatorNode.backgroundColor = .clear\n            self.bottomSeparatorNode.backgroundColor = .clear\n        } else {\n            self.backgroundNode.backgroundColor = presentationData.theme.list.itemBlocksBackgroundColor\n            self.topSeparatorNode.backgroundColor = presentationData.theme.list.itemBlocksSeparatorColor\n            self.bottomSeparatorNode.backgroundColor = presentationData.theme.list.itemBlocksSeparatorColor\n        }\n''',
    'section material'
)

section = one(
    section,
    '            let itemHeight = itemNode.update(context: context, width: width, safeInsets: safeInsets, presentationData: presentationData, item: item, topItem: topItem, bottomItem: bottomItem, hasCorners: hasCorners, transition: itemTransition)\n',
    '''            let itemHeight: CGFloat
            if self.ghostBaseGlassEnabled {
                itemHeight = PresentationResourcesItemList.withGhostBaseGlassCornerFillerSuppressed {
                    itemNode.update(context: context, width: width, safeInsets: safeInsets, presentationData: presentationData, item: item, topItem: topItem, bottomItem: bottomItem, hasCorners: hasCorners, transition: itemTransition)
                }
            } else {
                itemHeight = itemNode.update(context: context, width: width, safeInsets: safeInsets, presentationData: presentationData, item: item, topItem: topItem, bottomItem: bottomItem, hasCorners: hasCorners, transition: itemTransition)
            }
''',
    'section scoped legacy corner suppression'
)

section = one(
    section,
    '        transition.updateFrame(node: self.backgroundNode, frame: CGRect(origin: CGPoint(x: 0.0, y: contentWithBackgroundOffset), size: CGSize(width: width, height: max(0.0, contentWithBackgroundHeight - contentWithBackgroundOffset))))\n',
    '''        transition.updateFrame(node: self.backgroundNode, frame: CGRect(origin: CGPoint(x: 0.0, y: contentWithBackgroundOffset), size: CGSize(width: width, height: max(0.0, contentWithBackgroundHeight - contentWithBackgroundOffset))))\n        if self.ghostBaseGlassEnabled {\n            let radius: CGFloat = hasCorners ? 16.0 : 0.0\n            self.backgroundNode.cornerRadius = radius\n            self.backgroundNode.clipsToBounds = hasCorners\n            self.itemContainerNode.cornerRadius = radius\n            self.itemContainerNode.clipsToBounds = hasCorners\n        }\n''',
    'section real rounded geometry'
)

SECTION.write_text(section, encoding='utf-8')

mp = MEDIA_NODE.read_text(encoding='utf-8')

mp = one(
    mp,
    '    public var updateVideoInHierarchy: ((Bool) -> Void)?\n    \n    private var videoNode: MediaPlayerNodeDisplayNode\n',
    '''    public var updateVideoInHierarchy: ((Bool) -> Void)?\n\n    // MARK: GhostBase v1.1P SECONDARY_RENDER_OUTPUT1\n    private var secondaryVideoLayers: [ObjectIdentifier: AVSampleBufferDisplayLayer] = [:]\n    var secondaryVideoLayersUpdated: (([AVSampleBufferDisplayLayer]) -> Void)?\n    private let captureProtected: Bool\n\n    var currentSecondaryVideoLayers: [AVSampleBufferDisplayLayer] {\n        return Array(self.secondaryVideoLayers.values)\n    }\n    \n    private var videoNode: MediaPlayerNodeDisplayNode\n''',
    'media secondary properties'
)

mp = one(
    mp,
    '    public init(backgroundThread: Bool = false, captureProtected: Bool = false) {\n        self.videoNode = MediaPlayerNodeDisplayNode()\n',
    '    public init(backgroundThread: Bool = false, captureProtected: Bool = false) {\n        self.captureProtected = captureProtected\n        self.videoNode = MediaPlayerNodeDisplayNode()\n',
    'media capture property init'
)

mp = one(
    mp,
    '''                if !self.currentRotationAngle.isEqual(to: rotationAngle) || !self.currentAspect.isEqual(to: aspect) {\n                    self.currentRotationAngle = rotationAngle\n                    self.currentAspect = aspect\n                    var transform = CGAffineTransform(rotationAngle: CGFloat(rotationAngle))\n                    if abs(rotationAngle).remainder(dividingBy: Double.pi) > 0.1 {\n                        transform = transform.scaledBy(x: CGFloat(aspect), y: CGFloat(1.0 / aspect))\n                    }\n                    if videoLayer.affineTransform() != transform {\n                        videoLayer.setAffineTransform(transform)\n                    }\n                }\n''',
    '''                var transform = CGAffineTransform(rotationAngle: CGFloat(rotationAngle))\n                if abs(rotationAngle).remainder(dividingBy: Double.pi) > 0.1 {\n                    transform = transform.scaledBy(x: CGFloat(aspect), y: CGFloat(1.0 / aspect))\n                }\n\n                if !self.currentRotationAngle.isEqual(to: rotationAngle) || !self.currentAspect.isEqual(to: aspect) {\n                    self.currentRotationAngle = rotationAngle\n                    self.currentAspect = aspect\n                    if videoLayer.affineTransform() != transform {\n                        videoLayer.setAffineTransform(transform)\n                    }\n                }\n\n                for secondaryLayer in self.secondaryVideoLayers.values {\n                    videoQueue.async {\n                        if secondaryLayer.controlTimebase !== timebase || secondaryLayer.status == .failed {\n                            secondaryLayer.flush()\n                            secondaryLayer.controlTimebase = timebase\n                        }\n                    }\n                    if secondaryLayer.affineTransform() != transform {\n                        secondaryLayer.setAffineTransform(transform)\n                    }\n                }\n''',
    'media state mirror'
)

mp = one(
    mp,
    '    private func startPolling() {\n',
    '''    public func addSecondaryVideoLayer(_ layer: AVSampleBufferDisplayLayer) {\n        assert(Queue.mainQueue().isCurrent())\n        let key = ObjectIdentifier(layer)\n        guard self.secondaryVideoLayers[key] == nil else {\n            return\n        }\n        if #available(iOS 13.0, *) {\n            layer.preventsCapture = self.captureProtected\n        }\n        layer.videoGravity = .resizeAspectFill\n        self.secondaryVideoLayers[key] = layer\n        self.updateState()\n        self.secondaryVideoLayersUpdated?(self.currentSecondaryVideoLayers)\n    }\n\n    public func removeSecondaryVideoLayer(_ layer: AVSampleBufferDisplayLayer) {\n        assert(Queue.mainQueue().isCurrent())\n        let key = ObjectIdentifier(layer)\n        guard self.secondaryVideoLayers.removeValue(forKey: key) != nil else {\n            return\n        }\n        layer.flushAndRemoveImage()\n        layer.controlTimebase = nil\n        self.secondaryVideoLayersUpdated?(self.currentSecondaryVideoLayers)\n    }\n\n    private static func enqueueSecondaryCopies(\n        _ sampleBuffer: CMSampleBuffer,\n        layers: [AVSampleBufferDisplayLayer]\n    ) {\n        for layer in layers where layer.isReadyForMoreMediaData {\n            var copy: CMSampleBuffer?\n            if CMSampleBufferCreateCopy(\n                allocator: kCFAllocatorDefault,\n                sampleBuffer: sampleBuffer,\n                sampleBufferOut: &copy\n            ) == noErr, let copy {\n                layer.enqueue(copy)\n            }\n        }\n    }\n\n    private func startPolling() {\n''',
    'media secondary api'
)

mp = mp.replace(
    '                        videoLayer.enqueue(frame.sampleBuffer)\n',
    '                        videoLayer.enqueue(frame.sampleBuffer)\n                        MediaPlayerNode.enqueueSecondaryCopies(frame.sampleBuffer, layers: strongSelf.currentSecondaryVideoLayers)\n'
)

if mp.count('enqueueSecondaryCopies(frame.sampleBuffer') != 2:
    raise RuntimeError('[V11P] expected exactly two legacy enqueue mirrors')

poll_flush = '''                        guard let strongSelf = node, let videoLayer = strongSelf.videoLayer else {\n                            return\n                        }\n                        videoLayer.flush()\n'''

poll_flush_new = '''                        guard let strongSelf = node, let videoLayer = strongSelf.videoLayer else {\n                            return\n                        }\n                        videoLayer.flush()\n                        for secondaryLayer in strongSelf.currentSecondaryVideoLayers {\n                            secondaryLayer.flush()\n                        }\n'''

if mp.count(poll_flush) != 2:
    raise RuntimeError(f'[V11P] media poll flush anchors expected 2 found {mp.count(poll_flush)}')

mp = mp.replace(poll_flush, poll_flush_new)

mp = one(
    mp,
    '    public func reset() {\n        self.videoLayer?.flush()\n    }\n',
    '''    public func reset() {\n        self.videoLayer?.flush()\n        for layer in self.secondaryVideoLayers.values {\n            layer.flush()\n        }\n    }\n''',
    'media reset'
)

MEDIA_NODE.write_text(mp, encoding='utf-8')

# -----------------------------------------------------------------------------
# 3b) PLAYER FAN-OUT — ChunkMediaPlayerV2
# -----------------------------------------------------------------------------
chunk = CHUNK.read_text(encoding='utf-8')

chunk = one(
    chunk,
    '    private var videoRenderer: AVSampleBufferDisplayLayer\n    private var audioRenderer: AVSampleBufferAudioRenderer?\n',
    '''    private var videoRenderer: AVSampleBufferDisplayLayer\n    // MARK: GhostBase v1.1P CHUNK_SECONDARY_RENDER_OUTPUT1\n    private var secondaryVideoRenderers: [ObjectIdentifier: AVSampleBufferDisplayLayer] = [:]\n    private var audioRenderer: AVSampleBufferAudioRenderer?\n''',
    'chunk secondary property'
)

chunk = one(
    chunk,
    '''        if #available(iOS 17.0, *) {\n            self.renderSynchronizer.addRenderer(self.videoRenderer.sampleBufferRenderer)\n        } else {\n            self.renderSynchronizer.addRenderer(self.videoRenderer)\n        }\n    }\n''',
    '''        if #available(iOS 17.0, *) {\n            self.renderSynchronizer.addRenderer(self.videoRenderer.sampleBufferRenderer)\n        } else {\n            self.renderSynchronizer.addRenderer(self.videoRenderer)\n        }\n\n        playerNode.secondaryVideoLayersUpdated = { [weak self] layers in\n            self?.updateSecondaryVideoRenderers(layers)\n        }\n        self.updateSecondaryVideoRenderers(playerNode.currentSecondaryVideoLayers)\n    }\n''',
    'chunk init callback'
)

chunk = one(
    chunk,
    '    private func updateInternalState() {\n',
    '''    private func updateSecondaryVideoRenderers(_ layers: [AVSampleBufferDisplayLayer]) {\n        assert(Queue.mainQueue().isCurrent())\n\n        let updated = Dictionary(uniqueKeysWithValues: layers.map { (ObjectIdentifier($0), $0) })\n        for (key, layer) in self.secondaryVideoRenderers where updated[key] == nil {\n            if #available(iOS 17.0, *) {\n                self.renderSynchronizer.removeRenderer(layer.sampleBufferRenderer)\n            } else {\n                self.renderSynchronizer.removeRenderer(layer)\n            }\n            layer.flushAndRemoveImage()\n        }\n        for (key, layer) in updated where self.secondaryVideoRenderers[key] == nil {\n            if #available(iOS 17.0, *) {\n                self.renderSynchronizer.addRenderer(layer.sampleBufferRenderer)\n            } else {\n                self.renderSynchronizer.addRenderer(layer)\n            }\n        }\n        self.secondaryVideoRenderers = updated\n\n        if self.videoIsRequestingMediaData {\n            if #available(iOS 17.0, *) {\n                self.videoRenderer.sampleBufferRenderer.stopRequestingMediaData()\n            } else {\n                self.videoRenderer.stopRequestingMediaData()\n            }\n            self.videoIsRequestingMediaData = false\n        }\n        self.updateInternalState()\n    }\n\n    private func updateInternalState() {\n''',
    'chunk renderer updater'
)

chunk = chunk.replace(
    'self.renderSynchronizer.removeRenderer(layer.sampleBufferRenderer)',
    'self.renderSynchronizer.removeRenderer(layer.sampleBufferRenderer, at: .invalid)'
)

chunk = chunk.replace(
    'self.renderSynchronizer.removeRenderer(layer)',
    'self.renderSynchronizer.removeRenderer(layer, at: .invalid)'
)

chunk = one(
    chunk,
    '''                    if #available(iOS 17.0, *) {\n                        self.videoRenderer.sampleBufferRenderer.flush()\n                    } else {\n                        self.videoRenderer.flush()\n                    }\n                    if let audioRenderer = self.audioRenderer {\n''',
    '''                    if #available(iOS 17.0, *) {\n                        self.videoRenderer.sampleBufferRenderer.flush()\n                    } else {\n                        self.videoRenderer.flush()\n                    }\n                    for layer in self.secondaryVideoRenderers.values {\n                        if #available(iOS 17.0, *) {\n                            layer.sampleBufferRenderer.flush()\n                        } else {\n                            layer.flush()\n                        }\n                    }\n                    if let audioRenderer = self.audioRenderer {\n''',
    'chunk seek flush'
)

chunk = one(
    chunk,
    '            let didNotifySentVideoFrames = self.didNotifySentVideoFrames\n            videoTarget.requestMediaDataWhenReady',
    '''            let didNotifySentVideoFrames = self.didNotifySentVideoFrames\n            let secondaryVideoTargets: [AVQueuedSampleBufferRendering] = self.secondaryVideoRenderers.values.map { layer in\n                if #available(iOS 17.0, *) {\n                    return layer.sampleBufferRenderer\n                } else {\n                    return layer\n                }\n            }\n            videoTarget.requestMediaDataWhenReady''',
    'chunk target snapshot'
)

chunk = one(
    chunk,
    'ChunkMediaPlayerV2.fillRendererBuffer(bufferTarget: videoTarget, loadedPartsMediaData: loadedPartsMediaData, isVideo: true)',
    'ChunkMediaPlayerV2.fillRendererBuffer(bufferTarget: videoTarget, secondaryVideoTargets: secondaryVideoTargets, loadedPartsMediaData: loadedPartsMediaData, isVideo: true)',
    'chunk video fill call'
)

chunk = one(
    chunk,
    'ChunkMediaPlayerV2.fillRendererBuffer(bufferTarget: audioTarget, loadedPartsMediaData: loadedPartsMediaData, isVideo: false)',
    'ChunkMediaPlayerV2.fillRendererBuffer(bufferTarget: audioTarget, secondaryVideoTargets: [], loadedPartsMediaData: loadedPartsMediaData, isVideo: false)',
    'chunk audio fill call'
)

chunk = one(
    chunk,
    '    private static func fillRendererBuffer(bufferTarget: AVQueuedSampleBufferRendering, loadedPartsMediaData: LoadedPartsMediaData, isVideo: Bool) -> (bufferIsReadyForMoreData: Bool, didEnqueue: Bool) {\n',
    '''    private static func enqueueSampleBuffer(\n        _ sampleBuffer: CMSampleBuffer,\n        primary: AVQueuedSampleBufferRendering,\n        secondaryVideoTargets: [AVQueuedSampleBufferRendering],\n        isVideo: Bool\n    ) {\n        primary.enqueue(sampleBuffer)\n        guard isVideo else {\n            return\n        }\n        for target in secondaryVideoTargets where target.isReadyForMoreMediaData {\n            var copy: CMSampleBuffer?\n            if CMSampleBufferCreateCopy(allocator: kCFAllocatorDefault, sampleBuffer: sampleBuffer, sampleBufferOut: &copy) == noErr, let copy {\n                target.enqueue(copy)\n            }\n        }\n    }\n\n    private static func fillRendererBuffer(bufferTarget: AVQueuedSampleBufferRendering, secondaryVideoTargets: [AVQueuedSampleBufferRendering], loadedPartsMediaData: LoadedPartsMediaData, isVideo: Bool) -> (bufferIsReadyForMoreData: Bool, didEnqueue: Bool) {\n''',
    'chunk fill signature'
)

fill_start = chunk.index('    private static func fillRendererBuffer(')
head, tail = chunk[:fill_start], chunk[fill_start:]

tail_count = tail.count('                    bufferTarget.enqueue(sampleBuffer)')
if tail_count != 2:
    raise RuntimeError(f'[V11P] chunk enqueue anchors expected 2 found {tail_count}')

tail = tail.replace(
    '                    bufferTarget.enqueue(sampleBuffer)',
    '                    ChunkMediaPlayerV2.enqueueSampleBuffer(sampleBuffer, primary: bufferTarget, secondaryVideoTargets: secondaryVideoTargets, isVideo: isVideo)'
)

chunk = head + tail
CHUNK.write_text(chunk, encoding='utf-8')


# -----------------------------------------------------------------------------
# 4) UniversalVideo secondary-output registration
# -----------------------------------------------------------------------------
uv = UNIVERSAL.read_text(encoding='utf-8')

uv = one(
    uv,
    'public protocol UniversalVideoContentNode: AnyObject {\n',
    '''// MARK: GhostBase v1.1P UNIVERSAL_SECONDARY_OUTPUT1
public protocol UniversalVideoSecondaryOutputContentNode: AnyObject {
    func addSecondaryVideoLayer(_ layer: AVSampleBufferDisplayLayer)
    func removeSecondaryVideoLayer(_ layer: AVSampleBufferDisplayLayer)
}

public protocol UniversalVideoContentNode: AnyObject {
''',
    'universal companion protocol'
)

uv = one(
    uv,
    '    public func play() {\n',
    '''    public func registerSecondaryVideoLayer(_ layer: AVSampleBufferDisplayLayer) -> Disposable? {
        assert(Queue.mainQueue().isCurrent())

        var didAttach = false
        let manager = self.manager
        let contentId = self.content.id

        manager.withUniversalVideoContent(id: contentId, { contentNode in
            if let contentNode = contentNode as? UniversalVideoSecondaryOutputContentNode {
                contentNode.addSecondaryVideoLayer(layer)
                didAttach = true
            }
        })

        guard didAttach else {
            return nil
        }

        return ActionDisposable {
            Queue.mainQueue().async {
                manager.withUniversalVideoContent(id: contentId, { contentNode in
                    (contentNode as? UniversalVideoSecondaryOutputContentNode)?.removeSecondaryVideoLayer(layer)
                })
                layer.flushAndRemoveImage()
            }
        }
    }

    public func play() {
''',
    'universal register api'
)

UNIVERSAL.write_text(uv, encoding='utf-8')


native = NATIVE.read_text(encoding='utf-8')

if 'import AVFoundation\n' not in native:
    native = one(
        native,
        'import Foundation\n',
        'import Foundation\nimport AVFoundation\n',
        'native AVFoundation import'
    )

native = one(
    native,
    'private final class NativeVideoContentNode: ASDisplayNode, UniversalVideoContentNode {\n',
    'private final class NativeVideoContentNode: ASDisplayNode, UniversalVideoContentNode, UniversalVideoSecondaryOutputContentNode {\n',
    'native conformance'
)

native = one(
    native,
    '    func updateLayout(size: CGSize, actualSize: CGSize, transition: ContainedViewLayoutTransition) {\n',
    '''    func addSecondaryVideoLayer(_ layer: AVSampleBufferDisplayLayer) {
        self.playerNode.addSecondaryVideoLayer(layer)
    }

    func removeSecondaryVideoLayer(_ layer: AVSampleBufferDisplayLayer) {
        self.playerNode.removeSecondaryVideoLayer(layer)
    }

    func updateLayout(size: CGSize, actualSize: CGSize, transition: ContainedViewLayoutTransition) {
''',
    'native secondary forwarding'
)

NATIVE.write_text(native, encoding='utf-8')


# -----------------------------------------------------------------------------
# 5) FULLSCREEN PROFILE
# -----------------------------------------------------------------------------
bg = BG.read_text(encoding='utf-8')

bg = one(
    bg,
    'import UIKit\n',
    'import UIKit\nimport AVFoundation\n',
    'background AVFoundation import'
)

bg = bg.replace('import UniversalMediaPlayer\n', '')
bg = bg.replace('import TelegramUniversalVideoContent\n', '')
bg = bg.replace('import GalleryUI\n', '')

bg = bg.replace(
    '''\n            if presentationData.chatWallpaper\n                != presentationData.theme.chat.defaultWallpaper {\n                return true\n            }\n''',
    '\n'
)

bg = one(
    bg,
    '''private struct GhostBaseAnimatedMediaSource {\n    let identity: String\n    let content: NativeVideoContent\n}\n''',
    '''private struct GhostBaseAnimatedMediaSource {
    let identity: String
}

private final class GhostBaseProfileMirrorVideoView: UIView {
    override class var layerClass: AnyClass {
        return AVSampleBufferDisplayLayer.self
    }

    var videoLayer: AVSampleBufferDisplayLayer {
        return self.layer as! AVSampleBufferDisplayLayer
    }

    override init(frame: CGRect) {
        super.init(frame: frame)

        self.isUserInteractionEnabled = false
        self.backgroundColor = .clear
        self.layer.isOpaque = false
        self.videoLayer.videoGravity = .resizeAspectFill
        self.isHidden = true
    }

    required init?(coder: NSCoder) {
        preconditionFailure("init(coder:) has not been implemented")
    }
}
''',
    'animated source descriptor'
)

# V11P background video state:
# structural replacement instead of fragile V11O comment matching.
visual_state_start = bg.find(
    "    // MARK: GhostBase v1.1O VISUALRESET1\n"
)

source_disposable_start = bg.find(
    "    private let sourceDisposable",
    visual_state_start
)

if visual_state_start < 0:
    raise RuntimeError(
        "[V11P] background video properties: "
        "VISUALRESET1 marker not found"
    )

if source_disposable_start < 0:
    raise RuntimeError(
        "[V11P] background video properties: "
        "sourceDisposable boundary not found"
    )

old_video_state = bg[
    visual_state_start:
    source_disposable_start
]

for required in (
    "private var videoNode: UniversalVideoNode?",
    "private var videoContent: NativeVideoContent?",
    "private var currentVideoIdentity: String?",
):
    count = old_video_state.count(required)

    if count != 1:
        raise RuntimeError(
            "[V11P] background video properties: "
            f"{required!r} count = {count}"
        )

new_video_state = (
    "    // MARK: GhostBase v1.1P VIDEO_MIRROR1\n"
    "    // One native Telegram decoder/timeline owns playback.\n"
    "    // The fullscreen backdrop is a secondary render output.\n"
    "    private let mirrorVideoView: GhostBaseProfileMirrorVideoView\n"
    "    private var desiredVideoIdentity: String?\n"
    "    private var secondaryVideoDisposable: Disposable?\n"
    "    private weak var lastAvatarVideoNode: UniversalVideoNode?\n"
    "\n"
    "    // Blur/tint intentionally use the proven Build97/V11K visual recipe.\n"
    "\n"
)

bg = (
    bg[:visual_state_start]
    + new_video_state
    + bg[source_disposable_start:]
)

bg = one(
    bg,
    '''        self.blurView = UIVisualEffectView(effect: nil)\n        self.blurView.isUserInteractionEnabled = false\n\n        self.tintView = UIView()\n''',
    '''        self.mirrorVideoView = GhostBaseProfileMirrorVideoView(frame: .zero)

        self.blurView = UIVisualEffectView(effect: nil)
        self.blurView.isUserInteractionEnabled = false

        self.tintView = UIView()
''',
    'mirror init'
)

bg = one(
    bg,
    '''        self.addSubview(self.imageView)\n        self.addSubview(self.blurView)\n        self.addSubview(self.tintView)\n''',
    '''        self.addSubview(self.imageView)
        self.addSubview(self.mirrorVideoView)
        self.addSubview(self.blurView)
        self.addSubview(self.tintView)
''',
    'mirror hierarchy'
)

bg = one(
    bg,
    '''        self.sourceDisposable.dispose()\n    }\n''',
    '''        self.secondaryVideoDisposable?.dispose()
        self.secondaryVideoDisposable = nil
        self.sourceDisposable.dispose()
    }
''',
    'background deinit'
)

bg = one(
    bg,
    '''        let bounds = self.bounds\n        self.imageView.frame = bounds\n\n        if let videoNode = self.videoNode {\n            videoNode.frame = bounds\n            videoNode.updateLayout(\n                size: bounds.size,\n                transition: .immediate\n            )\n        }\n\n        self.blurView.frame = bounds\n''',
    '''        let bounds = self.bounds
        self.imageView.frame = bounds
        self.mirrorVideoView.frame = bounds
        self.blurView.frame = bounds
''',
    'background layout mirror'
)

bg = regex_one(
    bg,
    r'''    override func didMoveToWindow\(\) \{.*?\n    \}\n\n    func update\(''',
    '''    override func didMoveToWindow() {
        super.didMoveToWindow()

        if self.window == nil {
            self.secondaryVideoDisposable?.dispose()
            self.secondaryVideoDisposable = nil
            self.mirrorVideoView.isHidden = true
        } else {
            self.refreshAnimatedVideoOwner(self.lastAvatarVideoNode)
        }
    }

    func update(''',
    'background didMoveToWindow'
)

bg = bg.replace(
    '''\n            if presentationData.chatWallpaper\n                != presentationData.theme.chat.defaultWallpaper {\n\n                return .wallpaper(\n                    presentationData.chatWallpaper,\n                    .globalWallpaper\n                )\n            }\n''',
    '\n'
)

bg = regex_one(
    bg,
    r'''    private func animatedAvatarSource\(.*?\n    \}\n\n    private func stateKey\(''',
    '''    private func animatedAvatarSource(
        peer: EnginePeer,
        item: PeerInfoAvatarListItem?,
        isSettings _: Bool
    ) -> GhostBaseAnimatedMediaSource? {
        guard
            self.settings.animatedBackgroundEnabled,
            !self.settings.reducedBlur,
            !UIAccessibility.isReduceTransparencyEnabled,
            !ProcessInfo.processInfo.isLowPowerModeEnabled,
            let item
        else {
            return nil
        }

        let videoRepresentations: [VideoRepresentationWithReference]

        switch item {
        case .custom:
            return nil
        case let .topImage(_, values, _):
            videoRepresentations = values
        case let .image(_, _, values, _, _, _):
            videoRepresentations = values
        }

        guard let video = videoRepresentations.last else {
            return nil
        }

        return GhostBaseAnimatedMediaSource(
            identity: "video:\\(peer.id.toInt64()):\\(String(describing: video.representation.resource.id)):\\(video.representation.startTimestamp ?? 0.0)"
        )
    }

    private func stateKey(''',
    'background animated identity'
)

bg = regex_one(
    bg,
    r'''    private func clearAnimatedMedia\(\) \{.*?\n    \}\n\n    private func applyAnimatedMedia\(.*?\n    \}\n\n    private func apply\(''',
    '''    private func clearAnimatedMedia() {
        self.secondaryVideoDisposable?.dispose()
        self.secondaryVideoDisposable = nil
        self.lastAvatarVideoNode = nil
        self.desiredVideoIdentity = nil
        self.mirrorVideoView.isHidden = true
        self.mirrorVideoView.videoLayer.flushAndRemoveImage()
    }

    private func applyAnimatedMedia(_ source: GhostBaseAnimatedMediaSource?) {
        let updatedIdentity = source?.identity

        if self.desiredVideoIdentity != updatedIdentity {
            self.secondaryVideoDisposable?.dispose()
            self.secondaryVideoDisposable = nil
            self.lastAvatarVideoNode = nil
            self.mirrorVideoView.videoLayer.flushAndRemoveImage()
            self.desiredVideoIdentity = updatedIdentity
        }

        if updatedIdentity == nil {
            self.mirrorVideoView.isHidden = true
        }
    }

    func refreshAnimatedVideoOwner(_ videoNode: UniversalVideoNode?) {
        self.lastAvatarVideoNode = videoNode

        guard
            self.window != nil,
            self.desiredVideoIdentity != nil,
            let videoNode
        else {
            return
        }

        if self.secondaryVideoDisposable == nil {
            self.secondaryVideoDisposable =
                videoNode.registerSecondaryVideoLayer(
                    self.mirrorVideoView.videoLayer
                )
        }

        self.mirrorVideoView.isHidden =
            self.secondaryVideoDisposable == nil
    }

    private func apply(''',
    'background mirror methods'
)

bg = one(
    bg,
    '''            self.applyAnimatedMedia(\n                animatedSource\n            )\n\n            self.imageView.image = nil\n            self.currentLoadKey = loadKey\n''',
    '''            self.applyAnimatedMedia(
                animatedSource
            )

            // MARK: GhostBase v1.1P AVATAR_REOPEN_CACHE1
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

            self.currentLoadKey = loadKey
''',
    'avatar cache hit'
)

bg = one(
    bg,
    '''                self.imageView.image = entry.image\n                self.applyTint(entry.tint, fallback: fallback, isDark: isDark, reduced: reduced)\n''',
    '''                Self.imageCache.setObject(
                    entry,
                    forKey: cacheKey
                )
                self.imageView.image = entry.image
                self.applyTint(
                    entry.tint,
                    fallback: fallback,
                    isDark: isDark,
                    reduced: reduced
                )
''',
    'avatar cache store'
)

bg = bg.replace(
    '// MARK: GhostBase v1.1N AVATARPIPELINE_FINAL1',
    '// MARK: GhostBase v1.1P AVATARPIPELINE_FINAL2'
)

bg = bg.replace(
    '// Telegram owns decoding/caching.\n        // GhostBase never permanently caches a possibly\n        // intermediate avatar UIImage.',
    '// Telegram owns resource decode/cache. GhostBase keeps only a bounded\n        // final UIImage presentation cache keyed by peerId+resourceId for reopen.'
)

bg = bg.replace(
    '// MARK: GhostBase v1.1G PROFILE_RUNTIME1',
    MARK + '\n// MARK: GhostBase v1.1G PROFILE_RUNTIME1',
    1
)

BG.write_text(bg, encoding='utf-8')


screen = SCREEN.read_text(encoding='utf-8')

header_call = '        let headerHeight = self.headerNode.update(width: layout.size.width, containerHeight: layout.size.height, containerInset: headerInset, statusBarHeight: layout.statusBarHeight ?? 0.0, navigationHeight: navigationHeight, isModalOverlay: layout.isModalOverlay, isMediaOnly: self.isMediaOnly, contentOffset: self.isMediaOnly ? 212.0 : self.scrollNode.view.contentOffset.y, paneContainerY: self.paneContainerNode.frame.minY, presentationData: self.presentationData, peer: self.data?.savedMessagesPeer ?? self.data?.peer, cachedData: self.data?.cachedData, threadData: self.data?.threadData, peerNotificationSettings: self.data?.peerNotificationSettings, threadNotificationSettings: self.data?.threadNotificationSettings, globalNotificationSettings: self.data?.globalNotificationSettings, statusData: self.data?.status, panelStatusData: self.customStatusData, isSecretChat: self.peerId.namespace == Namespaces.Peer.SecretChat, isContact: self.data?.isContact ?? false, isSettings: self.isSettings, state: self.state, profileGiftsContext: self.data?.profileGiftsContext, screenData: self.data, isSearching: self.searchDisplayController != nil, metrics: layout.metrics, deviceMetrics: layout.deviceMetrics, transition: self.headerNode.navigationTransition == nil ? transition : .immediate, additive: additive, animateHeader: transition.isAnimated && self.headerNode.navigationTransition == nil)\n'

screen = one(
    screen,
    header_call,
    header_call + '''
        self.ghostBaseProfileBackgroundView?.refreshAnimatedVideoOwner(
            self.headerNode.avatarListNode.avatarContainerNode.videoNode
        )
''',
    'screen post-header mirror refresh'
)

SCREEN.write_text(screen, encoding='utf-8')

# -----------------------------------------------------------------------------
# 6) PREMIUM COVER COMPOSITION
# -----------------------------------------------------------------------------
cover = COVER.read_text(encoding='utf-8')

cover = one(
    cover,
    '''        public func setGhostBaseBackgroundFillAlpha(\n            _ alpha: CGFloat\n        ) {\n            self.backgroundView.alpha = alpha\n            self.backgroundGradientLayer.opacity =\n                Float(alpha)\n        }\n''',
    '''        public func setGhostBaseBackgroundFillAlpha(
            _ alpha: CGFloat
        ) {
            self.backgroundView.alpha = alpha
            self.backgroundGradientLayer.opacity = Float(alpha)
        }

        // MARK: GhostBase v1.1P PREMIUM_COMPOSITE1
        public func setGhostBaseDecorationAlpha(_ alpha: CGFloat) {
            let alpha = max(0.0, min(1.0, alpha))
            let patternFraction =
                self.component?.patternTransitionFraction ?? 1.0
            let avatarGradientFraction =
                1.0 -
                (self.component?.avatarTransitionFraction ?? 0.0)

            self.avatarBackgroundPatternContentsLayer.opacity =
                Float(alpha)

            self.backgroundPatternContainer.alpha =
                patternFraction * alpha

            self.avatarBackgroundGradientLayer.opacity =
                Float(
                    avatarGradientFraction * alpha
                )
        }
''',
    'cover decoration api'
)

COVER.write_text(cover, encoding='utf-8')


header = HEADER.read_text(encoding='utf-8')

header = one(
    header,
    '''            backgroundCoverView\n                .setGhostBaseBackgroundFillAlpha(\n                    ghostBaseBlendCover\n                        ? 0.0\n                        : 1.0\n                )\n''',
    '''            backgroundCoverView
                .setGhostBaseBackgroundFillAlpha(
                    ghostBaseBlendCover
                        ? 0.0
                        : 1.0
                )

            let ghostBaseDecorationAlpha: CGFloat

            if ghostBaseBlendCover {
                ghostBaseDecorationAlpha =
                    self.ghostBaseProfileGlassSettings?
                        .avatarBlurInProfile == true
                    ? 0.08
                    : 0.16
            } else {
                ghostBaseDecorationAlpha = 1.0
            }

            backgroundCoverView
                .setGhostBaseDecorationAlpha(
                    ghostBaseDecorationAlpha
                )
''',
    'header decoration alpha'
)

HEADER.write_text(header, encoding='utf-8')


def patch_header_text_field(
    path: Path,
    label: str
) -> None:
    text = path.read_text(encoding='utf-8')

    old = '''        self.maskNode.image = hasCorners ? PresentationResourcesItemList.cornersImage(presentationData.theme, top: hasTopCorners, bottom: hasBottomCorners, glass: true) : nil
'''

    new = '''        // MARK: GhostBase v1.1P HEADER_FIELD_GLASS_OWNER1
        let ghostBaseGlassEnabled =
            GhostBaseProfileBlurSettings
                .loadEnabled() != nil

        if ghostBaseGlassEnabled {
            let isDark =
                presentationData
                    .theme
                    .overallDarkAppearance

            self.backgroundNode.backgroundColor =
                UIColor(
                    white:
                        isDark
                        ? 0.0
                        : 1.0,
                    alpha:
                        isDark
                        ? 0.13
                        : 0.16
                )

            self.maskNode.image = nil
            self.backgroundNode.cornerRadius =
                hasCorners
                ? 26.0
                : 0.0
            self.backgroundNode.clipsToBounds =
                hasCorners

            if hasTopCorners && hasBottomCorners {
                self.backgroundNode
                    .layer
                    .maskedCorners = [
                        .layerMinXMinYCorner,
                        .layerMaxXMinYCorner,
                        .layerMinXMaxYCorner,
                        .layerMaxXMaxYCorner
                    ]
            } else if hasTopCorners {
                self.backgroundNode
                    .layer
                    .maskedCorners = [
                        .layerMinXMinYCorner,
                        .layerMaxXMinYCorner
                    ]
            } else if hasBottomCorners {
                self.backgroundNode
                    .layer
                    .maskedCorners = [
                        .layerMinXMaxYCorner,
                        .layerMaxXMaxYCorner
                    ]
            } else {
                self.backgroundNode
                    .layer
                    .maskedCorners = []
            }
        } else {
            self.backgroundNode.backgroundColor =
                presentationData
                    .theme
                    .list
                    .itemBlocksBackgroundColor

            self.backgroundNode.cornerRadius = 0.0
            self.backgroundNode.clipsToBounds = false

            self.backgroundNode
                .layer
                .maskedCorners = [
                    .layerMinXMinYCorner,
                    .layerMaxXMinYCorner,
                    .layerMinXMaxYCorner,
                    .layerMaxXMaxYCorner
                ]

            self.maskNode.image =
                hasCorners
                ? PresentationResourcesItemList
                    .cornersImage(
                        presentationData.theme,
                        top: hasTopCorners,
                        bottom: hasBottomCorners,
                        glass: true
                    )
                : nil
        }
'''

    text = one(
        text,
        old,
        new,
        f'{label} glass corner owner'
    )

    path.write_text(
        text,
        encoding='utf-8'
    )


patch_header_text_field(
    HEADER_SINGLE,
    'single-line header field'
)

patch_header_text_field(
    HEADER_MULTI,
    'multi-line header field'
)


members = MEMBERS.read_text(
    encoding='utf-8'
)

members = members.replace(
    '? 0.12\n                            : 0.16',
    '? 0.045\n                            : 0.075',
    1
)

if '? 0.045\n                            : 0.075' not in members:
    raise RuntimeError(
        '[V11P] members low-alpha material not applied'
    )

MEMBERS.write_text(
    members,
    encoding='utf-8'
)


groups = GROUPS.read_text(
    encoding='utf-8'
)

groups = groups.replace(
    '? 0.12\n                            : 0.16',
    '? 0.045\n                            : 0.075',
    1
)

groups = one(
    groups,
    '    func item(context: AccountContext, presentationData: PresentationData, openPeer: @escaping (EnginePeer) -> Void, openPeerContextAction: @escaping (EnginePeer, ASDisplayNode, ContextGesture?) -> Void) -> ListViewItem {\n',
    '    func item(context: AccountContext, presentationData: PresentationData, ghostBaseGlassEnabled: Bool, openPeer: @escaping (EnginePeer) -> Void, openPeerContextAction: @escaping (EnginePeer, ASDisplayNode, ContextGesture?) -> Void) -> ListViewItem {\n',
    'group item signature'
)

needle = 'return ItemListPeerItem(presentationData: ItemListPresentationData(presentationData), dateTimeFormat:'

groups = one(
    groups,
    needle,
    'return ItemListPeerItem(presentationData: ItemListPresentationData(presentationData), systemStyle: ghostBaseGlassEnabled ? .glass : .legacy, dateTimeFormat:',
    'group row system style'
)

groups = one(
    groups,
    '}, hasTopStripe: false, noInsets: true, noCorners: true, style: .plain)\n',
    '}, hasTopStripe: false, noInsets: true, noCorners: true, style: .plain, displayBackground: !ghostBaseGlassEnabled)\n',
    'group row background'
)

groups = one(
    groups,
    'private func preparedTransition(from fromEntries: [GroupsInCommonListEntry], to toEntries: [GroupsInCommonListEntry], context: AccountContext, presentationData: PresentationData, openPeer:',
    'private func preparedTransition(from fromEntries: [GroupsInCommonListEntry], to toEntries: [GroupsInCommonListEntry], context: AccountContext, presentationData: PresentationData, ghostBaseGlassEnabled: Bool, openPeer:',
    'group transition signature'
)

groups = groups.replace(
    '.item(context: context, presentationData: presentationData, openPeer:',
    '.item(context: context, presentationData: presentationData, ghostBaseGlassEnabled: ghostBaseGlassEnabled, openPeer:'
)

if groups.count(
    'ghostBaseGlassEnabled: ghostBaseGlassEnabled, openPeer:'
) != 2:
    raise RuntimeError(
        '[V11P] group transition item calls not both updated'
    )

groups = one(
    groups,
    'let transaction = preparedTransition(from: self.currentEntries, to: entries, context: self.context, presentationData: presentationData, openPeer:',
    'let transaction = preparedTransition(from: self.currentEntries, to: entries, context: self.context, presentationData: presentationData, ghostBaseGlassEnabled: self.ghostBaseGlassEnabled, openPeer:',
    'group transition call'
)

GROUPS.write_text(
    groups,
    encoding='utf-8'
)


gift = GIFT.read_text(
    encoding='utf-8'
)

gift = one(
    gift,
    '''                            ? 0.16\n                            : 0.20\n''',
    '''                            ? 0.56\n                            : 0.64\n''',
    'opened gift material'
)

GIFT.write_text(
    gift,
    encoding='utf-8'
)


pager = GIFT_PAGER.read_text(
    encoding='utf-8'
)

pager = one(
    pager,
    '? 0.12\n                        : 0.4',
    '? 0.28\n                        : 0.4',
    'gift pager dim'
)

GIFT_PAGER.write_text(
    pager,
    encoding='utf-8'
)


off_music = (
    OFFICIAL
    / 'submodules/TelegramUI/Sources/OverlayAudioPlayerControllerNode.swift'
)

if not off_music.is_file():
    raise RuntimeError(
        f'[V11P] missing official music controller {off_music}'
    )

music = off_music.read_text(
    encoding='utf-8'
)

music = one(
    music,
    '    func updatePresentationData(_ presentationData: PresentationData) {\n',
    '''    // MARK: GhostBase v1.1P MUSIC_REAL_PROFILE_GLASS1
    private var isGhostBaseProfileMusicActive: Bool {
        guard
            GhostBaseProfileBlurSettings
                .loadEnabled() != nil
        else {
            return false
        }

        if
            let playlistLocation =
                self.playlistLocation
                as? PeerMessagesPlaylistLocation,
            case .savedMusic = playlistLocation
        {
            return true
        }

        return false
    }

    private func updateGhostBaseMusicSurfaces() {
        guard self.isGhostBaseProfileMusicActive else {
            self.dimNode.backgroundColor =
                UIColor(
                    white: 0.0,
                    alpha: 0.5
                )

            self.historyBackgroundContentNode
                .backgroundColor =
                self.hasAnyHistoryMessages == true
                ? self.presentationData
                    .theme
                    .list
                    .itemModalBlocksBackgroundColor
                : self.presentationData
                    .theme
                    .list
                    .modalPlainBackgroundColor

            self.historyFrameLeftOverlayNode
                .backgroundColor =
                self.hasAnyHistoryMessages == true
                ? self.presentationData
                    .theme
                    .list
                    .modalBlocksBackgroundColor
                : self.presentationData
                    .theme
                    .list
                    .modalPlainBackgroundColor

            self.historyFrameRightOverlayNode
                .backgroundColor =
                self.hasAnyHistoryMessages == true
                ? self.presentationData
                    .theme
                    .list
                    .modalBlocksBackgroundColor
                : self.presentationData
                    .theme
                    .list
                    .modalPlainBackgroundColor

            self.historyFrameTopOverlayNode
                .backgroundColor =
                self.hasAnyHistoryMessages == true
                ? self.presentationData
                    .theme
                    .list
                    .modalBlocksBackgroundColor
                : self.presentationData
                    .theme
                    .list
                    .modalPlainBackgroundColor

            self.historyFrameTopMaskNode.alpha = 1.0

            self.controlsNode.hasPlainBackground =
                !self.historyNode.hasAnyMessages

            return
        }

        let isDark =
            self.presentationData
                .theme
                .overallDarkAppearance

        self.dimNode.backgroundColor =
            UIColor(
                white: 0.0,
                alpha: 0.06
            )

        self.historyBackgroundContentNode
            .backgroundColor = .clear

        let surface =
            UIColor(
                white:
                    isDark
                    ? 0.0
                    : 1.0,
                alpha:
                    isDark
                    ? 0.055
                    : 0.075
            )

        self.historyFrameLeftOverlayNode
            .backgroundColor = surface

        self.historyFrameRightOverlayNode
            .backgroundColor = surface

        self.historyFrameTopOverlayNode
            .backgroundColor = surface

        self.historyFrameTopMaskNode.alpha = 0.0
        self.controlsNode.hasPlainBackground = false
    }

    func updatePresentationData(_ presentationData: PresentationData) {
''',
    'music surface methods'
)

music = one(
    music,
    '        self.controlsNode.updatePresentationData(self.presentationData)\n    }\n',
    '        self.controlsNode.updatePresentationData(self.presentationData)\n        self.updateGhostBaseMusicSurfaces()\n    }\n',
    'music presentation surface refresh'
)

music = one(
    music,
    '        self.view.addGestureRecognizer(panRecognizer)\n    }\n',
    '        self.view.addGestureRecognizer(panRecognizer)\n        self.updateGhostBaseMusicSurfaces()\n    }\n',
    'music init surface refresh'
)

music = one(
    music,
    '        transition.updateFrame(node: self.dimNode, frame: CGRect(origin: CGPoint(), size: layout.size))\n',
    '        transition.updateFrame(node: self.dimNode, frame: CGRect(origin: CGPoint(), size: layout.size))\n        self.updateGhostBaseMusicSurfaces()\n',
    'music layout surface refresh'
)

MUSIC.write_text(
    music,
    encoding='utf-8'
)

_committed = True

print('[V11P] FULLCORRECTION1 materialized')
print('[V11P] wedges: scoped PeerInfo filler suppression + explicit rounded header-field owners')
print('[V11P] profile blur: Build97 silhouette recipe + stable reopen cache')
print('[V11P] animation: one decoder/timeline fan-out to avatar + backdrop')
print('[V11P] source priority / Premium composition / Members / Common Groups fixed')
print('[V11P] opened Gift strengthened; music uses real underlying PeerInfo')
