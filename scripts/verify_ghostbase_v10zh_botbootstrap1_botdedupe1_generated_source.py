#!/usr/bin/env python3

import os
from pathlib import Path

ROOT = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src"))
AUTH = ROOT / "submodules/TelegramCore/Sources/Authorization.swift"
CONTROLLER = ROOT / "submodules/AuthorizationUI/Sources/AuthorizationSequencePhoneEntryController.swift"
ACTIONS = ROOT / "submodules/TelegramUI/Components/PeerInfo/PeerInfoScreen/Sources/PeerInfoScreenSettingsActions.swift"

for path in (AUTH, CONTROLLER, ACTIONS):
    if not path.is_file():
        raise SystemExit(f"[V10ZH verifier] missing: {path}")

auth = AUTH.read_text(encoding="utf-8")
controller = CONTROLLER.read_text(encoding="utf-8")
actions = ACTIONS.read_text(encoding="utf-8")


def require(value: bool, message: str) -> None:
    if not value:
        raise SystemExit(f"[V10ZH verifier] {message}")


bootstrap_marker = "// MARK: GhostBase v1.0ZH BOTBOOTSTRAP1 zero-state backlog"
require(bootstrap_marker in auth, "BOTBOOTSTRAP1 marker missing")
bootstrap_start = auth.index(bootstrap_marker)
bootstrap_end = auth.index("public func ghostBaseAuthorizeBot(", bootstrap_start)
bootstrap = auth[bootstrap_start:bootstrap_end]
for proof in ("pts: 0", "qts: 0", "date: 0", "seq: 0", "return .single(state)"):
    require(proof in bootstrap, f"zero-state proof missing: {proof}")
require("Api.functions.updates.getState(" not in bootstrap, "current-state bootstrap still active")
require("candidatePts" not in bootstrap, "synthetic pts rewind returned")
require("data.pts - data.unreadCount" not in bootstrap, "unreadCount rewind returned")

for proof in (
    "// MARK: GhostBase v1.0ZH BOTDEDUPE1 token peer id",
    "case alreadyAdded",
    "botAuthToken.firstIndex(of: \":\")",
    "PeerId.Id._internalFromInt64Value(rawId)",
    'forKey: "GhostBase.BotAccount.\\(peerId.toInt64())"',
    "// MARK: GhostBase v1.0ZH BOTDEDUPE1 authorization gate",
    "return .fail(.alreadyAdded)",
):
    require(proof in auth, f"BOTDEDUPE1 core proof missing: {proof}")

# The secret must not be persisted in UserDefaults or logs.
require("UserDefaults.standard.set(botAuthToken" not in auth, "raw token persisted")
require("UserDefaults.standard.setValue(botAuthToken" not in auth, "raw token persisted")
require("Logger.shared.log(\"GhostBase.BotDedupe1\", botAuthToken" not in auth, "raw token logged")

require("GhostBase v1.0ZH BOTDEDUPE1 duplicate UI" in controller, "duplicate UI marker missing")
require("case .alreadyAdded:" in controller, "duplicate UI case missing")
require("Этот бот уже добавлен в GhostBase." in controller, "duplicate UI text missing")

require("GhostBase v1.0ZH BOTDEDUPE1 clear marker on logout" in actions, "logout marker cleanup missing")
require('forKey: "GhostBase.BotAccount.\\(user.id.toInt64())"' in actions, "bot marker key cleanup missing")
require("UserDefaults.standard.removeObject(" in actions, "bot marker is not removed")
require("alreadyLoggedOutRemotely: true" in actions, "local-only bot logout was lost")

for forbidden in (
    "Api.functions.messages.getDialogs(",
    "Api.functions.messages.getPinnedDialogs(",
):
    require(forbidden not in auth, f"forbidden bot RPC introduced: {forbidden}")

print("[V10ZH verifier] BOTBOOTSTRAP1 + BOTDEDUPE1 OK")
