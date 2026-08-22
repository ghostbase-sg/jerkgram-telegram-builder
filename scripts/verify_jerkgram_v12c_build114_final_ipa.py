#!/usr/bin/env python3

from pathlib import Path
import plistlib
import struct
import sys
import tempfile
import zipfile


IPA = Path(
    sys.argv[1]
    if len(sys.argv) > 1
    else "ghostbase-final/GhostBase.ipa"
).resolve()

PUBLIC_BASE = "ph.telegra.Telegraph"
PUBLIC_TEAM = "C67CF9S4VU"
PUBLIC_GROUP = "group.ph.telegra.Telegraph"

PRIVATE_BASE = "app.pumpkin6584.lion7414"

DISPLAY = "Jerkgram"
PRIMARY = "JerkgramGlassReveal"


EXTENSIONS = {
    "BroadcastUploadExtension.appex": {
        "bundle_id":
            PUBLIC_BASE + ".BroadcastUpload",

        "point":
            "com.apple.broadcast-services-upload",

        "class":
            "keychain",
    },

    "IntentsExtension.appex": {
        "bundle_id":
            PUBLIC_BASE + ".SiriIntents",

        "point":
            "com.apple.intents-service",

        "class":
            "keychain",
    },

    "NotificationContentExtension.appex": {
        "bundle_id":
            PUBLIC_BASE + ".NotificationContent",

        "point":
            "com.apple.usernotifications.content-extension",

        "class":
            "aps",
    },

    "NotificationServiceExtensionv1.appex": {
        "bundle_id":
            PUBLIC_BASE + ".NotificationService",

        "point":
            "com.apple.usernotifications.service",

        "class":
            "aps",
    },

    "ShareExtension.appex": {
        "bundle_id":
            PUBLIC_BASE + ".Share",

        "point":
            "com.apple.share-services",

        "class":
            "aps",
    },

    "WidgetExtension.appex": {
        "bundle_id":
            PUBLIC_BASE + ".Widget",

        "point":
            "com.apple.widgetkit-extension",

        "class":
            "keychain",
    },
}


def require(value, message):
    if not value:
        raise RuntimeError(
            "[verify Build114 final] "
            + message
        )


def load_plist(path):
    with path.open("rb") as f:
        return plistlib.load(f)


def thin_signature_blob(data):
    if len(data) < 32:
        return None

    magic = data[:4]

    if magic == b"\xcf\xfa\xed\xfe":
        endian = "<"
        header = 32

    elif magic == b"\xfe\xed\xfa\xcf":
        endian = ">"
        header = 32

    elif magic == b"\xce\xfa\xed\xfe":
        endian = "<"
        header = 28

    elif magic == b"\xfe\xed\xfa\xce":
        endian = ">"
        header = 28

    else:
        return None

    ncmds = struct.unpack_from(
        endian + "I",
        data,
        16
    )[0]

    offset = header

    for _ in range(
        ncmds
    ):
        require(
            offset + 8
            <= len(data),
            "truncated Mach-O load commands"
        )

        cmd, cmdsize = struct.unpack_from(
            endian + "II",
            data,
            offset
        )

        require(
            cmdsize >= 8
            and (
                offset
                + cmdsize
                <= len(data)
            ),
            "invalid Mach-O load command"
        )

        if cmd == 0x1D:
            require(
                cmdsize >= 16,
                "short LC_CODE_SIGNATURE"
            )

            dataoff, datasize = (
                struct.unpack_from(
                    endian + "II",
                    data,
                    offset + 8
                )
            )

            require(
                dataoff + datasize
                <= len(data),
                "signature blob outside Mach-O"
            )

            return data[
                dataoff:
                dataoff + datasize
            ]

        offset += cmdsize

    return b""


def macho_slices(data):
    thin = thin_signature_blob(
        data
    )

    if thin is not None:
        return [
            data
        ]

    require(
        len(data) >= 8,
        "invalid Mach-O/fat binary"
    )

    magic = struct.unpack_from(
        ">I",
        data,
        0
    )[0]

    require(
        magic
        in (
            0xCAFEBABE,
            0xCAFEBABF,
        ),
        "unknown Mach-O magic"
    )

    is64 = (
        magic
        == 0xCAFEBABF
    )

    count = struct.unpack_from(
        ">I",
        data,
        4
    )[0]

    offset = 8
    result = []

    for _ in range(
        count
    ):
        if is64:
            require(
                offset + 32
                <= len(data),
                "truncated fat64 header"
            )

            slice_offset, slice_size = (
                struct.unpack_from(
                    ">QQ",
                    data,
                    offset + 8
                )
            )

            offset += 32

        else:
            require(
                offset + 20
                <= len(data),
                "truncated fat header"
            )

            slice_offset, slice_size = (
                struct.unpack_from(
                    ">II",
                    data,
                    offset + 8
                )
            )

            offset += 20

        require(
            slice_offset + slice_size
            <= len(data),
            "fat slice outside binary"
        )

        result.append(
            data[
                slice_offset:
                slice_offset + slice_size
            ]
        )

    return result


