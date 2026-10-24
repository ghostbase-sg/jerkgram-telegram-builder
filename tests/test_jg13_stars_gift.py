import importlib
import os
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get('JG13_SOURCE', ROOT / 'work/swiftgram-src'))
sys.path.insert(0, str(ROOT / 'scripts'))


class StarsGiftTests(unittest.TestCase):
    def test_currency_scope_at_both_override_owners(self):
        core = (SOURCE / 'submodules/TelegramCore/Sources/TelegramEngine/Payments/Stars.swift').read_text()
        screen = (SOURCE / 'submodules/TelegramUI/Components/Stars/StarsTransactionsScreen/Sources/StarsTransactionsScreen.swift').read_text()
        self.assertTrue('if !self.ton, let ghostBaseBalance = ghostBaseLocalStarsVisualBalance()' in core, 'Core override must exclude TON/Gram')
        self.assertTrue('count: (component.starsContext.ton ? nil : ghostBaseLocalStarsAmountForDisplay()) ?? self.starsState?.balance ?? StarsAmount.zero,' in screen, 'UI override must exclude TON/Gram')

    def test_gift_opacity_and_pager_dim(self):
        screen = (SOURCE / 'submodules/TelegramUI/Components/Gifts/GiftViewScreen/Sources/GiftViewScreen.swift').read_text()
        pager = (SOURCE / 'submodules/TelegramUI/Components/Gifts/GiftViewScreen/Sources/GiftPagerComponent.swift').read_text()
        self.assertFalse('let ghostBaseSheetColor' in screen, 'Gift background must keep theme opacity')
        self.assertTrue('.color(environment.theme.actionSheet.opaqueItemBackgroundColor)' in screen)
        self.assertTrue('self.backgroundColor = environmentValue.theme.actionSheet.opaqueItemBackgroundColor' in screen)
        update=pager.split('func update(component: GiftPagerComponent,',1)[1]
        self.assertFalse('ghostBaseProfileGift' in update, 'Gift update must not lower dim for profile gifts')
        self.assertTrue('self.dimView.backgroundColor = UIColor(white: 0.0, alpha: 0.4)' in update)

    def test_exact_stage_and_all_tampering(self):
        self.assertTrue((ROOT/'scripts/materialize_jg13_stars_gift.py').exists(), 'Stars/Gift stage missing')
        stage=importlib.import_module('materialize_jg13_stars_gift')
        stage.verify_stars_gift(SOURCE)
        m=stage.read_manifest()
        with tempfile.TemporaryDirectory() as directory:
            source=Path(directory)
            for n in set(m['owners']) | set(m['locks']):
                p=source/n;p.parent.mkdir(parents=True,exist_ok=True)
                t=(SOURCE/n).read_text()
                if n in m['owners']:t=stage.restore_owner(n,t)
                p.write_text(t)
            stage.apply_stars_gift(source)
            with self.assertRaises(RuntimeError):stage.apply_stars_gift(source)
            for n in set(m['owners']) | set(m['locks']):
                p=source/n;before=p.read_bytes();p.write_bytes(before+b'\n// tampered\n')
                with self.assertRaises(RuntimeError):stage.verify_stars_gift(source)
                p.write_bytes(before)


if __name__ == '__main__':unittest.main()
