#!/usr/bin/env python3
from pathlib import Path
import subprocess
import sys
import re

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "work/swiftgram-src"
BASE = ROOT / "scripts/apply_ghostbase_v10o_read3_combined_probe.py"

def read(p):
    return Path(p).read_text()

def write(p, s):
    Path(p).write_text(s)

def ensure(s, needle, label):
    if needle not in s:
        raise SystemExit(f"[v1.0P+SH1+OT1] ERROR: missing {label}: {needle}")

def replace_once(s, old, new, label):
    if old in s:
        return s.replace(old, new, 1)
    if new in s:
        return s
    raise SystemExit(f"[v1.0P+SH1+OT1] ERROR: pattern not found: {label}")

def find_files(root, needles):
    out = []
    for p in root.rglob("*.swift"):
        try:
            s = p.read_text(errors="ignore")
        except Exception:
            continue
        if all(n in s for n in needles):
            out.append(p)
    return out

print("[v1.0P+SH1+OT1] running base v1.0O+READ3...")
subprocess.check_call([sys.executable, str(BASE)], cwd=str(ROOT))

telegram_core = SRC / "submodules/TelegramCore/Sources"
telegram_ui = SRC / "submodules/TelegramUI/Sources"

forward_p = telegram_ui / "ChatControllerForwardMessages.swift"
consume_p = telegram_core / "TelegramEngine/Messages/MarkMessageContentAsConsumedInteractively.swift"
auto_p = telegram_core / "State/ManagedAutoremoveMessageOperations.swift"
settings_p = SRC / "submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift"

forward = read(forward_p)
consume = read(consume_p)
auto = read(auto_p)
settings = read(settings_p)

ensure(settings, "Version: v1.0O+READ3", "base version")
ensure(forward, "let _ = (enqueueMessages(account: strongSelf.context.account, peerId: peer.id, messages: peerMessages)", "share peerMessages enqueue")
ensure(consume, "GhostBase v0.8I.2 voice/circle local keep", "old voice/circle keep")
ensure(auto, "Performing autoremove", "managed autoremove")

# v1.0P main branch: Pre-delete/Postbox shadow trace.
delete_files = find_files(telegram_core, ["DeleteMessagesWithGlobalIds"])
if not delete_files:
    raise SystemExit("[v1.0P+SH1+OT1] ERROR: no DeleteMessagesWithGlobalIds file")

patched_delete_files = []

helper = r"""
// MARK: GhostBase v1.0P Pre-delete Shadow Trace
private func ghostBaseV10PTracePreDelete(transaction: Transaction, messageIds: [MessageId], source: String) {
    let d = UserDefaults.standard
    d.set(d.integer(forKey: "GhostBase.V10P.DeleteEvents") + 1, forKey: "GhostBase.V10P.DeleteEvents")
    d.set(source, forKey: "GhostBase.V10P.LastDeleteSource")
    d.set(messageIds.count, forKey: "GhostBase.V10P.LastDeleteIdCount")

    var mh = 0
    var th = 0
    var lastId = "none"
    var lastPeer = "none"
    var lastText = "none"
    var lastLen = 0

    for id in messageIds {
        lastId = "\(id)"
        if let m = transaction.getMessage(id) {
            mh += 1
            lastPeer = "\(m.id.peerId)"
            let t = m.text
            lastLen = t.count
            if !t.isEmpty {
                th += 1
                lastText = t.count > 220 ? String(t.prefix(220)) : t
            } else {
                lastText = "empty"
            }
        }
    }

    d.set(d.integer(forKey: "GhostBase.V10P.PreDeleteMessageHits") + mh, forKey: "GhostBase.V10P.PreDeleteMessageHits")
    d.set(d.integer(forKey: "GhostBase.V10P.PreDeleteTextHits") + th, forKey: "GhostBase.V10P.PreDeleteTextHits")
    d.set(lastId, forKey: "GhostBase.V10P.LastPreDeleteId")
    d.set(lastPeer, forKey: "GhostBase.V10P.LastPreDeletePeer")
    d.set(lastLen, forKey: "GhostBase.V10P.LastPreDeleteTextLength")
    d.set(lastText, forKey: "GhostBase.V10P.LastPreDeleteText")
    d.set(th > 0 ? "PRE_DELETE_TEXT_FOUND" : (mh > 0 ? "PRE_DELETE_MESSAGE_NO_TEXT" : "PRE_DELETE_POSTBOX_MISS"), forKey: "GhostBase.V10P.Verdict")
}
"""

