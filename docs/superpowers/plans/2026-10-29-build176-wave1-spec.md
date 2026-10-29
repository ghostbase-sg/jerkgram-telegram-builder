Продолжай в ЭТОМ ЖЕ Work Local чате и используй завершённый аудит:

`docs/audits/2026-10-29-build175-performance-parity/AUDIT.md`

как source of truth.

Не повторяй аудит. Не исследуй проект заново. Не переходи к новым функциям Jerkgram.

## Цель

Начать фактическое устранение доказанных performance-проблем Build175 с целью приблизить whole-client performance Jerkgram к Swiftgram.

Текущий baseline:

- Jerkgram Build175
- commit `4881f8573e940ff503b7a5d4db6356050098c6a6`
- Telegram iOS 13.1.1
- Swiftgram reference SHA `e3a392272b182dbf975d4ac5fc33b40a5954d749`

Работать строго source-based через builder stages/materializers/hash manifests. Не редактировать случайный materialized tree как конечное решение.

## Реализовать сейчас только первую remediation wave

### PATCH A — Data & Backup ownership cycle

Исправить SP1 из аудита.

Файл:
`submodules/SettingsUI/Sources/Jerkgram/JerkgramDataAndBackupController.swift`

Нужно устранить цикл:

controller → stateSignal → arguments/actions → capture box → controller.

Требование:

- actions используют weak action target;
- сам controller создаётся strong local `let`;
- после construction weak target получает controller;
- strong local возвращается вызывающему коду;
- не использовать опасную схему `weak var controller` + `return controller!`.

Проверить все callbacks:

- export;
- import;
- cleanup;
- cancel;
- completion.

Добавить source/regression tests, доказывающие отсутствие strong cycle настолько, насколько это возможно без device runtime.

---

### PATCH B1 — убрать projection writes с page construction

Исправить SP2a.

Сейчас обычное создание GhostBase Settings page может давать до:

- 49 changed keys;
- 98 compatibility sets;
- +1 suite write;
- 69 caller-thread writes;
- 30 deferred writes;
- hot-cache invalidation;
- visual/blocked policy publication.

Это недопустимо для обычного открытия страницы.

Архитектура:

- legacy/account projection выполняется только при:
  - account activation;
  - migration;
  - import;
  - фактическом изменении setting;
- page constructor только читает готовый immutable snapshot;
- changed-domain equality до setters;
- hot cache invalidation только если реально изменён соответствующий hot key;
- blocked-message notification только если policy реально изменилась;
- playback/style publication только при реальном delta.

Acceptance:

**обычное открытие Settings после завершённой migration → 0 projection writes.**

Сохранить:

- account scoping;
- migration precedence;
- import semantics;
- shared scheduled-send suite;
- compatibility stores.

---

### PATCH B2 — style revision / hidden controller policy

Исправить SP2b.

Не создавать новые global observers.

Использовать существующую observer infrastructure, но:

- visual publication только при реальном visual state change;
- одна coherent revision на batch;
- hidden Settings owners не должны выполнять полный refresh/layout/material recreation;
- hidden owner получает dirty revision;
- reconcile выполняется при appearance;
- same-source/same-style backdrop/material обновляется in-place;
- не remove/create material без необходимости;
- ItemList state emission только при actual revision.

Acceptance:

- 0 visual posts при page-open без visual изменения;
- 0 visual posts при nonvisual setting change;
- максимум 1 visual revision на настоящий visual batch;
- скрытые контроллеры не выполняют full material/layout refresh;
- после возвращения экран получает актуальное состояние.

---

### PATCH C — coherent transparency + video ownership

Исправить V1/SP3/SP5.

Не делать косметический `.90 -> .26` one-liner.

Нужен единый visual contract:

#### Normal mode

Root/nested/list/field surfaces визуально согласованы.

Push на вложенную Settings page не должен внезапно делать интерфейс радикально темнее.

#### Low Power Mode

Не использовать произвольный black `.90` просто потому, что включена экономия.

