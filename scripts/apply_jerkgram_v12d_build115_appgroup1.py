#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(
    os.environ.get(
        "GHOSTBASE_SOURCE_ROOT",
        str(Path.cwd())
    )
).resolve()


TARGETS = (
    "submodules/TelegramUI/Sources/AppDelegate.swift",
    "Telegram/SiriIntents/IntentHandler.swift",
    "Telegram/WidgetKitWidget/TodayViewController.swift",
    "Telegram/BroadcastUpload/BroadcastUploadExtension.swift",
    "Telegram/Share/ShareRootController.swift",
    "Telegram/NotificationContent/NotificationViewController.swift",
    "Telegram/NotificationService/Sources/NotificationService.swift",
)


BUILD114_MARKER = (
    "// MARK: Jerkgram v1.2C "
    "BUILD114_SIGNER_APPGROUP1"
)

BUILD115_MARKER = (
    "// BUILD115_SHARED_APPGROUP_ROLE1"
)


OLD_SELECTION = r'''            let groups =
                entitlements[
                    "com.apple.security.application-groups"
                ] as? [String],
            let group =
                groups.first(
                    where: {
                        !$0.isEmpty
                    }
                )
        else {
            continue
        }

        return group
'''


NEW_SELECTION = r'''            let groups =
                entitlements[
                    "com.apple.security.application-groups"
                ] as? [String]
        else {
            continue
        }

        // BUILD115_SHARED_APPGROUP_ROLE1
        //
        // Never trust entitlement array ordering.
        //
        // 1. Prefer the normal Telegram-derived fallback
        //    when the signer actually grants it.
        //
        // 2. GhostBase historically stores shared state in
        //    the signer-provided App Group whose role suffix
        //    is ".1".
        //
        // 3. A single granted group is unambiguous.
        //
        // 4. For an ambiguous multi-group profile with no
        //    matching role, do not select an arbitrary first
        //    entry. Try the containing-app profile and then
        //    fall back to the normal Telegram derivation.
        let allowedGroups = groups.filter {
            !$0.isEmpty
        }

        if allowedGroups.contains(fallback) {
            return fallback
        }

        let roleOneGroups = allowedGroups.filter {
            $0.hasSuffix(".1")
        }

        if roleOneGroups.count == 1 {
            return roleOneGroups[0]
        }

        if allowedGroups.count == 1 {
            return allowedGroups[0]
        }
'''


def require(value, message):
    if not value:
        raise RuntimeError(
            "[Build115 AppGroup] "
            + message
        )


def patch_text(text, relative):
    require(
        BUILD114_MARKER in text,
        (
            "Build114 resolver missing: "
            + relative
        )
    )

    require(
        BUILD115_MARKER not in text,
        (
            "Build115 already applied: "
            + relative
        )
    )

    count = text.count(
        OLD_SELECTION
    )

    require(
        count == 1,
        (
            "Build114 arbitrary-first block "
            f"count != 1 in {relative}: {count}"
        )
    )

    result = text.replace(
        OLD_SELECTION,
        NEW_SELECTION,
        1
    )

    require(
        BUILD115_MARKER in result,
        (
            "Build115 marker not materialized: "
            + relative
        )
    )

    require(
        OLD_SELECTION not in result,
        (
            "arbitrary-first block survived: "
            + relative
        )
    )

    return result


def main():
    changed = []

    for relative in TARGETS:
        path = ROOT / relative

        require(
            path.is_file(),
            (
                "runtime owner missing: "
                + relative
            )
        )

        text = path.read_text(
            encoding="utf-8"
        )

        result = patch_text(
            text,
            relative
        )

        path.write_text(
            result,
            encoding="utf-8"
        )

        changed.append(
            relative
        )

    require(
        len(changed) == 7,
        (
            "unexpected owner count: "
            f"{len(changed)}"
        )
    )

    print(
        "[Build115] AppGroup selection fixed "
        "in 7/7 runtime owners"
    )

    print(
        "[Build115] priority: "
        "exact fallback -> role .1 -> "
        "single group -> non-arbitrary fallback"
    )


if __name__ == "__main__":
    main()
