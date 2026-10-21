"""Two profile capture owners; reuse the established paired capture override."""
import ast
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'patches/jg13-profile-capture.sha256.json'
PREFIX = 'submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/'
SCREEN = PREFIX + 'PeerInfoScreen.swift'
AVATAR = PREFIX + 'PeerInfoAvatarTransformContainerNode.swift'
HELPER = '''// Same paired override as chat capture; native protection remains authoritative when off.
enum JerkgramProfileCapturePolicy {
    static func isProtected(nativeProtected: Bool) -> Bool {
        let allowCapture = ((JerkgramHotSettings.object(forKey: "jerkgram.ProtectedContent.AllowScreenshots") as? Bool) ?? true)
            && ((JerkgramHotSettings.object(forKey: "jerkgram.ProtectedContent.AllowScreenRecording") as? Bool) ?? true)
        return nativeProtected && !allowCapture
    }
}

'''
REPLACEMENTS = {
    SCREEN: [
        ('setLayerDisableScreenshots(self.layer, peerInfoIsCopyProtected(data: data, sharedMediaFromForumTopic: self.sharedMediaFromForumTopic))', 'setLayerDisableScreenshots(self.layer, JerkgramProfileCapturePolicy.isProtected(nativeProtected: peerInfoIsCopyProtected(data: data, sharedMediaFromForumTopic: self.sharedMediaFromForumTopic)))'),
    ],
    AVATAR: [
        ('final class PeerInfoAvatarTransformContainerNode:', HELPER + 'final class PeerInfoAvatarTransformContainerNode:'),
        ('    private var videoContent: NativeVideoContent?\n', '    private var videoContent: NativeVideoContent?\n    private var videoCaptureProtected = false\n'),
        ('                    let videoContent = NativeVideoContent(id:', '                    let captureProtected = JerkgramProfileCapturePolicy.isProtected(nativeProtected: peer.isCopyProtectionEnabled)\n                    let videoContent = NativeVideoContent(id:'),
        ('captureProtected: peer.isCopyProtectionEnabled,', 'captureProtected: captureProtected,'),
        ('id: .profileVideo(videoId, nil)', 'id: .profileVideo(videoId, peer.isCopyProtectionEnabled && !captureProtected ? "jerkgram-capture-allowed" : nil)'),
        ('                    if videoContent.id != self.videoContent?.id {', '                    if videoContent.id != self.videoContent?.id || self.videoCaptureProtected != captureProtected {'),
        ('                            self.videoContent = videoContent\n', '                            self.videoContent = videoContent\n                            self.videoCaptureProtected = captureProtected\n'),
    ],
}

def digest(data): return hashlib.sha256(data).hexdigest()

def read_manifest():
    m=json.loads(MANIFEST.read_text())
    c=json.loads((ROOT/'jerkgram-migration.json').read_text())
    expanded=json.loads((ROOT/'patches/jg13-expanded-diagnostics.sha256.json').read_text())
    preferences=json.loads((ROOT/'patches/jg13-profile-preferences.sha256.json').read_text())
    if m['upstream_sha'] != c['upstream_new_sha'] or set(m['owners']) != set(REPLACEMENTS): raise RuntimeError('Profile capture scope/pin changed')
    for name,parent in ((SCREEN,expanded),(AVATAR,preferences)):
        if m['owners'][name]['before_sha256'] != parent['owners'][name]['after_sha256']: raise RuntimeError('Profile capture wrong product parent: '+name)
    return m

def transform(name,text):
    for old,new in REPLACEMENTS[name]:
        if text.count(old) != 1: raise RuntimeError('Profile capture anchor count changed: '+name+': '+old[:70])
        text=text.replace(old,new,1)
    return text

def restore_owner(name,text):
    values=read_manifest()['owners'][name]
    if digest(text.encode()) != values['after_sha256']: raise RuntimeError('Profile capture final owner changed: '+name)
    for old,new in reversed(REPLACEMENTS[name]): text=text.replace(new,old,1)
    if digest(text.encode()) != values['before_sha256']: raise RuntimeError('Profile capture preceding owner lost: '+name)
    return text

def verify_profile_capture(source):
    m=read_manifest(); source=Path(source)
    for name in m['owners']: restore_owner(name,(source/name).read_text())
    for name,expected in m['locks'].items():
        if digest((source/name).read_bytes()) != expected: raise RuntimeError('Profile capture unrelated owner changed: '+name)
    config=(ROOT/'scripts/configure_jg13.py').read_text()
    calls=[n for n in ast.walk(ast.parse(config)) if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id=='apply_profile_capture']
    if len(calls)!=1 or len(calls[0].args)!=1 or not isinstance(calls[0].args[0],ast.Name) or calls[0].args[0].id!='SOURCE': raise RuntimeError('Profile capture canonical stage missing/duplicated')
    if config.index('    apply_sponsored(SOURCE)') >= config.index('    apply_profile_capture(SOURCE)'): raise RuntimeError('Profile capture stage order changed')
    if '    verify_profile_capture(SOURCE)' not in (ROOT/'scripts/verify_jg13_source.py').read_text(): raise RuntimeError('Profile capture root verifier missing')
    return {n:{'after_sha256':v['after_sha256']} for n,v in m['owners'].items()}

def final_profile_owners(source):
    m=read_manifest(); source=Path(source)
    # About's isolated test fixture contains only its Settings owner. The root
    # verifier separately requires the complete profile stage, including locks.
    if not any((source/n).exists() for n in m['owners']): return {}
    if all(digest((source/n).read_bytes()) == v['before_sha256'] for n,v in m['owners'].items()): return {}
    return verify_profile_capture(source)

def apply_profile_capture(source):
    source=Path(source); m=read_manifest(); outputs={}
    for n,expected in m['locks'].items():
        if digest((source/n).read_bytes())!=expected: raise RuntimeError('Profile capture regression lock changed: '+n)
    for n,v in m['owners'].items():
        text=(source/n).read_text()
        if digest(text.encode())!=v['before_sha256']: raise RuntimeError('Profile capture wrong parent/repeat: '+n)
        output=transform(n,text)
        if digest(output.encode())!=v['after_sha256']: raise RuntimeError('Profile capture output changed: '+n)
        outputs[n]=output
    for n,text in outputs.items(): (source/n).write_text(text)
    verify_profile_capture(source)
    print('Two profile capture owners VERIFIED; native predicates and paired settings retained; NOT RUNTIME TESTED')
