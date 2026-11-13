"""Reviewed Wave2A2 integrated after history/native appearance in one product."""
from contextlib import contextmanager
from jg132_beta3_stages import parent_source_view, verify_source as verify_green
from jg132_post180 import apply_all as apply, build180_source_view
STAGE='post180-performance-wave2a2'
OWNER='submodules/SettingsUI/Sources/GhostBase/GhostBaseSettingsController.swift'

@contextmanager
def product_view(source):
    with parent_source_view(source,STAGE) as product:
        with build180_source_view(product) as green:
            verify_green(green)
        yield product
