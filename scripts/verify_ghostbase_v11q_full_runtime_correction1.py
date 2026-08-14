#!/usr/bin/env python3
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(os.environ.get(
    'GHOSTBASE_SOURCE_ROOT',
    '/root/gb_builder/work/swiftgram-src'
))

PEER = (
    ROOT
    / 'submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources'
)

FILES = {
    'listSection': ROOT / 'submodules/TelegramUI/Components/ListSectionComponent/Sources/ListSectionComponent.swift',
    'corners': ROOT / 'submodules/TelegramPresentationData/Sources/Resources/PresentationResourcesItemList.swift',
    'section': PEER / 'PeerInfoScreenItemSectionContainerNode.swift',
    'headerSingle': PEER / 'PeerInfoHeaderSingleLineTextFieldNode.swift',
    'headerMulti': PEER / 'PeerInfoHeaderMultiLineTextFieldNode.swift',
    'universal': ROOT / 'submodules/AccountContext/Sources/UniversalVideoNode.swift',
    'manager': ROOT / 'submodules/TelegramUniversalVideoContent/Sources/UniversalVideoContentManager.swift',
    'native': ROOT / 'submodules/TelegramUniversalVideoContent/Sources/NativeVideoContent.swift',
    'media': ROOT / 'submodules/MediaPlayer/Sources/MediaPlayerNode.swift',
    'chunk': ROOT / 'submodules/MediaPlayer/Sources/ChunkMediaPlayerV2.swift',
    'bg': PEER / 'GhostBaseProfileFullscreenBackground.swift',
    'screen': PEER / 'PeerInfoScreen.swift',
    'cover': ROOT / 'submodules/TelegramUI/Components/PeerInfo/PeerInfoCoverComponent/Sources/PeerInfoCoverComponent.swift',
    'header': PEER / 'PeerInfoHeaderNode.swift',
    'members': PEER / 'Panes/PeerInfoMembersPane.swift',
    'groups': PEER / 'Panes/PeerInfoGroupsInCommonPaneNode.swift',
    'gift': ROOT / 'submodules/TelegramUI/Components/Gifts/GiftViewScreen/Sources/GiftViewScreen.swift',
    'giftPager': ROOT / 'submodules/TelegramUI/Components/Gifts/GiftViewScreen/Sources/GiftPagerComponent.swift',
    'music': ROOT / 'submodules/TelegramUI/Sources/OverlayAudioPlayerControllerNode.swift',
    'report': PEER / 'GhostBaseProfileReportPaneNode.swift',
}

for name, path in FILES.items():
    if not path.is_file():
        raise RuntimeError(
            f'[V11Q VERIFY] missing {name}: {path}'
        )

TEXT = {
    name: path.read_text(encoding='utf-8')
    for name, path in FILES.items()
}


def compact(value: str) -> str:
    return ''.join(value.split())


def need(name: str, needle: str, label: str) -> None:
    if compact(needle) not in compact(TEXT[name]):
        raise RuntimeError(
            '[V11Q VERIFY] '
            f'missing {label} in {name}'
        )


def forbid(name: str, needle: str, label: str) -> None:
    if compact(needle) in compact(TEXT[name]):
        raise RuntimeError(
            '[V11Q VERIFY] '
            f'forbidden {label} in {name}'
        )


def between(name: str, start: str, end: str, label: str) -> str:
    source = TEXT[name]
    i = source.find(start)
    if i < 0:
        raise RuntimeError(
            '[V11Q VERIFY] '
            f'missing start for {label}'
        )
    j = source.find(end, i + len(start))
    if j < 0:
        raise RuntimeError(
            '[V11Q VERIFY] '
            f'missing end for {label}'
        )
    return source[i:j]


# ============================================================
# A. ZERO WEDGES
# ============================================================

need('corners', 'GhostBase v1.1P GLOBAL_GLASS_CORNERS1', 'scoped legacy filler gate')
need('corners', 'withGhostBaseGlassCornerFillerSuppressed', 'scoped legacy filler API')
need('section', 'PresentationResourcesItemList.withGhostBaseGlassCornerFillerSuppressed', 'PeerInfo child update gate')
need('section', 'self.itemContainerNode.cornerRadius = radius', 'PeerInfo real section radius')
need('section', 'self.itemContainerNode.clipsToBounds = hasCorners', 'PeerInfo section clipping')

for field in ('headerSingle', 'headerMulti'):
    need(field, 'GhostBase v1.1P HEADER_FIELD_GLASS_OWNER1', 'header edit-field glass owner')
    need(field, 'self.maskNode.image = nil', 'header edit-field opaque filler removal')
    need(field, 'self.backgroundNode.cornerRadius = hasCorners ? 26.0 : 0.0', 'header edit-field real radius')
    need(field, 'PresentationResourcesItemList.cornersImage', 'header edit-field Official OFF fallback')

