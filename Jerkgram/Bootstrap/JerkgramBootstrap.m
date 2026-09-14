#import "JGTelegramSettingsAdapter.h"

__attribute__((constructor))
static void JerkgramProductBootstrap(void) {
    JGInstallTelegram1294SettingsAdapter();
}
