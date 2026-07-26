#!/usr/bin/env python3
import os
from pathlib import Path

root = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src"))
authorization_path = root / "submodules/TelegramCore/Sources/Authorization.swift"
account_path = root / "submodules/TelegramCore/Sources/Account/Account.swift"

authorization = authorization_path.read_text(encoding="utf-8")
account = account_path.read_text(encoding="utf-8")

if "GhostBase v1.1C BOTSTATE4 startup replay" in account:
    print("[V11C] BOTSTATE4 already installed")
    raise SystemExit(0)

start_marker = "// MARK: GhostBase v1.1B BOTBACKFILL3 resumable guarded import\n"
end_marker = "public func ghostBaseAuthorizeBot(\n"
if start_marker not in authorization or end_marker not in authorization:
    raise SystemExit("[V11C BOTSTATE4] BOTBACKFILL3 block anchors missing")
start = authorization.index(start_marker)
end = authorization.index(end_marker, start)
authorization = authorization[:start] + authorization[end:]

trigger = '''                    // MARK: GhostBase v1.1B BOTBACKFILL3 trigger
                    ghostBaseStartBotBackfill(
                        account: authorizedAccount,
                        accountPeerId: user.id
                    )

'''
if trigger not in authorization:
    raise SystemExit("[V11C BOTSTATE4] fresh authorization trigger anchor missing")
authorization = authorization.replace(trigger, "", 1)

authorization_path.write_text(authorization, encoding="utf-8")

anchor = "        self.automaticCacheEvictionContext = AutomaticCacheEvictionContext(postbox: postbox, accountManager: accountManager)\n"
if anchor not in account:
    raise SystemExit("[V11C BOTSTATE4] Account.init anchor missing")

block = r'''

        // MARK: GhostBase v1.1C BOTSTATE4 startup replay
        // BOTSAFE keeps AccountStateManager alive. Poll from Telegram's current
        // AuthorizedAccountState so the official replay path handles messages,
        // otherUpdates, reactions, edits, deletes, channel pts and read state.
        if ghostBaseBotSafeMode && !supplementary {
            let botStatePeerId = peerId
            let runningKey = "GhostBase.BotState4.\(botStatePeerId.toInt64()).RunningAt"
            let now = Int64(Date().timeIntervalSince1970)
            let runningAt = Int64(UserDefaults.standard.double(forKey: runningKey))

            if runningAt == 0 || now - runningAt > 600 {
                UserDefaults.standard.set(Double(now), forKey: runningKey)
                ghostBaseBotSafeRecord(
                    peerId: botStatePeerId,
                    event: "BOTSTATE4 current-state Difference scheduled"
                )

                Queue.mainQueue().after(1.5) { [weak self] in
                    guard let strongSelf = self else {
                        UserDefaults.standard.removeObject(forKey: runningKey)
                        return
                    }

                    strongSelf.managedOperationsDisposable.add((strongSelf.stateManager.standalonePollDifference()
                    |> deliverOnMainQueue).start(next: { didReplay in
                        ghostBaseBotSafeRecord(
                            peerId: botStatePeerId,
                            event: "BOTSTATE4 official replay result=\(didReplay)"
                        )
                    }, completed: {
                        UserDefaults.standard.removeObject(forKey: runningKey)
                        ghostBaseBotSafeRecord(
                            peerId: botStatePeerId,
                            event: "BOTSTATE4 completed"
                        )
                    }))
                }
            } else {
                ghostBaseBotSafeRecord(
                    peerId: botStatePeerId,
                    event: "BOTSTATE4 duplicate startup suppressed"
                )
            }
        }
'''

account = account.replace(anchor, anchor + block, 1)
account_path.write_text(account, encoding="utf-8")
print("[V11C] BOTSTATE4 installed: zero/manual BOTBACKFILL3 removed; official current-state replay scheduled")
