import SwiftUI

// Native SwiftUI DESIGN LAB only. No TelegramCore, persistence or production code.
private enum Launch {
    static let args = ProcessInfo.processInfo.arguments
    static let ghost = args.contains("-labGhost")
    static let expanded = args.contains("-labExpanded")
    static let filters = args.contains("-labFilters")
    static let opaque = args.contains("-labOpaque")
}
private enum Palette {
    static let background = Color(red: 0.055, green: 0.066, blue: 0.085)
    static let accent = Color(red: 0.55, green: 0.74, blue: 1.0)
    static let secondary = Color(red: 0.68, green: 0.72, blue: 0.79)
}
@main
struct JerkgramUILabApp: App {
    var body: some Scene {
        WindowGroup {
            LabRoot()
                .preferredColorScheme(.dark)
                .tint(Palette.accent)
        }
    }
}
private enum Screen: String, Hashable, CaseIterable, Identifiable {
    case ghost, messages, protected, media, appearance, premium, data, about
    var id: String { rawValue }
    var title: String {
        switch self {
        case .ghost: "Режим призрака"
        case .messages: "Сообщения"
        case .protected: "Защищённый контент"
        case .media: "Медиа и истории"
        case .appearance: "Оформление"
        case .premium: "Локальный Premium"
        case .data: "Данные и архив"
        case .about: "О Jerkgram"
        }
    }
    var icon: String {
        switch self {
        case .ghost: "eye.slash.fill"
        case .messages: "bubble.left.and.bubble.right.fill"
        case .protected: "lock.shield.fill"
        case .media: "photo.stack.fill"
        case .appearance: "paintbrush.fill"
        case .premium: "star.fill"
        case .data: "archivebox.fill"
        case .about: "info.circle.fill"
        }
    }
}
private struct LabRoot: View {
    @State private var path: [Screen] = Launch.ghost ? [.ghost] : []
    @State private var translucency = !Launch.opaque
    var body: some View {
        NavigationStack(path: $path) {
            HomeScreen(translucency: $translucency) { path.append($0) }
                .navigationDestination(for: Screen.self) { page in
                    if page == .ghost {
                        GhostScreen(translucency: $translucency)
                    } else {
                        PlaceholderScreen(page: page)
                    }
                }
        }
    }
}
private struct Card<Content: View>: View {
    let translucent: Bool
    let content: Content
    init(_ translucent: Bool, @ViewBuilder content: () -> Content) {
        self.translucent = translucent
        self.content = content()
    }
    var body: some View {
        content
            .background {
                RoundedRectangle(cornerRadius: 21, style: .continuous)
                    .fill(translucent
                          ? AnyShapeStyle(.regularMaterial)
                          : AnyShapeStyle(Color(uiColor: .secondarySystemGroupedBackground)))
            }
            .overlay {
                RoundedRectangle(cornerRadius: 21, style: .continuous)
                    .strokeBorder(Color.white.opacity(0.08), lineWidth: 0.7)
            }
            .clipShape(RoundedRectangle(cornerRadius: 21, style: .continuous))
    }
}
private struct SectionTitle: View {
    let title: String
    var body: some View {
        Text(title.uppercased())
            .font(.system(size: 11, weight: .bold))
            .tracking(1.2)
            .foregroundStyle(Palette.secondary)
            .padding(.horizontal, 12)
    }
}
private struct HomeScreen: View {
    @Binding var translucency: Bool
    let navigate: (Screen) -> Void
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 24) {
                HStack(spacing: 15) {
                    Image(systemName: "paperplane.fill")
                        .font(.system(size: 28))
                        .foregroundStyle(.white)
                        .frame(width: 64, height: 64)
                        .background(LinearGradient(colors: [.cyan.opacity(0.6), .indigo.opacity(0.6)],
                                                   startPoint: .topLeading, endPoint: .bottomTrailing),
                                    in: RoundedRectangle(cornerRadius: 19))
                    VStack(alignment: .leading, spacing: 5) {
                        Text("Jerkgram").font(.system(size: 29, weight: .bold, design: .rounded))
                        Text("Твой Telegram. Твои правила.")
                            .font(.footnote).foregroundStyle(Palette.secondary)
                    }
                }
                .padding(.top, 12)
                homeGroup("Конфиденциальность", [.ghost, .messages, .protected])
                homeGroup("Возможности", [.media, .appearance, .premium])
                homeGroup("Приложение", [.data, .about])
                VStack(alignment: .leading, spacing: 9) {
                    SectionTitle(title: "Интерфейс")
                    Card(translucency) {
                        Toggle("Полупрозрачность настроек", isOn: $translucency)
                            .padding(17).tint(.green)
                    }
                }
                Text("Jerkgram UI Lab · Изменения не затрагивают установленный клиент")
                    .font(.system(size: 11)).foregroundStyle(Palette.secondary)
                    .multilineTextAlignment(.center).frame(maxWidth: .infinity)
            }
            .padding(.horizontal, 17)
            .padding(.bottom, 30)
        }
        .background(Palette.background.ignoresSafeArea())
        .navigationTitle("Настройки")
        .navigationBarTitleDisplayMode(.inline)
    }
    private func homeGroup(_ title: String, _ pages: [Screen]) -> some View {
        VStack(alignment: .leading, spacing: 9) {
            SectionTitle(title: title)
            Card(translucency) {
                VStack(spacing: 0) {
                    ForEach(pages) { page in
                        Button { navigate(page) } label: {
                            HStack(spacing: 13) {
                                Image(systemName: page.icon)
                                    .font(.system(size: 17, weight: .medium))
                                    .foregroundStyle(Palette.accent)
                                    .frame(width: 37, height: 37)
                                    .background(Palette.accent.opacity(0.14), in: RoundedRectangle(cornerRadius: 12))
                                Text(page.title).font(.system(size: 15, weight: .medium))
                                Spacer()
                                Image(systemName: "chevron.right")
                                    .font(.system(size: 11, weight: .semibold))
                                    .foregroundStyle(Palette.secondary)
                            }
                            .padding(13).contentShape(Rectangle())
                        }
                        .buttonStyle(.plain)
                        .accessibilityIdentifier("screen-" + page.rawValue)
                        if page != pages.last {
                            Divider().padding(.leading, 62)
                        }
                    }
                }
            }
        }
    }
}
private struct OptionSwitch: View {
    let title: String
    let subtitle: String
    @Binding var enabled: Bool
    var body: some View {
        Toggle(isOn: $enabled) {
            VStack(alignment: .leading, spacing: 4) {
                Text(title).font(.system(size: 14, weight: .medium))
                Text(subtitle).font(.system(size: 11)).foregroundStyle(Palette.secondary)
            }
        }
        .tint(.green)
        .padding(.vertical, 5)
    }
}
private struct InlineExpansion<Content: View>: View {
    let title: String
    let subtitle: String
    @Binding var enabled: Bool
    @Binding var expanded: Bool
    let content: Content
    init(title: String, subtitle: String,
         enabled: Binding<Bool>, expanded: Binding<Bool>,
         @ViewBuilder content: () -> Content) {
        self.title = title
        self.subtitle = subtitle
        self._enabled = enabled
        self._expanded = expanded
        self.content = content()
    }
    var body: some View {
        VStack(spacing: 0) {
            HStack(spacing: 12) {
                VStack(alignment: .leading, spacing: 5) {
                    Text(title).font(.system(size: 16, weight: .semibold))
                    Text(subtitle).font(.system(size: 11)).foregroundStyle(Palette.secondary)
                }
                Spacer(minLength: 4)
                Toggle(title, isOn: $enabled)
                    .labelsHidden().tint(.green)
                    .accessibilityIdentifier("master-switch")
                Button {
                    withAnimation(.spring(response: 0.36, dampingFraction: 0.86)) {
                        expanded.toggle()
                    }
                } label: {
                    Image(systemName: "chevron.down")
                        .font(.system(size: 15, weight: .semibold))
                        .rotationEffect(.degrees(expanded ? 180 : 0))
                        .frame(width: 36, height: 36)
                        .background(Color.white.opacity(0.08), in: Circle())
                }
                .buttonStyle(.plain)
                .accessibilityIdentifier("inline-expand")
                .accessibilityLabel(expanded ? "Свернуть параметры" : "Раскрыть параметры")
            }
            .padding(16)
            if expanded {
                Divider().padding(.horizontal, 16)
                VStack(alignment: .leading, spacing: 11) { content }
                    .padding(.horizontal, 16)
                    .padding(.vertical, 13)
                    .transition(.opacity.combined(with: .move(edge: .top)))
                    .accessibilityIdentifier("inline-expanded-content")
            }
        }
        .animation(.spring(response: 0.36, dampingFraction: 0.86), value: expanded)
    }
}
private enum GhostRule: String, CaseIterable, Identifiable {
    case global, hide, normal
    var id: String { rawValue }
    var label: String {
        switch self {
        case .global: "Общие правила"
        case .hide: "Скрывать"
        case .normal: "Обычный режим"
        }
    }
}
private struct RuleRow: View {
    let title: String
    @Binding var rule: GhostRule
    var body: some View {
        HStack {
            Text(title).font(.system(size: 14, weight: .medium))
            Spacer(minLength: 4)
            Menu {
                ForEach(GhostRule.allCases) { option in
                    Button {
                        rule = option
                    } label: {
                        if rule == option {
                            Label(option.label, systemImage: "checkmark")
                        } else {
                            Text(option.label)
                        }
                    }
                }
            } label: {
                HStack(spacing: 5) {
                    Text(rule.label).font(.system(size: 11, weight: .semibold))
                    Image(systemName: "chevron.up.chevron.down").font(.system(size: 9))
                }
                .foregroundStyle(Palette.accent)
            }
        }
        .padding(.vertical, 12)
    }
}
private struct GhostScreen: View {
    @Binding var translucency: Bool
    @State private var master = true
    @State private var expanded = Launch.expanded
    @State private var filtersExpanded = Launch.filters
    @State private var read = true
    @State private var typing = true
    @State private var recording = true
    @State private var upload = true
    @State private var online = true
    @State private var stickers = true
    @State private var emojis = true
    @State private var gaming = true
    @State private var contacts: GhostRule = .global
    @State private var others: GhostRule = .hide
    @State private var examplePeer: GhostRule = .global

    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 23) {
                HStack(alignment: .top, spacing: 15) {
                    Image(systemName: "eye.slash.fill")
                        .font(.system(size: 29))
                        .foregroundStyle(Palette.accent)
                        .frame(width: 63, height: 63)
                        .background(Palette.accent.opacity(0.14), in: RoundedRectangle(cornerRadius: 19))
                    VStack(alignment: .leading, spacing: 7) {
                        Text("Приватность под контролем")
                            .font(.system(size: 20, weight: .bold, design: .rounded))
                        Text("Настрой, какие действия видны собеседникам.")
                            .font(.system(size: 12))
                            .foregroundStyle(Palette.secondary)
                    }
                }
                .padding(.top, 13)

                VStack(alignment: .leading, spacing: 9) {
                    SectionTitle(title: "Главная функция")
                    Card(translucency) {
                        InlineExpansion(
                            title: "Режим призрака",
                            subtitle: master ? "Включён · расширенные параметры" : "Выключен · параметры сохранены",
                            enabled: $master, expanded: $expanded
                        ) {
                            OptionSwitch(title: "Не отмечать прочитанным", subtitle: "Не отправлять отметки", enabled: $read)
                            OptionSwitch(title: "Скрывать набор текста", subtitle: "Не показывать индикатор", enabled: $typing)
                            OptionSwitch(title: "Скрывать запись", subtitle: "Голосовые и видеосообщения", enabled: $recording)
                            OptionSwitch(title: "Скрывать загрузку", subtitle: "Индикатор отправки медиа", enabled: $upload)
                            OptionSwitch(title: "Скрывать статус онлайн", subtitle: "Активность и присутствие", enabled: $online)
                            OptionSwitch(title: "Выбор стикеров", subtitle: "Не показывать выбор", enabled: $stickers)
                            OptionSwitch(title: "Выбор эмодзи", subtitle: "Не показывать выбор", enabled: $emojis)
                            OptionSwitch(title: "Игровая активность", subtitle: "Не показывать действия", enabled: $gaming)
                        }
                    }
                    Text("Главный тумблер не сбрасывает внутренние настройки.")
                        .font(.system(size: 11)).foregroundStyle(Palette.secondary)
                        .padding(.horizontal, 12)
                }

                VStack(alignment: .leading, spacing: 9) {
                    SectionTitle(title: "Фильтрация")
                    Card(translucency) {
                        VStack(spacing: 0) {
                            Button {
                                withAnimation(.spring(response: 0.36, dampingFraction: 0.86)) {
                                    filtersExpanded.toggle()
                                }
                            } label: {
                                HStack {
                                    Image(systemName: "slider.horizontal.3")
                                        .foregroundStyle(Palette.accent)
                                        .frame(width: 31)
                                    VStack(alignment: .leading, spacing: 5) {
                                        Text("Правила и исключения")
                                            .font(.system(size: 15, weight: .semibold))
                                        Text("Контакты, остальные и отдельные чаты")
                                            .font(.system(size: 11))
                                            .foregroundStyle(Palette.secondary)
                                    }
                                    Spacer(minLength: 3)
                                    Image(systemName: "chevron.down")
                                        .rotationEffect(.degrees(filtersExpanded ? 180 : 0))
                                }
                                .padding(17).contentShape(Rectangle())
                            }
                            .buttonStyle(.plain)
                            .accessibilityIdentifier("filters-expand")
                            if filtersExpanded {
                                Divider().padding(.horizontal, 16)
                                VStack(spacing: 0) {
                                    RuleRow(title: "Контакты", rule: $contacts)
                                    Divider()
                                    RuleRow(title: "Остальные", rule: $others)
                                    Divider()
                                    RuleRow(title: "Алексей · пример", rule: $examplePeer)
                                    Text("Приоритет: чат → группа → глобальные правила.")
                                        .font(.system(size: 11)).foregroundStyle(Palette.secondary)
                                        .padding(.vertical, 9)
                                }
                                .padding(.horizontal, 16)
                                .transition(.opacity.combined(with: .move(edge: .top)))
                            }
                        }
                        .animation(.spring(response: 0.36, dampingFraction: 0.86), value: filtersExpanded)
                    }
                    Text("Фильтры — концепт. К реальному Ghost Mode пока не подключены.")
                        .font(.system(size: 11)).foregroundStyle(Palette.secondary)
                        .padding(.horizontal, 12)
                }

                VStack(alignment: .leading, spacing: 9) {
                    SectionTitle(title: "Интерфейс")
                    Card(translucency) {
                        Toggle("Полупрозрачность настроек", isOn: $translucency)
                            .padding(17).tint(.green)
                    }
                }
            }
            .padding(.horizontal, 17)
            .padding(.bottom, 32)
        }
        .background(Palette.background.ignoresSafeArea())
        .navigationTitle("Режим призрака")
        .navigationBarTitleDisplayMode(.inline)
    }
}
private struct PlaceholderScreen: View {
    let page: Screen
    var body: some View {
        VStack(spacing: 18) {
            Image(systemName: page.icon)
                .font(.system(size: 43)).foregroundStyle(Palette.accent)
            Text(page.title).font(.title2.bold())
            Text("В дизайн-плане. Первая нативная итерация посвящена Ghost Mode и раскрывающимся настройкам.")
                .font(.subheadline).foregroundStyle(Palette.secondary)
                .multilineTextAlignment(.center).padding(.horizontal, 28)
        }
        .frame(maxWidth: .infinity, maxHeight: .infinity)
        .background(Palette.background.ignoresSafeArea())
        .navigationTitle(page.title)
    }
}
