#!/usr/bin/env python3
from __future__ import annotations

import os
from pathlib import Path


ROOT = Path(os.environ.get(
    "GHOSTBASE_SOURCE_ROOT",
    "/root/gb_builder/work/swiftgram-src",
)).resolve()

BG = ROOT / (
    "submodules/TelegramUI/Components/PeerInfo/"
    "PeerInfoScreen/Sources/"
    "GhostBaseProfileFullscreenBackground.swift"
)
AVATAR = ROOT / "submodules/AvatarNode/Sources/PeerAvatar.swift"

MARK = "Jerkgram v1.2I BUILD120_PROFILE_COLDSTART1"
PIPELINE_MARK = "GhostBase v1.1T BUILD97_STATIC_AVATAR_PIPELINE1"
BLUR_MARK = "GhostBase v1.1U BUILD106_STATIC_AVATAR_BLUR1"
BUILD114_MARK = "Jerkgram v1.2C BUILD114_SOURCE_LUMINANCE1"
REMOVED_BUILD113_MARK = "Jerkgram v1.2B BUILD113_STATIC_AVATAR_BLUR_OWNER1"
CACHE_MARK = "GhostBase v1.1T AVATAR_REOPEN_NO_GREY1"
FINAL_CACHE_MARK = "Jerkgram v1.2L BUILD123_PROFILE_FINAL_CACHE1"
COMPLETE_EMISSION_MARK = "Jerkgram v1.2L BUILD123_PROFILE_COMPLETE_EMISSION1"


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build120 profile blur lifecycle] " + message)