def entitlement_dicts(data):
    result = []

    for slice_data in (
        macho_slices(
            data
        )
    ):
        signature = (
            thin_signature_blob(
                slice_data
            )
        )

        require(
            signature is not None
            and len(signature) >= 12,
            "LC_CODE_SIGNATURE missing"
        )

        require(
            signature,
            "empty LC_CODE_SIGNATURE"
        )

        magic, length, count = (
            struct.unpack_from(
                ">III",
                signature,
                0
            )
        )

        require(
            magic == 0xFADE0CC0,
            (
                "code signature "
                "is not SuperBlob"
            )
        )

        require(
            length
            <= len(signature),
            "invalid SuperBlob length"
        )

        for index in range(
            count
        ):
            entry = (
                12
                + index * 8
            )

            require(
                entry + 8
                <= len(signature),
                "truncated SuperBlob index"
            )

            slot_type, blob_offset = (
                struct.unpack_from(
                    ">II",
                    signature,
                    entry
                )
            )

            require(
                blob_offset + 8
                <= len(signature),
                "invalid signature blob offset"
            )

            blob_magic, blob_length = (
                struct.unpack_from(
                    ">II",
                    signature,
                    blob_offset
                )
            )

            require(
                blob_offset + blob_length
                <= len(signature),
                "signature blob overflow"
            )

            if (
                blob_magic
                == 0xFADE7171
            ):
                payload = signature[
                    blob_offset + 8:
                    blob_offset + blob_length
                ]

                value = (
                    plistlib.loads(
                        payload
                    )
                )

                require(
                    isinstance(
                        value,
                        dict
                    ),
                    "entitlements plist malformed"
                )

                result.append(
                    value
                )

    return result


def verify_entitlements(
    entitlements,
    bundle_id,
    kind
):
    require(
        entitlements.get(
            "application-identifier"
        )
        == (
            PUBLIC_TEAM
            + "."
            + bundle_id
        ),
        (
            "application-identifier "
            f"mismatch for {bundle_id}: "
            f"{entitlements.get('application-identifier')!r}"
        )
    )

    require(
        entitlements.get(
            "com.apple.security.application-groups"
        )
        == [
            PUBLIC_GROUP
        ],
        (
            "AppGroup mismatch for "
            f"{bundle_id}: "
            f"{entitlements.get('com.apple.security.application-groups')!r}"
        )
    )

    require(
        entitlements.get(
            "get-task-allow"
        )
        is False,
        (
            "get-task-allow must be false: "
            f"{bundle_id}"
        )
    )

    if kind == "main":
        require(
            entitlements.get(
                "aps-environment"
            )
            == "production",
            (
                "main aps-environment "
                "mismatch"
            )
        )

        require(
            "keychain-access-groups"
            not in entitlements,
            (
                "main carrier diverges "
                "from Whitegram keychain topology"
            )
        )

    elif kind == "keychain":
        require(
            entitlements.get(
                "com.apple.developer.team-identifier"
            )
            == PUBLIC_TEAM,
            (
                "team identifier mismatch: "
                f"{bundle_id}"
            )
        )

        require(
            entitlements.get(
                "keychain-access-groups"
            )
            == [
                f"{PUBLIC_TEAM}.*",
                "com.apple.token",
            ],
            (
                "keychain topology mismatch: "
                f"{bundle_id}"
            )
        )

        require(
            "aps-environment"
            not in entitlements,
            (
                "unexpected aps entitlement: "
                f"{bundle_id}"
            )
        )

    elif kind == "aps":
        require(
            entitlements.get(
                "aps-environment"
            )
            == "production",
            (
                "aps topology mismatch: "
                f"{bundle_id}"
            )
        )

        require(
            "keychain-access-groups"
            not in entitlements,
            (
                "unexpected keychain carrier: "
                f"{bundle_id}"
            )
        )

    else:
        raise RuntimeError(
            "[verify Build114 final] "
            f"unknown carrier kind: {kind}"
        )


require(
    IPA.is_file(),
    f"IPA missing: {IPA}"
)


