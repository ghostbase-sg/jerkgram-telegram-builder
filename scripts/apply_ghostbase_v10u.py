#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "work/swiftgram-src"

MEDIA = (
    SRC
    / "submodules/TelegramUI/Sources/Chat"
    / "ChatControllerMediaRecording.swift"
)

SETTINGS = (
    SRC
    / "submodules/SettingsUI/Sources/GhostBase"
    / "GhostBaseSettingsController.swift"
)

def require(value, message):
    if not value:
        raise RuntimeError(f"[v1.0U] {message}")

def replace_once(text, old, new, label):
    require(old in text, f"missing anchor: {label}")
    return text.replace(old, new, 1)

require(MEDIA.is_file(), f"missing: {MEDIA}")
require(SETTINGS.is_file(), f"missing: {SETTINGS}")

media = MEDIA.read_text(encoding="utf-8")
settings = SETTINGS.read_text(encoding="utf-8")

voice_marker = "GhostBase v1.0U scheduled voice complete cleanup"

if voice_marker not in media:
    media = replace_once(
        media,
        '''            if ghostBaseRuntimeScheduledVoice {
                self.chatDisplayNode.collapseInput()

                self.updateChatPresentationInterfaceState(animated: true, interactive: false, {
                    $0.updatedInterfaceState {
                        $0.withUpdatedReplyMessageSubject(nil)
                            .withUpdatedMediaDraftState(nil)
                            .withUpdatedSendMessageEffect(nil)
                            .withUpdatedPostSuggestionState(nil)
                    }
                })

                self.updateDownButtonVisibility()
''',
        '''            if ghostBaseRuntimeScheduledVoice {
                // MARK: GhostBase v1.0U scheduled voice complete cleanup
                self.audioRecorderStatusDisposable?.dispose()
                self.audioRecorderStatusDisposable = nil

                self.chatDisplayNode.collapseInput()

                self.updateChatPresentationInterfaceState(animated: true, interactive: false, {
                    $0.updatedInterfaceState {
                        $0.withUpdatedReplyMessageSubject(nil)
                            .withUpdatedMediaDraftState(nil)
                            .withUpdatedSendMessageEffect(nil)
                            .withUpdatedPostSuggestionState(nil)
                    }.updatedInputTextPanelState { panelState in
                        return panelState.withUpdatedMediaRecordingState(nil)
                    }
                })

                self.updateDownButtonVisibility()
''',
        "scheduled voice state cleanup"
    )

menu_marker = "GhostBase v1.0U correct context source"

if menu_marker not in settings:
    old = '''    func transitionInfo() -> ContextControllerTakeControllerInfo? {
        guard let sourceNode = self.sourceNode else {
            return nil
        }

        let contentArea = self.controller.view.convert(
            self.controller.view.bounds,
            to: nil
        )

        return ContextControllerTakeControllerInfo(
            contentAreaInScreenSpace: contentArea,
            sourceNode: { [weak sourceNode] in
                guard let sourceNode = sourceNode else {
                    return nil
                }

                return (
                    sourceNode.view,
                    sourceNode.bounds
                )
            }
        )
    }
'''

    new = '''    // MARK: GhostBase v1.0U correct context source
    func transitionInfo() -> ContextControllerTakeControllerInfo? {
        let sourceNode = self.sourceNode

        return ContextControllerTakeControllerInfo(
            contentAreaInScreenSpace: CGRect(
                origin: CGPoint(),
                size: CGSize(width: 10.0, height: 10.0)
            ),
            sourceNode: { [weak sourceNode] in
                if let sourceNode = sourceNode {
                    return (
                        sourceNode.view,
                        sourceNode.bounds
                    )
                } else {
                    return nil
                }
            }
        )
    }
'''

    settings = replace_once(
        settings,
        old,
        new,
        "context menu transition source"
    )

MEDIA.write_text(media, encoding="utf-8")
SETTINGS.write_text(settings, encoding="utf-8")

require(voice_marker in media, "voice marker missing")
require(menu_marker in settings, "menu marker missing")

print("[v1.0U] voice and context-menu fixes applied")
