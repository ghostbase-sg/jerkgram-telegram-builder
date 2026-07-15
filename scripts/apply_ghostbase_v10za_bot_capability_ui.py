#!/usr/bin/env python3

import os
from pathlib import Path

root = Path(os.environ.get(
    "GHOSTBASE_SOURCE_ROOT",
    "/root/gb_builder/work/swiftgram-src"
))

path = root / (
    "submodules/SettingsUI/Sources/GhostBase/"
    "GhostBaseSettingsController.swift"
)

if not path.is_file():
    raise SystemExit(f"missing settings source: {path}")

text = path.read_text(encoding="utf-8")

marker = "// MARK: GhostBase v1.0ZA Bot Capability UI"

def require(value: bool, message: str) -> None:
    if not value:
        raise SystemExit(f"[v1.0ZA bot UI] {message}")

require(
    "GhostBase v1.0ZA Hidden Gifts real send" in text,
    "Hidden Gifts Send overlay must be applied first"
)

if marker not in text:
    helper_anchor = "private func ghostBaseSettingsEntries("

    require(helper_anchor in text, "settings entries anchor missing")

    helper = r'''// MARK: GhostBase v1.0ZA Bot Capability UI

private let ghostBaseBotCapabilityPrefix =
    "GhostBase.Research.BotCapability."

private func ghostBaseBotCapabilityReport() -> String {
    let defaults = UserDefaults.standard

    let status = defaults.string(
        forKey: ghostBaseBotCapabilityPrefix + "Status"
    ) ?? "not tested"

    let updated = defaults.string(
        forKey: ghostBaseBotCapabilityPrefix + "Updated"
    ) ?? "none"

    let report = defaults.string(
        forKey: ghostBaseBotCapabilityPrefix + "Report"
    ) ?? "Результатов пока нет."

    return """
    Status: \(status)
    Updated: \(updated)

    \(report)
    """
}

'''

    text = text.replace(
        helper_anchor,
        helper + helper_anchor,
        1
    )

    entries_anchor = """    if page == .root {
"""

    require(entries_anchor in text, "root entries anchor missing")

    entries = r'''    if page == .debugResearch {
        entries.append(.header(
            debug,
            "Bot Account Capability Probe"
        ))
        entries.append(.researchAction(
            debug,
            940,
            "Проверить RPC bot-аккаунта",
            "botCapabilityProbe"
        ))
        entries.append(.researchInfo(
            debug,
            941,
            ghostBaseBotCapabilityReport()
        ))
    }

'''

    text = text.replace(
        entries_anchor,
        entries + entries_anchor,
        1
    )

    disposable_anchor = (
        "    let ghostBaseHiddenGiftsDisposable = MetaDisposable()\n"
    )

    require(
        disposable_anchor in text,
        "controller disposable anchor missing"
    )

    text = text.replace(
        disposable_anchor,
        disposable_anchor
        + "    let ghostBaseBotCapabilityDisposable = MetaDisposable()\n",
        1
    )

    switch_anchor = """        runResearchAction: { action in
            switch action {
"""

    require(switch_anchor in text, "research action switch missing")

    switch_start = text.index(switch_anchor)
    default_anchor = """            default:
                break
"""
    default_index = text.index(default_anchor, switch_start)

    action_case = r'''            case "botCapabilityProbe":
                let defaults = UserDefaults.standard

                defaults.set(
                    "running",
                    forKey:
                        ghostBaseBotCapabilityPrefix + "Status"
                )
                defaults.set(
                    "",
                    forKey:
                        ghostBaseBotCapabilityPrefix + "Report"
                )
                refreshResearchPage()

                ghostBaseBotCapabilityDisposable.set((
                    context.engine.peers
                    .ghostBaseBotCapabilityProbe()
                    |> take(1)
                    |> deliverOnMainQueue
                ).start(next: { report in
                    defaults.set(
                        "completed",
                        forKey:
                            ghostBaseBotCapabilityPrefix + "Status"
                    )
                    defaults.set(
                        report,
                        forKey:
                            ghostBaseBotCapabilityPrefix + "Report"
                    )
                    defaults.set(
                        ISO8601DateFormatter()
                            .string(from: Date()),
                        forKey:
                            ghostBaseBotCapabilityPrefix + "Updated"
                    )
                    refreshResearchPage()
                }))

'''

    text = (
        text[:default_index]
        + action_case
        + text[default_index:]
    )

for proof in (
    marker,
    "Bot Account Capability Probe",
    "botCapabilityProbe",
    "ghostBaseBotCapabilityProbe()",
    "ghostBaseBotCapabilityDisposable",
    "ghostBaseBotCapabilityReport()",
):
    require(proof in text, f"missing proof: {proof}")

path.write_text(text, encoding="utf-8")

print("[v1.0ZA] Bot Capability UI added")
print("[v1.0ZA] direct RPC report added to Debug / Research")
