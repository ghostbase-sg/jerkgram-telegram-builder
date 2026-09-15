# M1-R4.2 common destination crash

## Result

The failure is common host initialization, not eight page implementations.
R4.2 called UIKit's inherited nib initializer directly on an allocated Swift
`Display.ViewController`. That bypassed the class's designated Swift
initialization of required Display state. The object passed Telegram's runtime
type cast, then failed when its Display lifecycle used that state.

## Production 12.9.4 proof

The real carrier's `TelegramUIFramework.framework/TelegramUIFramework` export
trie contains:

- `_OBJC_CLASS_$__TtC7Display14ViewController`;
- `_$s7Display14ViewControllerC29navigationBarPresentationDataAcA010NavigationefG0CSg_tcfC`.

The latter is the allocating entry point for
`Display.ViewController.init(navigationBarPresentationData:)`. The bundled
verifier reads the production Mach-O export trie directly; it does not infer
this boundary from a historical build.

## R4.3 correction and device result

R4.3 resolved only that exact exported entry point and proved its image owner,
but declared the allocating initializer as a one-parameter `swiftcall` function.
DEVICE-RUNTIME showed that every route still crashed. The omitted parameter was
the hidden class-metatype `swiftself` context required by a Swift allocating
initializer.

## R4.4 correction

The function pointer now has two parameters: the explicit nil Optional reference
and a final `swift_context` class metatype. The call passes the runtime
`_TtC7Display14ViewController` class object as that context. The Apple workflow
emits LLVM IR from the actual Objective-C implementation and rejects the build
unless the call is `swiftcc` and its final argument is marked `swiftself`.

The existing symbol-image and returned-class checks remain fail-closed. All tap,
initializer, child-construction and push boundaries emit monotonic `JGM1Nav`
timings for the same route.

All eight main destinations and all reachable nested destinations use this one
factory. No plain UIKit controller or separate navigation controller is pushed.
If this ABI-correct invocation still crashes on device, investigation stops at
this boundary until the actual iOS `.ips` report is available.

## M1-only limitation

The Build138 Data & Backup UI is retained. Cleanup, export and import require
the final event/media archive owners, which are outside M1; those operations are
inert rather than pretending that a partial settings-only archive is a Build138
archive.
