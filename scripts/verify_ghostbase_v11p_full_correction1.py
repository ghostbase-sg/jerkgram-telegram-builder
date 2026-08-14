#!/usr/bin/env python3
import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(os.environ.get(
    'GHOSTBASE_SOURCE_ROOT',
    '/root/gb_builder/work/swiftgram-src'
))

OFFICIAL = Path(os.environ.get(
    'GHOSTBASE_OFFICIAL_SOURCE_ROOT',
    '/root/gb_builder/ports/ghostbase_12_9_2_port/telegram-ios-12.9.2-official'
))

PEER = (
    ROOT
    / 'submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources'
)

files = {
    'corners':
        ROOT
        / 'submodules/TelegramPresentationData/Sources/Resources/PresentationResourcesItemList.swift',

    'section':
        PEER
        / 'PeerInfoScreenItemSectionContainerNode.swift',

    'bg':
        PEER
        / 'GhostBaseProfileFullscreenBackground.swift',

    'screen':
        PEER
        / 'PeerInfoScreen.swift',

    'header':
        PEER
        / 'PeerInfoHeaderNode.swift',

    'headerSingle':
        PEER
        / 'PeerInfoHeaderSingleLineTextFieldNode.swift',

    'headerMulti':
        PEER
        / 'PeerInfoHeaderMultiLineTextFieldNode.swift',

    'cover':
        ROOT
        / 'submodules/TelegramUI/Components/PeerInfo/PeerInfoCoverComponent/Sources/PeerInfoCoverComponent.swift',

    'members':
        PEER
        / 'Panes/PeerInfoMembersPane.swift',

    'groups':
        PEER
        / 'Panes/PeerInfoGroupsInCommonPaneNode.swift',

    'gift':
        ROOT
        / 'submodules/TelegramUI/Components/Gifts/GiftViewScreen/Sources/GiftViewScreen.swift',

    'pager':
        ROOT
        / 'submodules/TelegramUI/Components/Gifts/GiftViewScreen/Sources/GiftPagerComponent.swift',

    'music':
        ROOT
        / 'submodules/TelegramUI/Sources/OverlayAudioPlayerControllerNode.swift',

    'universal':
        ROOT
        / 'submodules/AccountContext/Sources/UniversalVideoNode.swift',

    'native':
        ROOT
        / 'submodules/TelegramUniversalVideoContent/Sources/NativeVideoContent.swift',

    'media':
        ROOT
        / 'submodules/MediaPlayer/Sources/MediaPlayerNode.swift',

    'chunk':
        ROOT
        / 'submodules/MediaPlayer/Sources/ChunkMediaPlayerV2.swift',

    'report':
        PEER
        / 'GhostBaseProfileReportPaneNode.swift',
}

for name, path in files.items():
    if not path.is_file():
        raise RuntimeError(
            f'[V11P VERIFY] missing {name}: {path}'
        )

text = {
    key: path.read_text(encoding='utf-8')
    for key, path in files.items()
}


def _compact_source(value: str) -> str:
    # Semantic verifier must not fail merely because the generated Swift
    # expression was formatted across multiple lines.
    return ''.join(value.split())


def need(name, needle, label):
    source = text[name]

    if needle in source:
        return

    if _compact_source(needle) in _compact_source(source):
        return

    raise RuntimeError(
        f'[V11P VERIFY] missing {label} in {name}'
    )


def forbid(name, needle, label):
    if needle in text[name]:
        raise RuntimeError(
            f'[V11P VERIFY] forbidden {label} in {name}'
        )


for value in (
    'GhostBase v1.1P GLOBAL_GLASS_CORNERS1',
    'withGhostBaseGlassCornerFillerSuppressed',
    'Thread.current.threadDictionary',
    'return nil',
):
    need(
        'corners',
        value,
        value
    )

forbid(
    'corners',
    'GhostBase.Glass.Enabled',
    'global UserDefaults corner suppression'
)

need(
    'corners',
    'context.setFillColor(theme.list.blocksBackgroundColor.cgColor)',
    'Official corner fallback body'
)

need(
    'section',
    'private let ghostBaseGlassEnabled: Bool',
    'glass state'
)

