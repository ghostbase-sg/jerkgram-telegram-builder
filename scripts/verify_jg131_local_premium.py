"""Exact Hub owners, plus every prior contract on its restored recovery source."""
from pathlib import Path
from materialize_jg131_local_premium import verify_hub, parent_source_view
from verify_jg131_beta2_recovery import verify_source as verify_recovery_source

ROOT = Path(__file__).resolve().parents[1]


def verify_source(source):
    source = Path(source)
    verify_hub(source)
    with parent_source_view(source) as parent:
        verify_recovery_source(parent)
    print('Local Premium exact Hub and restored recovery contracts PASS; native/app/device evidence separate', flush=True)


if __name__ == '__main__':
    import sys
    verify_source(Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'work/swiftgram-src')