Снижать дорогую композицию через admission policy:

- animation/video;
- количество одновременно активных effects;
- composition cost.

При этом UI должен оставаться визуально Jerkgram.

#### Reduce Transparency

Уважать accessibility.

Использовать coherent readable opaque/native fallback для всех descendants, а не отдельное значение одного nested backing.

#### Theme/account/master changes

Background/header/panes/metadata/section masks должны получать одну coherent versioned state revision.

#### Video

- same-source update сохраняет session/material;
- replacement: successor получает lease до detach старого;
- account/avatar/identity switch делает явный release/reacquire;
- не создавать второй decoder;
- hidden screen не должен держать unnecessary visible output lease.

Сохранить Build175 exclusions:

- Devices detail;
- emoji popup;
- native modal boundary/dimming/gestures.

---

# Очень важно: НЕ СОБИРАТЬ IPA ПОСЛЕ КАЖДОГО PATCH

A, B1, B2 и C сначала:

1. реализовать;
2. обновить builder stages;
3. обновить exact hashes/manifests;
4. прогнать focused source/materialization/regression tests;
5. провести static review полного composite output.

Только когда вся первая wave проходит проверки — сделать **одну интеграционную Build176 candidate IPA**.

Не запускать четыре тяжёлых CI build подряд.

---

# Build176

Если A/B/C проходят source gates:

- bump только до следующего внутреннего candidate Build176;
- сохранить Telegram 13.1.1 baseline;
- сохранить все существующие Jerkgram функции;
- не добавлять новые функции;
- не менять compiler optimization flags;
- не менять history backend;
- не трогать credentials;
- не менять translation semantics;
- не менять protected/deleted/edit/archive semantics.

Это performance-remediation build.

---

# Instrumentation

Использовать минимальные counters/signposts из Patch I только там, где они нужны для проверки A/B/C.

Default OFF.

Никаких:

- polling;
- permanent CADisplayLink;
- per-frame string formatting;
- новых глобальных observers;
- network telemetry.

Нужны измеримые counters:

- retained DataBackup controllers;
- page-open projection writes;
- hot invalidations;
- visual publications;
- style callbacks;
- material effect creations;
- hidden-owner refreshes;
- active video output leases.

---

# Device validation plan

Подготовить Build176 так, чтобы после установки можно было сравнить Build175 → Build176.

Минимум:

1. cold first Settings open;
2. warm second Settings open;
3. nested Settings;
4. 20 push/pop;
5. 100 push/pop;
6. Data & Backup repeated push/pop;
7. self-profile;
8. foreign profile;
9. static avatar;
10. animated avatar;
11. typing 30–60 sec;
12. scrolling;
13. Low Power ON/OFF;
14. Reduce Transparency ON/OFF.

Не утверждать Swiftgram parity без device measurements.

Но source acceptance для этой wave должен доказать:

- retain cycle устранён;
- ordinary Settings page creation больше не пишет 99 settings API calls;
- no-op visual fanout устранён;
- hidden controller refresh ограничен;
- `.90` больше не является несогласованным nested-only затемнением;
- video ownership transition не имеет старого lease gap.

---

# Что сейчас НЕ делать

Не реализовывать пока:

- Patch D;
- Patch E;
- Patch F;
- Patch G;
- Patch H;
- новые Jerkgram features;
- automatic archive cleanup.

Особенно Patch H/S7 correctness оставить отдельной следующей задачей: cleanup/import race должен быть исправлен до automatic cleanup, но не смешивать его с первой performance wave.

---

# Отчёт

После выполнения дай:

1. новые commit SHA;
2. exact files/stages changed;
3. A/B1/B2/C implementation summary;
4. before/after source counters;
5. test results;
6. Build176 Actions run;
7. IPA artifact;
8. что требуется проверить на iPhone;
9. какие performance findings остаются после первой wave.

Не объявлять задачу «performance fixed» до device validation.

Но если source acceptance A/B/C пройден — зафиксировать это как **Performance Remediation Wave 1 complete**.