#!/usr/bin/env python3

import os
from pathlib import Path

root = Path(os.environ.get(
    "GHOSTBASE_SOURCE_ROOT",
    "/root/gb_builder/work/swiftgram-src"
))

def read(relative: str) -> str:
    path = root / relative
    if not path.is_file():
        raise SystemExit(f"missing generated source: {path}")
    return path.read_text(encoding="utf-8")

def require(value: bool, message: str) -> None:
    if not value:
        raise SystemExit(f"[v1.0Y verifier] {message}")

api = read("submodules/TelegramApi/Sources/Api42.swift")
auth = read("submodules/TelegramCore/Sources/Authorization.swift")

phoneController = read(
    "submodules/AuthorizationUI/Sources/"
    "AuthorizationSequencePhoneEntryController.swift"
)
phoneNode = read(
    "submodules/AuthorizationUI/Sources/"
    "AuthorizationSequencePhoneEntryControllerNode.swift"
)
passwordController = read(
    "submodules/AuthorizationUI/Sources/"
    "AuthorizationSequencePasswordEntryController.swift"
)
passwordNode = read(
    "submodules/AuthorizationUI/Sources/"
    "AuthorizationSequencePasswordEntryControllerNode.swift"
)

panel = read(
    "submodules/TelegramUI/Components/Chat/"
    "ChatMessageSelectionInputPanelNode/Sources/"
    "ChatMessageSelectionInputPanelNode.swift"
)
loadNode = read(
    "submodules/TelegramUI/Sources/Chat/"
    "ChatControllerLoadDisplayNode.swift"
)
voice = read(
    "submodules/TelegramUI/Sources/Chat/"
    "ChatControllerMediaRecording.swift"
)
settings = read(
    "submodules/SettingsUI/Sources/GhostBase/"
    "GhostBaseSettingsController.swift"
)

apiStart = api.index("static func importBotAuthorization")
apiEnd = api.index("static func importLoginToken", apiStart)
botApi = api[apiStart:apiEnd]

require(
    'ConstructorParameterDescription("[REDACTED]")' in botApi,
    "bot token metadata is not redacted"
)
require(
    'ConstructorParameterDescription(botAuthToken)' not in botApi,
    "raw bot token remains in FunctionDescription"
)

for proof in (
    "GhostBase v1.0Y Bot Authorization Core",
    "auth.importBotAuthorization(",
    "AuthorizedAccountState(",
    "initializedAppSettingsAfterLogin(",
    "switchToAuthorizedAccount("
):
    require(proof in auth, f"missing Bot Authorization proof: {proof}")

combinedUi = (
    phoneController + phoneNode
    + passwordController + passwordNode
)

phoneNodeClassMarker = (
    "final class AuthorizationSequencePhoneEntryControllerNode: "
    "ASDisplayNode {"
)

require(
    phoneNodeClassMarker in phoneNode,
    "phone entry controller node class is missing"
)

phoneNodeClass = phoneNode[
    phoneNode.index(phoneNodeClassMarker):
]

require(
    "    var loginAsBot: (() -> Void)?" in phoneNodeClass,
    "loginAsBot callback is outside the controller node class"
)

for proof in (
    "GhostBase v1.0Y Bot Login UI",
    "ghostBaseBotLoginNode",
    "openGhostBaseBotLogin",
    "mode: .ghostBaseBotToken",
    "ghostBaseAuthorizeBot(",
    "func clearInput()"
):
    require(proof in combinedUi, f"missing Bot Login UI proof: {proof}")

for proof in (
    "GhostBase v1.0Y multi-select forward without author",
    "forwardWithoutAuthorButton",
    "hideNames: true"
):
    require(
        proof in panel + loadNode,
        f"missing multi-select proof: {proof}"
    )

require(
    "options: strongSelf.presentationInterfaceState."
    "interfaceState.forwardOptionsState" in loadNode,
    "multi-select options are not passed to forwardMessages"
)

for proof in (
    "GhostBase v1.0Y repeated scheduled voice reset",
    "GhostBase v1.0X scheduled voice immediate success cleanup",
    "self.recorderFeedback = nil",
    "self.chatDisplayNode.updateRecordedMediaDeleted(false)"
):
    require(proof in voice, f"missing voice proof: {proof}")

for proof in (
    "GhostBase v1.0Y Hidden Gifts no-spend probe",
    "5956217000635139069",
    "5922558454332916696",
    "5800655655995968830",
    "5866352046986232958",
    "5801108895304779062",
    "5893356958802511476",
    "5935895822435615975",
    "5969796561943660080",
    "6026193266406327981",
    "checkCanSendStarGift",
    "fetchBotPaymentForm",
    "hiddenGiftsSelf",
    "hiddenGiftsOther"
):
    require(proof in settings, f"missing Hidden Gifts proof: {proof}")

require(
    'case "hiddenGiftsOther":\n'
    '                let presentationData' not in settings,
    "unused presentationData remains in Hidden Gifts selector"
)

for forbidden in (
    "sendStarsPaymentForm",
    "sendPaymentForm",
    "sendStarsForm"
):
    require(
        forbidden not in settings,
        f"forbidden spending method found: {forbidden}"
    )

print("[v1.0Y verifier] Bot Login OK")
print("[v1.0Y verifier] token redaction OK")
print("[v1.0Y verifier] multi-select forward OK")
print("[v1.0Y verifier] repeated voice reset OK")
print("[v1.0Y verifier] Hidden Gifts no-spend probe OK")
