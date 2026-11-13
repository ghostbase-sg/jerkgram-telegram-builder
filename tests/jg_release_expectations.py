"""Explicit product identity expectations; historical source identities stay pinned."""
def candidate_identity(config):
    stages = config.get('post180_stages', [])
    if stages:
        if stages not in (['post180-history-wallet'], ['post180-history-wallet', 'post180-local-appearance']):
            raise AssertionError('Unknown post180 product successor chain')
        return ('1.2.0 Beta 2', '1.2.0-beta.2', 181, 'BETA2')
    return ('1.2.0 Beta 3', '1.2.0-beta.3', 180, 'BETA3')