for fp in delete_files:
    t = read(fp)

    if "case .DeleteMessagesWithGlobalIds" not in t and "case let .DeleteMessagesWithGlobalIds" not in t:
        continue

    if "GhostBase v1.0P Pre-delete Shadow Trace" not in t:
        lines = t.splitlines()
        if "import Foundation" not in t:
            at = max([i + 1 for i, x in enumerate(lines) if x.startswith("import ")] or [0])
            lines.insert(at, "import Foundation")
        at = max([i + 1 for i, x in enumerate(lines) if x.startswith("import ")] or [0])
        lines.insert(at, helper)
        t = "\n".join(lines) + "\n"

    if "GhostBase.V10P.CaseDeleteMessagesWithGlobalIds" not in t:
        pat = re.compile(r'^(\s*case(?:\s+let)?\s+\.DeleteMessagesWithGlobalIds\(([^)]+)\):\s*)$', re.M)
        m = pat.search(t)
        if not m:
            continue

        indent = re.match(r'^(\s*)', m.group(1)).group(1)
        arg = m.group(2).strip()

        call = (
            "\n" + indent + "    // MARK: GhostBase.V10P.CaseDeleteMessagesWithGlobalIds\n"
            + indent + "    let ghostBaseV10PMessageIds = transaction.messageIdsForGlobalIds(" + arg + ")\n"
            + indent + "    ghostBaseV10PTracePreDelete(transaction: transaction, messageIds: ghostBaseV10PMessageIds, source: \"DeleteMessagesWithGlobalIds\")"
        )

        t = t[:m.end()] + call + t[m.end():]

    write(fp, t)
    patched_delete_files.append(fp)

if not patched_delete_files:
    raise SystemExit("[v1.0P+SH1+OT1] ERROR: v1.0P case patch failed")

print("[v1.0P+SH1+OT1] P patched files:")
for fp in patched_delete_files:
    print(" -", fp.relative_to(ROOT))

# SH1 side block: Share/Forward path scheduled-send attribute.
old = '''                                    if let maybeAmount = sendPaidMessageStars[peer.id], let amount = maybeAmount {
                                        peerMessages = peerMessages.map { message -> EnqueueMessage in
                                            return message.withUpdatedAttributes { attributes in
                                                var attributes = attributes
                                                attributes.append(PaidStarsMessageAttribute(stars: amount, postponeSending: false))
                                                return attributes
                                            }
                                        }
                                    }
                                    
                                    let _ = (enqueueMessages(account: strongSelf.context.account, peerId: peer.id, messages: peerMessages)
'''

new = '''                                    // MARK: GhostBase v1.0P+SH1 Share Scheduled Send
                                    let ghostBaseSH1ScheduledSendEnabled = ((UserDefaults.standard.object(forKey: "GhostBase.GhostMode.ScheduledSend") as? Bool) ?? false)
                                    if ghostBaseSH1ScheduledSendEnabled && !shouldDivert {
                                        let ghostBaseSH1ScheduleTime = Int32(Date().timeIntervalSince1970) + 12
                                        peerMessages = peerMessages.map { message -> EnqueueMessage in
                                            return message.withUpdatedAttributes { attributes in
                                                var attributes = attributes
                                                if !attributes.contains(where: { $0 is OutgoingScheduleInfoMessageAttribute }) {
                                                    attributes.append(OutgoingScheduleInfoMessageAttribute(scheduleTime: ghostBaseSH1ScheduleTime, repeatPeriod: nil))
                                                }
                                                return attributes
                                            }
                                        }
                                        UserDefaults.standard.set(UserDefaults.standard.integer(forKey: "GhostBase.SH1.ShareScheduledIntercept.Count") + 1, forKey: "GhostBase.SH1.ShareScheduledIntercept.Count")
                                        UserDefaults.standard.set("\\(peer.id)", forKey: "GhostBase.SH1.LastSharePeerId")
                                        UserDefaults.standard.set(peerMessages.count, forKey: "GhostBase.SH1.LastShareMessageCount")
                                        UserDefaults.standard.set(Int(ghostBaseSH1ScheduleTime), forKey: "GhostBase.SH1.LastShareScheduleTime")
                                    }

                                    if let maybeAmount = sendPaidMessageStars[peer.id], let amount = maybeAmount {
                                        peerMessages = peerMessages.map { message -> EnqueueMessage in
                                            return message.withUpdatedAttributes { attributes in
                                                var attributes = attributes
                                                attributes.append(PaidStarsMessageAttribute(stars: amount, postponeSending: false))
                                                return attributes
                                            }
                                        }
                                    }
                                    
                                    let _ = (enqueueMessages(account: strongSelf.context.account, peerId: peer.id, messages: peerMessages)
'''

