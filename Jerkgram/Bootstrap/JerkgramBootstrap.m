#import "JGTelegramSettingsAdapter.h"
#import <Foundation/Foundation.h>

__attribute__((constructor))
static void JerkgramM1Bootstrap(void) {
    dispatch_async(dispatch_get_main_queue(), ^{
        JGInstallTelegram1294SettingsAdapter();
    });
}
