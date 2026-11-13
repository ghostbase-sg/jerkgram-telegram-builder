"""One bounded Settings request/subscription successor of GREEN Build180."""
from contextlib import contextmanager
from pathlib import Path
from jg132_beta3_stages import apply_stage, parent_source_view, verify_source as verify_green, manifest, digest
STAGE='perf180-wave2a2-about-lifecycle'
OWNER='submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift'

@contextmanager
def green_view(source):
    with parent_source_view(source,STAGE) as before:
        verify_green(before)
        yield before

def apply(source):
    values=manifest(STAGE)
    actual=digest((Path(source)/OWNER).read_bytes())
    if actual==values['owners'][OWNER]['after_sha256']:
        with green_view(source):pass
        return
    verify_green(source)
    apply_stage(source,STAGE)
    with green_view(source):pass