forward = replace_once(forward, old, new, "SH1 peerMessages share scheduled path")
write(forward_p, forward)

# OT1 side block: image keep in consume path.
old = '''                                if let _ = updatedMedia[i] as? TelegramMediaImage {
                                    updatedMedia[i] = TelegramMediaExpiredContent(data: .image)
                                } else if let file = updatedMedia[i] as? TelegramMediaFile {
'''

new = '''                                if let _ = updatedMedia[i] as? TelegramMediaImage {
                                    let ghostBaseOT1KeepOutgoingTimerLocal = (((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.Enabled") as? Bool) ?? true) && ((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.OneTimeSave") as? Bool) ?? false) && message.id.peerId.namespace != Namespaces.Peer.SecretChat)
                                    if ghostBaseOT1KeepOutgoingTimerLocal {
                                        UserDefaults.standard.set(UserDefaults.standard.integer(forKey: "GhostBase.OT1.OutgoingKeepBlocked.Count") + 1, forKey: "GhostBase.OT1.OutgoingKeepBlocked.Count")
                                        UserDefaults.standard.set("consumeImage", forKey: "GhostBase.OT1.OutgoingKeepPath")
                                    } else {
                                        updatedMedia[i] = TelegramMediaExpiredContent(data: .image)
                                    }
                                } else if let file = updatedMedia[i] as? TelegramMediaFile {
'''

consume = replace_once(consume, old, new, "OT1 consume image keep")
write(consume_p, consume)

old = '''                                    let ghostBaseKeepVoiceCircleLocal = (((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.Enabled") as? Bool) ?? true) && ((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.OneTimeSave") as? Bool) ?? false) && message.id.peerId.namespace != Namespaces.Peer.SecretChat && (file.isInstantVideo || file.isVoice))
                                    if file.isInstantVideo {
                                        if !ghostBaseKeepVoiceCircleLocal {
                                            updatedMedia[i] = TelegramMediaExpiredContent(data: .videoMessage)
                                        }
                                    } else if file.isVoice {
                                        if !ghostBaseKeepVoiceCircleLocal {
                                            updatedMedia[i] = TelegramMediaExpiredContent(data: .voiceMessage)
                                        }
                                    } else {
                                        updatedMedia[i] = TelegramMediaExpiredContent(data: .file)
                                    }
'''

