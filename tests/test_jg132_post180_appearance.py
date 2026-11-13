"""Account-local presentation isolation and pinned Postbox codec regression."""
from pathlib import Path
import os, re, shutil, subprocess, tempfile, unittest
import test_jg131_beta2_bot_codec as codec

ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path(os.environ.get('JG_POST180_SOURCE',ROOT/'work/swiftgram-src'))
CORE=SOURCE/'submodules/TelegramCore/Sources/Settings'
FIX=ROOT/'tests/fixtures/post180'

def fixture():
    def source(name):
        return '\n'.join(l for l in (CORE/name).read_text().splitlines() if not l.startswith('import '))
    native_picker=(SOURCE/'submodules/TelegramUI/Components/EmojiStatusSelectionComponent/Sources/EmojiStatusSelectionComponent.swift').read_text()
    mode=codec.declaration((SOURCE/'submodules/AccountContext/Sources/AccountContext.swift').read_text(),'public enum EmojiStatusSelectionControllerMode')
    route=codec.declaration(native_picker,'private func completeLocalSelection(')
    picker='public struct TelegramMediaFile: Equatable { let id: Int64 }\n'+mode+'\nfinal class PickerHarness { let localAppearance: Bool; let mode: EmojiStatusSelectionControllerMode; init(_ local: Bool, _ mode: EmojiStatusSelectionControllerMode) { localAppearance=local; self.mode=mode }\n'+route+'\nfunc run(_ file: TelegramMediaFile?, _ expiry: Int32?) -> Bool { completeLocalSelection(file: file, expirationDate: expiry) } }\n'
    return 'import Foundation\n'+(FIX/'appearance-boundaries.swift').read_text()+'\n'+source('JerkgramLocalAppearanceSettings.swift')+'\n'+source('JerkgramLocalAppearanceStore.swift')+'\n'+picker+(FIX/'appearance-matrix.swift').read_text()

class Appearance(unittest.TestCase):
    def test_preferences_key_does_not_collide(self):
        own=CORE/'JerkgramLocalAppearanceStore.swift'
        key=re.search(r'key.setInt32\(0, value: (0x[0-9A-Fa-f]+)\)',own.read_text()).group(1)
        collisions=[str(p.relative_to(SOURCE)) for p in (SOURCE/'submodules').rglob('*.swift') if p!=own and f'key.setInt32(0, value: {key})' in p.read_text()]
        self.assertEqual(collisions,[], 'Appearance must not overwrite saved tags or other preferences')

    def test_actual_fixture_and_picker_boundary(self):
        code=fixture()
        self.assertIn('old picker callback after A-B-A rejected',code)
        self.assertIn('private func completeLocalSelection',code)
        picker=(SOURCE/'submodules/TelegramUI/Components/EmojiStatusSelectionComponent/Sources/EmojiStatusSelectionComponent.swift').read_text()
        preview=picker[picker.index('if let result, let previewItem = strongSelf.previewItem'):]
        self.assertLess(preview.index('completeLocalSelection'),preview.index('setStarGiftStatus'))
        tap=codec.declaration(picker,'private func applyItem(')
        self.assertLess(tap.index('completeLocalSelection'),tap.index('setEmojiStatus'))
        self.assertIn('localAppearance: Bool = false',picker)

    def test_native_store_matrix(self):
        if not shutil.which('xcrun'):
            if os.environ.get('JG_BETA3_REQUIRE_NATIVE')=='1':self.fail('appearance requires native Swift/Clang/xcrun')
            self.skipTest('actual store/codec execution requires macOS')
        with tempfile.TemporaryDirectory(prefix='post180-appearance-') as directory:
            folder=Path(directory)
            for opt in ('-Onone','-O'):
                executable=codec.compile_fixture(folder,opt,main_override=fixture())
                result=subprocess.run([str(executable)],capture_output=True,text=True,timeout=30)
                self.assertEqual(result.returncode,0,result.stdout+result.stderr)

if __name__=='__main__':unittest.main(verbosity=2)
