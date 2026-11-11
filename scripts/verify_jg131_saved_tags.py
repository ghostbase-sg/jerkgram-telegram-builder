"""Exact Tags owners and immutable Hub/recovery/BOT contracts on restored views."""
from pathlib import Path
from materialize_jg131_saved_tags import verify_tags, parent_source_view
from verify_jg131_local_premium import verify_source as verify_hub_source

ROOT = Path(__file__).resolve().parents[1]


def verify_source(source):
    source = Path(source)
    verify_tags(source)
    with parent_source_view(source) as parent:
        verify_hub_source(parent)
    print('Saved Tags exact owners and restored Hub contracts PASS; native/app/device evidence separate', flush=True)


if __name__ == '__main__':
    import sys
    verify_source(Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'work/swiftgram-src')
