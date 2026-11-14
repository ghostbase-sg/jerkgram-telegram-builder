#!/usr/bin/env python3
"""Verify encryption setup against the actual SQLCipher C dependency.

This supplements the native Swift suite; it does not claim Swift compilation.
"""
import argparse
import ctypes
import re
from pathlib import Path
import subprocess
import tempfile

parser = argparse.ArgumentParser()
parser.add_argument('--source-root', type=Path, required=True)
args = parser.parse_args()
cipher = args.source_root.resolve() / 'submodules/sqlcipher'
with tempfile.TemporaryDirectory(prefix='profile-store-cipher-probe-') as scratch:
    root = Path(scratch)
    library = root / 'libsqlcipher.so'
    subprocess.run(['cc', '-shared', '-fPIC', '-O2', '-DSQLITE_HAS_CODEC=1', '-DSQLITE_EXTRA_INIT=sqlcipher_extra_init', '-DSQLITE_EXTRA_SHUTDOWN=sqlcipher_extra_shutdown', '-DSQLCIPHER_CRYPTO_OPENSSL=1', '-DSQLITE_TEMP_STORE=2', '-DSQLITE_THREADSAFE=1', '-DSQLITE_OMIT_LOAD_EXTENSION=1', '-I', str(cipher / 'PublicHeaders'), str(cipher / 'Sources/sqlite3.c'), '-o', str(library), '-lcrypto', '-ldl', '-lpthread', '-lm'], check=True)
    sql = ctypes.CDLL(str(library))
    sql.sqlite3_open.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_void_p)]
    sql.sqlite3_exec.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
    sql.sqlite3_close.argtypes = [ctypes.c_void_p]
    def connect(path):
        result = ctypes.c_void_p()
        assert sql.sqlite3_open(str(path).encode(), ctypes.byref(result)) == 0
        return result
    def run(db, statement):
        return sql.sqlite3_exec(db, statement.encode(), None, None, None)
    first = connect(root / 'postbox-defaults.sqlite')
    assert run(first, 'PRAGMA cipher_default_plaintext_header_size=32') == 0
    db = connect(root / 'history.sqlite')
    assert run(db, 'PRAGMA key="x\'' + bytes(range(32)).hex() + '\'"') == 0
    assert run(db, 'PRAGMA cipher_plaintext_header_size=0') == 0
    assert run(db, 'SELECT count(*) FROM sqlite_master') == 0
    assert run(db, 'PRAGMA journal_mode=WAL') == 0
    assert run(db, 'PRAGMA synchronous=FULL') == 0
    production = Path(__file__).resolve().parents[1] / 'scripts/jerkgram_profile_observer_v1_payload/JerkgramProfileHistoryStore.swift'
    schema = re.findall(r'self\.execute\("(CREATE [^"\\]+)"\)', production.read_text())
    assert len(schema) >= 12, 'production schema extraction failed'
    for statement in schema:
        assert run(db, statement) == 0, statement
    assert run(db, "CREATE TABLE proof(value TEXT); INSERT INTO proof VALUES('personal-secret-marker')") == 0
    for file in root.glob('history.sqlite*'):
        value = file.read_bytes()
        assert b'personal-secret-marker' not in value, file
        if file.name == 'history.sqlite':
            assert not value.startswith(b'SQLite format 3'), file
    sql.sqlite3_close(db)
    wrong = connect(root / 'history.sqlite')
    assert run(wrong, 'PRAGMA key="x\'' + bytes([9] * 32).hex() + '\'"') == 0
    assert run(wrong, 'PRAGMA cipher_plaintext_header_size=0') == 0
    assert run(wrong, 'SELECT * FROM proof') != 0
    sql.sqlite3_close(wrong)
    reopened = connect(root / 'history.sqlite')
    assert run(reopened, 'PRAGMA key="x\'' + bytes(range(32)).hex() + '\'"') == 0
    assert run(reopened, 'PRAGMA cipher_plaintext_header_size=0') == 0
    assert run(reopened, 'SELECT * FROM proof') == 0
    sql.sqlite3_close(reopened)
    sql.sqlite3_close(first)
    print('Real SQLCipher probe passed: encrypted header/WAL, global-default isolation, wrong-key rejection, reopen preservation')
