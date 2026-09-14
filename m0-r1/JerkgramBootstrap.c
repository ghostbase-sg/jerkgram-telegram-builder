static volatile unsigned int jerkgram_m0_bootstrap_state = 0;

__attribute__((used, visibility("default")))
const char JerkgramM0BootstrapMarker[] = "JG M0 PRODUCT BOOTSTRAP R1";

__attribute__((constructor, used))
static void JerkgramM0Bootstrap(void) {
    if (jerkgram_m0_bootstrap_state == 0) {
        jerkgram_m0_bootstrap_state = 1;
    }
}
