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
    raise SystemExit(f"[PROFILEINTEL2 UI] missing settings source: {path}")

text = path.read_text(encoding="utf-8")
marker = "// MARK: GhostBase v1.0ZF PROFILEINTEL2 UI"


def require(value: bool, message: str) -> None:
    if not value:
        raise SystemExit(f"[PROFILEINTEL2 UI] {message}")


require(
    "// MARK: GhostBase v1.0ZD PROFILEINTEL1 UI" in text,
    "PROFILEINTEL1 UI must be applied first"
)

if marker not in text:
    helper_anchor = "private func ghostBaseSettingsEntries("
    require(helper_anchor in text, "settings entries helper missing")

    helper = r'''// MARK: GhostBase v1.0ZF PROFILEINTEL2 UI

private let ghostBaseProfileIntel2Prefix =
    "GhostBase.Research.ProfileIntel2."

private func ghostBaseProfileIntel2Report() -> String {
    let defaults = UserDefaults.standard
    let target = defaults.string(
        forKey: ghostBaseProfileIntel2Prefix + "Target"
    ) ?? "none"
    let status = defaults.string(
        forKey: ghostBaseProfileIntel2Prefix + "Status"
    ) ?? "not tested"
    let updated = defaults.string(
        forKey: ghostBaseProfileIntel2Prefix + "Updated"
    ) ?? "none"
    let report = defaults.string(
        forKey: ghostBaseProfileIntel2Prefix + "Report"
    ) ?? "Снимков пока нет."

    return """
    Target: \(target)
    Status: \(status)
    Updated: \(updated)

    \(report)
    """
}

'''
    text = text.replace(helper_anchor, helper + helper_anchor, 1)

    entries_anchor = '''        entries.append(.researchInfo(
            debug,
            951,
            ghostBaseProfileIntelReport()
        ))
'''
    require(entries_anchor in text, "PROFILEINTEL1 entries anchor missing")

    entries = entries_anchor + r'''

        entries.append(.header(
            debug,
            "PROFILEINTEL2"
        ))
        entries.append(.researchAction(
            debug,
            952,
            "Снимок профиля + история фото",
            "profileIntel2Snapshot"
        ))
        entries.append(.researchInfo(
            debug,
            953,
            ghostBaseProfileIntel2Report()
        ))
'''
    text = text.replace(entries_anchor, entries, 1)

    disposable_anchor = (
        "    let ghostBaseProfileIntelDisposable = MetaDisposable()\n"
    )
    require(disposable_anchor in text, "PROFILEINTEL1 disposable missing")
    text = text.replace(
        disposable_anchor,
        disposable_anchor
        + "    let ghostBaseProfileIntel2Disposable = MetaDisposable()\n",
        1
    )

    switch_start = text.index("        runResearchAction: { action in")
    default_anchor = '''            default:
                break
'''
    default_index = text.index(default_anchor, switch_start)

    action = r'''            case "profileIntel2Snapshot":
                let defaults = UserDefaults.standard
                let rawTarget = UIPasteboard.general.string ?? ""
                let target = rawTarget.trimmingCharacters(
                    in: .whitespacesAndNewlines
                )

                guard !target.isEmpty else {
                    defaults.set(
                        "failed: clipboard empty",
                        forKey: ghostBaseProfileIntel2Prefix + "Status"
                    )
                    refreshResearchPage()
                    break
                }

                defaults.set(
                    target,
                    forKey: ghostBaseProfileIntel2Prefix + "Target"
                )
                defaults.set(
                    "running",
                    forKey: ghostBaseProfileIntel2Prefix + "Status"
                )
                refreshResearchPage()

                ghostBaseProfileIntel2Disposable.set((
                    context.engine.peers
                    .ghostBaseProfileIntel2Snapshot(username: target)
                    |> take(1)
                    |> deliverOnMainQueue
                ).start(next: { report in
                    defaults.set(
                        "completed",
                        forKey: ghostBaseProfileIntel2Prefix + "Status"
                    )
                    defaults.set(
                        report,
                        forKey: ghostBaseProfileIntel2Prefix + "Report"
                    )
                    defaults.set(
                        ISO8601DateFormatter().string(from: Date()),
                        forKey: ghostBaseProfileIntel2Prefix + "Updated"
                    )
                    refreshResearchPage()
                }))

'''
    text = text[:default_index] + action + text[default_index:]

for proof in (
    marker,
    "PROFILEINTEL2",
    "Снимок профиля + история фото",
    'case "profileIntel2Snapshot":',
    ".ghostBaseProfileIntel2Snapshot(username: target)",
    "ghostBaseProfileIntel2Report()",
):
    require(proof in text, f"proof missing: {proof}")

path.write_text(text, encoding="utf-8")
print("[PROFILEINTEL2 UI] snapshot/photo-history action added")
