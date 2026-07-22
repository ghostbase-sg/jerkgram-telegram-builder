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
marker = "// MARK: GhostBase v1.0ZD PROFILEINTEL1 UI"


def require(value: bool, message: str) -> None:
    if not value:
        raise SystemExit(f"[v1.0ZD PROFILEINTEL1 UI] {message}")


require(
    "GhostBase v1.0ZB Bot Difference UI" in text,
    "v1.0ZB Debug / Research UI must be applied first"
)

if marker not in text:
    helper_anchor = "private func ghostBaseSettingsEntries("
    require(helper_anchor in text, "settings entries helper missing")

    helper = r'''// MARK: GhostBase v1.0ZD PROFILEINTEL1 UI

private let ghostBaseProfileIntelPrefix =
    "GhostBase.Research.ProfileIntel1."

private func ghostBaseProfileIntelReport() -> String {
    let defaults = UserDefaults.standard

    let target = defaults.string(
        forKey: ghostBaseProfileIntelPrefix + "Target"
    ) ?? "none"

    let status = defaults.string(
        forKey: ghostBaseProfileIntelPrefix + "Status"
    ) ?? "not tested"

    let updated = defaults.string(
        forKey: ghostBaseProfileIntelPrefix + "Updated"
    ) ?? "none"

    let current = defaults.string(
        forKey: ghostBaseProfileIntelPrefix + "Report"
    ) ?? "Результатов пока нет."

    let previousUpdated = defaults.string(
        forKey: ghostBaseProfileIntelPrefix + "PreviousUpdated"
    ) ?? "none"

    let previous = defaults.string(
        forKey: ghostBaseProfileIntelPrefix + "PreviousReport"
    ) ?? "Предыдущего результата нет."

    return """
    Target: \(target)
    Status: \(status)
    Updated: \(updated)

    CURRENT
    \(current)

    PREVIOUS
    Updated: \(previousUpdated)
    \(previous)
    """
}

'''
    text = text.replace(helper_anchor, helper + helper_anchor, 1)

    entries_anchor = '''        entries.append(.researchInfo(
            debug,
            943,
            ghostBaseBotDifferenceReport()
        ))
'''
    require(entries_anchor in text, "bot difference entries anchor missing")

    entries = entries_anchor + r'''

        entries.append(.header(
            debug,
            "PROFILEINTEL1"
        ))
        entries.append(.researchAction(
            debug,
            950,
            "Проверить username из буфера",
            "profileIntel1Probe"
        ))
        entries.append(.researchInfo(
            debug,
            951,
            ghostBaseProfileIntelReport()
        ))
'''
    text = text.replace(entries_anchor, entries, 1)

    disposable_anchor = (
        "    let ghostBaseBotDifferenceDisposable = MetaDisposable()\n"
    )
    require(disposable_anchor in text, "bot difference disposable missing")
    text = text.replace(
        disposable_anchor,
        disposable_anchor
        + "    let ghostBaseProfileIntelDisposable = MetaDisposable()\n",
        1
    )

    switch_start = text.index("        runResearchAction: { action in")
    default_anchor = '''            default:
                break
'''
    default_index = text.index(default_anchor, switch_start)

    action = r'''            case "profileIntel1Probe":
                let defaults = UserDefaults.standard
                let rawTarget = UIPasteboard.general.string ?? ""
                let target = rawTarget.trimmingCharacters(
                    in: .whitespacesAndNewlines
                )

                guard !target.isEmpty else {
                    defaults.set(
                        "failed: clipboard empty",
                        forKey: ghostBaseProfileIntelPrefix + "Status"
                    )
                    refreshResearchPage()
                    break
                }

                if let current = defaults.string(
                    forKey: ghostBaseProfileIntelPrefix + "Report"
                ), !current.isEmpty {
                    defaults.set(
                        current,
                        forKey:
                            ghostBaseProfileIntelPrefix
                            + "PreviousReport"
                    )
                    defaults.set(
                        defaults.string(
                            forKey:
                                ghostBaseProfileIntelPrefix + "Updated"
                        ) ?? "none",
                        forKey:
                            ghostBaseProfileIntelPrefix
                            + "PreviousUpdated"
                    )
                }

                defaults.set(
                    target,
                    forKey: ghostBaseProfileIntelPrefix + "Target"
                )
                defaults.set(
                    "running",
                    forKey: ghostBaseProfileIntelPrefix + "Status"
                )
                defaults.set(
                    "",
                    forKey: ghostBaseProfileIntelPrefix + "Report"
                )
                refreshResearchPage()

                ghostBaseProfileIntelDisposable.set((
                    context.engine.peers
                    .ghostBaseProfileIntelProbe(username: target)
                    |> take(1)
                    |> deliverOnMainQueue
                ).start(next: { report in
                    defaults.set(
                        "completed",
                        forKey:
                            ghostBaseProfileIntelPrefix + "Status"
                    )
                    defaults.set(
                        report,
                        forKey:
                            ghostBaseProfileIntelPrefix + "Report"
                    )
                    defaults.set(
                        ISO8601DateFormatter().string(from: Date()),
                        forKey:
                            ghostBaseProfileIntelPrefix + "Updated"
                    )
                    refreshResearchPage()
                }))

'''
    text = text[:default_index] + action + text[default_index:]

for proof in (
    marker,
    "PROFILEINTEL1",
    "Проверить username из буфера",
    'case "profileIntel1Probe":',
    "UIPasteboard.general.string",
    ".ghostBaseProfileIntelProbe(username: target)",
    "CURRENT",
    "PREVIOUS",
):
    require(proof in text, f"missing proof: {proof}")

path.write_text(text, encoding="utf-8")
print("[v1.0ZD] PROFILEINTEL1 Debug / Research action added")
