#!/usr/bin/env python3

import os
from pathlib import Path

root = Path(os.environ.get(
    "GHOSTBASE_SOURCE_ROOT",
    "/root/gb_builder/work/swiftgram-src"
))
dry_run = os.environ.get("GHOSTBASE_DRY_RUN") == "1"

panel_path = root / (
    "submodules/TelegramUI/Components/Chat/"
    "ChatMessageSelectionInputPanelNode/Sources/"
    "ChatMessageSelectionInputPanelNode.swift"
)
controller_path = root / (
    "submodules/TelegramUI/Sources/Chat/"
    "ChatControllerLoadDisplayNode.swift"
)

def once(text: str, old: str, new: str, label: str) -> str:
    if new in text:
        return text
    if old not in text:
        raise SystemExit(f"anchor not found: {label}")
    return text.replace(old, new, 1)

panel = panel_path.read_text(encoding="utf-8")
controller = controller_path.read_text(encoding="utf-8")

panel = once(
    panel,
    """    private let forwardButton: GlassButtonView
    private let shareButton: GlassButtonView
""",
    """    private let forwardButton: GlassButtonView
    private let forwardWithoutAuthorButton: GlassButtonView
    private let shareButton: GlassButtonView
""",
    "button property"
)

panel = once(
    panel,
    """        self.forwardButton.accessibilityLabel = strings.VoiceOver_MessageContextForward
        
        self.shareButton = GlassButtonView()
""",
    """        self.forwardButton.accessibilityLabel = strings.VoiceOver_MessageContextForward
        
        self.forwardWithoutAuthorButton = GlassButtonView()
        self.forwardWithoutAuthorButton.icon = "Chat/Input/Accessory Panels/MessageSelectionForward"
        self.forwardWithoutAuthorButton.isAccessibilityElement = true
        self.forwardWithoutAuthorButton.accessibilityLabel = "Переслать без автора"
        
        self.shareButton = GlassButtonView()
""",
    "button creation"
)

panel = once(
    panel,
    """        self.view.addSubview(self.forwardButton)
        self.view.addSubview(self.shareButton)
""",
    """        self.view.addSubview(self.forwardButton)
        self.view.addSubview(self.forwardWithoutAuthorButton)
        self.view.addSubview(self.shareButton)
""",
    "add button"
)

panel = once(
    panel,
    """        self.forwardButton.isImplicitlyDisabled = true
        self.shareButton.isImplicitlyDisabled = true
""",
    """        self.forwardButton.isImplicitlyDisabled = true
        self.forwardWithoutAuthorButton.isImplicitlyDisabled = true
        self.shareButton.isImplicitlyDisabled = true
""",
    "initial state"
)

panel = once(
    panel,
    """        self.forwardButton.button.addTarget(self, action: #selector(self.forwardButtonPressed), for: .touchUpInside)
        self.shareButton.button.addTarget(self, action: #selector(self.shareButtonPressed), for: .touchUpInside)
""",
    """        self.forwardButton.button.addTarget(self, action: #selector(self.forwardButtonPressed), for: .touchUpInside)
        self.forwardWithoutAuthorButton.button.addTarget(self, action: #selector(self.forwardWithoutAuthorButtonPressed), for: .touchUpInside)
        self.shareButton.button.addTarget(self, action: #selector(self.shareButtonPressed), for: .touchUpInside)
""",
    "button action"
)

panel = once(
    panel,
    """        self.forwardButton.isEnabled = self.selectedMessages.count != 0
""",
    """        self.forwardButton.isEnabled = self.selectedMessages.count != 0
        self.forwardWithoutAuthorButton.isEnabled = self.selectedMessages.count != 0
""",
    "button enabled state"
)

old_forward = """    @objc private func forwardButtonPressed() {
        if let _ = self.presentationInterfaceState?.renderedPeer?.peer as? TelegramSecretChat {
            return
        }
        if let actions = self.actions, actions.isCopyProtected {
            self.interfaceInteraction?.displayCopyProtectionTip(self.forwardButton, false)
        } else if !self.forwardButton.isImplicitlyDisabled {
            self.interfaceInteraction?.forwardSelectedMessages()
        }
    }
"""

