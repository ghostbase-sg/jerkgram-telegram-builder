#!/usr/bin/env python3

from pathlib import Path
import importlib.util
import unittest


REPO = Path(__file__).resolve().parents[1]
PATCH = REPO / "scripts" / "apply_jerkgram_v12m_build124_onetime_persistence1.py"
VERIFY = REPO / "scripts" / "verify_jerkgram_v12m_build124_onetime_persistence1.py"

LEGACY_AUTOREMOVE_FIXTURE = '''                                var updatedMedia = currentMessage.media
                                let ghostBaseOT1KeepOutgoingTimerLocal = (((UserDefaults.standard.object(forKey: "jerkgram.ProtectedContent.Enabled") as? Bool) ?? true) && ((UserDefaults.standard.object(forKey: "jerkgram.ProtectedContent.OneTimeSave") as? Bool) ?? false) && message.id.peerId.namespace != Namespaces.Peer.SecretChat)

                                for i in 0 ..< updatedMedia.count {
                                    if let _ = updatedMedia[i] as? TelegramMediaImage {
                                        if ghostBaseOT1KeepOutgoingTimerLocal {
                                            UserDefaults.standard.set(UserDefaults.standard.integer(forKey: "GhostBase.OT1.AutoremoveKeepBlocked.Count") + 1, forKey: "GhostBase.OT1.AutoremoveKeepBlocked.Count")
                                            UserDefaults.standard.set("managedAutoremoveImage", forKey: "jerkgram.OT1.OutgoingKeepPath")
                                        } else {
                                            updatedMedia[i] = TelegramMediaExpiredContent(data: .image)
                                        }
                                    } else if let file = updatedMedia[i] as? TelegramMediaFile {
                                        if ghostBaseOT1KeepOutgoingTimerLocal {
                                            UserDefaults.standard.set(UserDefaults.standard.integer(forKey: "GhostBase.OT1.AutoremoveKeepBlocked.Count") + 1, forKey: "GhostBase.OT1.AutoremoveKeepBlocked.Count")
                                            UserDefaults.standard.set(file.isInstantVideo ? "managedAutoremoveInstantVideo" : (file.isVoice ? "managedAutoremoveVoice" : "managedAutoremoveFile"), forKey: "jerkgram.OT1.OutgoingKeepPath")
                                        } else if file.isInstantVideo {
                                            updatedMedia[i] = TelegramMediaExpiredContent(data: .videoMessage)
                                        } else if file.isVoice {
                                            updatedMedia[i] = TelegramMediaExpiredContent(data: .voiceMessage)
                                        } else {
                                            updatedMedia[i] = TelegramMediaExpiredContent(data: .file)
                                        }
                                    }
                                }
                                var updatedAttributes = currentMessage.attributes
                                for i in 0 ..< updatedAttributes.count {
                                    if let _ = updatedAttributes[i] as? AutoclearTimeoutMessageAttribute {
                                        updatedAttributes.remove(at: i)
                                        break
                                    }
                                }
'''

REMOTE_FIXTURE = '''        let timestamp = Int32(CFAbsoluteTimeGetCurrent() + NSTimeIntervalSince1970)
        let countdownBeginTime = consumeDate ?? timestamp
        
        for i in 0 ..< updatedAttributes.count {
            if let attribute = updatedAttributes[i] as? AutoremoveTimeoutMessageAttribute {
                if (attribute.countdownBeginTime == nil || attribute.countdownBeginTime == 0) && message.containsSecretMedia {
                    updatedAttributes[i] = AutoremoveTimeoutMessageAttribute(timeout: attribute.timeout, countdownBeginTime: countdownBeginTime)
                    updateMessage = true
                                 
                    if message.id.peerId.namespace == Namespaces.Peer.SecretChat {
                    } else {
                        if attribute.timeout == viewOnceTimeout || timestamp >= countdownBeginTime + attribute.timeout {
                            for i in 0 ..< updatedMedia.count {
                                if let _ = updatedMedia[i] as? TelegramMediaImage {
                                    updatedMedia[i] = TelegramMediaExpiredContent(data: .image)
                                }
                            }
                        }
                    }
                }
            } else if let attribute = updatedAttributes[i] as? AutoclearTimeoutMessageAttribute {
                if (attribute.countdownBeginTime == nil || attribute.countdownBeginTime == 0) && message.containsSecretMedia {
                    updatedAttributes[i] = AutoclearTimeoutMessageAttribute(timeout: attribute.timeout, countdownBeginTime: countdownBeginTime)
                    updateMessage = true
                    
                    if message.id.peerId.namespace == Namespaces.Peer.SecretChat {
                    } else {
                        for i in 0 ..< updatedMedia.count {
                            if attribute.timeout == viewOnceTimeout || timestamp >= countdownBeginTime + attribute.timeout {
                                if let _ = updatedMedia[i] as? TelegramMediaImage {
                                    updatedMedia[i] = TelegramMediaExpiredContent(data: .image)
                                }
                            }
                        }
                    }
                }
            }
        }
'''

