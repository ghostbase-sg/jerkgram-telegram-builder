#!/usr/bin/env python3

from pathlib import Path
import os

ROOT = Path(__file__).resolve().parents[1]
SRC = Path(os.environ.get(
    "GHOSTBASE_SOURCE_ROOT",
    str(ROOT / "work/swiftgram-src")
))

AUTH = SRC / "submodules/TelegramCore/Sources/Authorization.swift"
NETWORK = SRC / "submodules/TelegramCore/Sources/Network/Network.swift"
UI = SRC / "submodules/AuthorizationUI/Sources/AuthorizationSequenceController.swift"

for path in (AUTH, NETWORK, UI):
    if not path.exists():
        raise SystemExit(f"missing: {path}")

def replace_once(text, old, new, name):
    if old not in text:
        raise SystemExit(f"anchor not found: {name}")
    return text.replace(old, new, 1)

auth = AUTH.read_text()

if "authorizationBeforeNetworkRequest" not in auth:
    old = (
        "        let codeAndAccount = "
        "account.network.request(sendCode, automaticFloodWait: false)\n"
    )

    new = (
        '        UserDefaults.standard.set(true, forKey: "GhostBase.LOGINPROBE.Active")\n'
        '        UserDefaults.standard.set("authorizationBeforeNetworkRequest", forKey: "GhostBase.LOGINPROBE.Stage")\n'
        "\n"
        "        let codeAndAccount = "
        "account.network.request(sendCode, automaticFloodWait: false)\n"
    )

    auth = replace_once(auth, old, new, "auth.sendCode")

timeout20 = (
    "|> timeout(20.0, queue: Queue.concurrentDefaultQueue(), "
    "alternate: .fail(.timeout))"
)

timeout60 = (
    "|> timeout(60.0, queue: Queue.concurrentDefaultQueue(), "
    "alternate: .fail(.timeout))"
)

if timeout20 in auth:
    auth = auth.replace(timeout20, timeout60, 1)

AUTH.write_text(auth)

network = NETWORK.read_text()

start = network.find("    public func request<T>(_ data:")
end = network.find(
    "\n    func updateNetworkSpeedLimitedEventNotifyInterval",
    start
)

if start < 0 or end < 0:
    raise SystemExit("Network.request boundaries not found")

block = network[start:end]

if "networkSignalSubscribed" not in block:
    old = (
        "        return Signal { subscriber in\n"
        "            let request = MTRequest()\n"
    )

    new = (
        "        return Signal { subscriber in\n"
        '            let gbProbe = UserDefaults.standard.bool(forKey: "GhostBase.LOGINPROBE.Active")\n'
        "            if gbProbe {\n"
        '                UserDefaults.standard.set("networkSignalSubscribed", forKey: "GhostBase.LOGINPROBE.Stage")\n'
        "            }\n"
        "\n"
        "            let request = MTRequest()\n"
        "\n"
        "            if gbProbe {\n"
        '                UserDefaults.standard.set("mtRequestCreated", forKey: "GhostBase.LOGINPROBE.Stage")\n'
        "            }\n"
    )

    block = replace_once(block, old, new, "Network Signal")

    old = (
        "            request.completed = { "
        "(boxedResponse, timestamp, error) -> () in\n"
        "                if let error = error {\n"
    )

    new = (
        "            request.completed = { "
        "(boxedResponse, timestamp, error) -> () in\n"
        "                if gbProbe {\n"
        "                    if let error = error {\n"
        '                        UserDefaults.standard.set("rpcError:\\(error.errorCode)", forKey: "GhostBase.LOGINPROBE.Stage")\n'
        "                    } else {\n"
        '                        UserDefaults.standard.set("rpcResponseReceived", forKey: "GhostBase.LOGINPROBE.Stage")\n'
        "                    }\n"
        '                    UserDefaults.standard.set(false, forKey: "GhostBase.LOGINPROBE.Active")\n'
        "                }\n"
        "\n"
        "                if let error = error {\n"
    )

    block = replace_once(block, old, new, "request.completed")

    old = "            requestService.add(request)\n"

    new = (
        "            if gbProbe {\n"
        '                UserDefaults.standard.set("beforeRequestServiceAdd", forKey: "GhostBase.LOGINPROBE.Stage")\n'
        "            }\n"
        "\n"
        "            requestService.add(request)\n"
        "\n"
        "            if gbProbe {\n"
        '                UserDefaults.standard.set("requestServiceAddReturned", forKey: "GhostBase.LOGINPROBE.Stage")\n'
        "            }\n"
    )

    block = replace_once(block, old, new, "requestService.add")

    old = (
        "            return ActionDisposable { [weak requestService] in\n"
        "                requestService?.removeRequest(byInternalId: internalId)\n"
        "            }\n"
    )

    new = (
        "            return ActionDisposable { [weak requestService] in\n"
        '                if gbProbe && UserDefaults.standard.bool(forKey: "GhostBase.LOGINPROBE.Active") {\n'
        '                    let previous = UserDefaults.standard.string(forKey: "GhostBase.LOGINPROBE.Stage") ?? "none"\n'
        '                    UserDefaults.standard.set("disposedWithoutRpcResponse;prev=\\(previous)", forKey: "GhostBase.LOGINPROBE.Stage")\n'
        '                    UserDefaults.standard.set(false, forKey: "GhostBase.LOGINPROBE.Active")\n'
        "                }\n"
        "\n"
        "                requestService?.removeRequest(byInternalId: internalId)\n"
        "            }\n"
    )

    block = replace_once(block, old, new, "ActionDisposable")

network = network[:start] + block + network[end:]
NETWORK.write_text(network)

ui = UI.read_text()

if "Stage: \\(ghostBaseLoginStage)" not in ui:
    case_pos = ui.find("case .timeout:")

    if case_pos < 0:
        raise SystemExit("timeout case not found")

    target = "text = strongSelf.presentationData.strings.Login_NetworkError"
    target_pos = ui.find(target, case_pos, case_pos + 1500)

    if target_pos < 0:
        raise SystemExit("timeout text not found")

    line_start = ui.rfind("\n", case_pos, target_pos) + 1
    line_end = ui.find("\n", target_pos)

    indent = ui[line_start:target_pos]

    replacement = (
        indent
        + 'let ghostBaseLoginStage = UserDefaults.standard.string(forKey: "GhostBase.LOGINPROBE.Stage") ?? "none"\n'
        + indent
        + 'text = strongSelf.presentationData.strings.Login_NetworkError + "\\n\\nGhostBase.LOGINPROBE:\\nStage: \\(ghostBaseLoginStage)\\nauth.sendCode local timeout after 60s."'
    )

    ui = ui[:line_start] + replacement + ui[line_end:]

UI.write_text(ui)

print("[LOGINPROBE v2] OK")
