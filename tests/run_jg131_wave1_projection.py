#!/usr/bin/env python3
"""Runs unmodified production Foundation sections, with only UI publication sinks replaced.
Apple Foundation behavior is required; Linux has a deliberate, reported skip.
Usage: python3 run_foundation_fixture.py [composite-source-root]
"""
import os, platform, subprocess, sys, tempfile
from pathlib import Path
root=Path(sys.argv[1]) if len(sys.argv)>1 else Path(__file__).resolve().parents[1]/'work/swiftgram-src'
baseline=root
g=(root/'submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift').read_text()
a=(root/'submodules/SettingsUI/Sources/Jerkgram/JerkgramArchiveFlowController.swift').read_text()
account=(root/'submodules/TelegramCore/Sources/Account/Account.swift').read_text()
def section(text,start,end): return text[text.index(start):text.index(end,text.index(start))]
parts=['import Foundation\n',section(g,'private enum GhostBaseKey {','private func ghostBaseIsValidStarsAmountInput'),
       'private let ghostBaseSendTextStyleKey = "jerkgram.Messages.SendTextStyle"\n',
       section(g,'private func jerkgramScopedSettingsKey(', '// Regression sentinel'),
       section(g,'struct GhostBaseSettingsState:', 'private func jerkgramSettingsMenuIcon('),
       section(account,'public enum JerkgramHotSettings {','public final class AccountAuxiliaryMethods'),
       section(a,'private let jerkgramPortableBooleanKeys:', 'private func jerkgramCoreRootURL()'),
       section(a,'private func jerkgramProjectImportedSettingsToActiveDefaults(', 'private func jerkgramPresentArchiveImportError(')]
# These production cache owners live in other files and are copied exactly from the
# audited baseline, not reimplemented by the fixture.
for rel,end in [('submodules/TelegramCore/Sources/Utils/JerkgramSponsoredContentPolicy.swift',None),('submodules/TelegramCore/Sources/Network/JerkgramDownloadBoostPolicy.swift','enum JerkgramDownloadBoostPolicy {')]:
 p=root/rel
 t=(p if p.exists() else baseline/rel).read_text().replace('import Foundation','')
 parts.append(t.split(end)[0] if end else t)
parts.insert(1,(Path(__file__).parent/'fixtures/build176/foundation_sinks.swift').read_text())
parts.append((Path(__file__).parent/'fixtures/build176/foundation_cases.swift').read_text())
with tempfile.TemporaryDirectory(prefix='jg176-b1-') as tmp:
 source=Path(tmp)/'fixture.swift';source.write_text('\n'.join(parts))
 # Always materialize for inspection; execution is intentionally Apple-only.
 if platform.system()!='Darwin':
  print('SKIP: production Foundation fixture requires macOS / Apple Foundation; extraction succeeded')
  sys.exit(0)
 env=dict(os.environ,CFFIXED_USER_HOME=tmp)
 subprocess.run(['swift',str(source)],check=True,env=env)
