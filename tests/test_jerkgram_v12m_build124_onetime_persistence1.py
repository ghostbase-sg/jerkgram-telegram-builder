#!/usr/bin/env python3

from pathlib import Path
import importlib

from scripts.apply_jerkgram_v12m_build124_onetime_persistence1 import (
    patch_autoremove_text,
    patch_voice_file_text,
)


AUTOREMOVE_FIXTURE = '''                                var updatedAttributes = currentMessage.attributes
                                for i in 0 ..< updatedAttributes.count {
                                    if let _ = updatedAttributes[i] as? AutoclearTimeoutMessageAttribute {
                                        updatedAttributes.remove(at: i)
                                        break
                                    }
                                }
'''

VOICE_FIXTURE = '''                var isConsumed: Bool?
                
                var consumableContentIcon: UIImage?
                for attribute in arguments.message.attributes {
                    if let attribute = attribute as? ConsumableContentMessageAttribute {
                        if !attribute.consumed {
                            if arguments.incoming {
                                consumableContentIcon = PresentationResourcesChat.chatBubbleConsumableContentIncomingIcon(arguments.presentationData.theme.theme)
                            } else {
                                consumableContentIcon = PresentationResourcesChat.chatBubbleConsumableContentOutgoingIcon(arguments.presentationData.theme.theme)
                            }
                        }
                        isConsumed = attribute.consumed
                        break
                    }
                }
'''


def test_autoremove_keeps_view_once_identity_without_rearming_timestamp_operation():
    updated = patch_autoremove_text(AUTOREMOVE_FIXTURE)

    assert "BUILD124_PERSISTENT_ONETIME_MARKER1" in updated
    assert "currentMessage.minAutoremoveOrClearTimeout == viewOnceTimeout" in updated
    assert "AutoclearTimeoutMessageAttribute(timeout: viewOnceTimeout, countdownBeginTime: nil)" in updated

    # Ordinary autoclear messages still follow Telegram's stock removal path.
    assert "updatedAttributes.remove(at: i)" in updated

    # Never falsify the consumed/read state just to preserve the one-time look.
    assert "ConsumableContentMessageAttribute(consumed: false)" not in updated


def test_voice_keeps_one_time_visual_after_consumption_but_preserves_consumed_state():
    updated = patch_voice_file_text(VOICE_FIXTURE)

    assert "BUILD124_PERSISTENT_ONETIME_VOICE_VISUAL1" in updated
    assert "arguments.message.minAutoremoveOrClearTimeout == viewOnceTimeout" in updated
    assert "if !attribute.consumed || jerkgramKeepConsumedOneTimeVisual" in updated
    assert "isConsumed = attribute.consumed" in updated
    assert "ConsumableContentMessageAttribute(consumed: false)" not in updated


def test_build124_onetime_patch_is_idempotent():
    once_auto = patch_autoremove_text(AUTOREMOVE_FIXTURE)
    twice_auto = patch_autoremove_text(once_auto)
    assert twice_auto == once_auto

    once_voice = patch_voice_file_text(VOICE_FIXTURE)
    twice_voice = patch_voice_file_text(once_voice)
    assert twice_voice == once_voice


def test_patch_targets_only_materialized_official_owners():
    module = importlib.import_module("scripts.apply_jerkgram_v12m_build124_onetime_persistence1")
    source = Path(module.__file__).read_text(encoding="utf-8")

    assert "submodules/TelegramCore/Sources/State/ManagedAutoremoveMessageOperations.swift" in source
    assert "submodules/TelegramUI/Components/Chat/ChatMessageInteractiveFileNode/Sources/ChatMessageInteractiveFileNode.swift" in source

    # Build124 is a late overlay; do not rewrite historical OT1/OT2 scripts.
    assert "apply_ghostbase_v10p_sh1_ot1_combined.py" not in source
    assert "apply_ghostbase_v10q_sh2_ot2_combined.py" not in source
