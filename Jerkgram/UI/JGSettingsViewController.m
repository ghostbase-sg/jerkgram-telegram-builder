#import "JGSettingsViewController.h"
#import "JGSettingsStore.h"
#import "JGStrings.h"

@interface JGAboutViewController : UITableViewController
@property(nonatomic, copy) NSString *accountPeerId;
- (instancetype)initWithAccountPeerId:(NSString *)accountPeerId;
@end

@implementation JGAboutViewController
- (instancetype)initWithAccountPeerId:(NSString *)accountPeerId {
    self = [super initWithStyle:UITableViewStyleInsetGrouped];
    if (self) { _accountPeerId = [accountPeerId copy]; }
    return self;
}
- (void)viewDidLoad {
    [super viewDidLoad];
    self.title = JGString(@"section.about");
}
- (NSInteger)numberOfSectionsInTableView:(UITableView *)tableView { return 2; }
- (NSInteger)tableView:(UITableView *)tableView numberOfRowsInSection:(NSInteger)section { return section == 0 ? 2 : 1; }
- (NSString *)tableView:(UITableView *)tableView titleForHeaderInSection:(NSInteger)section {
    return section == 0 ? JGString(@"section.about") : JGString(@"about.account");
}
- (UITableViewCell *)tableView:(UITableView *)tableView cellForRowAtIndexPath:(NSIndexPath *)indexPath {
    UITableViewCell *cell = [[UITableViewCell alloc] initWithStyle:UITableViewCellStyleDefault reuseIdentifier:nil];
    cell.selectionStyle = UITableViewCellSelectionStyleNone;
    if (indexPath.section == 0 && indexPath.row == 0) {
        cell.textLabel.text = @"Jerkgram 1.0.2";
    } else if (indexPath.section == 0) {
        cell.textLabel.text = @"Telegram 12.9.4";
    } else {
        cell.textLabel.text = self.accountPeerId;
        cell.textLabel.font = [UIFont monospacedDigitSystemFontOfSize:15.0 weight:UIFontWeightRegular];
    }
    return cell;
}
@end

@interface JGSettingsViewController ()
@property(nonatomic) int64_t accountPeerId;
@property(nonatomic) NSArray<NSString *> *sections;
@property(nonatomic) NSDictionary<NSString *, NSString *> *sectionTitleKeys;
@property(nonatomic) NSDictionary<NSString *, NSArray<JGSettingDescriptor *> *> *itemsBySection;
@end

