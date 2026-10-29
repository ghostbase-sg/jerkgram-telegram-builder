// This fixture is appended to the exact production policy extraction by runner.
func expect(_ value: Bool, _ message: String) { precondition(value, message) }
expect(JerkgramVisualPolicy.allowsTransparency(reduceTransparency: false), "normal remains transparent")
expect(JerkgramVisualPolicy.allowsTransparency(reduceTransparency: false), "Low Power preserves surface identity")
expect(!JerkgramVisualPolicy.allowsTransparency(reduceTransparency: true), "accessibility opaque descendants")
expect(JerkgramVisualPolicy.allowsMotion(lowPower: false, reduceTransparency: false), "normal motion")
expect(!JerkgramVisualPolicy.allowsMotion(lowPower: true, reduceTransparency: false), "Low Power blocks output")
expect(!JerkgramVisualPolicy.allowsMotion(lowPower: false, reduceTransparency: true), "accessibility blocks output")
expect(!JerkgramVisualPolicy.shouldReconcile(visible: false, applied: 0, current: 1, dirty: true), "hidden owner defers")
expect(JerkgramVisualPolicy.shouldReconcile(visible: true, applied: 0, current: 1, dirty: true), "appearance catches up")
expect(!JerkgramVisualPolicy.shouldReconcile(visible: true, applied: 1, current: 1, dirty: false), "no-op no refresh")
print("production visual policy fixtures passed")