new_forward = """    @objc private func forwardButtonPressed() {
        if let _ = self.presentationInterfaceState?.renderedPeer?.peer as? TelegramSecretChat {
            return
        }
        if let actions = self.actions, actions.isCopyProtected {
            self.interfaceInteraction?.displayCopyProtectionTip(self.forwardButton, false)
        } else if !self.forwardButton.isImplicitlyDisabled {
            self.interfaceInteraction?.updateForwardOptionsState { _ in
                ChatInterfaceForwardOptionsState(
                    hideNames: false,
                    hideCaptions: false,
                    unhideNamesOnCaptionChange: false
                )
            }
            self.interfaceInteraction?.forwardSelectedMessages()
        }
    }
    
    // MARK: GhostBase v1.0Y multi-select forward without author
    @objc private func forwardWithoutAuthorButtonPressed() {
        if let _ = self.presentationInterfaceState?.renderedPeer?.peer as? TelegramSecretChat {
            return
        }
        if let actions = self.actions, actions.isCopyProtected {
            self.interfaceInteraction?.displayCopyProtectionTip(
                self.forwardWithoutAuthorButton,
                false
            )
        } else if !self.forwardWithoutAuthorButton.isImplicitlyDisabled {
            self.interfaceInteraction?.updateForwardOptionsState { _ in
                ChatInterfaceForwardOptionsState(
                    hideNames: true,
                    hideCaptions: false,
                    unhideNamesOnCaptionChange: false
                )
            }
            self.interfaceInteraction?.forwardSelectedMessages()
        }
    }
"""

panel = once(
    panel,
    old_forward,
    new_forward,
    "button handlers"
)

panel = once(
    panel,
    """            self.forwardButton.isImplicitlyDisabled = !actions.options.contains(.forward)
""",
    """            self.forwardButton.isImplicitlyDisabled = !actions.options.contains(.forward)
            self.forwardWithoutAuthorButton.isImplicitlyDisabled = !actions.options.contains(.forward)
""",
    "available actions"
)

panel = once(
    panel,
    """            self.forwardButton.isImplicitlyDisabled = true
            self.shareButton.isImplicitlyDisabled = true
""",
    """            self.forwardButton.isImplicitlyDisabled = true
            self.forwardWithoutAuthorButton.isImplicitlyDisabled = true
            self.shareButton.isImplicitlyDisabled = true
""",
    "unavailable actions"
)

old_pair = """                    self.shareButton,
                    self.forwardButton
"""

new_pair = """                    self.shareButton,
                    self.forwardWithoutAuthorButton,
                    self.forwardButton
"""

pair_count = panel.count(old_pair)

if pair_count == 0 and new_pair not in panel:
    raise SystemExit("button arrays anchor not found")

panel = panel.replace(old_pair, new_pair)

old_closure = """        }, forwardSelectedMessages: { [weak self] in
            if let strongSelf = self {
                strongSelf.commitPurposefulAction()
                if let forwardMessageIdsSet = strongSelf.presentationInterfaceState.interfaceState.selectionState?.selectedIds {
                    let forwardMessageIds = Array(forwardMessageIdsSet).sorted()
                    strongSelf.forwardMessages(messageIds: forwardMessageIds)
                }
            }
        }, forwardCurrentForwardMessages:"""

new_closure = """        }, forwardSelectedMessages: { [weak self] in
            if let strongSelf = self {
                strongSelf.commitPurposefulAction()
                if let forwardMessageIdsSet = strongSelf.presentationInterfaceState.interfaceState.selectionState?.selectedIds {
                    let forwardMessageIds = Array(forwardMessageIdsSet).sorted()
                    strongSelf.forwardMessages(
                        messageIds: forwardMessageIds,
                        options: strongSelf.presentationInterfaceState.interfaceState.forwardOptionsState
                    )
                }
            }
        }, forwardCurrentForwardMessages:"""

controller = once(
    controller,
    old_closure,
    new_closure,
    "selected messages forwarding"
)

required = [
    "forwardWithoutAuthorButton",
    "GhostBase v1.0Y multi-select forward without author",
    "hideNames: true",
    "options: strongSelf.presentationInterfaceState.interfaceState.forwardOptionsState"
]

combined = panel + controller

for value in required:
    if value not in combined:
        raise SystemExit(f"missing proof: {value}")

if dry_run:
    print(f"[DRY RUN] would update {panel_path}")
    print(f"[DRY RUN] would update {controller_path}")
else:
    panel_path.write_text(panel, encoding="utf-8")
    controller_path.write_text(controller, encoding="utf-8")

print("[v1.0Y] multi-select forwarding anchors OK")