need('listSection', 'GhostBase v1.1Q MODERN_GLASS_OWNER1', 'modern component glass owner')
need('listSection', 'GhostBaseGlassStyle.isEnabled', 'modern glass master OFF gate')
need('listSection', 'case (.glass, .all)', 'modern glass scope')
need('listSection', 'self.ghostBaseDirectGlassBackgroundView', 'modern real backing view')
need('listSection', 'cornerRadius: cornerRadius', 'modern rounded direct surface')
need('listSection', 'transition.setAlpha(view: self.externalContentBackgroundView, alpha: 0.0)', 'modern external background suppression')
need('listSection', 'alpha: isDark ? 0.13 : 0.16', 'modern glass material')


# ============================================================
# B. ANIMATION
# ============================================================

need('media', 'GhostBase v1.1P SECONDARY_RENDER_OUTPUT1', 'legacy player fanout')
need('media', 'CMSampleBufferCreateCopy', 'legacy shared-frame copy')
need('chunk', 'GhostBase v1.1P CHUNK_SECONDARY_RENDER_OUTPUT1', 'Chunk player fanout')
need('chunk', 'renderSynchronizer.addRenderer(layer.sampleBufferRenderer)', 'shared iOS17 synchronizer')
need('chunk', 'renderSynchronizer.addRenderer(layer)', 'shared pre-iOS17 synchronizer')
need('chunk', 'CMSampleBufferCreateCopy', 'Chunk shared-frame copy')
need('native', 'UniversalVideoSecondaryOutputContentNode', 'NativeVideo forwarding conformance')
need('universal', 'GhostBase v1.1Q SECONDARY_OUTPUT_REGISTRY1', 'persistent secondary registry')
need('universal', 'weak var value: AVSampleBufferDisplayLayer?', 'weak output ownership')
need('universal', 'GhostBaseUniversalVideoSecondaryOutputRegistry.register', 'durable register before holder exists')
need('universal', 'GhostBaseUniversalVideoSecondaryOutputRegistry.unregister', 'durable unregister cleanup')
need('manager', 'GhostBase v1.1Q SECONDARY_OUTPUT_REATTACH1', 'manager holder reattach')
need('manager', 'GhostBaseUniversalVideoSecondaryOutputRegistry.attachRegisteredLayers', 'reattach on each holder attach')
need('bg', 'GhostBaseProfileMirrorVideoView', 'fullscreen secondary renderer')
need('bg', 'registerSecondaryVideoLayer', 'profile secondary registration')
need('screen', 'refreshAnimatedVideoOwner', 'Settings/Profile owner refresh path')
forbid('bg', 'let videoNode = UniversalVideoNode(', 'second UniversalVideoNode player owner')
forbid('bg', 'NativeVideoContent(', 'independent NativeVideoContent playback')


# ============================================================
# C. BUILD97 silhouette + reopen + source priority
# ============================================================

need('bg', 'GhostBase v1.1Q BUILD97_NEUTRAL_REOPEN1', 'neutral unresolved avatar state')
need('bg', 'let immediateTint = fallback', 'neutral cache-miss fallback')
need('bg', 'Self.imageCache.object(forKey: cacheKey)', 'exact final-image reopen cache')
need('bg', 'Self.imageCache.setObject(entry, forKey: cacheKey)', 'final image cache store')
need('bg', '.systemUltraThinMaterialDark', 'Build97 dark blur material')
need('bg', '.systemUltraThinMaterialLight', 'Build97 light blur material')
need('bg', 'width: 360.0', 'Build97 avatar decode width')
need('bg', 'height: 360.0', 'Build97 avatar decode height')
need('bg', 'self.imageView.contentMode = .scaleAspectFill', 'Build97 silhouette fill')

avatar_block = between(
    'bg',
    'case let .avatar(',
    'case let .placeholder(',
    'avatar apply block'
)

if 'Self.persistentTint(' in avatar_block:
    raise RuntimeError(
        '[V11Q VERIFY] avatar branch still uses persistentTint before pixels'
    )

resolve_block = between(
    'bg',
    'private func resolveSource(',
    'private func',
    'resolveSource block'
)

if 'presentationData.chatWallpaper' in resolve_block:
    raise RuntimeError(
        '[V11Q VERIFY] global chatWallpaper still outranks peer avatar/Premium'
    )

need('bg', 'case let .placeholder(', 'no-avatar source')
need('bg', 'self.clearAnimatedMedia()', 'no-avatar stale video cleanup')
need('bg', 'self.currentLoadKey = nil', 'no-avatar stale async-load cancellation')


# ============================================================
# D. PREMIUM
# ============================================================

need('cover', 'setGhostBaseDecorationAlpha', 'Premium decoration-specific compositing')
need('cover', 'patternTransitionFraction', 'Premium pattern transition preservation')
need('cover', 'avatarTransitionFraction', 'Premium avatar transition preservation')
need('header', 'setGhostBaseDecorationAlpha', 'header Premium composition application')
need('header', '? 0.08', 'Build97 avatar-blur decoration weight')


# ============================================================
# E. MEMBERS / COMMON GROUPS
# ============================================================

