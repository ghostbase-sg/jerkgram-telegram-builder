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

marker = "// MARK: GhostBase v1.0ZB Bot Difference UI"

def require(value: bool, message: str) -> None:
    if not value:
        raise SystemExit(f"[v1.0ZB bot difference UI] {message}")

require(
    "GhostBase v1.0ZA Bot Capability UI" in text,
    "v1.0ZA bot UI must be applied first"
)

if marker not in text:
    helper_anchor = "private func ghostBaseSettingsEntries("

    require(helper_anchor in text, "entries helper anchor missing")

    helper = r'''// MARK: GhostBase v1.0ZB Bot Difference UI

private let ghostBaseBotDifferencePrefix =
    "GhostBase.Research.BotDifference."

private func ghostBaseBotDifferenceReport() -> String {
    let defaults = UserDefaults.standard

    let status = defaults.string(
        forKey: ghostBaseBotDifferencePrefix + "Status"
    ) ?? "not tested"

    let updated = defaults.string(
        forKey: ghostBaseBotDifferencePrefix + "Updated"
    ) ?? "none"

    let report = defaults.string(
        forKey: ghostBaseBotDifferencePrefix + "Report"
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

    entries_anchor = '''        entries.append(.researchInfo(
            debug,
            941,
            ghostBaseBotCapabilityReport()
        ))
'''

    entries = entries_anchor + r'''

        entries.append(.researchAction(
            debug,
            942,
            "Проверить updates.getDifference",
            "botDifferenceProbe"
        ))
        entries.append(.researchInfo(
            debug,
            943,
            ghostBaseBotDifferenceReport()
        ))
'''

    require(entries_anchor in text, "bot capability entries anchor missing")
    text = text.replace(entries_anchor, entries, 1)

    disposable_anchor = (
        "    let ghostBaseBotCapabilityDisposable = MetaDisposable()\n"
    )

    require(disposable_anchor in text, "bot disposable anchor missing")

    text = text.replace(
        disposable_anchor,
        disposable_anchor
        + "    let ghostBaseBotDifferenceDisposable = MetaDisposable()\n",
        1
    )

    switch_anchor = '''            case "botCapabilityProbe":
'''

    require(switch_anchor in text, "bot capability action missing")

    default_anchor = '''            default:
                break
'''

    switch_start = text.index(
        "        runResearchAction: { action in"
    )
    default_index = text.index(default_anchor, switch_start)

    action = r'''            case "botDifferenceProbe":
                let defaults = UserDefaults.standard

                defaults.set(
                    "running",
                    forKey: ghostBaseBotDifferencePrefix + "Status"
                )
                defaults.set(
                    "",
                    forKey: ghostBaseBotDifferencePrefix + "Report"
                )
                refreshResearchPage()

                ghostBaseBotDifferenceDisposable.set((
                    context.engine.peers
                    .ghostBaseBotDifferenceProbe()
                    |> take(1)
                    |> deliverOnMainQueue
                ).start(next: { report in
                    defaults.set(
                        "completed",
                        forKey:
                            ghostBaseBotDifferencePrefix + "Status"
                    )
                    defaults.set(
                        report,
                        forKey:
                            ghostBaseBotDifferencePrefix + "Report"
                    )
                    defaults.set(
                        ISO8601DateFormatter()
                            .string(from: Date()),
                        forKey:
                            ghostBaseBotDifferencePrefix + "Updated"
                    )
                    refreshResearchPage()
                }))

'''

    text = (
        text[:default_index]
        + action
        + text[default_index:]
    )

for proof in (
    marker,
    "Проверить updates.getDifference",
    'case "botDifferenceProbe":',
    ".ghostBaseBotDifferenceProbe()",
    "ghostBaseBotDifferenceReport()",
):
    require(proof in text, f"missing proof: {proof}")

path.write_text(text, encoding="utf-8")

print("[v1.0ZB] Bot Difference UI added")
