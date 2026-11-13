"""All identified native GRAM balance surfaces use one account-local presentation stream."""
from pathlib import Path
import os,shutil,subprocess,tempfile,unittest,json,sys
ROOT=Path(__file__).resolve().parents[1]
SOURCE=Path(os.environ.get('JG_STABLE182_SOURCE',ROOT.parent/'jerkgram-next/stable182-combined'))
PREFIX='submodules/TelegramUI/Components/'
OWNERS=[PREFIX+'Gifts/GiftStoreScreen/Sources/BalanceComponent.swift',PREFIX+'Gifts/GiftStoreScreen/Sources/GiftStoreScreen.swift',PREFIX+'Stars/StarsBalanceOverlayComponent/Sources/StarsBalanceOverlayComponent.swift']
HELPER='submodules/AccountContext/Sources/JerkgramLocalGramBalanceSignal.swift'
def fixture():
    boundaries=(ROOT/'tests/fixtures/wave2a2/lifecycle-boundaries.swift').read_text().split('class ItemListController {',1)[0]
    policy=(SOURCE/'submodules/AccountContext/Sources/JerkgramLocalGramBalance.swift').read_text()
    helper='\n'.join(l for l in (SOURCE/HELPER).read_text().splitlines() if not l.startswith('import ')).replace('public static func','static func')
    matrix=(ROOT/'tests/fixtures/stable182/gram-signal-matrix.swift').read_text().replace('// ACTUAL_GRAM_SIGNAL',helper)
    return boundaries+'\n'+policy+'\n'+matrix
class Presentations(unittest.TestCase):
    def test_native_parent_bytes_match_pinned_official_sources(self):
        sys.path.insert(0,str(ROOT/'scripts'))
        from jg132_beta3_stages import manifest,UPSTREAM
        official=json.loads((ROOT/'tests/fixtures/stable182/gram-native-provenance.json').read_text())
        self.assertEqual(official['upstream_sha'],UPSTREAM)
        stage=manifest('post181-gram-presentation-completion')
        self.assertEqual(set(official['owners']),set(OWNERS))
        for name,row in official['owners'].items():
            self.assertEqual(stage['owners'][name]['before_sha256'],row['sha256'],name+' must match official bytes, including EOF')

    def test_ui_only_stream_owners_and_lifetime(self):
        for owner in OWNERS:
            text=(SOURCE/owner).read_text()
            self.assertEqual(text.count('JerkgramLocalGramBalance.displayedBalance('),1,owner)
            self.assertIn('component.context.account.peerId.toInt64()',text)
        gift=(SOURCE/OWNERS[1]).read_text()
        self.assertIn('self.starsStateDisposable = (tonContext.state',gift,'native business state retained')
        overlay=(SOURCE/OWNERS[2]).read_text()
        self.assertIn('if component.peerId == component.context.account.peerId',overlay)
        helper=(SOURCE/HELPER).read_text()
        self.assertIn('removeObserver(observer)',helper)
        self.assertIn('notification.userInfo?["accountPeerId"]',helper)
        self.assertNotIn('Timer',helper)
        self.assertNotIn('updateState',helper)
        self.assertNotIn('// ACTUAL_',fixture())
    def test_native_notification_and_account_matrix(self):
        if not shutil.which('xcrun'):
            if os.environ.get('JG_STABLE182_REQUIRE_NATIVE')=='1':self.fail('GRAM stream matrix requires native Swift')
            self.skipTest('macOS Swift pending')
        with tempfile.TemporaryDirectory(prefix='stable182-gram-stream-') as d:
            d=Path(d);(d/'main.swift').write_text(fixture())
            for opt in ['-Onone','-O']:
                r=subprocess.run(['xcrun','swiftc','-swift-version','5',opt,str(d/'main.swift'),'-o',str(d/'test')],capture_output=True,text=True,timeout=90)
                self.assertEqual(r.returncode,0,r.stdout+r.stderr)
                r=subprocess.run([str(d/'test')],capture_output=True,text=True,timeout=30)
                self.assertEqual(r.returncode,0,r.stdout+r.stderr)
                print(r.stdout.strip(),flush=True)
if __name__=='__main__':unittest.main(verbosity=2)
