#!/usr/bin/env python3

import os
from pathlib import Path

root = Path(os.environ.get(
    "GHOSTBASE_SOURCE_ROOT",
    "/root/gb_builder/work/swiftgram-src"
))

paths = {
    "phone_controller": root / "submodules/AuthorizationUI/Sources/AuthorizationSequencePhoneEntryController.swift",
    "phone_node": root / "submodules/AuthorizationUI/Sources/AuthorizationSequencePhoneEntryControllerNode.swift",
    "account": root / "submodules/TelegramCore/Sources/Account/Account.swift",
}

for name, path in paths.items():
    if not path.is_file():
        raise SystemExit(f"[BOTSAFE2] missing {name}: {path}")


def require(value: bool, message: str) -> None:
    if not value:
        raise SystemExit(f"[BOTSAFE2] {message}")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"[BOTSAFE2] {label} anchor count: {count}")
    return text.replace(old, new, 1)


# 1) Make bot-token login available on the very first phone entry screen.
controller_path = paths["phone_controller"]
controller = controller_path.read_text(encoding="utf-8")
controller_marker = "// MARK: GhostBase v1.0ZF BOTSAFE2 first bot login"

require(
    "private func openGhostBaseBotLogin()" in controller,
    "existing bot login UI must be applied first"
)

if controller_marker not in controller:
    old_guard = '''    private func openGhostBaseBotLogin() {
        guard self.otherAccountPhoneNumbers.0 != nil,
              self.account != nil,
              !self.ghostBaseBotLoginOpening else {
            return
        }
'''
    new_guard = '''    // MARK: GhostBase v1.0ZF BOTSAFE2 first bot login
    private func openGhostBaseBotLogin() {
        guard self.account != nil,
              !self.ghostBaseBotLoginOpening else {
            return
        }
'''
    controller = replace_once(
        controller,
        old_guard,
        new_guard,
        "first-login guard"
    )

controller_path.write_text(controller, encoding="utf-8")

node_path = paths["phone_node"]
node = node_path.read_text(encoding="utf-8")
node_marker = "// MARK: GhostBase v1.0ZF BOTSAFE2 first-screen button"

require(
    "ghostBaseBotLoginNode" in node,
    "existing bot login node must be applied first"
)

if node_marker not in node:
    node = replace_once(
        node,
        '''        self.ghostBaseBotLoginNode.setAttributedTitle(NSAttributedString(string: "Войти как бот — Экспериментально", font: Font.regular(16.0), textColor: self.theme.list.itemAccentColor, paragraphAlignment: .center), for: [])
        self.ghostBaseBotLoginNode.accessibilityLabel = "Войти как бот"
        self.ghostBaseBotLoginNode.accessibilityTraits = [.button]
        self.ghostBaseBotLoginNode.isHidden = !hasOtherAccounts
''',
        '''        // MARK: GhostBase v1.0ZF BOTSAFE2 first-screen button
        self.ghostBaseBotLoginNode.setAttributedTitle(
            NSAttributedString(
                string: "Войти как бот",
                font: Font.regular(16.0),
                textColor: self.theme.list.itemAccentColor,
                paragraphAlignment: .center
            ),
            for: []
        )
        self.ghostBaseBotLoginNode.accessibilityLabel = "Войти как бот"
        self.ghostBaseBotLoginNode.accessibilityTraits = [.button]
        self.ghostBaseBotLoginNode.isHidden = false
''',
        "first-screen button creation"
    )

    node = replace_once(
        node,
        '''        let botLoginReservedHeight: CGFloat =
            self.hasOtherAccounts ? 40.0 : 0.0
''',
        '''        let botLoginReservedHeight: CGFloat = 40.0
''',
        "first-screen reserved height"
    )

    node = replace_once(
        node,
        '''        if self.hasOtherAccounts {
            self.ghostBaseBotLoginNode.isHidden = false
            transition.updateFrame(
                node: self.ghostBaseBotLoginNode,
                frame: CGRect(
                    x: floorToScreenPixels(
                        (layout.size.width - botLoginSize.width) / 2.0
                    ),
                    y: buttonFrame.maxY + 4.0,
                    width: botLoginSize.width,
                    height: 36.0
                )
            )
        } else {
            self.ghostBaseBotLoginNode.isHidden = true
        }
''',
        '''        self.ghostBaseBotLoginNode.isHidden = false
        transition.updateFrame(
            node: self.ghostBaseBotLoginNode,
            frame: CGRect(
                x: floorToScreenPixels(
                    (layout.size.width - botLoginSize.width) / 2.0
                ),
                y: buttonFrame.maxY + 4.0,
                width: botLoginSize.width,
                height: 36.0
            )
        )
''',
        "first-screen button layout"
    )

