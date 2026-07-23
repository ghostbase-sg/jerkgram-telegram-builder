#!/usr/bin/env python3

import os
from pathlib import Path

ROOT = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src"))

PATHS = {
    "search": ROOT / "submodules/SettingsUI/Sources/Search/SettingsSearchableItems.swift",
    "delete": ROOT / "submodules/SettingsUI/Sources/DeleteAccountOptionsController.swift",
    "actions": ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoScreenSettingsActions.swift",
}

for name, path in PATHS.items():
    if not path.is_file():
        raise SystemExit(f"[V10ZG account] missing {name}: {path}")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"[V10ZG account] {label} anchor count: {count}")
    return text.replace(old, new, 1)


# 1. Settings search must always expose Add Account.
path = PATHS["search"]
text = path.read_text(encoding="utf-8")
marker = "// MARK: GhostBase v1.0ZG ACCOUNTUNLOCK1 settings search"
if marker not in text:
    text = replace_once(
        text,
        """    |> map { accountsAndPeers -> Bool in
        return accountsAndPeers.1.count + 1 < maximumNumberOfAccounts
    }
""",
        """    |> map { _ -> Bool in
        // MARK: GhostBase v1.0ZG ACCOUNTUNLOCK1 settings search
        return true
    }
""",
        "settings-search gate",
    )
    path.write_text(text, encoding="utf-8")

# 2. Delete-account alternatives must not hide Add Account.
path = PATHS["delete"]
text = path.read_text(encoding="utf-8")
marker = "// MARK: GhostBase v1.0ZG ACCOUNTUNLOCK1 delete alternatives"
if marker not in text:
    text = replace_once(
        text,
        "        let canAddAccounts = accountsAndPeers.1.count + 1 < maximumNumberOfAccounts\n",
        """        // MARK: GhostBase v1.0ZG ACCOUNTUNLOCK1 delete alternatives
        let canAddAccounts = true
""",
        "delete-options gate",
    )
    path.write_text(text, encoding="utf-8")

# 3. Main Add Account action: remove the hardcoded 3/4 and PremiumLimitScreen branch.
#    Bot logout: bots have no phone, so present a dedicated confirmation and use
#    logoutFromAccount in local-only mode (no auth.logOut RPC).
path = PATHS["actions"]
text = path.read_text(encoding="utf-8")

add_marker = "// MARK: GhostBase v1.0ZG ACCOUNTUNLOCK1 main action"
if add_marker not in text:
    start_anchor = "        case .addAccount:\n"
    end_anchor = "        case .logout:\n"
    start = text.find(start_anchor)
    end = text.find(end_anchor, start + len(start_anchor))
    if start == -1 or end == -1:
        raise SystemExit("[V10ZG account] add-account case anchors not found")
    replacement = """        case .addAccount:
            // MARK: GhostBase v1.0ZG ACCOUNTUNLOCK1 main action
            self.context.sharedContext.beginNewAuth(
                testingEnvironment: self.context.account.testingEnvironment
            )
"""
    text = text[:start] + replacement + text[end:]

logout_marker = "// MARK: GhostBase v1.0ZG BOTLOGOUT1"
if logout_marker not in text:
    start_anchor = "        case .logout:\n"
    end_anchor = "        case .rememberPassword:\n"
    start = text.find(start_anchor)
    end = text.find(end_anchor, start + len(start_anchor))
    if start == -1 or end == -1:
        raise SystemExit("[V10ZG account] logout case anchors not found")
    replacement = r'''        case .logout:
            // MARK: GhostBase v1.0ZG BOTLOGOUT1
            if case let .user(user) = self.data?.peer {
                if user.botInfo != nil {
                    self.controller?.present(
                        textAlertController(
                            context: self.context,
                            updatedPresentationData: self.controller?.updatedPresentationData,
                            title: "Выйти из аккаунта бота?",
                            text: "Аккаунт будет удалён только из GhostBase. Сам бот и его токен в BotFather не удаляются.",
                            actions: [
                                TextAlertAction(
                                    type: .genericAction,
                                    title: self.presentationData.strings.Common_Cancel,
                                    action: {}
                                ),
                                TextAlertAction(
                                    type: .defaultAction,
                                    title: "Выйти",
                                    action: { [weak self] in
                                        guard let self else {
                                            return
                                        }
                                        let _ = logoutFromAccount(
                                            id: self.context.account.id,
                                            accountManager: self.context.sharedContext.accountManager,
                                            alreadyLoggedOutRemotely: true
                                        ).startStandalone()
                                    }
                                )
                            ]
                        ),
                        in: .window(.root)
                    )
                } else if let phoneNumber = user.phone {
                    if let controller = self.controller,
                       let navigationController = controller.navigationController as? NavigationController {
                        self.controller?.push(
                            logoutOptionsController(
                                context: self.context,
                                navigationController: navigationController,
                                canAddAccounts: true,
                                phoneNumber: phoneNumber
                            )
                        )
                    }
                }
            }
'''
    text = text[:start] + replacement + text[end:]

path.write_text(text, encoding="utf-8")

# Proofs.
proofs = {
    PATHS["search"]: [
        "GhostBase v1.0ZG ACCOUNTUNLOCK1 settings search",
        "return true",
    ],
    PATHS["delete"]: [
        "GhostBase v1.0ZG ACCOUNTUNLOCK1 delete alternatives",
        "let canAddAccounts = true",
    ],
    PATHS["actions"]: [
        "GhostBase v1.0ZG ACCOUNTUNLOCK1 main action",
        "GhostBase v1.0ZG BOTLOGOUT1",
        "logoutFromAccount(",
        "user.botInfo != nil",
    ],
}
for file_path, values in proofs.items():
    source = file_path.read_text(encoding="utf-8")
    for value in values:
        if value not in source:
            raise SystemExit(f"[V10ZG account] proof missing in {file_path.name}: {value}")

print("[V10ZG] ACCOUNTUNLOCK1 applied: client account gates removed")
print("[V10ZG] BOTLOGOUT1 applied: bot account reaches standard local cleanup")
