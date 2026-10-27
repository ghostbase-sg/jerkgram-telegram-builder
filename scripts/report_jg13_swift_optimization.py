"""Report optimization tokens only; never publish full compiler arguments."""
import json
from pathlib import Path
import re
import sys

payload = Path(sys.argv[1]).read_text(errors='replace')
flags = sorted(set(re.findall(r'(?<![\w-])(?:-Osize|-Onone|-O|-whole-module-optimization)(?![\w-])', payload)))
print(json.dumps({'owner': 'ChatTextInputPanelNode.swift', 'optimization_flags': flags,
                  'evidence': 'retained SwiftCompile action' if flags else 'unavailable; no conclusion'}))
