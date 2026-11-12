"""Apply reviewed Beta3 source-native successors after the exact32-stage baseline."""
from pathlib import Path
from jg132_baseline import require_genuine, verify_source as verify_baseline
from jg132_beta3_stages import apply_all, is_present, verify_source

ROOT = Path(__file__).resolve().parents[1]


def main():
    source = ROOT / 'work/swiftgram-src'
    require_genuine(source)
    if not is_present(source) and verify_baseline(source) != 32:
        raise RuntimeError('Beta3 requires the complete accepted32-stage baseline')
    apply_all(source)
    verify_source(source)


if __name__ == '__main__':
    main()
