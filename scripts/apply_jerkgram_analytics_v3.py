#!/usr/bin/env python3
"""Apply a narrow Analytics v3 successor to the unchanged current13.2 product."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
PIN = '24638bc69bd083981b178dd1e7f921eebbf7fc46'
APP = 'submodules/TelegramUI/Sources/AppDelegate.swift'
STRINGS = 'submodules/TelegramPresentationData/Sources/JerkgramStrings.swift'
PAYLOAD_ROOT = ROOT / 'scripts/jerkgram_analytics_v3_payload'
MANIFEST = ROOT / 'patches/analytics-v3-integration.sha256.json'
MARKER = '// MARK: Jerkgram ANALYTICS_V3_LIFECYCLE'
PAYLOADS = ('JerkgramAnalyticsV3.swift', 'JerkgramAnalyticsV3Bridge.swift', 'JerkgramAnalyticsV3InstallationProbe.swift')


def digest(data):
    return hashlib.sha256(data).hexdigest()


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise RuntimeError('Analytics v3 exact owner changed: ' + old[:90])
    return text.replace(old, new, 1)


def legacy_telemetry(text):
    start = text.index('private final class JerkgramTelemetry {')
    end = text.index('\n}\n', start) + 3
    return text[start:end]


def patch_app(text):
    if MARKER in text:
        raise RuntimeError("Analytics v3 app owner already patched; verify exact output hash")
    old_legacy = legacy_telemetry(text)
    text = replace_once(text,
        '        JerkGramLegacyDefaultsMigration.run()\n',
        '        ' + MARKER + '\n'
        '        JerkgramAnalyticsV3Bridge.shared.bootstrap(appGroupURL: FileManager.default.containerURL(\n'
        '            forSecurityApplicationGroupIdentifier: jerkgramResolvedApplicationGroupIdentifier(\n'
        '                fallback: "group.\\(Bundle.main.bundleIdentifier ?? "")"\n'
        '            )\n'
        '        ))\n'
        '        JerkGramLegacyDefaultsMigration.run()\n'
        '        JerkgramAnalyticsV3Bridge.shared.synchronizeConsent()\n')
    for function, method in [('handleDidBecomeActive', 'didBecomeActive'), ('handleDidEnterBackground', 'didEnterBackground'), ('handleWillResignActive', 'didResignActive')]:
        anchor = '    func ' + function + '() {\n'
        text = replace_once(text, anchor, anchor + '        JerkgramAnalyticsV3Bridge.shared.' + method + '()\n')
    if legacy_telemetry(text) != old_legacy:
        raise RuntimeError('Existing v1 telemetry must remain byte-identical')
    return text


RU = 'При включении аналитики Jerkgram использует случайный псевдонимный ID установки, связывающий её активность между днями, и собирает открытия приложения, сессии, модель и регион устройства, версии Jerkgram и iOS. Это не полностью анонимные данные. Telegram ID, аккаунты, сообщения, имена пользователей, контакты и номера телефонов не собираются. При выключении сбор и отправка прекращаются, очередь событий очищается.'
EN = 'When analytics is enabled, Jerkgram uses a random pseudonymous installation ID that links its activity across days and collects app opens, sessions, device model and region, and Jerkgram and iOS versions. These data are not fully anonymous. Telegram IDs, accounts, messages, usernames, contacts and phone numbers are not collected. Turning analytics off stops collection and delivery and clears queued events.'


def patch_strings(text):
    old_ru = 'Помогайте улучшать Jerkgram, отправляя анонимную статистику использования: версию Jerkgram, версию iOS и регион устройства. Аккаунты Telegram, сообщения, имена пользователей и номера телефонов никогда не собираются.'
    old_en = 'Help improve Jerkgram by sharing anonymous usage statistics such as Jerkgram version, iOS version and device region. Telegram accounts, messages, usernames and phone numbers are never collected.'
    text = replace_once(text, old_ru, RU)
    return replace_once(text, old_en, EN)


def verify_pin(source):
    source = Path(source).resolve()
    if subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=source, text=True).strip() != PIN:
        raise RuntimeError('Analytics v3 requires genuine pinned Telegram13.2')
    return source


def apply(source):
    source = verify_pin(source)
    manifest = json.loads(MANIFEST.read_text())
    if manifest.get('upstream_sha') != PIN or manifest.get('production_v3_delivery') is not False or set(manifest.get('owners', {})) != {APP, STRINGS}:
        raise RuntimeError('Analytics v3 reviewed integration scope or disabled production gate changed')
    changes = {}
    for name, patch in [(APP, patch_app), (STRINGS, patch_strings)]:
        data = (source / name).read_bytes()
        expected = manifest['owners'][name]
        if digest(data) == expected['after_sha256']:
            continue
        if digest(data) != expected['before_sha256']:
            raise RuntimeError('Analytics v3 unexpected product owner: ' + name)
        changed = patch(data.decode()).encode()
        if digest(changed) != expected['after_sha256']:
            raise RuntimeError('Analytics v3 output hash changed: ' + name)
        changes[source / name] = changed
    if set(manifest['payloads']) != set(PAYLOADS):
        raise RuntimeError('Analytics v3 payload scope changed')
    for name in PAYLOADS:
        payload = PAYLOAD_ROOT / name
        if not payload.is_file() or digest(payload.read_bytes()) != manifest['payloads'][name]:
            raise RuntimeError('Analytics v3 reviewed payload hash changed: ' + name)
        if name == 'JerkgramAnalyticsV3.swift' and payload.read_text().count('static let productionTransportEnabled = false') != 1:
            raise RuntimeError('Analytics v3 production transport must remain hard-disabled')
        target = source / 'submodules/TelegramUI/Sources' / payload.name
        data = payload.read_bytes()
        if target.exists() and target.read_bytes() != data:
            raise RuntimeError('Analytics v3 unexpected existing payload: ' + target.name)
        changes[target] = data
    if not (PAYLOAD_ROOT / 'JerkgramAnalyticsV3.swift').is_file():
        raise RuntimeError('Analytics v3 production core payload missing')
    for path, data in changes.items():
        path.write_bytes(data)
    print('Analytics v3 guarded source successor applied; production v3 delivery remains disabled')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root', type=Path, default=ROOT / 'work/swiftgram-src')
    apply(parser.parse_args().source_root)
