#!/usr/bin/env python3

from pathlib import Path
import os
import plistlib
import shutil
import struct
import subprocess
import sys
import tempfile
import zipfile


INTERNAL_BASE = "app.pumpkin6584.lion7414"

PUBLIC_BASE = "ph.telegra.Telegraph"
PUBLIC_TEAM = "C67CF9S4VU"
PUBLIC_GROUP = "group.ph.telegra.Telegraph"

DISPLAY = "Jerkgram"
PRIMARY = "JerkgramGlassReveal"


EXTENSIONS = {
    "BroadcastUploadExtension.appex": {
        "bundle_id":
            PUBLIC_BASE + ".BroadcastUpload",

        "extension_point":
            "com.apple.broadcast-services-upload",

        "whitegram_class":
            "keychain",
    },

    "IntentsExtension.appex": {
        "bundle_id":
            PUBLIC_BASE + ".SiriIntents",

        "extension_point":
            "com.apple.intents-service",

        "whitegram_class":
            "keychain",
    },

    "NotificationContentExtension.appex": {
        "bundle_id":
            PUBLIC_BASE + ".NotificationContent",

        "extension_point":
            "com.apple.usernotifications.content-extension",

        "whitegram_class":
            "aps",
    },

    "NotificationServiceExtensionv1.appex": {
        "bundle_id":
            PUBLIC_BASE + ".NotificationService",

        "extension_point":
            "com.apple.usernotifications.service",

        "whitegram_class":
            "aps",
    },

    "ShareExtension.appex": {
        "bundle_id":
            PUBLIC_BASE + ".Share",

        "extension_point":
            "com.apple.share-services",

        "whitegram_class":
            "aps",
    },

    "WidgetExtension.appex": {
        "bundle_id":
            PUBLIC_BASE + ".Widget",

        "extension_point":
            "com.apple.widgetkit-extension",

        "whitegram_class":
            "keychain",
    },
}


def require(value, message):
    if not value:
        raise RuntimeError(
            "[Build114 finalizer] "
            + message
        )


def load_plist(path):
    with path.open("rb") as f:
        return plistlib.load(f)


def save_plist(path, value):
    old = path.read_bytes()

    fmt = (
        plistlib.FMT_BINARY
        if old.startswith(b"bplist")
        else plistlib.FMT_XML
    )

    path.write_bytes(
        plistlib.dumps(
            value,
            fmt=fmt,
            sort_keys=False
        )
    )


def carrier_entitlements(
    bundle_id,
    kind
):
    value = {
        "application-identifier":
            f"{PUBLIC_TEAM}.{bundle_id}",

        "com.apple.security.application-groups": [
            PUBLIC_GROUP
        ],

        "get-task-allow":
            False,
    }

    if kind == "main":
        value["aps-environment"] = (
            "production"
        )

    elif kind == "keychain":
        value[
            "com.apple.developer.team-identifier"
        ] = PUBLIC_TEAM

        value[
            "keychain-access-groups"
        ] = [
            f"{PUBLIC_TEAM}.*",
            "com.apple.token",
        ]

    elif kind == "aps":
        value["aps-environment"] = (
            "production"
        )

    else:
        raise RuntimeError(
            "[Build114 finalizer] "
            f"unknown entitlement class: {kind}"
        )

    return value


