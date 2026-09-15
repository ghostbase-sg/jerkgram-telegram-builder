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

## Correction

`JGCreateSettingsHost` now resolves only that exact exported entry point,
requires it to originate in `TelegramUIFramework`, invokes it using Swift's
calling convention with a nil Optional reference, transfers ownership to ARC,
and verifies that the returned object is a runtime Display controller. Failure
at any check returns nil and performs no push.

All eight main destinations and all reachable nested destinations use this one
factory. No plain UIKit controller or separate navigation controller is pushed.

## M1-only limitation

The Build138 Data & Backup UI is retained. Cleanup, export and import require
the final event/media archive owners, which are outside M1; those operations are
inert rather than pretending that a partial settings-only archive is a Build138
archive.
