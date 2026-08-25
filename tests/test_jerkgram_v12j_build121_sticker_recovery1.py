import os
import plistlib
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
APPLY = REPO / 'scripts/apply_jerkgram_v12j_build121_sticker_recovery1.py'
VERIFY = REPO / 'scripts/verify_jerkgram_v12j_build121_sticker_recovery1.py'
INSTALL = REPO / 'scripts/install_jerkgram_v12j_build121_probe_hook.py'
FINALIZE = REPO / 'scripts/jerkgram_finalize_build121_identity.py'
VERIFY_IPA = REPO / 'scripts/verify_jerkgram_v12j_build121_final_ipa.py'
PUBLISH = REPO / 'scripts/jerkgram_publish_build121_artifact.py'

BUILD107_ENQUEUE = '''
private func ghostBaseReconstructedMedia(
    account: Account,
    peerId: PeerId,
    source: Message,
    outgoing: EnqueueMessage
) -> AnyMediaReference? {
    // MARK: GhostBase v1.1V BUILD107_STICKER_TEXT_FALLBACK1
    // Deleted stickers intentionally remain textual portable replies.
    // Do not reconstruct or reupload sticker media.
    if let file = media as? TelegramMediaFile, file.isSticker {
        return nil
    }

    let cachedExtension: String = {
        var ext = "bin"
        switch file.mimeType {
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
        return ext
    }()

    let copied = TelegramMediaFile(
        fileId: file.fileId,
        partialReference: nil,
        resource: resource,
        previewRepresentations: file.previewRepresentations,
        videoThumbnails: file.videoThumbnails,
        immediateThumbnailData: file.immediateThumbnailData,
        mimeType: file.mimeType,
        size: file.size,
        attributes: file.attributes,
        alternativeRepresentations: []
    )
    return .standalone(media: copied)
}

private func ghostBaseDeletedMediaFallbackLabel(_ media: Media) -> String {
    if let file = media as? TelegramMediaFile, file.isSticker {
        return "Sticker"
    }
    return "File"
}
// MARK: GhostBase v1.1U BUILD106_FINAL1
// MARK: GhostBase v1.1U BUILD106_ALBUM_RECOVERY1
// MARK: GhostBase v1.1U BUILD106_PORTABLE_AUTHOR1
'''

PROBE = '''#!/usr/bin/env bash
python3 ../../scripts/verify_jerkgram_v12i_build120_profile_blur_lifecycle1.py
python3 ../../scripts/apply_jerkgram_v12i_build120_sticker_alpha1.py
python3 ../../scripts/verify_jerkgram_v12i_build120_sticker_alpha1.py
"$BAZEL_BIN" build //Telegram:Telegram
python3 ../../scripts/jerkgram_finalize_build120_identity.py ghostbase-final/GhostBase.ipa
python3 ../../scripts/verify_jerkgram_v12i_build120_final_ipa.py ghostbase-final/GhostBase.ipa
'''

EXTENSIONS = (
    'BroadcastUploadExtension.appex',
    'IntentsExtension.appex',
    'NotificationContentExtension.appex',
    'NotificationServiceExtensionv1.appex',
    'ShareExtension.appex',
    'WidgetExtension.appex',
)


