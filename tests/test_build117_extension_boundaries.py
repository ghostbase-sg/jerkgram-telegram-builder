import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


def load(name):
    path = ROOT / "scripts" / name
    spec = importlib.util.spec_from_file_location(name[:-3], path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class Build117ExtensionBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.overlay = load("apply_jerkgram_v12f_build117_extension_boundaries1.py")

    def test_classifier_distinguishes_real_shared_and_process_local_paths(self):
        header = "@interface BuildConfig (JerkgramExtensionDiagnostics)\n@end\n"
        implementation = "@implementation BuildConfig (JerkgramExtensionDiagnostics)\n@end\n"
        header, implementation = self.overlay.patch_buildconfig(header, implementation)
        self.assertIn("jerkgramExtensionContainerClassification", header)
        self.assertIn('@"shared"', implementation)
        self.assertIn('@"processLocal"', implementation)
        self.assertIn('/Containers/Shared/AppGroup/', implementation)
        self.assertIn('/Documents/AppGroup', implementation)
        self.assertNotIn("sharedContainerPath ?: @\"\"", implementation)

    def test_share_replaces_white_screen_with_visible_bounded_diagnostic(self):
        source = '''class ShareRootController: UIViewController {
    private var impl: ShareRootControllerImpl?
    let maybeAppGroupUrl = FileManager.default.containerURL(forSecurityApplicationGroupIdentifier: appGroupName)
    guard let appGroupUrl = maybeAppGroupUrl else {
                return
            }
    self.impl = ShareRootControllerImpl(
}
'''
        patched = self.overlay.patch_share(source)
        self.assertIn("BUILD117_SHARE_VISIBLE_DIAGNOSTIC1", patched)
        self.assertIn("showJerkgramExtensionDiagnostic", patched)
        self.assertIn("classification != \"shared\"", patched)
        self.assertIn("prefix(240)", patched)

    def test_widget_returns_diagnostic_timeline_and_renders_it(self):
        source = '''enum Contents {
        case recent
        case preview
        case peers(ParsedPeers)
    }
    guard let appGroupUrl = maybeAppGroupUrl else {
        completion(Timeline(entries: [SimpleEntry(date: entryDate, contents: .recent)], policy: .atEnd))
        return
    }
enum PeersWidgetData {
    case empty
    case preview
    case peers(ParsedPeers)
}
switch contents {
    case .recent:
        return .empty
    case .preview:
        return .preview
    case let .peers(peers):
        return .peers(peers)
    }
@available(iOSApplicationExtension 14.0, iOS 14.0, *)
struct WidgetView: View {
    var body: some View {
        GeometryReader(content: { geometry in
            return VStack(alignment: .center, spacing: 0.0, content: {
                chatContentView(0, size: geometry.size)
                chatSeparatorView(size: geometry.size)
                chatContentView(1, size: geometry.size)
                chatUpdateView(size: geometry.size)
            })
        })
    }
}
struct AvatarsWidgetView: View {
    var body: some View {
        return VStack(alignment: .center, spacing: 18.0, content: {
        })
        .padding(EdgeInsets(top: 10.0, leading: 10.0, bottom: 10.0, trailing: 10.0))
    }
}
'''
        patched = self.overlay.patch_widget(source)
        self.assertIn("BUILD117_WIDGET_VISIBLE_DIAGNOSTIC1", patched)
        self.assertIn("case diagnostic(String)", patched)
        self.assertIn("contents: .diagnostic", patched)
        self.assertIn("JerkgramWidgetDiagnosticView", patched)

    def test_broadcast_reports_boundary_stage_instead_of_finished(self):
        source = '''    private func finishWithError() {
        let errorString = "Finished"
        let error = NSError(domain: "BroadcastUploadExtension", code: 1, userInfo: [
            NSLocalizedDescriptionKey: errorString
        ])
        self.finishBroadcastWithError(error)
    }
        self.finishWithError()
        let maybeAppGroupUrl = FileManager.default.containerURL(forSecurityApplicationGroupIdentifier: appGroupName)
        guard let appGroupUrl = maybeAppGroupUrl else {
            self.finishWithError()
            return
        }
'''
        patched = self.overlay.patch_broadcast(source)
        self.assertIn("BUILD117_BROADCAST_VISIBLE_DIAGNOSTIC1", patched)
        self.assertIn("finishWithError(stage:", patched)
        self.assertNotIn('let errorString = "Finished"', patched)
        self.assertIn("classification != \"shared\"", patched)


if __name__ == "__main__":
    unittest.main()
