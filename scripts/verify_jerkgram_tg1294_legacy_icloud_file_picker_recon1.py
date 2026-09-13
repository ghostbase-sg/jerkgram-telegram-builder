#!/usr/bin/env python3

from pathlib import Path
import os


ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
TARGET = ROOT / "submodules/LegacyMediaPickerUI/Sources/LegacyICloudFilePicker.swift"
MARKER = "// JERKGRAM_TG1294_LEGACY_ICLOUD_FILE_PICKER_RECON1"


def require(value: bool, message: str) -> None:
    if not value:
        raise RuntimeError("[TG12.9.4 LegacyICloudFilePicker recon1 verifier] " + message)


def verify(text: str) -> None:
    require(text.count("import UniformTypeIdentifiers\n") == 1, "UniformTypeIdentifiers import count != 1")
    require(text.count(MARKER) == 1, "reconstruction marker count != 1")

    bridge = "let contentTypes = documentTypes.compactMap { UTType($0) }"
    require(text.count(bridge) == 1, "legacy UTI -> UTType bridge count != 1")

    default_owner = "controller = DocumentPickerViewController(forOpeningContentTypes: contentTypes, asCopy: false)"
    import_owner = "controller = DocumentPickerViewController(forOpeningContentTypes: contentTypes, asCopy: true)"
    require(text.count(default_owner) == 1, "default/open modern owner count != 1")
    require(text.count(import_owner) == 1, "import modern owner count != 1")

    marker = text.index(MARKER)
    switch_window = text[marker:marker + 900]
    require("switch mode" in switch_window, "modern mode switch missing")
    require("case .default:" in switch_window and default_owner in switch_window, "default mode is not mapped to opening-asCopy=false")
    require("case .import:" in switch_window and import_owner in switch_window, "import mode is not mapped to opening-asCopy=true")
    require("case .export:" in switch_window, "export-without-url fallback branch missing from modern path")
    require("controller = DocumentPickerViewController(documentTypes: documentTypes, in: mode.documentPickerMode)" in switch_window, "export-without-url legacy fallback missing")

    require(text.count("controller = DocumentPickerViewController(forExporting: [url], asCopy: true)") == 1, "iOS 14+ URL export owner changed")
    require(text.count("controller = DocumentPickerViewController(url: url, in: mode.documentPickerMode)") == 1, "pre-iOS14 URL export fallback changed")
    require(text.count("controller = DocumentPickerViewController(documentTypes: documentTypes, in: mode.documentPickerMode)") == 2, "legacy documentTypes fallback count != 2")

    enum_owner = '''        case .default:\n            return .open\n        case .import:\n            return .import\n        case .export:\n            return .exportToService\n'''
    require(text.count(enum_owner) == 1, "LegacyICloudFilePickerMode mapping drifted")

    for callback in (
        "func documentPickerWasCancelled(_ controller: UIDocumentPickerViewController)",
        "func documentPicker(_ controller: UIDocumentPickerViewController, didPickDocumentsAt urls: [URL])",
        "func documentPicker(_ controller: UIDocumentPickerViewController, didPickDocumentAt url: URL)",
    ):
        require(text.count(callback) == 1, "delegate callback drifted: " + callback)

    for invariant in (
        "controller.didDisappear = {",
        "controller.delegate = legacyController",
        "controller.allowsMultipleSelection = true",
        "window.rootViewController?.present(controller, animated: true)",
        "legacyController.dismiss()",
        "dismissed()",
        "legacyController.bind(controller: UIViewController())",
    ):
        require(text.count(invariant) == 1, "presentation/dismiss invariant drifted: " + invariant)

    require("startAccessingSecurityScopedResource" not in text, "reconstruction must not take over security-scoped resource ownership")
    require("stopAccessingSecurityScopedResource" not in text, "reconstruction must not take over security-scoped resource ownership")


def main() -> None:
    require(TARGET.is_file(), "missing LegacyICloudFilePicker.swift")
    verify(TARGET.read_text(encoding="utf-8"))
    print("[TG12.9.4 LegacyICloudFilePicker recon1 verifier] GREEN")
    print("[TG12.9.4 LegacyICloudFilePicker recon1 verifier] modern opening/import semantics restored; export, legacy fallbacks, delegates and presentation owners preserved")


if __name__ == "__main__":
    main()
