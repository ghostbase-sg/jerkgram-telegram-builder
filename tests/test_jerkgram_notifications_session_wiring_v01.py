from pathlib import Path


ROOT = Path(__file__).parents[1]
INSTALLER = ROOT / "scripts/install_jerkgram_v12w_build133_probe_hook.py"


def test_notifications_session_pairing_is_wired_after_binding_and_before_identity():
    text = INSTALLER.read_text()

    apply_binding = '"apply_jerkgram_push_binding_bridge_v01.py"'
    verify_binding = '"verify_jerkgram_push_binding_bridge_v01.py"'
    apply_pairing = '"apply_jerkgram_notifications_session_pairing_v01.py"'
    verify_pairing = '"verify_jerkgram_notifications_session_pairing_v01.py"'
    identity = '"apply_jerkgram_build140_identity.py"'

    for marker in (apply_binding, verify_binding, apply_pairing, verify_pairing, identity):
        assert text.count(marker) == 1, marker

    assert text.index(apply_binding) < text.index(verify_binding)
    assert text.index(verify_binding) < text.index(apply_pairing)
    assert text.index(apply_pairing) < text.index(verify_pairing)
    assert text.index(verify_pairing) < text.index(identity)

    assert "backend session pairing" in text


def test_pairing_patch_and_verifier_exist_in_builder_tree():
    assert (ROOT / "scripts/apply_jerkgram_notifications_session_pairing_v01.py").is_file()
    assert (ROOT / "scripts/verify_jerkgram_notifications_session_pairing_v01.py").is_file()