# Exact v10p composition shape: replace_once() changed only the first
# remote image/file owner. The second autoclear-image owner stayed stock.
LEGACY_REMOTE_FIXTURE = '''        let timestamp = Int32(CFAbsoluteTimeGetCurrent() + NSTimeIntervalSince1970)
        let countdownBeginTime = consumeDate ?? timestamp
        
        for i in 0 ..< updatedAttributes.count {
            if let attribute = updatedAttributes[i] as? AutoremoveTimeoutMessageAttribute {
                if (attribute.countdownBeginTime == nil || attribute.countdownBeginTime == 0) && message.containsSecretMedia {
                    updatedAttributes[i] = AutoremoveTimeoutMessageAttribute(timeout: attribute.timeout, countdownBeginTime: countdownBeginTime)
                    updateMessage = true
                                 
                    if message.id.peerId.namespace == Namespaces.Peer.SecretChat {
                    } else {
                        if attribute.timeout == viewOnceTimeout || timestamp >= countdownBeginTime + attribute.timeout {
                            for i in 0 ..< updatedMedia.count {
                                if let _ = updatedMedia[i] as? TelegramMediaImage {
                                    let ghostBaseOT1KeepOutgoingTimerLocal = (((UserDefaults.standard.object(forKey: "jerkgram.ProtectedContent.Enabled") as? Bool) ?? true) && ((UserDefaults.standard.object(forKey: "jerkgram.ProtectedContent.OneTimeSave") as? Bool) ?? false) && message.id.peerId.namespace != Namespaces.Peer.SecretChat)
                                    if ghostBaseOT1KeepOutgoingTimerLocal {
                                        UserDefaults.standard.set(UserDefaults.standard.integer(forKey: "jerkgram.OT1.OutgoingKeepBlocked.Count") + 1, forKey: "jerkgram.OT1.OutgoingKeepBlocked.Count")
                                        UserDefaults.standard.set("consumeImage", forKey: "jerkgram.OT1.OutgoingKeepPath")
                                    } else {
                                        updatedMedia[i] = TelegramMediaExpiredContent(data: .image)
                                    }
                                } else if let file = updatedMedia[i] as? TelegramMediaFile {
                                    let ghostBaseKeepVoiceCircleLocal = (((UserDefaults.standard.object(forKey: "jerkgram.ProtectedContent.Enabled") as? Bool) ?? true) && ((UserDefaults.standard.object(forKey: "jerkgram.ProtectedContent.OneTimeSave") as? Bool) ?? false) && message.id.peerId.namespace != Namespaces.Peer.SecretChat && (file.isInstantVideo || file.isVoice))
                                    let ghostBaseOT1KeepOutgoingTimerLocal = (((UserDefaults.standard.object(forKey: "jerkgram.ProtectedContent.Enabled") as? Bool) ?? true) && ((UserDefaults.standard.object(forKey: "jerkgram.ProtectedContent.OneTimeSave") as? Bool) ?? false) && message.id.peerId.namespace != Namespaces.Peer.SecretChat)

                                    if file.isInstantVideo {
                                        if !(ghostBaseKeepVoiceCircleLocal || ghostBaseOT1KeepOutgoingTimerLocal) {
                                            updatedMedia[i] = TelegramMediaExpiredContent(data: .videoMessage)
                                        } else {
                                            UserDefaults.standard.set(UserDefaults.standard.integer(forKey: "jerkgram.OT1.OutgoingKeepBlocked.Count") + 1, forKey: "jerkgram.OT1.OutgoingKeepBlocked.Count")
                                            UserDefaults.standard.set("consumeInstantVideo", forKey: "jerkgram.OT1.OutgoingKeepPath")
                                        }
                                    } else if file.isVoice {
                                        if !(ghostBaseKeepVoiceCircleLocal || ghostBaseOT1KeepOutgoingTimerLocal) {
                                            updatedMedia[i] = TelegramMediaExpiredContent(data: .voiceMessage)
                                        } else {
                                            UserDefaults.standard.set(UserDefaults.standard.integer(forKey: "jerkgram.OT1.OutgoingKeepBlocked.Count") + 1, forKey: "jerkgram.OT1.OutgoingKeepBlocked.Count")
                                            UserDefaults.standard.set("consumeVoice", forKey: "jerkgram.OT1.OutgoingKeepPath")
                                        }
                                    } else {
                                        if !ghostBaseOT1KeepOutgoingTimerLocal {
                                            updatedMedia[i] = TelegramMediaExpiredContent(data: .file)
                                        } else {
                                            UserDefaults.standard.set(UserDefaults.standard.integer(forKey: "jerkgram.OT1.OutgoingKeepBlocked.Count") + 1, forKey: "jerkgram.OT1.OutgoingKeepBlocked.Count")
                                            UserDefaults.standard.set("consumeFile", forKey: "jerkgram.OT1.OutgoingKeepPath")
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            } else if let attribute = updatedAttributes[i] as? AutoclearTimeoutMessageAttribute {
                if (attribute.countdownBeginTime == nil || attribute.countdownBeginTime == 0) && message.containsSecretMedia {
                    updatedAttributes[i] = AutoclearTimeoutMessageAttribute(timeout: attribute.timeout, countdownBeginTime: countdownBeginTime)
                    updateMessage = true
                    
                    if message.id.peerId.namespace == Namespaces.Peer.SecretChat {
                    } else {
                        for i in 0 ..< updatedMedia.count {
                            if attribute.timeout == viewOnceTimeout || timestamp >= countdownBeginTime + attribute.timeout {
                                if let _ = updatedMedia[i] as? TelegramMediaImage {
                                    updatedMedia[i] = TelegramMediaExpiredContent(data: .image)
                                }
                            }
                        }
                    }
                }
            }
        }
'''