need('members', 'GhostBase v1.1Q MEMBERS_PANE_GLASS1', 'Members pane owner')
need('members', 'UIVisualEffectView', 'Members one pane-level blur')
need('members', '.systemUltraThinMaterialDark', 'Members dark material')
need('members', '.systemUltraThinMaterialLight', 'Members light material')
need('members', 'self.listBackgroundView.isHidden = true', 'Members old filled background disabled')
need('members', 'self.listMaskView.isHidden = true', 'Members old mask disabled')
need('members', 'self.ghostBaseGlassEffectView.layer.cornerRadius = 26.0', 'Members real radius')
need('members', 'hideBackground: true', 'Members ContactsPeerItem row background disabled')
need('members', 'self.listBackgroundView.isHidden = false', 'Members OFF fallback restored')
need('members', 'self.listMaskView.isHidden = false', 'Members OFF mask restored')
need('groups', 'systemStyle: ghostBaseGlassEnabled ? .glass : .legacy', 'Common Groups row system style')
need('groups', 'displayBackground: !ghostBaseGlassEnabled', 'Common Groups opaque row removal')


# ============================================================
# F. OPENED GIFT
# ============================================================

need('gift', 'GhostBase v1.1Q PROFILE_GIFT_READABILITY1', 'opened gift correction')
need('gift', 'actionSheet.opaqueItemBackgroundColor', 'Official readable gift sheet')
forbid('gift', '? 0.56 : 0.64', 'weak V11P gift sheet material')
need('giftPager', '? 0.28 : 0.4', 'profile gift modal separation')


# ============================================================
# G. MUSIC
# ============================================================

need('music', 'GhostBase v1.1P MUSIC_REAL_PROFILE_GLASS1', 'real underlying profile music mode')

for bad in (
    'GhostBaseMusicProfileBackdropView',
    'ghostBaseBackdropView',
    'ghostBaseWallpaper',
):
    forbid('music', bad, 'independent cloned music scene')

need('music', 'alpha: 0.06', 'light modal dim over real profile')


# ============================================================
# H. HISTORY
# ============================================================

need('report', 'static let maximumEvents = 200', 'bounded history event count')
need('report', 'afterPendingWrites', 'async history persistence')
need('report', 'var tabBarOffset: CGFloat {', 'history tab geometry property')
need('report', 'return 0.0', 'history tab geometry isolation')
need('report', 'let viewportTop = max(0.0, topInset)', 'physical history viewport top')
need('report', 'size.height - viewportTop', 'physical history viewport height')
need('report', 'y: viewportTop', 'physical history viewport placement')
need('report', 'GhostBase v1.1Q HISTORY_CLIP_HARDENING1', 'node-level viewport hardening')
need('report', 'self.clipsToBounds = true', 'report root clipping')
need('report', 'self.scrollNode.clipsToBounds = true', 'scroll node clipping')
need('report', 'self.scrollNode.view.clipsToBounds = true', 'scroll view clipping')


# ============================================================
# I. OFF / NATIVE regression locks
# ============================================================

need('corners', 'context.setFillColor(theme.list.blocksBackgroundColor.cgColor)', 'Official legacy corners fallback')
need('listSection', 'self.externalContentBackgroundView.updateColor(color: backgroundColor, transition: transition)', 'Official modern background fallback')
need('members', 'presentationData.theme.list.itemBlocksBackgroundColor', 'Official Members background fallback')
need('members', 'presentationData.theme.list.blocksBackgroundColor', 'Official Members mask fallback')
need('headerSingle', 'PresentationResourcesItemList.cornersImage', 'Official edit-field fallback')
need('headerMulti', 'PresentationResourcesItemList.cornersImage', 'Official edit-field fallback')


# ============================================================
# J. PARSE
# ============================================================

swiftc = shutil.which('swiftc')

if swiftc:
    parse_names = (
        'listSection',
        'corners',
        'section',
        'headerSingle',
        'headerMulti',
        'universal',
        'manager',
        'native',
        'media',
        'chunk',
        'bg',
        'screen',
        'cover',
        'header',
        'members',
        'groups',
        'gift',
        'giftPager',
        'music',
        'report',
    )

    for name in parse_names:
        result = subprocess.run(
            [
                swiftc,
                '-frontend',
                '-parse',
                str(FILES[name]),
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        if result.returncode != 0:
            raise RuntimeError(
                '[V11Q VERIFY] Swift parse failed '
                f'in {name}: {FILES[name]}\n'
                f'{result.stderr}'
            )


print('[V11Q VERIFY] GREEN')
print('[V11Q VERIFY] ZERO-wedge owners: legacy PeerInfo + edit fields + modern .glass sections GREEN')
print('[V11Q VERIFY] Build97 silhouette/reopen + peer source priority + no-avatar cleanup GREEN')
print('[V11Q VERIFY] one-decoder dual presentation + holder-handoff persistence GREEN')
print('[V11Q VERIFY] Premium / Members / Common Groups / opened Gift / real-profile music GREEN')
print('[V11Q VERIFY] bounded physical history viewport + OFF fallbacks GREEN')
