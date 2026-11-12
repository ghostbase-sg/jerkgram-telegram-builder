"""Exact recovery owner and shared Settings/telemetry release identity guard."""
import json
from pathlib import Path
from materialize_jg131_beta2_recovery import verify_recovery, parent_source_view
from verify_jg131_botbridge1 import verify_source as verify_bot_source

ROOT = Path(__file__).resolve().parents[1]


def verify_source(source):
    source = Path(source)
    verify_recovery(source)
    config = json.loads((ROOT/'jerkgram-migration.json').read_text())
    from jg132_baseline import enabled
    if enabled():
        # This predecessor is intentionally the frozen Build179 boundary.
        # The Beta3 successor verifies the current release identity separately.
        config = dict(config, product_display_version='1.2.0 Beta 2',
                      product_technical_version='1.2.0-beta.2', build_number=179,
                      upstream_new_version='13.1.2')
    strings = (source/'submodules/TelegramPresentationData/Sources/JerkgramStrings.swift').read_text()
    for key, value in (('displayVersion', config['product_display_version']), ('technicalVersion', config['product_technical_version']), ('build', str(config['build_number'])), ('telegramBase', config['upstream_new_version'])):
        if strings.count(f'public static let {key} = "{value}"') != 1:
            raise RuntimeError('Beta2 release identity changed: '+key)
    settings = (source/'submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift').read_text()
    telemetry = (source/'submodules/TelegramUI/Sources/AppDelegate.swift').read_text()
    if 'JerkgramReleaseIdentity.displayVersion' not in settings:
        raise RuntimeError('Beta2 Settings shared identity lost')
    if any(value not in telemetry for value in ('let version=JerkgramReleaseIdentity.technicalVersion', 'let build=JerkgramReleaseIdentity.build')):
        raise RuntimeError('Beta2 telemetry shared identity lost')
    # Validate the preceding BOT boundaries without giving it modified owners.
    with parent_source_view(source) as parent:
        verify_bot_source(parent)
    print('Beta2 exact recovery owners and shared release identity PASS; native/app/device evidence separate', flush=True)


if __name__ == '__main__':
    import sys
    verify_source(Path(sys.argv[1]) if len(sys.argv)>1 else ROOT/'work/swiftgram-src')
