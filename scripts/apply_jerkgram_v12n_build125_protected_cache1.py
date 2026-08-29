#!/usr/bin/env python3
from pathlib import Path
import os

ROOT = Path(os.environ.get("JERKGRAM_SOURCE_ROOT", os.environ.get("GHOSTBASE_SOURCE_ROOT", str(Path.cwd())))).resolve()
TARGET = ROOT / "submodules/TelegramUI/Sources/ChatControllerForwardMessages.swift"
MARKER = "// MARK: Jerkgram v1.2N BUILD125_PROTECTED_FORWARD_CACHE_FIRST1"

def require(value, message):
    if not value:
        raise RuntimeError("[Build125 protected cache] " + message)

def fixture():
    return '''// MARK: Jerkgram v1.2M BUILD124_PROTECTED_FORWARD_LOCAL_COPY1
private func jerkgramProtectedResourceData(context: AccountContext, resource: TelegramMediaResource) -> Signal<EngineMediaResource.ResourceData, NoError> {
    return Signal { subscriber in
        let fetchDisposable = context.engine.resources.fetch(reference: ref, userLocation: .peer(peer), userContentType: type).start()
        let dataDisposable = context.engine.resources.data(resource: EngineMediaResource(resource), pathExtension: nil, waitUntilFetchStatus: true).start(next: { data in
            if data.isComplete { subscriber.putNext(data); subscriber.putCompletion() }
        })
        return ActionDisposable { fetchDisposable.dispose(); dataDisposable.dispose() }
    }
    |> take(1)
}
'''

def patch_text(text):
    if MARKER in text:
        return text
    require(text.count("BUILD124_PROTECTED_FORWARD_LOCAL_COPY1") == 1, "Build124 protected-forward owner missing")
    old = '''    return Signal { subscriber in
        let fetchDisposable = context.engine.resources.fetch(
            reference: mediaReference.resourceReference(resource),
            userLocation: .peer(message.id.peerId),
            userContentType: userContentType
        ).start()
        let dataDisposable = context.engine.resources.data(
            resource: EngineMediaResource(resource),
            pathExtension: pathExtension,
            waitUntilFetchStatus: true
        ).start(next: { data in
            if data.isComplete {
                subscriber.putNext(data)
                subscriber.putCompletion()
            }
        }, completed: {
            subscriber.putCompletion()
        })
        return ActionDisposable {
            fetchDisposable.dispose()
            dataDisposable.dispose()
        }
    }
    |> take(1)'''
    new = '''    // MARK: Jerkgram v1.2N BUILD125_PROTECTED_FORWARD_CACHE_FIRST1
    // A viewed private/protected post is normally already in MediaBox. Reuse
    // that completed local file before attempting a server fetch: the latter
    // is rejected for no-forward channels and led to the red failure state.
    return context.engine.resources.data(
        resource: EngineMediaResource(resource),
        pathExtension: pathExtension,
        waitUntilFetchStatus: false
    )
    |> take(1)
    |> mapToSignal { cachedData -> Signal<EngineMediaResource.ResourceData, NoError> in
        if cachedData.isComplete {
            return .single(cachedData)
        }
        return Signal { subscriber in
            let fetchDisposable = context.engine.resources.fetch(
                reference: mediaReference.resourceReference(resource),
                userLocation: .peer(message.id.peerId),
                userContentType: userContentType
            ).start()
            let dataDisposable = context.engine.resources.data(
                resource: EngineMediaResource(resource),
                pathExtension: pathExtension,
                waitUntilFetchStatus: true
            ).start(next: { data in
                if data.isComplete {
                    subscriber.putNext(data)
                    subscriber.putCompletion()
                }
            }, completed: {
                subscriber.putCompletion()
            })
            return ActionDisposable {
                fetchDisposable.dispose()
                dataDisposable.dispose()
            }
        }
        |> take(1)
    }'''
    if old not in text:
        # Compact fixture used by regression tests.
        old = '''    return Signal { subscriber in
        let fetchDisposable = context.engine.resources.fetch(reference: ref, userLocation: .peer(peer), userContentType: type).start()
        let dataDisposable = context.engine.resources.data(resource: EngineMediaResource(resource), pathExtension: nil, waitUntilFetchStatus: true).start(next: { data in
            if data.isComplete { subscriber.putNext(data); subscriber.putCompletion() }
        })
        return ActionDisposable { fetchDisposable.dispose(); dataDisposable.dispose() }
    }
    |> take(1)'''
        new = '''    // MARK: Jerkgram v1.2N BUILD125_PROTECTED_FORWARD_CACHE_FIRST1
    return context.engine.resources.data(resource: EngineMediaResource(resource), pathExtension: nil, waitUntilFetchStatus: false)
    |> take(1)
    |> mapToSignal { cachedData -> Signal<EngineMediaResource.ResourceData, NoError> in
        if cachedData.isComplete { return .single(cachedData) }
        return Signal { subscriber in
            let fetchDisposable = context.engine.resources.fetch(reference: ref, userLocation: .peer(peer), userContentType: type).start()
            let dataDisposable = context.engine.resources.data(resource: EngineMediaResource(resource), pathExtension: nil, waitUntilFetchStatus: true).start(next: { data in
                if data.isComplete { subscriber.putNext(data); subscriber.putCompletion() }
            })
            return ActionDisposable { fetchDisposable.dispose(); dataDisposable.dispose() }
        } |> take(1)
    }'''
    require(text.count(old) == 1, "protected resource fetch owner missing")
    return text.replace(old, new, 1)

def main():
    TARGET.write_text(patch_text(TARGET.read_text(encoding="utf-8")), encoding="utf-8")
    print("[Build125 protected cache] GREEN")

if __name__ == "__main__":
    main()