with tempfile.TemporaryDirectory(
    prefix="build114-final-"
) as td:
    root = Path(td)

    with zipfile.ZipFile(
        IPA,
        "r"
    ) as archive:
        names = [
            item.filename
            for item
            in archive.infolist()
        ]

        require(
            not any(
                name.endswith(
                    "/embedded.mobileprovision"
                )
                for name
                in names
            ),
            (
                "developer provisioning profile "
                "survived raw IPA"
            )
        )

        require(
            not any(
                "/_CodeSignature/"
                in name
                for name
                in names
            ),
            (
                "bundle CodeResources signature "
                "survived; expected Mach-O "
                "entitlement-carrier only"
            )
        )

        archive.extractall(
            root
        )

    apps = list(
        (root / "Payload")
        .glob("*.app")
    )

    require(
        len(apps) == 1,
        (
            "expected one app, got "
            f"{[x.name for x in apps]}"
        )
    )

    app = apps[0]

    info = load_plist(
        app
        / "Info.plist"
    )

    require(
        info.get(
            "CFBundleIdentifier"
        )
        == PUBLIC_BASE,
        (
            "main public BID mismatch: "
            f"{info.get('CFBundleIdentifier')!r}"
        )
    )

    require(
        info.get(
            "CFBundleName"
        )
        == DISPLAY,
        "main CFBundleName != Jerkgram"
    )

    require(
        info.get(
            "CFBundleDisplayName"
        )
        == DISPLAY,
        (
            "main CFBundleDisplayName "
            "!= Jerkgram"
        )
    )

    for icon_key in (
        "CFBundleIcons",
        "CFBundleIcons~ipad",
    ):
        icons = info.get(
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
                f"!= {PRIMARY}"
            )
        )

    main_exe_name = (
        info.get(
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

    main_executable = (
        app
        / main_exe_name
    )

    require(
        main_executable.is_file(),
        "main executable missing"
    )

    main_entitlements = (
        entitlement_dicts(
            main_executable
                .read_bytes()
        )
    )

    require(
        main_entitlements,
        (
            "main entitlement carrier "
            "missing"
        )
    )

    verify_entitlements(
        main_entitlements[0],
        PUBLIC_BASE,
        "main"
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

    for name, spec in (
        EXTENSIONS.items()
    ):
        extension = (
            present[
                name
            ]
        )

        ext_info = load_plist(
            extension
            / "Info.plist"
        )

        require(
            ext_info.get(
                "CFBundleIdentifier"
            )
            == spec[
                "bundle_id"
            ],
            (
                f"{name} BID mismatch: "
                f"{ext_info.get('CFBundleIdentifier')!r}"
            )
        )

        require(
            ext_info.get(
                "CFBundleName"
            )
            == DISPLAY,
            (
                f"{name} CFBundleName "
                "!= Jerkgram"
            )
        )

        require(
            ext_info.get(
                "CFBundleDisplayName"
            )
            == DISPLAY,
            (
                f"{name} display name "
                "!= Jerkgram"
            )
        )

        ns = ext_info.get(
            "NSExtension"
        )

        require(
            isinstance(
                ns,
                dict
            ),
            (
                f"{name} NSExtension "
                "missing"
            )
        )

        require(
            ns.get(
                "NSExtensionPointIdentifier"
            )
            == spec[
                "point"
            ],
            (
                f"{name} extension "
                "point mismatch"
            )
        )

        exe_name = ext_info.get(
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

        ents = entitlement_dicts(
            executable.read_bytes()
        )

        require(
            ents,
            (
                f"{name} entitlement "
                "carrier missing"
            )
        )

        verify_entitlements(
            ents[0],
            spec[
                "bundle_id"
            ],
            spec[
                "class"
            ]
        )

    broadcast = load_plist(
        present[
            "BroadcastUploadExtension.appex"
        ]
        / "Info.plist"
    ).get(
        "NSExtension",
        {}
    )

    require(
        (
            "BroadcastUploadSampleHandler"
            in str(
                broadcast.get(
                    "NSExtensionPrincipalClass"
                )
            )
        ),
        "Broadcast principal mismatch"
    )

    require(
        broadcast.get(
            "RPBroadcastProcessMode"
        )
        == (
            "RPBroadcastProcessModeSampleBuffer"
        ),
        (
            "Broadcast process mode "
            "mismatch"
        )
    )


print(
    "[verify Build114 final] GREEN"
)

print(
    "[verify Build114 final] "
    "raw public namespace:",
    PUBLIC_BASE
)

print(
    "[verify Build114 final] "
    "6/6 official Telegram extension "
    "suffixes"
)

print(
    "[verify Build114 final] "
    "all extension system names: Jerkgram"
)

print(
    "[verify Build114 final] "
    "7/7 Whitegram-matched embedded "
    "entitlement carriers"
)

print(
    "[verify Build114 final] "
    "no developer provisioning profile"
)

print(
    "[verify Build114 final] "
    "primary icon:",
    PRIMARY
)
