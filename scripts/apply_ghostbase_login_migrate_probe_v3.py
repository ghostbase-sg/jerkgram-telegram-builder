#!/usr/bin/env python3

from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[1]
SRC = Path(os.environ.get(
    "GHOSTBASE_SOURCE_ROOT",
    str(ROOT / "work/swiftgram-src")
))

P = SRC / "submodules/TelegramCore/Sources/Authorization.swift"
s = P.read_text()

def replace_once(old: str, new: str, name: str):
    global s
    if old not in s:
        raise SystemExit(f"anchor not found: {name}")
    s = s.replace(old, new, 1)

old = '''        |> `catch` { error -> Signal<(SendCodeResult, UnauthorizedAccount), MTRpcError> in
            switch MatchString(error.errorDescription ?? "") {
'''

new = '''        |> `catch` { error -> Signal<(SendCodeResult, UnauthorizedAccount), MTRpcError> in
            UserDefaults.standard.set(
                "firstRpcError:\\(error.errorCode):\\(error.errorDescription ?? "none")",
                forKey: "GhostBase.LOGINPROBE.Stage"
            )

            switch MatchString(error.errorDescription ?? "") {
'''

if "firstRpcError:" not in s:
    replace_once(old, new, "first RPC catch")

old = '''                    let updatedMasterDatacenterId = Int32(error.errorDescription[range.upperBound ..< error.errorDescription.endIndex])!
                    let updatedAccount = account.changedMasterDatacenterId(accountManager: accountManager, masterDatacenterId: updatedMasterDatacenterId)
'''

new = '''                    let updatedMasterDatacenterId = Int32(error.errorDescription[range.upperBound ..< error.errorDescription.endIndex])!

                    UserDefaults.standard.set(
                        "migrateParsed:dc=\\(updatedMasterDatacenterId)",
                        forKey: "GhostBase.LOGINPROBE.Stage"
                    )

                    let updatedAccount = account.changedMasterDatacenterId(
                        accountManager: accountManager,
                        masterDatacenterId: updatedMasterDatacenterId
                    )
'''

if "migrateParsed:dc=" not in s:
    replace_once(old, new, "migration DC")

old = '''                    return updatedAccount
                    |> mapToSignalPromotingError { updatedAccount -> Signal<(SendCodeResult, UnauthorizedAccount), MTRpcError> in
                        return updatedAccount.network.request(sendCode, automaticFloodWait: false)
'''

new = '''                    return updatedAccount
                    |> mapToSignalPromotingError { updatedAccount -> Signal<(SendCodeResult, UnauthorizedAccount), MTRpcError> in
                        UserDefaults.standard.set(
                            "changedAccountEmitted:dc=\\(updatedMasterDatacenterId);retryStarting",
                            forKey: "GhostBase.LOGINPROBE.Stage"
                        )

                        return updatedAccount.network.request(sendCode, automaticFloodWait: false)
'''

if "changedAccountEmitted:dc=" not in s:
    replace_once(old, new, "changed account emission")

old = '''                        |> map { sentCode in
                            return (.sentCode(sentCode), updatedAccount)
                        }
                        |> `catch` { error -> Signal<(SendCodeResult, UnauthorizedAccount), MTRpcError> in
'''

new = '''                        |> map { sentCode in
                            UserDefaults.standard.set(
                                "retryRpcResponse:dc=\\(updatedMasterDatacenterId)",
                                forKey: "GhostBase.LOGINPROBE.Stage"
                            )
                            return (.sentCode(sentCode), updatedAccount)
                        }
                        |> `catch` { error -> Signal<(SendCodeResult, UnauthorizedAccount), MTRpcError> in
                            UserDefaults.standard.set(
                                "retryRpcError:\\(error.errorCode):\\(error.errorDescription ?? "none")",
                                forKey: "GhostBase.LOGINPROBE.Stage"
                            )
'''

if "retryRpcResponse:dc=" not in s:
    replace_once(old, new, "retry response")

P.write_text(s)
print("[LOGINPROBE v3] OK: migration path instrumented")