@implementation JGSettingsViewController
- (instancetype)initWithAccountPeerId:(int64_t)peerId {
    self = [super initWithStyle:UITableViewStyleInsetGrouped];
    if (self) { _accountPeerId = peerId; }
    return self;
}
- (void)viewDidLoad {
    [super viewDidLoad];
    self.title = @"Jerkgram";
    self.navigationItem.largeTitleDisplayMode = UINavigationItemLargeTitleDisplayModeNever;
    [[JGSettingsStore sharedStore] activateAccountPeerId:self.accountPeerId];
    self.sections = @[@"Ghost Mode", @"Messages", @"Protected Content", @"Stories / Media", @"Profile", @"Appearance", @"Other", @"About"];
    self.sectionTitleKeys = @{
        @"Ghost Mode": @"section.ghost", @"Messages": @"section.messages",
        @"Protected Content": @"section.protected", @"Stories / Media": @"section.stories",
        @"Profile": @"section.profile", @"Appearance": @"section.appearance",
        @"Other": @"section.other", @"About": @"section.about"
    };
    NSMutableDictionary *grouped = [NSMutableDictionary dictionary];
    for (NSString *name in self.sections) { grouped[name] = [NSMutableArray array]; }
    for (JGSettingDescriptor *descriptor in JGSettingDescriptor.allDescriptors) {
        [(NSMutableArray *)grouped[descriptor.section] addObject:descriptor];
    }
    self.itemsBySection = grouped;
}
- (NSInteger)numberOfSectionsInTableView:(UITableView *)tableView { return self.sections.count; }
- (NSInteger)tableView:(UITableView *)tableView numberOfRowsInSection:(NSInteger)section {
    NSString *name = self.sections[section];
    return [name isEqualToString:@"About"] ? 1 : self.itemsBySection[name].count;
}
- (NSString *)tableView:(UITableView *)tableView titleForHeaderInSection:(NSInteger)section {
    NSString *name = self.sections[section];
    return JGString(self.sectionTitleKeys[name]);
}
- (JGSettingDescriptor *)descriptorAtIndexPath:(NSIndexPath *)indexPath {
    NSString *name = self.sections[indexPath.section];
    if ([name isEqualToString:@"About"]) return nil;
    NSArray *items = self.itemsBySection[name];
    return indexPath.row < items.count ? items[indexPath.row] : nil;
}
- (NSString *)displayValueForDescriptor:(JGSettingDescriptor *)descriptor {
    NSInteger value = [[JGSettingsStore sharedStore] integerForKey:descriptor.key];
    if ([descriptor.key isEqualToString:@"jerkgram.global.DownloadBoost"]) {
        return value <= 0 ? JGString(@"boost.off") : (value == 1 ? JGString(@"boost.medium") : JGString(@"boost.maximum"));
    }
    if ([descriptor.key isEqualToString:@"jerkgram.Messages.DeletedMediaCacheLimit"]) {
        double gib = (double)value / 1073741824.0;
        return [NSString stringWithFormat:@"%.1f GiB", gib];
    }
    return [NSString stringWithFormat:@"%ld", (long)value];
}
- (UITableViewCell *)tableView:(UITableView *)tableView cellForRowAtIndexPath:(NSIndexPath *)indexPath {
    NSString *sectionName = self.sections[indexPath.section];
    if ([sectionName isEqualToString:@"About"]) {
        UITableViewCell *cell = [[UITableViewCell alloc] initWithStyle:UITableViewCellStyleSubtitle reuseIdentifier:nil];
        cell.textLabel.text = JGString(@"about.jerkgram");
        cell.detailTextLabel.text = JGString(@"about.base");
        cell.accessoryType = UITableViewCellAccessoryDisclosureIndicator;
        return cell;
    }
    JGSettingDescriptor *descriptor = [self descriptorAtIndexPath:indexPath];
    UITableViewCell *cell = [[UITableViewCell alloc] initWithStyle:UITableViewCellStyleValue1 reuseIdentifier:nil];
    cell.textLabel.text = JGString(descriptor.labelKey);
    if (descriptor.type == JGSettingValueTypeBool) {
        UISwitch *toggle = [UISwitch new];
        toggle.on = [[JGSettingsStore sharedStore] boolForKey:descriptor.key];
        toggle.accessibilityIdentifier = descriptor.key;
        [toggle addTarget:self action:@selector(toggleChanged:) forControlEvents:UIControlEventValueChanged];
        cell.accessoryView = toggle;
        cell.selectionStyle = UITableViewCellSelectionStyleNone;
    } else {
        cell.detailTextLabel.text = [self displayValueForDescriptor:descriptor];
        cell.accessoryType = UITableViewCellAccessoryDisclosureIndicator;
    }
    return cell;
}
- (void)toggleChanged:(UISwitch *)sender {
    NSString *key = sender.accessibilityIdentifier;
    if (key.length != 0) [[JGSettingsStore sharedStore] setBool:sender.isOn forKey:key];
}
- (void)tableView:(UITableView *)tableView didSelectRowAtIndexPath:(NSIndexPath *)indexPath {
    [tableView deselectRowAtIndexPath:indexPath animated:YES];
    NSString *sectionName = self.sections[indexPath.section];
    if ([sectionName isEqualToString:@"About"]) {
        NSString *account = [JGSettingsStore sharedStore].activeAccountPeerId ?: @"—";
        [self.navigationController pushViewController:[[JGAboutViewController alloc] initWithAccountPeerId:account] animated:YES];
        return;
    }
    JGSettingDescriptor *descriptor = [self descriptorAtIndexPath:indexPath];
    if (descriptor.type != JGSettingValueTypeInteger) return;
    if ([descriptor.key isEqualToString:@"jerkgram.global.DownloadBoost"]) {
        UIAlertController *sheet = [UIAlertController alertControllerWithTitle:JGString(descriptor.labelKey) message:nil preferredStyle:UIAlertControllerStyleActionSheet];
        NSArray *labels = @[JGString(@"boost.off"), JGString(@"boost.medium"), JGString(@"boost.maximum")];
        for (NSInteger value=0; value<3; value++) {
            [sheet addAction:[UIAlertAction actionWithTitle:labels[value] style:UIAlertActionStyleDefault handler:^(__unused UIAlertAction *action) {
                [[JGSettingsStore sharedStore] setInteger:value forKey:descriptor.key];
                [self.tableView reloadRowsAtIndexPaths:@[indexPath] withRowAnimation:UITableViewRowAnimationNone];
            }]];
        }
        [sheet addAction:[UIAlertAction actionWithTitle:JGString(@"action.cancel") style:UIAlertActionStyleCancel handler:nil]];
        UIPopoverPresentationController *popover = sheet.popoverPresentationController;
        if (popover) { popover.sourceView = self.view; popover.sourceRect = [tableView rectForRowAtIndexPath:indexPath]; }
        [self presentViewController:sheet animated:YES completion:nil];
        return;
    }
    UIAlertController *alert = [UIAlertController alertControllerWithTitle:JGString(descriptor.labelKey) message:nil preferredStyle:UIAlertControllerStyleAlert];
    [alert addTextFieldWithConfigurationHandler:^(UITextField *field) {
        field.keyboardType = UIKeyboardTypeNumberPad;
        field.placeholder = JGString(@"value.enter");
        field.text = [NSString stringWithFormat:@"%ld", (long)[[JGSettingsStore sharedStore] integerForKey:descriptor.key]];
    }];
    [alert addAction:[UIAlertAction actionWithTitle:JGString(@"action.cancel") style:UIAlertActionStyleCancel handler:nil]];
    [alert addAction:[UIAlertAction actionWithTitle:JGString(@"action.save") style:UIAlertActionStyleDefault handler:^(__unused UIAlertAction *action) {
        NSInteger value = alert.textFields.firstObject.text.integerValue;
        [[JGSettingsStore sharedStore] setInteger:value forKey:descriptor.key];
        [self.tableView reloadRowsAtIndexPaths:@[indexPath] withRowAnimation:UITableViewRowAnimationNone];
    }]];
    [self presentViewController:alert animated:YES completion:nil];
}
@end
