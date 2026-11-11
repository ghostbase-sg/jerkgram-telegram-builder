"""Verify exact candidate, then structural contracts on restored Build179."""
from pathlib import Path
from materialize_jg131_wave2a1 import verify_wave2a1, parent_source_view
from materialize_jg131_saved_tags import verify_tags


def verify_source(source):
    verify_wave2a1(source)
    with parent_source_view(source) as parent:
        verify_tags(parent)
    print('Wave2A1 exact two owners and restored Build179 structural contracts PASS; behavior/native/app/device are separate gates', flush=True)


if __name__ == '__main__':
    verify_source(Path(__file__).resolve().parents[1] / 'work/swiftgram-src')
