#!/usr/bin/env python3

from pathlib import Path
import importlib.util
import os


ROOT = Path(
    os.environ.get(
        "GHOSTBASE_SOURCE_ROOT",
        str(Path.cwd())
    )
).resolve()

BUILDER = Path(
    __file__
).resolve().parent.parent

APPLY = (
    BUILDER
    / "scripts"
    / "apply_jerkgram_v12d_build115_appgroup1.py"
)


TARGETS = {
    "submodules/TelegramUI/Sources/AppDelegate.swift": 2,
    "Telegram/SiriIntents/IntentHandler.swift": 2,
    "Telegram/WidgetKitWidget/TodayViewController.swift": 1,
    "Telegram/BroadcastUpload/BroadcastUploadExtension.swift": 1,
    "Telegram/Share/ShareRootController.swift": 1,
    "Telegram/NotificationContent/NotificationViewController.swift": 1,
    "Telegram/NotificationService/Sources/NotificationService.swift": 1,
}


def require(value, message):
    if not value:
        raise RuntimeError(
            "[verify Build115 AppGroup] "
            + message
        )


def select_model(groups, fallback):
    allowed = [
        value
        for value in groups
        if value
    ]

    if fallback in allowed:
        return fallback

    role_one = [
        value
        for value in allowed
        if value.endswith(".1")
    ]

    if len(role_one) == 1:
        return role_one[0]

    if len(allowed) == 1:
        return allowed[0]

    return fallback


real_order = [
    "group.signed.4",
    "group.signed.2",
    "group.signed.1",
    "group.signed.5",
    "group.signed.3",
]

require(
    select_model(
        real_order,
        "group.ph.telegra.Telegraph"
    )
    == "group.signed.1",
    "real ESign order did not resolve to role .1"
)

require(
    select_model(
        [
            "group.other",
            "group.telegram"
        ],
        "group.telegram"
    )
    == "group.telegram",
    "exact fallback must have priority"
)

require(
    select_model(
        ["group.only"],
        "group.fallback"
    )
    == "group.only",
    "single-group profile must resolve to its only group"
)

require(
    select_model(
        [
            "group.multi.4",
            "group.multi.2"
        ],
        "group.fallback"
    )
    == "group.fallback",
    "ambiguous multi-group profile must not use arbitrary first"
)


require(
    APPLY.is_file(),
    "Build115 apply script missing"
)

spec = importlib.util.spec_from_file_location(
    "build115_appgroup",
    APPLY
)

require(
    spec is not None
    and spec.loader is not None,
    "cannot load Build115 apply module"
)

module = importlib.util.module_from_spec(
    spec
)

spec.loader.exec_module(
    module
)


fixture = (
    module.BUILD114_MARKER
    + "\n"
    + module.OLD_SELECTION
)

patched = module.patch_text(
    fixture,
    "fixture.swift"
)

require(
    module.BUILD115_MARKER in patched,
    "production transform marker missing"
)

require(
    module.OLD_SELECTION not in patched,
    "production transform kept arbitrary-first"
)

for token in (
    "allowedGroups.contains(fallback)",
    '$0.hasSuffix(".1")',
    "roleOneGroups.count == 1",
    "allowedGroups.count == 1",
):
    require(
        token in patched,
        "production transform token missing: "
        + token
    )


resolved_call = (
    "let appGroupName = "
    "jerkgramResolvedApplicationGroupIdentifier("
)

total_sites = 0

for relative, expected_sites in TARGETS.items():
    path = ROOT / relative

    require(
        path.is_file(),
        "runtime owner missing: "
        + relative
    )

    text = path.read_text(
        encoding="utf-8"
    )

    require(
        module.BUILD114_MARKER in text,
        "Build114 resolver missing: "
        + relative
    )

    require(
        text.count(
            module.BUILD115_MARKER
        )
        == 1,
        (
            "Build115 resolver marker count "
            f"invalid: {relative}"
        )
    )

    start = text.index(
        module.BUILD114_MARKER
    )

    end_token = (
        "    return fallback\n"
        "}\n"
    )

    end = text.index(
        end_token,
        start
    ) + len(end_token)

    helper = text[
        start:end
    ]

    require(
        "groups.first(" not in helper,
        "arbitrary groups.first survived: "
        + relative
    )

    ordered_tokens = (
        "allowedGroups.contains(fallback)",
        '$0.hasSuffix(".1")',
        "roleOneGroups.count == 1",
        "allowedGroups.count == 1",
    )

    positions = []

    for token in ordered_tokens:
        require(
            token in helper,
            (
                "resolver token missing: "
                f"{relative}: {token}"
            )
        )

        positions.append(
            helper.index(token)
        )

    require(
        positions
        == sorted(positions),
        "resolver priority order invalid: "
        + relative
    )

    actual_sites = text.count(
        resolved_call
    )

    require(
        actual_sites == expected_sites,
        (
            "AppGroup call-site count invalid: "
            f"{relative}: "
            f"{actual_sites} != {expected_sites}"
        )
    )

    total_sites += actual_sites


require(
    total_sites == 9,
    (
        "total AppGroup call sites != 9: "
        f"{total_sites}"
    )
)


print(
    "[verify Build115] GREEN"
)

print(
    "[verify Build115] "
    "ESign order [.4,.2,.1,.5,.3] -> .1"
)

print(
    "[verify Build115] "
    "7 processes / 9 AppGroup call sites"
)

print(
    "[verify Build115] "
    "no arbitrary groups.first selection"
)
