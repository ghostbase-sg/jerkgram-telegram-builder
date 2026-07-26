#!/usr/bin/env python3
import os
from pathlib import Path

root = Path(os.environ.get("GHOSTBASE_SOURCE_ROOT", "/root/gb_builder/work/swiftgram-src"))
path = root / "submodules/Display/Source/GhostBaseGlass.swift"
path.parent.mkdir(parents=True, exist_ok=True)

content = r'''import Foundation
import UIKit

// MARK: GhostBase v1.1C GLASSCORE1
public enum GhostBaseGlassStyle {
    public static let enabledKey = "GhostBase.Glass.Enabled"

    public static var isEnabled: Bool {
        if let value = UserDefaults.standard.object(forKey: self.enabledKey) as? Bool {
            return value
        }
        return true
    }

    public static var usesReducedEffects: Bool {
        return UIAccessibility.isReduceTransparencyEnabled || ProcessInfo.processInfo.isLowPowerModeEnabled
    }

    public static var backdropOverlayAlpha: CGFloat {
        if !self.isEnabled {
            return 1.0
        }
        return self.usesReducedEffects ? 0.78 : 0.52
    }

    public static var coldSurfaceAlpha: CGFloat {
        if !self.isEnabled {
            return 1.0
        }
        return self.usesReducedEffects ? 0.92 : 0.70
    }

    public static var lightweightSurfaceAlpha: CGFloat {
        if !self.isEnabled {
            return 1.0
        }
        return self.usesReducedEffects ? 0.96 : 0.82
    }

    public static var borderAlpha: CGFloat {
        return self.usesReducedEffects ? 0.08 : 0.20
    }

    public static let compactCornerRadius: CGFloat = 13.0
    public static let cardCornerRadius: CGFloat = 18.0

    public static func coldFillColor(_ base: UIColor) -> UIColor {
        guard self.isEnabled else {
            return base
        }
        return base.withAlphaComponent(self.coldSurfaceAlpha)
    }

    public static func lightweightFillColor(_ base: UIColor) -> UIColor {
        guard self.isEnabled else {
            return base
        }
        return base.withAlphaComponent(self.lightweightSurfaceAlpha)
    }

    public static func borderColor(_ base: UIColor) -> UIColor {
        guard self.isEnabled else {
            return .clear
        }
        return base.withAlphaComponent(self.borderAlpha)
    }
}
'''

if path.exists() and "GhostBase v1.1C GLASSCORE1" in path.read_text(encoding="utf-8"):
    print("[V11C] GLASSCORE1 already installed")
else:
    path.write_text(content, encoding="utf-8")
    print("[V11C] GLASSCORE1 shared performance tokens installed")