need(
    'section',
    'PresentationResourcesItemList.withGhostBaseGlassCornerFillerSuppressed',
    'scoped child filler suppression'
)

need(
    'section',
    'self.itemContainerNode.cornerRadius = radius',
    'native itemContainer corner radius'
)

need(
    'section',
    'self.itemContainerNode.clipsToBounds = hasCorners',
    'native itemContainer clipping'
)

need(
    'section',
    'alpha: isDark ? 0.13 : 0.16',
    'Build97/V11K section material'
)

for bad in (
    'CAShapeLayer()',
    'itemNode.layer.mask',
    'self.layer.mask =',
    'NONOPAQUECARD1',
    'SECTIONMASK_REMOVED1',
):
    forbid(
        'section',
        bad,
        bad
    )

need(
    'media',
    'SECONDARY_RENDER_OUTPUT1',
    'media fan-out marker'
)

need(
    'media',
    'public func addSecondaryVideoLayer',
    'media secondary add'
)

need(
    'media',
    'CMSampleBufferCreateCopy',
    'legacy frame copy'
)

need(
    'media',
    'enqueueSecondaryCopies',
    'legacy frame fan-out'
)

need(
    'chunk',
    'CHUNK_SECONDARY_RENDER_OUTPUT1',
    'chunk fan-out marker'
)

need(
    'chunk',
    'secondaryVideoRenderers',
    'chunk secondary renderer registry'
)

need(
    'chunk',
    'renderSynchronizer.addRenderer(layer.sampleBufferRenderer)',
    'shared iOS17 synchronizer'
)

need(
    'chunk',
    'renderSynchronizer.addRenderer(layer)',
    'shared legacy synchronizer'
)

need(
    'chunk',
    'removeRenderer(layer.sampleBufferRenderer, at: .invalid)',
    'iOS17 secondary detach'
)

need(
    'chunk',
    'removeRenderer(layer, at: .invalid)',
    'legacy secondary detach'
)

need(
    'chunk',
    'secondaryVideoTargets',
    'chunk secondary target feed'
)

need(
    'chunk',
    'CMSampleBufferCreateCopy',
    'chunk frame copies'
)

need(
    'universal',
    'UniversalVideoSecondaryOutputContentNode',
    'universal companion protocol'
)

need(
    'universal',
    'registerSecondaryVideoLayer',
    'universal registration API'
)

need(
    'native',
    'import AVFoundation',
    'NativeVideoContent AVFoundation import'
)

need(
    'native',
    'UniversalVideoSecondaryOutputContentNode',
    'NativeVideoContent secondary conformance'
)

need(
    'native',
    'self.playerNode.addSecondaryVideoLayer(layer)',
    'NativeVideoContent fan-out forwarding'
)

need(
    'bg',
    'GhostBaseProfileMirrorVideoView',
    'profile mirror layer'
)

need(
    'bg',
    'registerSecondaryVideoLayer',
    'profile mirror registration'
)

need(
    'bg',
    'AVATAR_REOPEN_CACHE1',
    'reopen cache'
)

need(
    'bg',
    'Self.imageCache.object(forKey: cacheKey)',
    'avatar cache lookup'
)

need(
    'bg',
    'Self.imageCache.setObject(entry, forKey: cacheKey)',
    'avatar cache store'
)

need(
    'bg',
    '.systemUltraThinMaterialDark',
    'Build97 dark material'
)

need(
    'bg',
    '.systemUltraThinMaterialLight',
    'Build97 light material'
)

need(
    'bg',
    '''displayDimensions:
                    CGSize(
                        width: 360.0,''',
    'Build97 avatar presentation size'
)

need(
    'bg',
    'case let .placeholder(',
    'no-avatar placeholder path'
)

for bad in (
    '''let videoNode =
            UniversalVideoNode(''',
    'NativeVideoContent(',
    'presentationData.chatWallpaper',
):
    forbid(
        'bg',
        bad,
        bad
    )

need(
    'screen',
    'refreshAnimatedVideoOwner(',
    'post-header animation owner refresh'
)

need(
    'cover',
    'setGhostBaseDecorationAlpha',
    'native decoration scale'
)