def run(script: Path, *args: str, cwd=None, env=None):
    return subprocess.run(
        [sys.executable, str(script), *args],
        cwd=cwd,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def make_source(root: Path) -> Path:
    target = root / 'submodules/TelegramCore/Sources/PendingMessages/EnqueueMessage.swift'
    target.parent.mkdir(parents=True)
    target.write_text(BUILD107_ENQUEUE, encoding='utf-8')
    return target


def make_ipa(path: Path):
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        app = root / 'Payload/Jerkgram.app'
        plugins = app / 'PlugIns'
        plugins.mkdir(parents=True)
        main = {
            'CFBundleDisplayName': 'Jerkgram',
            'CFBundleName': 'Jerkgram',
            'CFBundleIdentifier': 'ph.telegra.Telegraph',
            'CFBundleVersion': '120',
        }
        (app / 'Info.plist').write_bytes(plistlib.dumps(main))
        for name in EXTENSIONS:
            ext = plugins / name
            ext.mkdir()
            suffix = name.replace('.appex', '').replace('Extensionv1', '').replace('Extension', '') or 'Ext'
            (ext / 'Info.plist').write_bytes(plistlib.dumps({
                'CFBundleIdentifier': 'ph.telegra.Telegraph.' + suffix,
                'CFBundleVersion': '120',
            }))
        with zipfile.ZipFile(path, 'w') as archive:
            for item in root.rglob('*'):
                if item.is_file():
                    archive.write(item, item.relative_to(root).as_posix())


def read_versions(path: Path):
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        with zipfile.ZipFile(path) as archive:
            archive.extractall(root)
        app = next((root / 'Payload').glob('*.app'))
        result = [plistlib.loads((app / 'Info.plist').read_bytes())['CFBundleVersion']]
        for extension in sorted((app / 'PlugIns').glob('*.appex')):
            result.append(plistlib.loads((extension / 'Info.plist').read_bytes())['CFBundleVersion'])
        return result


class Build121StickerRecoveryTests(unittest.TestCase):
    def test_restores_native_sticker_reconstruction_without_touching_fallback(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            target = make_source(root)
            env = os.environ.copy()
            env['GHOSTBASE_SOURCE_ROOT'] = str(root)

            before = run(VERIFY, env=env)
            self.assertNotEqual(before.returncode, 0, msg='verifier must reject active Build107 sticker fallback')

            applied = run(APPLY, env=env)
            self.assertEqual(applied.returncode, 0, msg=applied.stdout + applied.stderr)
            verified = run(VERIFY, env=env)
            self.assertEqual(verified.returncode, 0, msg=verified.stdout + verified.stderr)

            text = target.read_text(encoding='utf-8')
            self.assertEqual(text.count('BUILD121_NATIVE_STICKER_RECOVERY1'), 1)
            self.assertNotIn('BUILD107_STICKER_TEXT_FALLBACK1', text)
            self.assertEqual(text.count('case "video/webm":'), 1)
            self.assertEqual(text.count('case "application/x-tgsticker":'), 1)
            self.assertEqual(text.count('case "image/webp":'), 1)
            self.assertIn('mimeType: file.mimeType', text)
            self.assertIn('attributes: file.attributes', text)
            self.assertIn('return "Sticker"', text)
            self.assertIn('BUILD106_ALBUM_RECOVERY1', text)
            self.assertIn('BUILD106_PORTABLE_AUTHOR1', text)

            again = run(APPLY, env=env)
            self.assertEqual(again.returncode, 0, msg=again.stdout + again.stderr)
            self.assertEqual(target.read_text(encoding='utf-8'), text)

    def test_probe_hook_orders_build121_between_build120_and_bazel(self):
        with tempfile.TemporaryDirectory() as td:
            probe = Path(td) / 'bazel_build_probe_official.sh'
            probe.write_text(PROBE, encoding='utf-8')
            env = os.environ.copy()
            env['JERKGRAM_PROBE_PATH'] = str(probe)

            installed = run(INSTALL, env=env)
            self.assertEqual(installed.returncode, 0, msg=installed.stdout + installed.stderr)
            text = probe.read_text(encoding='utf-8')
            b120 = text.index('verify_jerkgram_v12i_build120_sticker_alpha1.py')
            apply = text.index('apply_jerkgram_v12j_build121_sticker_recovery1.py')
            verify = text.index('verify_jerkgram_v12j_build121_sticker_recovery1.py')
            bazel = text.index('"$BAZEL_BIN" build')
            final120 = text.index('verify_jerkgram_v12i_build120_final_ipa.py')
            final121 = text.index('jerkgram_finalize_build121_identity.py')
            verify121 = text.index('verify_jerkgram_v12j_build121_final_ipa.py')
            self.assertLess(b120, apply)
            self.assertLess(apply, verify)
            self.assertLess(verify, bazel)
            self.assertLess(bazel, final120)
            self.assertLess(final120, final121)
            self.assertLess(final121, verify121)

            second = run(INSTALL, env=env)
            self.assertEqual(second.returncode, 0, msg=second.stdout + second.stderr)
            text = probe.read_text(encoding='utf-8')
            for name in (
                'apply_jerkgram_v12j_build121_sticker_recovery1.py',
                'verify_jerkgram_v12j_build121_sticker_recovery1.py',
                'jerkgram_finalize_build121_identity.py',
                'verify_jerkgram_v12j_build121_final_ipa.py',
            ):
                self.assertEqual(text.count(name), 1)

    def test_finalize_verify_and_publish_build121(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            source = root / 'work/swiftgram-src/ghostbase-final/GhostBase.ipa'
            source.parent.mkdir(parents=True)
            make_ipa(source)

            finalized = run(FINALIZE, str(source), cwd=root)
            self.assertEqual(finalized.returncode, 0, msg=finalized.stdout + finalized.stderr)
            self.assertEqual(read_versions(source), ['121'] * 7)

            verified = run(VERIFY_IPA, str(source), cwd=root)
            self.assertEqual(verified.returncode, 0, msg=verified.stdout + verified.stderr)

            published = run(PUBLISH, cwd=root)
            self.assertEqual(published.returncode, 0, msg=published.stdout + published.stderr)
            output = root / 'artifacts/Jerkgram-build121.ipa'
            info = root / 'artifacts/Jerkgram-build121-info.txt'
            self.assertTrue(output.is_file())
            self.assertIn('Build=121', info.read_text(encoding='utf-8'))
            self.assertEqual(read_versions(output), ['121'] * 7)


if __name__ == '__main__':
    unittest.main()