node_path.write_text(node, encoding="utf-8")

# 2) Close local chat-list holes without starting managedServiceViews or
# calling messages.getDialogs / messages.getPinnedDialogs.
account_path = paths["account"]
account = account_path.read_text(encoding="utf-8")
account_marker = "// MARK: GhostBase v1.0ZF BOTSAFE2 local chat-list holes"

require(
    "// MARK: GhostBase v1.0ZE BOTSAFE1 account quarantine" in account,
    "BOTSAFE1 quarantine must be applied first"
)

if account_marker not in account:
    old = '''        let _ = (postbox.transaction { transaction -> Void in
            transaction.updatePeerPresencesInternal(presences: [peerId: TelegramUserPresence(status: .present(until: Int32.max - 1), lastActivity: 0)], merge: { _, updated in return updated })
            transaction.setNeedsPeerGroupMessageStatsSynchronization(groupId: Namespaces.PeerGroup.archive, namespace: Namespaces.Message.Cloud)
        }).start()
'''
    new = '''        let _ = (postbox.transaction { transaction -> Void in
            transaction.updatePeerPresencesInternal(presences: [peerId: TelegramUserPresence(status: .present(until: Int32.max - 1), lastActivity: 0)], merge: { _, updated in return updated })
            transaction.setNeedsPeerGroupMessageStatsSynchronization(groupId: Namespaces.PeerGroup.archive, namespace: Namespaces.Message.Cloud)

            // MARK: GhostBase v1.0ZF BOTSAFE2 local chat-list holes
            if ghostBaseBotSafeMode {
                var removedRootHoles = 0
                for hole in transaction.allChatListHoles(groupId: .root) {
                    transaction.replaceChatListHole(
                        groupId: .root,
                        index: hole.index,
                        hole: nil
                    )
                    removedRootHoles += 1
                }

                var removedArchiveHoles = 0
                for hole in transaction.allChatListHoles(
                    groupId: Namespaces.PeerGroup.archive
                ) {
                    transaction.replaceChatListHole(
                        groupId: Namespaces.PeerGroup.archive,
                        index: hole.index,
                        hole: nil
                    )
                    removedArchiveHoles += 1
                }

                ghostBaseBotSafeRecord(
                    peerId: peerId,
                    event: "local chat-list holes closed root=\\(removedRootHoles) archive=\\(removedArchiveHoles)"
                )
            }
        }).start()
'''
    account = replace_once(account, old, new, "local chat-list transaction")

account_path.write_text(account, encoding="utf-8")

# Proofs.
for proof in (
    controller_marker,
    "guard self.account != nil",
):
    require(proof in controller, f"controller proof missing: {proof}")

for proof in (
    node_marker,
    'string: "Войти как бот"',
    "let botLoginReservedHeight: CGFloat = 40.0",
    "self.ghostBaseBotLoginNode.isHidden = false",
):
    require(proof in node, f"node proof missing: {proof}")

for proof in (
    account_marker,
    "transaction.allChatListHoles(groupId: .root)",
    "Namespaces.PeerGroup.archive",
    "local chat-list holes closed",
):
    require(proof in account, f"account proof missing: {proof}")

require(
    "messages.getDialogs" not in account[
        account.index(account_marker):
        account.index(account_marker) + 2200
    ],
    "BOTSAFE2 local hole closure must not add getDialogs"
)

print("[BOTSAFE2] bot-token login enabled on first authorization screen")
print("[BOTSAFE2] root/archive chat-list holes closed locally")
print("[BOTSAFE2] BOTSAFE1 quarantine remains enabled")
print("[BOTSAFE2] no dialog RPC restored")
