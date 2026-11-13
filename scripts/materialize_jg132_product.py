"""One clean source projection for the current product, without historical test replay."""
from pathlib import Path
import json, subprocess
from jg132_baseline import require_genuine, apply_range, verify_source as verify_baseline
from jg132_beta3_stages import apply_all as apply_beta3
from jg132_post180 import apply_all as apply_post180
from jg132_post181 import apply_all as apply_post181
ROOT = Path(__file__).resolve().parents[1]

def materialize(source):
    source = Path(source).resolve()
    require_genuine(source)
    if subprocess.check_output(['git', 'status', '--porcelain'], cwd=source):
        raise RuntimeError('Product materialization requires clean pinned upstream')
    apply_range(source, 1, 32)
    if verify_baseline(source) != 32:
        raise RuntimeError('Product requires complete historical baseline')
    apply_beta3(source)
    apply_post180(source)
    apply_post181(source)
    from configure_jg13 import configure_build_inputs
    configure_build_inputs(source, json.loads((ROOT / "jerkgram-migration.json").read_text()))

if __name__ == '__main__':
    materialize(ROOT / 'work/swiftgram-src')
