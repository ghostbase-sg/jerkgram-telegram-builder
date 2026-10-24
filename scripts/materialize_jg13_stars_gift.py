"""Four-owner Build167 fix: Stars currency scope and readable gift sheets."""
import ast
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/'patches/jg13-stars-gift.sha256.json'
STARS='submodules/TelegramCore/Sources/TelegramEngine/Payments/Stars.swift'
BALANCE='submodules/TelegramUI/Components/Stars/StarsTransactionsScreen/Sources/StarsTransactionsScreen.swift'
GIFT='submodules/TelegramUI/Components/Gifts/GiftViewScreen/Sources/GiftViewScreen.swift'
PAGER='submodules/TelegramUI/Components/Gifts/GiftViewScreen/Sources/GiftPagerComponent.swift'
REPLACEMENTS={
    STARS:[
        ('if let ghostBaseBalance = ghostBaseLocalStarsVisualBalance() {','if !self.ton, let ghostBaseBalance = ghostBaseLocalStarsVisualBalance() {'),
    ],
    BALANCE:[
        ('count: ghostBaseLocalStarsAmountForDisplay() ?? self.starsState?.balance ?? StarsAmount.zero,','count: (component.starsContext.ton ? nil : ghostBaseLocalStarsAmountForDisplay()) ?? self.starsState?.balance ?? StarsAmount.zero,'),
    ],
    GIFT:[
        ('''            let ghostBaseSheetColor =
                environment.theme.actionSheet.opaqueItemBackgroundColor
                    .withAlphaComponent(
                        environment.theme.overallDarkAppearance
                            ? 0.56
                            : 0.64
                    )

''',''),
        ('''                    backgroundColor:
                        .color(
                            ghostBaseSheetColor
                        ),''','''                    backgroundColor: .color(environment.theme.actionSheet.opaqueItemBackgroundColor),'''),
        ('''            let environmentValue = environment[EnvironmentType.self].value

            self.content.parentState = state''','''            let environmentValue = environment[EnvironmentType.self].value
            self.backgroundColor = environmentValue.theme.actionSheet.opaqueItemBackgroundColor

            self.content.parentState = state'''),
    ],
    PAGER:[
        ('''            let ghostBaseProfileGift =
                GhostBaseProfileBlurSettings
                    .loadEnabled() != nil
                && component.items.contains(
                    where: { item in
                        if case .profileGift =
                            item.subject {

                            return true
                        } else {
                            return false
                        }
                    }
                )

            self.dimView.backgroundColor =
                UIColor(
                    white: 0.0,
                    alpha:
                        ghostBaseProfileGift
                        ? 0.28
                        : 0.4
                )''','''            // Keep the profile grid subdued behind the gift sheet.
            self.dimView.backgroundColor = UIColor(white: 0.0, alpha: 0.4)'''),
    ],
}

def digest(data):return hashlib.sha256(data).hexdigest()

def read_manifest():
    m=json.loads(MANIFEST.read_text())
    c=json.loads((ROOT/'jerkgram-migration.json').read_text())
    parent=json.loads((ROOT/'patches/jg13-stable.product.sha256.json').read_text())
    if m['upstream_sha']!=c['upstream_new_sha'] or set(m['owners'])!=set(REPLACEMENTS):raise RuntimeError('Stars/Gift scope or pin changed')
    for n,v in m['owners'].items():
        if v['before_sha256']!=parent[n]:raise RuntimeError('Stars/Gift reviewed parent changed: '+n)
    return m

def transform(name,text):
    for old,new in REPLACEMENTS[name]:
        if text.count(old)!=1:raise RuntimeError('Stars/Gift anchor changed: '+name+': '+old[:70])
        text=text.replace(old,new,1)
    return text

def restore_owner(name,text):
    v=read_manifest()['owners'][name]
    if digest(text.encode())!=v['after_sha256']:raise RuntimeError('Stars/Gift final owner changed: '+name)
    for old,new in reversed(REPLACEMENTS[name]):
        if new:
            text=text.replace(new,old,1)
        else:
            anchor='            let sheet = sheet.update('
            if text.count(anchor)!=1:raise RuntimeError('Stars/Gift removed-block restoration anchor changed')
            text=text.replace(anchor,old+anchor,1)
    if digest(text.encode())!=v['before_sha256']:raise RuntimeError('Stars/Gift preceding bytes lost: '+name)
    return text

def check_locks(source,m):
    for n,h in m['locks'].items():
        if digest((Path(source)/n).read_bytes())!=h:raise RuntimeError('Stars/Gift regression lock changed: '+n)

def verify_stars_gift(source):
    m=read_manifest()
    for n in m['owners']:restore_owner(n,(Path(source)/n).read_text())
    check_locks(source,m)
    config=(ROOT/'scripts/configure_jg13.py').read_text()
    calls=[n for n in ast.walk(ast.parse(config)) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='apply_stars_gift']
    if len(calls)!=1 or len(calls[0].args)!=1 or not isinstance(calls[0].args[0],ast.Name) or calls[0].args[0].id!='SOURCE':raise RuntimeError('Stars/Gift canonical apply missing/duplicated')
    if config.index('    apply_profile_capture(SOURCE)')>=config.index('    apply_stars_gift(SOURCE)'):raise RuntimeError('Stars/Gift stage order changed')
    verifier=ast.parse((ROOT/'scripts/verify_jg13_source.py').read_text())
    calls=[n for n in ast.walk(verifier) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='verify_stars_gift']
    if len(calls)!=1:raise RuntimeError('Stars/Gift canonical verification missing/duplicated')
    return {n:{'after_sha256':v['after_sha256']} for n,v in m['owners'].items()}

def apply_stars_gift(source):
    source=Path(source);m=read_manifest();check_locks(source,m);outputs={}
    for n,v in m['owners'].items():
        text=(source/n).read_text()
        if digest(text.encode())!=v['before_sha256']:raise RuntimeError('Stars/Gift wrong parent or repeat: '+n)
        output=transform(n,text)
        if digest(output.encode())!=v['after_sha256']:raise RuntimeError('Stars/Gift output changed: '+n)
        restore_owner(n,output)
        outputs[n]=output
    for n,text in outputs.items():(source/n).write_text(text)
    verify_stars_gift(source)
    print('Stars-only override and opaque gift sheets VERIFIED; NOT RUNTIME TESTED')
