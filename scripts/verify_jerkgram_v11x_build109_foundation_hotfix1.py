#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(__file__).resolve().parents[1]

SRC = Path(
    os.environ.get(
        "JERKGRAM_SOURCE_ROOT",
        os.environ.get(
            "GHOSTBASE_SOURCE_ROOT",
            str(ROOT / "work/swiftgram-src"),
        ),
    )
)

APP_DELEGATE = (
    SRC / "submodules/TelegramUI/Sources/AppDelegate.swift"
)

BEGIN = "// JERKGRAM_LEGACY_NAMESPACE_BEGIN"
END = "// JERKGRAM_LEGACY_NAMESPACE_END"


def require(condition, message):
    if not condition:
        raise RuntimeError(
            "[verify Build109] " + message
        )


text = APP_DELEGATE.read_text(
    encoding="utf-8"
)

require(
    BEGIN in text and END in text,
    "migration region missing",
)

_, rest = text.split(BEGIN, 1)
region, _ = rest.split(END, 1)

for required in (
    "BUILD109_FOUNDATION_HOTFIX1",
    '"jerkgram.runtime.namespaceMigration.v1"',
    "persistentDomain(",
    "setPersistentDomain(",
    'lower.hasPrefix("ghostbase.")',
    'lower.hasPrefix("gb.")',
    'suiteName: "group.4a348a9b186b700c.1"',
):
    require(
        required in region,
        f"missing: {required}",
    )

for forbidden in (
    "dictionaryRepresentation()",
    "defaults.set(",
):
    require(
        forbidden not in region,
        f"old migration remains: {forbidden}",
    )

require(
    text.count(
        "JerkGramLegacyDefaultsMigration.run()"
    ) == 1,
    "unexpected startup-call count",
)

print(
    "[verify Build109] GREEN: "
    "safe one-shot namespace migration"
)
