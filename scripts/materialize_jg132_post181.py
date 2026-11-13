from pathlib import Path
from jg132_baseline import require_genuine
from jg132_post181 import apply_all,verify_source
if __name__=='__main__':
    source=Path(__file__).resolve().parents[1]/'work/swiftgram-src'
    require_genuine(source);apply_all(source);verify_source(source)
