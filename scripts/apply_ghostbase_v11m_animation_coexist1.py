#!/usr/bin/env python3

import os
from pathlib import Path

ROOT = Path(os.environ.get(
    "GHOSTBASE_SOURCE_ROOT",
    "/root/gb_builder/work/swiftgram-src"
))

P = (
    ROOT
    / "submodules/TelegramUI/Components/"
      "PeerInfo/PeerInfoScreen/Sources"
)

AVATAR = P / "PeerInfoAvatarTransformContainerNode.swift"

if not AVATAR.is_file():
    raise RuntimeError(
        f"[V11M-A2] missing: {AVATAR}"
    )

text = AVATAR.read_text(
    encoding="utf-8"
)

if "GhostBase v1.1M ANIMCOEXIST1" in text:
    print("[V11M-A2] already materialized")
    raise SystemExit(0)

old = '''        if let videoNode = self.videoNode {
            if case .immediate = transition, fraction == 1.0 {
                return
            }
            if fraction > 0.0 {
                videoNode.pause()
            } else {
                videoNode.play()
            }
            transition.updateAlpha(node: videoNode, alpha: 1.0 - fraction)
        }
'''

new = '''        if let videoNode = self.videoNode {
            if case .immediate = transition, fraction == 1.0 {
                return
            }

            // MARK: GhostBase v1.1M ANIMCOEXIST1
            //
            // V11L created a second fullscreen video source.
            // Telegram's native profile transition normally pauses
            // the circular avatar whenever fraction > 0.
            //
            // With GhostBase animated background enabled, keep the
            // native avatar decoder alive as well. V11M-A already
            // gives the fullscreen backdrop a separate playback id,
            // so both consumers can coexist on the same MediaBox file.
            let keepVideoAlive =
                GhostBaseProfileBlurSettings
                    .loadEnabled()?
                    .animatedBackgroundEnabled
                == true

            if keepVideoAlive {
                videoNode.play()
            } else if fraction > 0.0 {
                videoNode.pause()
            } else {
                videoNode.play()
            }

            transition.updateAlpha(
                node: videoNode,
                alpha: 1.0 - fraction
            )
        }
'''

count = text.count(old)

if count != 1:
    raise RuntimeError(
        "[V11M-A2] native avatar transition: "
        f"expected 1 found {count}"
    )

text = text.replace(
    old,
    new,
    1
)

AVATAR.write_text(
    text,
    encoding="utf-8"
)

print("[V11M-A2] applied")
print("  native video-avatar stays playing with GhostBase animation")
print("  Official pause behavior remains when GhostBase animation is off")