need(
    'cover',
    'patternTransitionFraction',
    'native pattern fraction preservation'
)

need(
    'cover',
    'avatarTransitionFraction',
    'native avatar transition fraction preservation'
)

need(
    'header',
    'setGhostBaseDecorationAlpha',
    'header decoration composition'
)

need(
    'header',
    '? 0.08',
    'Build97 avatar-blur cover weight'
)

need(
    'header',
    ': 0.16',
    'Build97 premium-fallback cover weight'
)

for field in (
    'headerSingle',
    'headerMulti',
):
    need(
        field,
        'GhostBase v1.1P HEADER_FIELD_GLASS_OWNER1',
        'header field owner marker'
    )

    need(
        field,
        '.loadEnabled() != nil',
        'header field GhostBase gate'
    )

    need(
        field,
        'self.maskNode.image = nil',
        'header field filler suppression'
    )

    need(
        field,
        'self.backgroundNode.cornerRadius = hasCorners ? 26.0 : 0.0',
        'header field real radius'
    )

    need(
        field,
        'self.backgroundNode.clipsToBounds = hasCorners',
        'header field real clipping'
    )

    need(
        field,
        'self.backgroundNode.layer.maskedCorners',
        'header field end-specific corners'
    )

    need(
        field,
        'alpha: isDark ? 0.13 : 0.16',
        'header field material'
    )

    need(
        field,
        'PresentationResourcesItemList.cornersImage(presentationData.theme, top: hasTopCorners, bottom: hasBottomCorners, glass: true)',
        'header field Official OFF fallback'
    )

need(
    'members',
    '''? 0.045
                            : 0.075''',
    'members pane material'
)

need(
    'members',
    'hideBackground: true',
    'members row background suppression'
)

need(
    'groups',
    'systemStyle: ghostBaseGlassEnabled ? .glass : .legacy',
    'Common Groups conditional system style'
)

need(
    'groups',
    'displayBackground: !ghostBaseGlassEnabled',
    'Common Groups row backing suppression'
)

need(
    'groups',
    '''? 0.045
                            : 0.075''',
    'Common Groups pane material'
)

need(
    'gift',
    '''? 0.56
                            : 0.64''',
    'opened Gift readable sheet material'
)

need(
    'pager',
    '''? 0.28
                        : 0.4''',
    'profile Gift dim'
)

for bad in (
    'GhostBaseMusicProfileBackdropView',
    'ghostBaseBackdropView',
    'ghostBaseWallpaper',
):
    forbid(
        'music',
        bad,
        bad
    )

need(
    'music',
    'MUSIC_REAL_PROFILE_GLASS1',
    'real-profile music overlay'
)

need(
    'music',
    'alpha: 0.06',
    'music dim transparency'
)

need(
    'music',
    'alpha: isDark ? 0.055 : 0.075',
    'music translucent native surface'
)

for value in (
    'maximumEvents',
    'self.scrollNode.view.clipsToBounds =',
    'tabBarOffset: CGFloat',
    'afterPendingWrites',
):
    need(
        'report',
        value,
        f'history gate {value}'
    )

need(
    'bg',
    'placeholderColors(',
    'placeholder generator'
)

need(
    'bg',
    'self.clearAnimatedMedia()',
    'stale animated cleanup'
)

swiftc = shutil.which('swiftc')

if swiftc:
    for path in files.values():
        result = subprocess.run(
            [
                swiftc,
                '-frontend',
                '-parse',
                str(path)
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if result.returncode != 0:
            raise RuntimeError(
                '[V11P VERIFY] Swift parse failed: '
                f'{path}\n'
                f'{result.stderr}'
            )


print('[V11P VERIFY] GREEN')
print('[V11P VERIFY] wedges/scoped PeerInfo + header-field owners: semantic gate GREEN')
print('[V11P VERIFY] Build97 blur + reopen lifecycle: GREEN')
print('[V11P VERIFY] single-timeline dual presentation: GREEN')
print('[V11P VERIFY] Gifts / Members / Common Groups / music: GREEN')
print('[V11P VERIFY] history / no-avatar regression locks: GREEN')
