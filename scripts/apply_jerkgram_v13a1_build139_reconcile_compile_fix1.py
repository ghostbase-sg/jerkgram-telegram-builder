#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
APP_DELEGATE = ROOT / "submodules/TelegramUI/Sources/AppDelegate.swift"

GUARD = "        guard url.absoluteString.utf8.count <= 3072,\n"
DUPLICATE_GUARD = GUARD + GUARD
AUTHORIZE = "private func handleJerkgramNotificationsAuthorizeUrl(_ url: URL) -> Bool"
RECONCILE = "private func handleJerkgramNotificationsReconcileUrl(_ url: URL) -> Bool"

OLD_ACCOUNT_LABEL_BLOCK = r'''                let _ = (context.account.postbox.transaction { transaction -> TelegramUser? in
                    return transaction.getPeer(context.account.peerId) as? TelegramUser
                }
                |> take(1)
                |> deliverOnMainQueue).start(next: { [weak self] user in
                    guard let self else { return }
                    let accountLabel: String
                    if let username = user?.username, !username.isEmpty {
                        accountLabel = "@\(username)"
                    } else if let user {
                        let displayName = [user.firstName, user.lastName]
                            .compactMap { value -> String? in
                                guard let value, !value.isEmpty else { return nil }
                                return value
                            }
                            .joined(separator: " ")
                        accountLabel = displayName.isEmpty ? "Telegram account" : displayName
                    } else {
                        accountLabel = "Telegram account"
                    }
'''

NEW_ACCOUNT_LABEL_BLOCK = r'''                let _ = (context.account.postbox.transaction { transaction -> String in
                    guard let user = transaction.getPeer(context.account.peerId) as? TelegramUser else {
                        return "Telegram account"
                    }
                    if let username = user.username, !username.isEmpty {
                        return "@\(username)"
                    }
                    let displayName = [user.firstName, user.lastName]
                        .compactMap { value -> String? in
                            guard let value, !value.isEmpty else { return nil }
                            return value
                        }
                        .joined(separator: " ")
                    return displayName.isEmpty ? "Telegram account" : displayName
                }
                |> take(1)
                |> deliverOnMainQueue).start(next: { [weak self] accountLabel in
                    guard let self else { return }
'''

OLD_PRESENT_PREFIX = "self.mainWindow?.viewController?.present("
NEW_PRESENT_PREFIX = "self.mainWindow?.viewController?.view.window?.rootViewController?.present("


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[Build139 reconcile compile fix] " + message)


def normalize_text(text: str) -> str:
    require(AUTHORIZE in text, "authorize helper missing")
    require(RECONCILE in text, "reconcile helper missing")

    while DUPLICATE_GUARD in text:
        text = text.replace(DUPLICATE_GUARD, GUARD, 1)

    require(text.count(GUARD) == 2, f"expected exactly two URL size guards, found {text.count(GUARD)}")
    require(DUPLICATE_GUARD not in text, "duplicate guard survived normalization")

    old_account_count = text.count(OLD_ACCOUNT_LABEL_BLOCK)
    new_account_count = text.count(NEW_ACCOUNT_LABEL_BLOCK)
    require(
        old_account_count + new_account_count == 1,
        f"expected exactly one account-label implementation, found old={old_account_count} new={new_account_count}",
    )
    if old_account_count == 1:
        text = text.replace(OLD_ACCOUNT_LABEL_BLOCK, NEW_ACCOUNT_LABEL_BLOCK, 1)

    old_present_count = text.count(OLD_PRESENT_PREFIX)
    new_present_count = text.count(NEW_PRESENT_PREFIX)
    require(
        old_present_count + new_present_count == 5,
        f"expected exactly five notification alert presentations, found old={old_present_count} new={new_present_count}",
    )
    text = text.replace(OLD_PRESENT_PREFIX, NEW_PRESENT_PREFIX)

    require(OLD_ACCOUNT_LABEL_BLOCK not in text, "optional TelegramUser account-label implementation survived normalization")
    require(NEW_ACCOUNT_LABEL_BLOCK in text, "String account-label implementation missing after normalization")
    require(OLD_PRESENT_PREFIX not in text, "ContainableController UIKit presentation survived normalization")
    require(text.count(NEW_PRESENT_PREFIX) == 5, "root UIViewController presentation count mismatch after normalization")
    return text


def main() -> None:
    require(APP_DELEGATE.is_file(), "AppDelegate missing: " + str(APP_DELEGATE))
    text = APP_DELEGATE.read_text(encoding="utf-8")
    normalized = normalize_text(text)
    APP_DELEGATE.write_text(normalized, encoding="utf-8")
    print("[Build139 reconcile compile fix] GREEN")
    print("[Build139 reconcile compile fix] guards normalized; account label is non-optional; UIKit alerts use root UIViewController")


if __name__ == "__main__":
    main()
