"""Explicit product identity expectations; historical source identities stay pinned."""
def candidate_identity(config):
    stable = config.get('post181_stages', [])
    if stable and 'post181-stable182-identity' in stable:
        if stable not in (['post181-performance-wave2a3', 'post181-bot-native-history-send', 'post181-unified-local-premium', 'post181-local-gram-balance', 'post181-stable182-identity'], ['post181-performance-wave2a3', 'post181-bot-native-history-send', 'post181-unified-local-premium', 'post181-local-gram-balance', 'post181-stable182-identity', 'post181-gram-presentation-completion']):
            raise AssertionError('Unknown Stable182 successor chain')
        return ('1.2.0 Stable', '1.2.0', 182, 'STABLE')
    stages = config.get('post180_stages', [])
    if stages:
        if stages not in (['post180-history-wallet'], ['post180-history-wallet', 'post180-local-appearance'], ['post180-history-wallet', 'post180-local-appearance', 'post180-performance-wave2a2']):
            raise AssertionError('Unknown post180 product successor chain')
        return ('1.2.0 Beta 2', '1.2.0-beta.2', 181, 'BETA2')
    return ('1.2.0 Beta 3', '1.2.0-beta.3', 180, 'BETA3')