def sign_entitlement_carrier(
    executable,
    entitlements,
    temp_root
):
    codesign = shutil.which(
        "codesign"
    )

    require(
        codesign is not None,
        (
            "codesign missing; Build114 carrier "
            "must run on macOS CI"
        )
    )

    plist_path = (
        temp_root
        / (
            executable.name
            + ".build114.entitlements.plist"
        )
    )

    plist_path.write_bytes(
        plistlib.dumps(
            entitlements,
            fmt=plistlib.FMT_XML,
            sort_keys=False
        )
    )

    command = [
        codesign,
        "--force",
        "--sign",
        "-",
        "--timestamp=none",
        "--generate-entitlement-der",
        "--entitlements",
        str(plist_path),
        str(executable),
    ]

    result = subprocess.run(
        command,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    require(
        result.returncode == 0,
        (
            f"ad-hoc carrier signing failed "
            f"for {executable}:\n"
            f"{result.stdout}\n"
            f"{result.stderr}"
        )
    )


ipa = Path(
    sys.argv[1]
    if len(sys.argv) > 1
    else "ghostbase-final/GhostBase.ipa"
).resolve()

require(
    ipa.is_file(),
    f"IPA missing: {ipa}"
)


with tempfile.TemporaryDirectory(
    prefix="build114-finalizer-"
) as td:
    root = Path(td)

    with zipfile.ZipFile(
        ipa,
        "r"
    ) as zin:
        infos = zin.infolist()

        zin.extractall(
            root
        )

        mains = list(
            (root / "Payload")
            .glob("*.app")
        )

        require(
            len(mains) == 1,
            (
                "expected one app, got "
                f"{[x.name for x in mains]}"
            )
        )

        app = mains[0]

        main_info_path = (
            app
            / "Info.plist"
        )

        main_info = load_plist(
            main_info_path
        )

        require(
            main_info.get(
                "CFBundleIdentifier"
            )
            == INTERNAL_BASE,
            (
                "Build113 verifier topology "
                "not preserved before Build114: "
                f"{main_info.get('CFBundleIdentifier')!r}"
            )
        )

        main_info[
            "CFBundleIdentifier"
        ] = PUBLIC_BASE

        main_info[
            "CFBundleName"
        ] = DISPLAY

        main_info[
            "CFBundleDisplayName"
        ] = DISPLAY

        for icon_key in (
            "CFBundleIcons",
            "CFBundleIcons~ipad",
        ):
            icons = main_info.get(
                icon_key
            )

            require(
                isinstance(
                    icons,
                    dict
                ),
                f"{icon_key} missing"
            )

            primary = icons.get(
                "CFBundlePrimaryIcon"
            )

            require(
                isinstance(
                    primary,
                    dict
                )
                and primary.get(
                    "CFBundleIconName"
                )
                == PRIMARY,
                (
                    f"{icon_key} primary "
                    f"must remain {PRIMARY}"
                )
            )

        save_plist(
            main_info_path,
            main_info
        )

        plugins = (
            app
            / "PlugIns"
        )

        require(
            plugins.is_dir(),
            "PlugIns missing"
        )

        present = {
            path.name: path
            for path
            in plugins.glob(
                "*.appex"
            )
            if path.is_dir()
        }

        require(
            set(present)
            == set(EXTENSIONS),
            (
                "extension set mismatch: "
                f"{sorted(present)}"
            )
        )

        modified_files = {
            main_info_path
        }

        carrier_targets = []

        main_exe_name = (
            main_info.get(
                "CFBundleExecutable"
            )
        )

        require(
            isinstance(
                main_exe_name,
                str
            ),
            "main executable key missing"
        )

        main_exe = (
            app
            / main_exe_name
        )

        require(
            main_exe.is_file(),
            "main executable missing"
        )

        carrier_targets.append(
            (
                main_exe,
                carrier_entitlements(
                    PUBLIC_BASE,
                    "main"
                )
            )
        )

        modified_files.add(
            main_exe
        )

        for name, spec in (
            EXTENSIONS.items()
        ):
            extension = present[
                name
            ]

            info_path = (
                extension
                / "Info.plist"
            )

            info = load_plist(
                info_path
            )

            old_bid = info.get(
                "CFBundleIdentifier"
            )

            require(
                old_bid
                == (
                    INTERNAL_BASE
                    + "."
                    + spec[
                        "bundle_id"
                    ][
                        len(PUBLIC_BASE) + 1:
                    ]
                ),
                (
                    f"{name} unexpected "
                    f"Build113 BID: "
                    f"{old_bid!r}"
                )
            )

            ns = info.get(
                "NSExtension"
            )

            require(
                isinstance(
                    ns,
                    dict
                ),
                (
                    f"{name} "
                    "NSExtension missing"
                )
            )

            require(
                ns.get(
                    "NSExtensionPointIdentifier"
                )
                == spec[
                    "extension_point"
                ],
                (
                    f"{name} extension "
                    "point mismatch"
                )
            )

            info[
                "CFBundleIdentifier"
            ] = spec[
                "bundle_id"
            ]

            info[
                "CFBundleName"
            ] = DISPLAY

            info[
                "CFBundleDisplayName"
            ] = DISPLAY

            save_plist(
                info_path,
                info
            )

            modified_files.add(
                info_path
            )

            exe_name = info.get(
                "CFBundleExecutable"
            )

            require(
                isinstance(
                    exe_name,
                    str
                ),
                (
                    f"{name} executable "
                    "key missing"
                )
            )

            executable = (
                extension
                / exe_name
            )

            require(
                executable.is_file(),
                (
                    f"{name} executable "
                    "missing"
                )
            )

            carrier_targets.append(
                (
                    executable,
                    carrier_entitlements(
                        spec[
                            "bundle_id"
                        ],
                        spec[
                            "whitegram_class"
                        ]
                    )
                )
            )

            modified_files.add(
                executable
            )

        for bundle in (
            [app]
            + list(
                present.values()
            )
        ):
            profile = (
                bundle
                / "embedded.mobileprovision"
            )

            if profile.exists():
                profile.unlink()

            signature_dir = (
                bundle
                / "_CodeSignature"
            )

            if signature_dir.exists():
                shutil.rmtree(
                    signature_dir
                )

        for executable, entitlements in (
            carrier_targets
        ):
            sign_entitlement_carrier(
                executable,
                entitlements,
                root
            )

        modified_data = {}

        for path in modified_files:
            member = (
                path
                .relative_to(root)
                .as_posix()
            )

            modified_data[
                member
            ] = path.read_bytes()

        fd, tmp_name = tempfile.mkstemp(
            prefix=(
                ipa.name
                + ".build114."
            ),
            suffix=".tmp",
            dir=str(
                ipa.parent
            )
        )

        os.close(fd)

        tmp = Path(
            tmp_name
        )

        try:
            with zipfile.ZipFile(
                tmp,
                "w"
            ) as zout:
                for item in infos:
                    member = (
                        item.filename
                    )

                    if (
                        member.endswith(
                            "/embedded.mobileprovision"
                        )
                        or "/_CodeSignature/"
                        in member
                    ):
                        continue

                    if (
                        member
                        in modified_data
                    ):
                        data = modified_data[
                            member
                        ]
                    else:
                        data = zin.read(
                            item
                        )

                    zout.writestr(
                        item,
                        data
                    )

            os.replace(
                tmp,
                ipa
            )

        finally:
            tmp.unlink(
                missing_ok=True
            )


print(
    "[Build114 finalizer] "
    "public raw namespace:",
    PUBLIC_BASE
)

print(
    "[Build114 finalizer] "
    "6 extension suffixes restored"
)

print(
    "[Build114 finalizer] "
    "system extension name:",
    DISPLAY
)

print(
    "[Build114 finalizer] "
    "Whitegram-matched entitlement "
    "carrier topology: 7/7"
)

print(
    "[Build114 finalizer] "
    "developer profiles: none"
)

print(
    "[Build114 finalizer] "
    "developer certificate: none "
    "(ad-hoc carrier only)"
)
