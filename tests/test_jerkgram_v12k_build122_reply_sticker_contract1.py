#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


REPO = Path(__file__).resolve().parents[1]
APPLY = REPO / "scripts/apply_jerkgram_v12k_build122_reply_sticker_contract1.py"
VERIFY = REPO / "scripts/verify_jerkgram_v12k_build122_reply_sticker_contract1.py"


def load_apply():
    spec = importlib.util.spec_from_file_location("jerkgram_build122_contract", APPLY)
    if spec is None or spec.loader is None:
        raise RuntimeError("unable to load Build122 apply script")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


ENQUEUE_FIXTURE = r'''
// GhostBase v1.1U BUILD106_FINAL1
// BUILD106_ALBUM_RECOVERY1
// Jerkgram v1.2J BUILD121_NATIVE_STICKER_RECOVERY1
private func ghostBaseBuildPortableDeletedReply() {}
private func ghostBaseResolveDeletedReplies() {
    |> mapToSignal { plans -> Signal<[EnqueueMessage], NoError> in
                for plan in plans {
                    guard let source = plan.source else {
                        continue
                    }
                    var recoveredGroup: [AnyMediaReference] = []
                    for groupSource in plan.sourceGroup {
                        if let recovered = ghostBaseReconstructedMedia(account: account, peerId: peerId, source: groupSource, outgoing: plan.outgoing) {
                            recoveredGroup.append(recovered)
                        }
                    }
                    if recoveredGroup.count >= 2 {
                        result.append(ghostBaseBuildRecoveredAlbumTail(outgoing: plan.outgoing, recoveredMedia: recoveredGroup[0], localGroupingKey: 1))
                    }
                    let recovered = recoveredGroup.first
                    result.append(ghostBaseBuildPortableDeletedReply(outgoing: plan.outgoing, source: source, authorName: authorName, authorUsername: plan.authorUsername, mentionPeerId: plan.mentionPeerId, recoveredMedia: recovered))
                }
    }
}
'''

STATIC_FIXTURE = r'''
// Jerkgram v1.2I BUILD120_STICKER_DELETED_ALPHA1
let ghostBaseDeletedStickerAlpha: CGFloat = (((item.message.attributes.first(where: { $0 is GhostBaseMessageAttribute }) as? GhostBaseMessageAttribute)?.isDeleted) ?? false) ? 0.55 : 1.0
        self.contextSourceNode.contentNode.alpha = ghostBaseDeletedStickerAlpha
'''

ANIMATED_FIXTURE = r'''
public class ChatMessageAnimatedStickerItemNode: ChatMessageItemView {
    override public func setupItem(_ item: ChatMessageItem, synchronousLoad: Bool) {
        super.setupItem(item, synchronousLoad: synchronousLoad)
        for media in item.message.media {
        }
    }

    private func updateVisibility() {}
}
'''


class Build122ReplyStickerContractTests(unittest.TestCase):
    def test_deleted_sticker_reply_does_not_reupload_sticker_media(self):
        module = load_apply()
        patched = module.patch_enqueue(ENQUEUE_FIXTURE)
        resolver = patched[patched.index("private func ghostBaseResolveDeletedReplies("):]
        self.assertIn("BUILD122_STICKER_REPLY_NO_REUPLOAD1", resolver)
        self.assertIn("let jerkgramStickerReply", resolver)
        self.assertIn("file.isSticker", resolver)
        self.assertIn("let recovered = jerkgramStickerReply ? nil : recoveredGroup.first", resolver)

    def test_non_sticker_and_album_recovery_paths_survive(self):
        module = load_apply()
        patched = module.patch_enqueue(ENQUEUE_FIXTURE)
        resolver = patched[patched.index("private func ghostBaseResolveDeletedReplies("):]
        self.assertIn("ghostBaseReconstructedMedia(", resolver)
        self.assertIn("recoveredGroup", resolver)
        self.assertIn("ghostBaseBuildRecoveredAlbumTail(", resolver)
        self.assertIn("recoveredMedia: recovered", resolver)

    def test_static_sticker_has_one_effective_alpha_owner(self):
        module = load_apply()
        patched = module.patch_static_sticker(STATIC_FIXTURE)
        self.assertIn("BUILD122_STATIC_STICKER_ALPHA_OWNER1", patched)
        self.assertIn("? 0.55 : 1.0", patched)
        self.assertIn("self.contextSourceNode.contentNode.alpha = ghostBaseDeletedStickerAlpha", patched)
        self.assertNotIn("self.contextSourceNode.alpha = ghostBaseDeletedStickerAlpha", patched)
        assignment_count = patched.count(".alpha = ghostBaseDeletedStickerAlpha")
        self.assertEqual(assignment_count, 1)
        self.assertEqual(0.55 ** assignment_count, 0.55)

    def test_animated_and_video_sticker_has_one_effective_alpha_owner(self):
        module = load_apply()
        patched = module.patch_animated_sticker(ANIMATED_FIXTURE)
        self.assertIn("BUILD122_ANIMATED_STICKER_ALPHA1", patched)
        self.assertIn("GhostBaseMessageAttribute", patched)
        self.assertIn("? 0.55 : 1.0", patched)
        self.assertIn("self.contextSourceNode.contentNode.alpha = ghostBaseDeletedAnimatedStickerAlpha", patched)
        self.assertNotIn("self.contextSourceNode.alpha = ghostBaseDeletedAnimatedStickerAlpha", patched)
        assignment_count = patched.count(".alpha = ghostBaseDeletedAnimatedStickerAlpha")
        self.assertEqual(assignment_count, 1)
        self.assertEqual(0.55 ** assignment_count, 0.55)

    def test_patches_are_idempotent(self):
        module = load_apply()
        enqueue_once = module.patch_enqueue(ENQUEUE_FIXTURE)
        static_once = module.patch_static_sticker(STATIC_FIXTURE)
        animated_once = module.patch_animated_sticker(ANIMATED_FIXTURE)
        self.assertEqual(module.patch_enqueue(enqueue_once), enqueue_once)
        self.assertEqual(module.patch_static_sticker(static_once), static_once)
        self.assertEqual(module.patch_animated_sticker(animated_once), animated_once)

    def test_verifier_accepts_single_alpha_and_preserved_non_sticker_recovery(self):
        module = load_apply()
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            files = {
                "submodules/TelegramCore/Sources/PendingMessages/EnqueueMessage.swift": module.patch_enqueue(ENQUEUE_FIXTURE),
                "submodules/TelegramUI/Components/Chat/ChatMessageStickerItemNode/Sources/ChatMessageStickerItemNode.swift": module.patch_static_sticker(STATIC_FIXTURE),
                "submodules/TelegramUI/Components/Chat/ChatMessageAnimatedStickerItemNode/Sources/ChatMessageAnimatedStickerItemNode.swift": module.patch_animated_sticker(ANIMATED_FIXTURE),
            }
            for relative, content in files.items():
                target = root / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content, encoding="utf-8")
            env = os.environ.copy()
            env["GHOSTBASE_SOURCE_ROOT"] = str(root)
            result = subprocess.run(
                [sys.executable, str(VERIFY)],
                env=env,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            self.assertEqual(result.returncode, 0, msg=result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
