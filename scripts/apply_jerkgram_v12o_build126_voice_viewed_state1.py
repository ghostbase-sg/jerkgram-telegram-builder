#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
TARGET = ROOT / "submodules/TelegramUI/Components/Chat/ChatMessageInteractiveFileNode/Sources/ChatMessageInteractiveFileNode.swift"
MARKER = "// MARK: Jerkgram v1.2O BUILD126_OUTGOING_ONETIME_VIEWED_VOICE1"
OLD_MARKER = "// MARK: Jerkgram v1.2M BUILD124_OUTGOING_ONETIME_VIEWED_VOICE1"


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build126 voice viewed state] " + message)


def patch_text(text: str) -> str:
    if MARKER in text:
        return text

    marker_index = text.find(OLD_MARKER)
    require(marker_index >= 0, "Build124 voice viewed owner missing")
    start = text.rfind("                        if !attribute.consumed", 0, marker_index)
    # Build124's persistent owner is followed directly by `break` in the
    # current materialized source; older revisions also assigned isConsumed
    # before that same boundary.
    end = text.find("\n                        break", marker_index)
    require(start >= 0 and end >= 0, "Build124 voice consumed branch bounds missing")

    replacement = '''                        // MARK: Jerkgram v1.2O BUILD126_OUTGOING_ONETIME_VIEWED_VOICE1
                        // Build124 rendered the outgoing check inside
                        // `if !attribute.consumed`, making the consumed branch
                        // unreachable. Preserve Telegram's incoming dot and
                        // derive outgoing status from the actual remote bit.
                        if arguments.incoming {
                            if !attribute.consumed {
                                consumableContentIcon = PresentationResourcesChat.chatBubbleConsumableContentIncomingIcon(arguments.presentationData.theme.theme)
                            }
                        } else if attribute.consumed {
                            let jerkgramViewedColor = arguments.presentationData.theme.theme.chat.message.outgoing.accentTextColor
                            consumableContentIcon = generateImage(CGSize(width: 13.0, height: 7.0), contextGenerator: { size, context in
                                context.clear(CGRect(origin: .zero, size: size))
                                context.setFillColor(jerkgramViewedColor.cgColor)
                                context.fillEllipse(in: CGRect(x: 0.0, y: 1.5, width: 4.0, height: 4.0))
                                context.setStrokeColor(jerkgramViewedColor.cgColor)
                                context.setLineWidth(1.4)
                                context.setLineCap(.round)
                                context.setLineJoin(.round)
                                context.move(to: CGPoint(x: 6.0, y: 3.6))
                                context.addLine(to: CGPoint(x: 8.2, y: 5.4))
                                context.addLine(to: CGPoint(x: 12.2, y: 1.4))
                                context.strokePath()
                            })
                        } else {
                            consumableContentIcon = PresentationResourcesChat.chatBubbleConsumableContentOutgoingIcon(arguments.presentationData.theme.theme)
                        }
'''
    return text[:start] + replacement + text[end:]


def main() -> None:
    require(TARGET.is_file(), f"missing voice owner: {TARGET}")
    TARGET.write_text(patch_text(TARGET.read_text(encoding="utf-8")), encoding="utf-8")
    print("[Build126 voice viewed state] GREEN")


if __name__ == "__main__":
    main()
