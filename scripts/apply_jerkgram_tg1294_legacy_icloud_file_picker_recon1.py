#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
TARGET = ROOT / "submodules/LegacyMediaPickerUI/Sources/LegacyICloudFilePicker.swift"

MARKER = "// JERKGRAM_TG1294_LEGACY_ICLOUD_FILE_PICKER_RECON1"
IMPORT_OWNER = "import UIKit\nimport Display\n"
IMPORT_REPLACEMENT = "import UIKit\nimport UniformTypeIdentifiers\nimport Display\n"

STOCK_NON_EXPORT_OWNER = '''    } else {
        controller = DocumentPickerViewController(documentTypes: documentTypes, in: mode.documentPickerMode)
    }
    controller.forceDarkTheme = forceDarkTheme || theme.overallDarkAppearance
'''

RECONSTRUCTED_NON_EXPORT_OWNER = '''    } else {
        if #available(iOS 14.0, *) {
            // JERKGRAM_TG1294_LEGACY_ICLOUD_FILE_PICKER_RECON1
            let contentTypes = documentTypes.compactMap { UTType($0) }
            switch mode {
            case .default:
                controller = DocumentPickerViewController(forOpeningContentTypes: contentTypes, asCopy: false)
            case .import:
                controller = DocumentPickerViewController(forOpeningContentTypes: contentTypes, asCopy: true)
            case .export:
                controller = DocumentPickerViewController(documentTypes: documentTypes, in: mode.documentPickerMode)
            }
        } else {
            controller = DocumentPickerViewController(documentTypes: documentTypes, in: mode.documentPickerMode)
        }
    }
    controller.forceDarkTheme = forceDarkTheme || theme.overallDarkAppearance
'''

EXPORT_MODERN_OWNER = "            controller = DocumentPickerViewController(forExporting: [url], asCopy: true)\n"
EXPORT_LEGACY_OWNER = "            controller = DocumentPickerViewController(url: url, in: mode.documentPickerMode)\n"
MODE_OWNER = '''        case .default:
            return .open
        case .import:
            return .import
        case .export:
            return .exportToService
'''


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[TG12.9.4 LegacyICloudFilePicker recon1] " + message)


def verify_stock_owners(text: str) -> None:
    require(text.count(IMPORT_OWNER) == 1, f"stock import owner: expected 1, found {text.count(IMPORT_OWNER)}")
    require(text.count(STOCK_NON_EXPORT_OWNER) == 1, f"stock non-export owner: expected 1, found {text.count(STOCK_NON_EXPORT_OWNER)}")
    require(text.count(EXPORT_MODERN_OWNER) == 1, "iOS 14+ URL export owner drifted")
    require(text.count(EXPORT_LEGACY_OWNER) == 1, "pre-iOS14 URL export owner drifted")
    require(text.count(MODE_OWNER) == 1, "LegacyICloudFilePickerMode owner drifted")

    for invariant in (
        "func documentPickerWasCancelled(_ controller: UIDocumentPickerViewController)",
        "func documentPicker(_ controller: UIDocumentPickerViewController, didPickDocumentsAt urls: [URL])",
        "func documentPicker(_ controller: UIDocumentPickerViewController, didPickDocumentAt url: URL)",
        "controller.delegate = legacyController",
        "controller.allowsMultipleSelection = true",
        "window.rootViewController?.present(controller, animated: true)",
        "legacyController.bind(controller: UIViewController())",
    ):
        require(text.count(invariant) == 1, "stock invariant drifted: " + invariant)


def verify_reconstructed_owners(text: str) -> None:
    require(text.count(MARKER) == 1, "reconstruction marker count != 1")
    require(text.count("import UniformTypeIdentifiers\n") == 1, "UniformTypeIdentifiers import count != 1")
    require(text.count(RECONSTRUCTED_NON_EXPORT_OWNER) == 1, "reconstructed non-export owner drifted")
    require(text.count(EXPORT_MODERN_OWNER) == 1, "iOS 14+ URL export owner changed")
    require(text.count(EXPORT_LEGACY_OWNER) == 1, "pre-iOS14 URL export owner changed")
    require(text.count(MODE_OWNER) == 1, "LegacyICloudFilePickerMode owner changed")


def patch(text: str) -> str:
    if MARKER in text:
        verify_reconstructed_owners(text)
        require(STOCK_NON_EXPORT_OWNER not in text, "stock non-export owner survived beside reconstruction")
        return text

    require("import UniformTypeIdentifiers\n" not in text, "UniformTypeIdentifiers import exists without recon1 marker")
    verify_stock_owners(text)

    text = text.replace(IMPORT_OWNER, IMPORT_REPLACEMENT, 1)
    text = text.replace(STOCK_NON_EXPORT_OWNER, RECONSTRUCTED_NON_EXPORT_OWNER, 1)

    verify_reconstructed_owners(text)
    require(STOCK_NON_EXPORT_OWNER not in text, "stock non-export owner survived patch")
    return text


def main() -> None:
    require(TARGET.is_file(), "missing LegacyICloudFilePicker.swift")
    source = TARGET.read_text(encoding="utf-8")
    patched = patch(source)
    if patched != source:
        TARGET.write_text(patched, encoding="utf-8")
        print("[TG12.9.4 LegacyICloudFilePicker recon1] APPLIED")
    else:
        print("[TG12.9.4 LegacyICloudFilePicker recon1] ALREADY_APPLIED")
    print("[TG12.9.4 LegacyICloudFilePicker recon1] iOS 14+ default/import use UTType opening API; export and pre-iOS14 owners preserved")


if __name__ == "__main__":
    main()
