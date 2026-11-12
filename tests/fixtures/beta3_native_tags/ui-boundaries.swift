import UIKit

// Real UIKit SDK checks button APIs. Display boundaries preserve its actual
// distinct ViewController / UINavigationController hierarchy; this is not a
// substitute for compiling the complete TelegramUI module.
protocol ContainableController {}
class ViewController: UIViewController, ContainableController {}
struct MessageId {}
struct Theme {}
struct PresentationData { let theme = Theme() }
final class PresentationValue {
    func with<T>(_ body: (PresentationData) -> T) -> T { body(PresentationData()) }
}
struct NavigationControllerTheme {
    init(presentationTheme: Theme) {}
}
class NavigationController: UINavigationController, ContainableController {
    enum Mode { case single }
    init(mode: Mode, theme: NavigationControllerTheme) { super.init(nibName: nil, bundle: nil) }
    required init?(coder: NSCoder) { fatalError() }
}
struct PresentationSurfaceLevel { static let root = PresentationSurfaceLevel() }
final class Window1 {
    func present(_ controller: ContainableController, on level: PresentationSurfaceLevel) {}
}
final class SharedContext {
    let currentPresentationData = PresentationValue()
    let mainWindow: Window1? = Window1()
}
final class AccountContext { let sharedContext = SharedContext() }
final class JerkgramSavedTagsController: ViewController {
    init(context: AccountContext, selectedIds: [MessageId]) { super.init(nibName: nil, bundle: nil) }
    required init?(coder: NSCoder) { fatalError() }
}
enum Font { static func medium(_ size: CGFloat) -> UIFont { .systemFont(ofSize: size, weight: .medium) } }
struct FixtureTag { let id: String; let name: String; let count: Int32 }
struct FixtureCatalogue { let tags: [FixtureTag] }
final class StripFixture {
    /* EXACT_LOCAL_BUTTON */
    /* EXACT_LOCAL_TAGS_STORAGE */
    func receive(_ catalogue: FixtureCatalogue) {
        /* EXACT_LOCAL_TAGS_ASSIGNMENT */
    }
}
/* EXACT_FACTORY */
/* EXACT_PRESENTATION */
