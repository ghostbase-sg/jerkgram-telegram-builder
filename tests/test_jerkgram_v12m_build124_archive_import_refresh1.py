from pathlib import Path
import importlib.util
import unittest


REPO = Path(__file__).resolve().parents[1]
PATCH = REPO / "scripts/apply_jerkgram_v12m_build124_archive_import_runtime1.py"

SETTINGS_FIXTURE = '''import Foundation
import SwiftSignalKit

// MARK: Jerkgram v1.2L BUILD123_ACCOUNT_SETTINGS_OWNER1
private struct GhostBaseSettingsState: Equatable {
    static func load(accountPeerId: Int64, mirrorLegacy: Bool) -> GhostBaseSettingsState {
        return GhostBaseSettingsState()
    }
}

public func ghostBaseSettingsController(
    context: AccountContext
) -> ViewController {
    return ghostBaseSettingsPageController(
        context: context,
        page: .root
    )
}

private func ghostBaseSettingsPageController(
    context: AccountContext,
    page: GhostBaseSettingsPage
) -> ViewController {
    let accountPeerId = context.account.peerId.toInt64()
    let initialState = GhostBaseSettingsState.load(accountPeerId: accountPeerId, mirrorLegacy: true)
    let statePromise = ValuePromise(initialState, ignoreRepeated: true)
    let stateValue = Atomic(value: initialState)

    // Build123 may already compose unrelated runtime data here. Build124 must
    // preserve this pipeline instead of assuming a two-signal combineLatest.
    let auxiliarySignal = Signal<Int, NoError>.single(1)
    let signal = combineLatest(
        context.sharedContext.presentationData,
        statePromise.get(),
        auxiliarySignal
    )
    |> deliverOnMainQueue
    |> map { presentationData, state, auxiliary -> (ItemListControllerState, (ItemListNodeState, Any)) in
        _ = auxiliary
        fatalError()
    }

    let controller = ItemListController(
        context: context,
        state: signal
    )
    return controller
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
        self.assertIn("jerkgramImportRefreshSignal", updated)
        self.assertIn("let stateSignal = combineLatest(", updated)
        self.assertIn("combineLatest(stateSignal, jerkgramImportRefreshSignal)", updated)
        self.assertIn("|> map { value, _ in value }", updated)
        self.assertLess(
            updated.index("BUILD124_ARCHIVE_IMPORT_REFRESH1"),
            updated.index("private func ghostBaseSettingsPageController("),
        )

    def test_existing_build123_state_pipeline_is_preserved_verbatim_except_local_name(self):
        module = self.load_patch()
        updated = module.patch_settings_refresh_text(SETTINGS_FIXTURE)
        self.assertIn("        statePromise.get(),\n        auxiliarySignal\n    )", updated)
        self.assertIn("|> map { presentationData, state, auxiliary ->", updated)
        self.assertNotIn("presentationData, state, _ ->", updated)
        self.assertNotIn("combineLatest(context.sharedContext.presentationData, statePromise.get(), jerkgramImportRefreshSignal)", updated)

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
