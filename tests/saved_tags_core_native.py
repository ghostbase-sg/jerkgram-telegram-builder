"""Exact Core helper/provider assembly atop the pinned production SQLite fixture."""
from pathlib import Path
from saved_tags_native import assemble, declaration

def assemble_core(root, source, folder):
    paths = assemble(root, source, folder)
    core=source/'submodules/TelegramCore/Sources/TelegramEngine/Messages'
    service=(core/'LocalSavedTagsService.swift').read_text()
    boundary=folder/'Boundary.swift'
    body=boundary.read_text().replace('    var disposed = false', '''    var fixtureState: AuthorizedAccountState?
    var fixtureMessageReads = 0
    var fixtureMessages: [MessageId: Message] = [:]
    func getState() -> Any? { fixtureState }
    func getMessage(_ id: MessageId) -> Message? { fixtureMessageReads += 1; return fixtureMessages[id] }
    var disposed = false''')
    boundary.write_text(body)
    support=(root/'tests/fixtures/beta2_saved_tags/official/submodules/Postbox/Sources/Message.swift').read_text()
    shell='''import Foundation
final class AuthorizedAccountState { let peerId: PeerId; init(peerId: PeerId) { self.peerId = peerId } }
public final class Message { let id: MessageId; let timestamp: Int32; let threadId: Int64?
init(id: MessageId, timestamp: Int32, threadId: Int64?) { self.id = id; self.timestamp = timestamp; self.threadId = threadId } }
enum Namespaces { enum Message { static let Cloud: Int32 = 0 } }
'''
    shell+=declaration(support,'public enum MessageIdNamespaces:')+'\n'
    shell+='\n'.join(declaration(service,anchor) for anchor in ['public struct LocalSavedTagsSelectionSummary {','public struct LocalSavedTagsContentRow {','public struct LocalSavedTagsContentPage {','public enum LocalSavedTagsPageEvent {', 'final class LocalSavedTagsDelivery {'])
    for name in ['LocalSavedTagsLifecycle.swift','LocalSavedTagsOperations.swift']:
        shell+='\n'+'\n'.join(line for line in (core/name).read_text().splitlines() if not line.startswith('import '))
    signal=(root/'tests/fixtures/beta2_saved_tags/CoreSignalBoundary.swift').read_text()
    signal=signal.replace('/* EXACT_SERVICE_BIND */', declaration(service,'fileprivate func bind<T>'))
    signal=signal.replace('/* EXACT_SERVICE_DISPOSE */', declaration(service,'public func dispose()'))
    signal=signal.replace('/* EXACT_PAGE_PROVIDER */', declaration(service,'public final class LocalSavedTagsPageProvider {'))
    shell+='\n'+signal.replace('import Foundation','')
    (folder/'Core.swift').write_text(shell)
    # Reuse only the tiny identity/SQLite assertion setup, not the accepted
    # store stress suite. Separate mandatory store gate retains all its cases.
    prefix=(folder/'main.swift').read_text().split('if CommandLine.arguments.count == 3')[0]
    reopen='''
if CommandLine.arguments.count == 3 && CommandLine.arguments[2] == "--reopen-process" {
    let (_, reopenedCore) = open("core.sqlite")
    let result = try reopenedCore.catalogue(selfPeerId: peer)
    require(result.totalMembershipCount == 1000 && result.tags.count == 3, "Core fresh process lost committed cleanup/assignment")
    require(result.tags.contains(where: { $0.name == "Changed" && $0.count == 1000 }), "Core fresh process lost renamed catalogue")
    print("PASS fresh-process SQLite reopen")
    exit(0)
}
'''
    (folder/'main.swift').write_text(prefix+reopen+(root/'tests/fixtures/beta2_saved_tags/core-native.swift').read_text())
    return paths+[folder/'Core.swift']
