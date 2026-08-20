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

MARKER = (
    "// MARK: JerkGram v1.1X "
    "BUILD109_FOUNDATION_HOTFIX1"
)

APP_GROUP = "group.4a348a9b186b700c.1"


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def main():
    require(
        APP_DELEGATE.is_file(),
        f"missing AppDelegate: {APP_DELEGATE}",
    )

    text = APP_DELEGATE.read_text(
        encoding="utf-8"
    )

    require(
        BEGIN in text and END in text,
        "Build108 migration region missing",
    )

    require(
        "JerkGramLegacyDefaultsMigration.run()"
        in text,
        "Build108 startup migration call missing",
    )

    before, rest = text.split(BEGIN, 1)
    old_region, after = rest.split(END, 1)

    if MARKER in old_region:
        print(
            "[Build109] safe migration already installed"
        )
        return

    require(
        "dictionaryRepresentation()"
        in old_region,
        "Build108 migration implementation not found",
    )

    new_region = f'''{BEGIN}
{MARKER}
//
// Build109 hotfix.
//
// Build108 migrated every value with repeated
// UserDefaults.set(...) calls at the very beginning
// of didFinishLaunching.
//
// Build109 instead:
//
//   1. reads one persistent domain;
//   2. converts legacy keys in memory;
//   3. writes the domain once;
//   4. stores a one-shot migration marker.
//
// Canonical namespace remains jerkgram.*.
// Legacy values are copied, never deleted.
// Existing jerkgram.* values always win.
//
private enum JerkGramLegacyDefaultsMigration {{
    private static let canonicalPrefix = "jerkgram."

    private static let migrationMarker =
        "jerkgram.runtime.namespaceMigration.v1"

    private static func legacyPrefixLength(
        _ key: String
    ) -> Int? {{
        let lower = key.lowercased()

        if lower.hasPrefix("ghostbase.") {{
            return "ghostbase.".count
        }}

        if lower.hasPrefix("gb.") {{
            return "gb.".count
        }}

        return nil
    }}

    private static func migrateDomain(
        defaults: UserDefaults,
        domainName: String
    ) {{
        var domain =
            defaults.persistentDomain(
                forName: domainName
            ) ?? [:]

        if let completed =
            domain[self.migrationMarker] as? Bool,
           completed {{
            return
        }}

        let legacyKeys = domain.keys.filter {{ key in
            self.legacyPrefixLength(key) != nil
        }}.sorted {{ lhs, rhs in
            let lhsLower = lhs.lowercased()
            let rhsLower = rhs.lowercased()

            let lhsRank =
                lhsLower.hasPrefix("ghostbase.") ? 0 : 1

            let rhsRank =
                rhsLower.hasPrefix("ghostbase.") ? 0 : 1

            if lhsRank != rhsRank {{
                return lhsRank < rhsRank
            }}

            return lhs < rhs
        }}

        var migratedCount = 0

        for legacyKey in legacyKeys {{
            guard
                let prefixLength =
                    self.legacyPrefixLength(legacyKey),
                let value = domain[legacyKey]
            else {{
                continue
            }}

            let suffix = String(
                legacyKey.dropFirst(prefixLength)
            )

            let canonicalKey =
                self.canonicalPrefix + suffix

            if domain[canonicalKey] == nil {{
                domain[canonicalKey] = value
                migratedCount += 1
            }}
        }}

        domain[self.migrationMarker] = true

        defaults.setPersistentDomain(
            domain,
            forName: domainName
        )

        print(
            "[JerkGram Build109] migrated \\\\(migratedCount) legacy defaults in \\\\(domainName)"
        )
    }}

    static func run() {{
        if let bundleId =
            Bundle.main.bundleIdentifier {{
            self.migrateDomain(
                defaults: UserDefaults.standard,
                domainName: bundleId
            )
        }}

        if let sharedDefaults =
            UserDefaults(
                suiteName: "{APP_GROUP}"
            ) {{
            self.migrateDomain(
                defaults: sharedDefaults,
                domainName: "{APP_GROUP}"
            )
        }}
    }}
}}
{END}'''

    text = before + new_region + after

    APP_DELEGATE.write_text(
        text,
        encoding="utf-8",
    )

    print(
        "[Build109] Build108 migration replaced "
        "with one-shot persistent-domain migration"
    )


if __name__ == "__main__":
    main()
