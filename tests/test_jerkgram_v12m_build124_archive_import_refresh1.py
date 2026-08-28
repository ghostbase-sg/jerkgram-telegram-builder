from pathlib import Path
import importlib.util
import unittest


REPO = Path(__file__).resolve().parents[1]
PATCH = REPO / "scripts/apply_jerkgram_v12m_build124_archive_import_runtime1.py"

SETTINGS_FIXTURE = '''import Foundation
import SwiftSignalKit

private struct GhostBaseSettingsState: Equatable {
    static func load(accountPeerId: Int64, mirrorLegacy: Bool) -> GhostBaseSettingsState {
        return GhostBaseSettingsState()
    }
}

// Stable Build123/Build124 settings entries owner. Keep the public controller
// declaration deliberately multiline so this fixture catches regressions back
// to formatting-sensitive controller anchors.
private func ghostBaseSettingsEntries(
    presentationData: PresentationData,
    state: GhostBaseSettingsState
) -> [Any] {
    return []
}

public func ghostBaseSettingsController(
    context: AccountContext,
    initialPage: GhostBaseSettingsPage = .root
) -> ViewController {
    // MARK: Jerkgram v1.2L BUILD123_ACCOUNT_SETTINGS_SCOPE1
    let accountPeerId = context.account.peerId.toInt64()
    let initialState = GhostBaseSettingsState.load(accountPeerId: accountPeerId, mirrorLegacy: true)
    let statePromise = ValuePromise(initialState, ignoreRepeated: true)
    let stateValue = Atomic(value: initialState)

    let signal = combineLatest(context.sharedContext.presentationData, statePromise.get())
    |> deliverOnMainQueue
    |> map { presentationData, state -> (ItemListControllerState, (ItemListNodeState, Any)) in
        fatalError()
    }
    return ItemListController(context: context, state: signal)
}
'''


class Build124ArchiveImportRefreshTests(unittest.TestCase):
    def load_patch(self):
        spec = importlib.util.spec_from_file_location("build124_archive_import_runtime", PATCH)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_settings_controller_gets_account_scoped_import_refresh_bridge(self):
        module = self.load_patch()
        updated = module.patch_settings_refresh_text(SETTINGS_FIXTURE)
        self.assertIn("BUILD124_ARCHIVE_IMPORT_REFRESH1", updated)
        self.assertIn("JerkgramSettingsDidImport", updated)
        self.assertIn("ActionDisposable", updated)
        self.assertIn("rawAccountPeerId.int64Value == accountPeerId", updated)
        self.assertIn("GhostBaseSettingsState.load(accountPeerId: accountPeerId, mirrorLegacy: true)", updated)
        self.assertIn("stateValue.modify", updated)
        self.assertIn("statePromise.set(refreshed)", updated)
        self.assertIn("let jerkgramImportRefreshStateSignal = combineLatest(", updated)
        self.assertIn("statePromise.get(),\n        jerkgramImportRefreshSignal", updated)
        self.assertIn("|> map { state, _ in state }", updated)
        self.assertIn(
            "let signal = combineLatest(context.sharedContext.presentationData, jerkgramImportRefreshStateSignal)",
            updated,
        )
        self.assertNotIn(
            "combineLatest(context.sharedContext.presentationData, statePromise.get(), jerkgramImportRefreshSignal)",
            updated,
        )
        self.assertLess(updated.index("BUILD124_ARCHIVE_IMPORT_REFRESH1"), updated.index("private func ghostBaseSettingsEntries("))

    def test_multiline_controller_signature_does_not_drive_helper_anchor(self):
        module = self.load_patch()
        updated = module.patch_settings_refresh_text(SETTINGS_FIXTURE)
        self.assertIn("public func ghostBaseSettingsController(\n    context: AccountContext,", updated)
        self.assertIn("BUILD124_ARCHIVE_IMPORT_REFRESH1", updated)

    def test_refresh_bridge_handles_a_state_signal_declared_before_atomic_owner(self):
        module = self.load_patch()
        early_signal_fixture = SETTINGS_FIXTURE.replace(
            "    let statePromise = ValuePromise(initialState, ignoreRepeated: true)\n"
            "    let stateValue = Atomic(value: initialState)\n\n"
            "    let signal = combineLatest(context.sharedContext.presentationData, statePromise.get())\n",
            "    let statePromise = ValuePromise(initialState, ignoreRepeated: true)\n\n"
            "    let signal = combineLatest(context.sharedContext.presentationData, statePromise.get())\n",
        ).replace(
            "    |> map { presentationData, state -> (ItemListControllerState, (ItemListNodeState, Any)) in\n"
            "        fatalError()\n"
            "    }\n"
            "    return ItemListController(context: context, state: signal)\n",
            "    |> map { presentationData, state -> (ItemListControllerState, (ItemListNodeState, Any)) in\n"
            "        fatalError()\n"
            "    }\n"
            "    let stateValue = Atomic(value: initialState)\n"
            "    return ItemListController(context: context, state: signal)\n",
        )
        updated = module.patch_settings_refresh_text(early_signal_fixture)
        self.assertIn(
            "let signal = combineLatest(context.sharedContext.presentationData, jerkgramImportRefreshStateSignal)",
            updated,
        )

    def test_success_path_notifies_only_after_persisted_settings_are_projected(self):
        module = self.load_patch()
        replacement = module.REPLACEMENT
        apply_pos = replacement.index("JerkgramArchiveTransaction.apply(")
        project_pos = replacement.index("jerkgramProjectImportedSettingsToActiveDefaults(settings)")
        notify_pos = replacement.index("jerkgramNotifySettingsImported(accountPeerId: accountPeerId)")
        self.assertLess(apply_pos, project_pos)
        self.assertLess(project_pos, notify_pos)
        success_tail = replacement[project_pos:notify_pos + 80]
        self.assertIn("Queue.mainQueue().async", success_tail)

    def test_settings_refresh_patch_is_idempotent(self):
        module = self.load_patch()
        once = module.patch_settings_refresh_text(SETTINGS_FIXTURE)
        self.assertEqual(once, module.patch_settings_refresh_text(once))


if __name__ == "__main__":
    unittest.main()