class Build124OneTimeRemotePersistenceTests(unittest.TestCase):
    def load_patch(self):
        spec = importlib.util.spec_from_file_location("build124_onetime_persistence", PATCH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_build124_replaces_legacy_ot1_managed_autoremove_owner(self):
        module = self.load_patch()
        updated = module.patch_autoremove_text(LEGACY_AUTOREMOVE_FIXTURE)
        self.assertIn("BUILD124_PERSISTENT_ONETIME_MEDIA1", updated)
        self.assertIn("BUILD124_PERSISTENT_ONETIME_MARKER1", updated)
        self.assertIn("if !jerkgramKeepOneTimeIdentity {", updated)
        self.assertEqual(updated.count("if !jerkgramKeepOneTimeRemoteMedia && (attribute.timeout == viewOnceTimeout"), 2)
        self.assertIn("AutoremoveTimeoutMessageAttribute(timeout: attribute.timeout, countdownBeginTime: nil)", updated)
        self.assertIn("AutoclearTimeoutMessageAttribute(timeout: attribute.timeout, countdownBeginTime: nil)", updated)
        self.assertIn("TelegramMediaExpiredContent(data: .image)", updated)
        self.assertIn("TelegramMediaExpiredContent(data: .videoMessage)", updated)
        self.assertIn("TelegramMediaExpiredContent(data: .voiceMessage)", updated)
        self.assertIn("TelegramMediaExpiredContent(data: .file)", updated)

    def test_remote_consume_patch_is_idempotent(self):
        module = self.load_patch()
        once = module.patch_remote_consumed_text(REMOTE_FIXTURE)
        self.assertEqual(once, module.patch_remote_consumed_text(once))

    def test_remote_consume_owner_is_in_materialized_official_telegramcore(self):
        source = PATCH.read_text(encoding="utf-8")
        self.assertIn("submodules/TelegramCore/Sources/TelegramEngine/Messages/MarkMessageContentAsConsumedInteractively.swift", source)

    def test_source_verifier_requires_remote_persistence_owner(self):
        source = VERIFY.read_text(encoding="utf-8")
        self.assertIn("BUILD124_PERSISTENT_ONETIME_REMOTE1", source)
        self.assertIn("remote.count(REMOTE_MARKER) == 1", source)
        self.assertIn('remote.count("if !jerkgramKeepOneTimeRemoteMedia && (attribute.timeout == viewOnceTimeout") == 2', source)
        self.assertIn("AutoclearTimeoutMessageAttribute(timeout: attribute.timeout, countdownBeginTime: nil)", source)
        self.assertIn('UserDefaults.standard.object(forKey: \\"jerkgram.ProtectedContent.Enabled\\")', source)
        self.assertIn('UserDefaults.standard.object(forKey: \\"jerkgram.ProtectedContent.OneTimeSave\\")', source)


if __name__ == "__main__":
    unittest.main()