new = '''                                    let ghostBaseKeepVoiceCircleLocal = (((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.Enabled") as? Bool) ?? true) && ((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.OneTimeSave") as? Bool) ?? false) && message.id.peerId.namespace != Namespaces.Peer.SecretChat && (file.isInstantVideo || file.isVoice))
                                    let ghostBaseOT1KeepOutgoingTimerLocal = (((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.Enabled") as? Bool) ?? true) && ((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.OneTimeSave") as? Bool) ?? false) && message.id.peerId.namespace != Namespaces.Peer.SecretChat)

                                    if file.isInstantVideo {
                                        if !(ghostBaseKeepVoiceCircleLocal || ghostBaseOT1KeepOutgoingTimerLocal) {
                                            updatedMedia[i] = TelegramMediaExpiredContent(data: .videoMessage)
                                        } else {
                                            UserDefaults.standard.set(UserDefaults.standard.integer(forKey: "GhostBase.OT1.OutgoingKeepBlocked.Count") + 1, forKey: "GhostBase.OT1.OutgoingKeepBlocked.Count")
                                            UserDefaults.standard.set("consumeInstantVideo", forKey: "GhostBase.OT1.OutgoingKeepPath")
                                        }
                                    } else if file.isVoice {
                                        if !(ghostBaseKeepVoiceCircleLocal || ghostBaseOT1KeepOutgoingTimerLocal) {
                                            updatedMedia[i] = TelegramMediaExpiredContent(data: .voiceMessage)
                                        } else {
                                            UserDefaults.standard.set(UserDefaults.standard.integer(forKey: "GhostBase.OT1.OutgoingKeepBlocked.Count") + 1, forKey: "GhostBase.OT1.OutgoingKeepBlocked.Count")
                                            UserDefaults.standard.set("consumeVoice", forKey: "GhostBase.OT1.OutgoingKeepPath")
                                        }
                                    } else {
                                        if !ghostBaseOT1KeepOutgoingTimerLocal {
                                            updatedMedia[i] = TelegramMediaExpiredContent(data: .file)
                                        } else {
                                            UserDefaults.standard.set(UserDefaults.standard.integer(forKey: "GhostBase.OT1.OutgoingKeepBlocked.Count") + 1, forKey: "GhostBase.OT1.OutgoingKeepBlocked.Count")
                                            UserDefaults.standard.set("consumeFile", forKey: "GhostBase.OT1.OutgoingKeepPath")
                                        }
                                    }
'''

consume = replace_once(consume, old, new, "OT1 consume file keep")
write(consume_p, consume)

old = '''                                var updatedMedia = currentMessage.media
                                for i in 0 ..< updatedMedia.count {
                                    if let _ = updatedMedia[i] as? TelegramMediaImage {
                                        updatedMedia[i] = TelegramMediaExpiredContent(data: .image)
                                    } else if let file = updatedMedia[i] as? TelegramMediaFile {
                                        if file.isInstantVideo {
                                            updatedMedia[i] = TelegramMediaExpiredContent(data: .videoMessage)
                                        } else if file.isVoice {
                                            updatedMedia[i] = TelegramMediaExpiredContent(data: .voiceMessage)
                                        } else {
                                            updatedMedia[i] = TelegramMediaExpiredContent(data: .file)
                                        }
                                    }
                                }
'''

new = '''                                var updatedMedia = currentMessage.media
                                let ghostBaseOT1KeepOutgoingTimerLocal = (((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.Enabled") as? Bool) ?? true) && ((UserDefaults.standard.object(forKey: "GhostBase.ProtectedContent.OneTimeSave") as? Bool) ?? false) && message.id.peerId.namespace != Namespaces.Peer.SecretChat)

                                for i in 0 ..< updatedMedia.count {
                                    if let _ = updatedMedia[i] as? TelegramMediaImage {
                                        if ghostBaseOT1KeepOutgoingTimerLocal {
                                            UserDefaults.standard.set(UserDefaults.standard.integer(forKey: "GhostBase.OT1.AutoremoveKeepBlocked.Count") + 1, forKey: "GhostBase.OT1.AutoremoveKeepBlocked.Count")
                                            UserDefaults.standard.set("managedAutoremoveImage", forKey: "GhostBase.OT1.OutgoingKeepPath")
                                        } else {
                                            updatedMedia[i] = TelegramMediaExpiredContent(data: .image)
                                        }
                                    } else if let file = updatedMedia[i] as? TelegramMediaFile {
                                        if ghostBaseOT1KeepOutgoingTimerLocal {
                                            UserDefaults.standard.set(UserDefaults.standard.integer(forKey: "GhostBase.OT1.AutoremoveKeepBlocked.Count") + 1, forKey: "GhostBase.OT1.AutoremoveKeepBlocked.Count")
                                            UserDefaults.standard.set(file.isInstantVideo ? "managedAutoremoveInstantVideo" : (file.isVoice ? "managedAutoremoveVoice" : "managedAutoremoveFile"), forKey: "GhostBase.OT1.OutgoingKeepPath")
                                        } else if file.isInstantVideo {
                                            updatedMedia[i] = TelegramMediaExpiredContent(data: .videoMessage)
                                        } else if file.isVoice {
                                            updatedMedia[i] = TelegramMediaExpiredContent(data: .voiceMessage)
                                        } else {
                                            updatedMedia[i] = TelegramMediaExpiredContent(data: .file)
                                        }
                                    }
                                }
'''