def main() -> None:
    require(BG.is_file(), "profile background source missing: " + str(BG))
    require(AVATAR.is_file(), "Telegram avatar source missing: " + str(AVATAR))
    text = BG.read_text(encoding="utf-8")
    avatar_text = AVATAR.read_text(encoding="utf-8")

    if MARK in text and FINAL_CACHE_MARK in text and COMPLETE_EMISSION_MARK in avatar_text and "avatar-final-v2:" in text:
        print("[Build120 profile blur lifecycle] already materialized")
        return

    if COMPLETE_EMISSION_MARK not in avatar_text:
        account_signature = "public func peerAvatarImage(account: Account, peerReference: PeerReference?, authorOfMessage: MessageReference?, representation: TelegramMediaImageRepresentation?, displayDimensions: CGSize = CGSize(width: 60.0, height: 60.0), clipStyle: AvatarNodeClipStyle = .round, blurred: Bool = false, inset: CGFloat = 0.0, emptyColor: UIColor? = nil, synchronousLoad: Bool = false, provideUnrounded: Bool = false, cutoutRect: CGRect? = nil) -> Signal<(UIImage, UIImage)?, NoError>? {"
        account_signature_complete = account_signature.replace(
            "cutoutRect: CGRect? = nil)",
            "cutoutRect: CGRect? = nil, completeOnly: Bool = false)",
        )
        require(avatar_text.count(account_signature) == 1, "account avatar API anchor")
        avatar_text = avatar_text.replace(account_signature, account_signature_complete, 1)

        account_forward = '''        provideUnrounded: synchronousLoad,
        cutoutRect: cutoutRect
'''
        account_forward_complete = '''        provideUnrounded: synchronousLoad,
        cutoutRect: cutoutRect,
        completeOnly: completeOnly
'''
        require(avatar_text.count(account_forward) == 1, "account avatar forwarding anchor")
        avatar_text = avatar_text.replace(account_forward, account_forward_complete, 1)

        postbox_signature = "public func peerAvatarImage(postbox: Postbox, peerReference: PeerReference?, authorOfMessage: MessageReference?, representation: TelegramMediaImageRepresentation?, displayDimensions: CGSize = CGSize(width: 60.0, height: 60.0), clipStyle: AvatarNodeClipStyle = .round, blurred: Bool = false, inset: CGFloat = 0.0, emptyColor: UIColor? = nil, synchronousLoad: Bool = false, provideUnrounded: Bool = false, cutoutRect: CGRect? = nil) -> Signal<(UIImage, UIImage)?, NoError>? {"
        postbox_signature_complete = postbox_signature.replace(
            "cutoutRect: CGRect? = nil)",
            "cutoutRect: CGRect? = nil, completeOnly: Bool = false)",
        )
        require(avatar_text.count(postbox_signature) == 1, "Postbox avatar API anchor")
        avatar_text = avatar_text.replace(postbox_signature, postbox_signature_complete, 1)

        data_owner = '''    if let imageData = peerAvatarImageData(postbox: postbox, peerReference: peerReference, authorOfMessage: authorOfMessage, representation: representation, synchronousLoad: synchronousLoad) {
        return imageData
        |> mapToSignal { data -> Signal<(UIImage, UIImage)?, NoError> in
'''
        complete_data_owner = '''    if let imageData = peerAvatarImageData(postbox: postbox, peerReference: peerReference, authorOfMessage: authorOfMessage, representation: representation, synchronousLoad: synchronousLoad) {
        // MARK: Jerkgram v1.2L BUILD123_PROFILE_COMPLETE_EMISSION1
        // Filter while PeerAvatarImageType is still attached to the emission.
        // A MediaBox completion check after UIImage decoding has a race with
        // an already-queued immediateThumbnailData preview.
        let selectedImageData = imageData
        |> filter { value in
            guard completeOnly else {
                return true
            }
            guard let (_, dataType) = value else {
                return false
            }
            if case .complete = dataType {
                return true
            } else {
                return false
            }
        }
        return selectedImageData
        |> mapToSignal { data -> Signal<(UIImage, UIImage)?, NoError> in
'''
        require(avatar_text.count(data_owner) == 1, "typed avatar emission owner")
        avatar_text = avatar_text.replace(data_owner, complete_data_owner, 1)
        AVATAR.write_text(avatar_text, encoding="utf-8")

    # Build114 intentionally removed the Build113 systemMaterial override and
    # restored the Build106 persistent-alpha owner. Bind Build120 to the
    # actually materialized final chain instead of silently reviving Build113.
    for token in (PIPELINE_MARK, BLUR_MARK, BUILD114_MARK, CACHE_MARK):
        require(token in text, "required final owner missing: " + token)
    require(
        REMOVED_BUILD113_MARK not in text,
        "obsolete Build113 blur owner unexpectedly survived Build114",
    )

    start = text.find("    // MARK: " + PIPELINE_MARK + "\n")
    end = text.find("    private func resourceEntrySignal(\n", start)
    require(start >= 0 and end > start, "static avatar pipeline boundaries missing")

    region = text[start:end]
    require("blurred: false" in region, "Telegram avatar pipeline no longer owns unblurred decode")

    # The native circular avatar has normally already populated Telegram's
    # avatar cache when PeerInfo opens. Ask the same peerAvatarImage pipeline
    # for its cached presentation synchronously so the fullscreen background
    # does not spend its first rendered frame on itemBlocksBackgroundColor.
    # If Telegram still needs network/media work, the existing signal remains
    # live and completes normally. No raw MediaBox decode, disk scan, observer,
    # image processing pass, or second blur stage is introduced here.
    if MARK not in region:
        require(region.count("synchronousLoad: false") == 1, "expected one async static-avatar load owner")
        require("synchronousLoad: true" not in region, "unexpected pre-existing synchronous static-avatar load")
        region = region.replace(
            "            synchronousLoad: false\n",
            "            // MARK: Jerkgram v1.2I BUILD120_PROFILE_COLDSTART1\n"
            "            synchronousLoad: true\n",
            1,
        )
    else:
        require("synchronousLoad: true" in region, "existing cold-start owner is not synchronous")

    old_guard = '''        |> map { versions -> GhostBaseProfileBackgroundCacheEntry? in
            guard let image = versions?.0 else {
                return nil
            }
'''
    raced_guard = '''        |> map { versions -> GhostBaseProfileBackgroundCacheEntry? in
            // MARK: Jerkgram v1.2L BUILD123_PROFILE_FINAL_CACHE1
            // peerAvatarImage may emit immediateThumbnailData as a strongly
            // blurred preview before the real avatar resource is complete.
            // Never publish or persist that preview as a reopen cache entry.
            guard self.context.account.postbox.mediaBox.completedResourcePath(representation.resource) != nil,
                  let image = versions?.0 else {
                return nil
            }
'''
    new_guard = '''        |> map { versions -> GhostBaseProfileBackgroundCacheEntry? in
            // MARK: Jerkgram v1.2L BUILD123_PROFILE_FINAL_CACHE1
            // AvatarNode has already rejected every .blurred typed emission.
            guard let image = versions?.0 else {
                return nil
            }
'''
    if raced_guard in region:
        region = region.replace(raced_guard, new_guard, 1)
    elif FINAL_CACHE_MARK not in region:
        require(region.count(old_guard) == 1, "final static-avatar cache guard anchor")
        region = region.replace(old_guard, new_guard, 1)

    synchronous_tail = '''            // MARK: Jerkgram v1.2I BUILD120_PROFILE_COLDSTART1
            synchronousLoad: true
'''
    complete_tail = '''            // MARK: Jerkgram v1.2I BUILD120_PROFILE_COLDSTART1
            synchronousLoad: true,
            completeOnly: true
'''
    if "completeOnly: true" not in region:
        require(region.count(synchronous_tail) == 1, "complete-only avatar call anchor")
        region = region.replace(synchronous_tail, complete_tail, 1)

    text = text[:start] + region + text[end:]

    old_load_key = '''            let loadKey =
                cacheKey as String
'''
    new_load_key = '''            // Ignore disk entries written from the old blurred-thumbnail
            // pipeline; RAM is process-local and naturally starts clean.
            let loadKey =
                "avatar-final-v2:" + (cacheKey as String)
'''
    if "avatar-final-v2:" not in text:
        require(text.count(old_load_key) == 1, "avatar disk cache revision anchor")
        text = text.replace(old_load_key, new_load_key, 1)
    BG.write_text(text, encoding="utf-8")

    print("[Build120 profile blur lifecycle] GREEN")
    print("[Build120 profile blur lifecycle] cold/open/reopen use Telegram cached avatar synchronously when available")
    print("[Build120 profile blur lifecycle] Build114-restored Build106 persistent blur owner preserved")
    print("[Build120 profile blur lifecycle] Build105 bounded RAM/disk reopen cache preserved")
    print("[Build120 profile blur lifecycle] typed .blurred emissions rejected before UIImage decode and caching")


if __name__ == "__main__":
    main()
