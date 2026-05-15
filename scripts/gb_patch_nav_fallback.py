from pathlib import Path

p = Path("work/swiftgram-src/submodules/ChatListUI/Sources/ChatListController.swift")
s = p.read_text()

if "fileprivate var gbNavigationController" in s:
    print("v0.9B nav fallback already patched")
    raise SystemExit(0)

marker = """// MARK: Swiftgram
extension ChatListControllerImpl {

"""

if marker not in s:
    raise SystemExit("ChatListControllerImpl Swiftgram extension marker not found")

repls = {
    "self.navigationController as? NavigationController": "self.gbNavigationController",
    "self?.navigationController as? NavigationController": "self?.gbNavigationController",
    "strongSelf.navigationController as? NavigationController": "strongSelf.gbNavigationController",
}

changed = 0
for old, new in repls.items():
    c = s.count(old)
    if c:
        print(f"replace {c}: {old}")
        s = s.replace(old, new)
        changed += c

if changed == 0:
    raise SystemExit("no navigation casts replaced")

helper = """// MARK: Swiftgram
extension ChatListControllerImpl {
    fileprivate var gbNavigationController: NavigationController? {
        if let navigationController = self.navigationController as? NavigationController {
            return navigationController
        }
        if let navigationController = self.context.sharedContext.mainWindow?.viewController as? NavigationController {
            return navigationController
        }
        return nil
    }

"""

s = s.replace(marker, helper, 1)

p.write_text(s)
print("v0.9B nav fallback patch OK")