auto = replace_once(auto, old, new, "OT1 managed autoremove keep")
write(auto_p, auto)

if "v1.0P Pre-delete Shadow Trace:" not in settings:
    block = r'''v1.0P Pre-delete Shadow Trace:
PDeleteEvents: \(UserDefaults.standard.integer(forKey: "GhostBase.V10P.DeleteEvents"))
PLastDeleteSource: \(UserDefaults.standard.string(forKey: "GhostBase.V10P.LastDeleteSource") ?? "none")
PLastDeleteIdCount: \(UserDefaults.standard.integer(forKey: "GhostBase.V10P.LastDeleteIdCount"))
PPreDeleteMessageHits: \(UserDefaults.standard.integer(forKey: "GhostBase.V10P.PreDeleteMessageHits"))
PPreDeleteTextHits: \(UserDefaults.standard.integer(forKey: "GhostBase.V10P.PreDeleteTextHits"))
PLastPreDeleteId: \(UserDefaults.standard.string(forKey: "GhostBase.V10P.LastPreDeleteId") ?? "none")
PLastPreDeletePeer: \(UserDefaults.standard.string(forKey: "GhostBase.V10P.LastPreDeletePeer") ?? "none")
PLastPreDeleteTextLength: \(UserDefaults.standard.integer(forKey: "GhostBase.V10P.LastPreDeleteTextLength"))
PLastPreDeleteText: \(UserDefaults.standard.string(forKey: "GhostBase.V10P.LastPreDeleteText") ?? "none")
PVerdict: \(UserDefaults.standard.string(forKey: "GhostBase.V10P.Verdict") ?? "none")

SH1 Share Scheduled Send:
SH1ShareScheduledIntercept: \(UserDefaults.standard.integer(forKey: "GhostBase.SH1.ShareScheduledIntercept.Count"))
SH1LastSharePeerId: \(UserDefaults.standard.string(forKey: "GhostBase.SH1.LastSharePeerId") ?? "none")
SH1LastShareMessageCount: \(UserDefaults.standard.integer(forKey: "GhostBase.SH1.LastShareMessageCount"))
SH1LastShareScheduleTime: \(UserDefaults.standard.integer(forKey: "GhostBase.SH1.LastShareScheduleTime"))

OT1 Timer Media Local Keep:
OT1OutgoingKeepBlocked: \(UserDefaults.standard.integer(forKey: "GhostBase.OT1.OutgoingKeepBlocked.Count"))
OT1AutoremoveKeepBlocked: \(UserDefaults.standard.integer(forKey: "GhostBase.OT1.AutoremoveKeepBlocked.Count"))
OT1OutgoingKeepPath: \(UserDefaults.standard.string(forKey: "GhostBase.OT1.OutgoingKeepPath") ?? "none")

'''
    settings = settings.replace("v1.0O Persistent SourcePeer Candidate:", block + "v1.0O Persistent SourcePeer Candidate:", 1)

settings = settings.replace("Version: v1.0O+READ3", "Version: v1.0P+SH1+OT1")
write(settings_p, settings)

forward = read(forward_p)
consume = read(consume_p)
auto = read(auto_p)
settings = read(settings_p)

ensure(forward, "GhostBase v1.0P+SH1 Share Scheduled Send", "SH1 patch")
ensure(forward, "GhostBase.SH1.ShareScheduledIntercept.Count", "SH1 diagnostics")

ensure(consume, "GhostBase.OT1.OutgoingKeepBlocked.Count", "OT1 consume diagnostics")
ensure(auto, "GhostBase.OT1.AutoremoveKeepBlocked.Count", "OT1 autoremove diagnostics")

ensure(settings, "v1.0P Pre-delete Shadow Trace:", "P settings")
ensure(settings, "SH1 Share Scheduled Send:", "SH1 settings")
ensure(settings, "OT1 Timer Media Local Keep:", "OT1 settings")
ensure(settings, "Version: v1.0P+SH1+OT1", "version")

for p in patched_delete_files:
    s = read(p)
    ensure(s, "GhostBase v1.0P Pre-delete Shadow Trace", "P helper")
    ensure(s, "ghostBaseV10PTracePreDelete(transaction: transaction", "P call")

print("[v1.0P+SH1+OT1] patch OK")
