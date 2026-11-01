for mask in 0..<16 {
    let optIn = mask & 1 != 0
    let master = mask & 2 != 0
    let enabled = mask & 4 != 0
    let reduce = mask & 8 != 0
    assert(JerkgramSettingsMaterialPolicy.active(optIn: optIn, master: master, enabled: enabled, reduceTransparency: reduce) == (optIn && master && enabled && !reduce))
}
for lowPower in [false, true] {
    // Low Power is deliberately outside the tint policy: both paths call the same production function.
    _ = lowPower
    assert(JerkgramSettingsMaterialPolicy.itemAlpha(isDark: true) == 0.34)
    assert(JerkgramSettingsMaterialPolicy.itemAlpha(isDark: false) == 0.26)
    assert(JerkgramSettingsMaterialPolicy.cardAlpha(isDark: true) == 0.60)
    assert(JerkgramSettingsMaterialPolicy.cardAlpha(isDark: false) == 0.70)
}
