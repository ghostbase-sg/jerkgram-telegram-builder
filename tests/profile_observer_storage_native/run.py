#!/usr/bin/env python3
"""Compile the production store and native tests against pinned real SQLCipher."""
import argparse
import os
from pathlib import Path
import platform
import shutil
import subprocess
import tempfile

parser = argparse.ArgumentParser()
parser.add_argument("--source-root", type=Path, required=True)
args = parser.parse_args()
repo = Path(__file__).resolve().parents[2]
store = repo / "scripts/jerkgram_profile_observer_v1_payload/JerkgramProfileHistoryStore.swift"
if not store.is_file():
    raise SystemExit("FAIL: production history store is not implemented")
swift = os.environ.get("SWIFTC") or shutil.which("swiftc")
if not swift:
    raise SystemExit("FAIL: swiftc is required; native storage verification did not run")
cipher = args.source_root.resolve() / "submodules/sqlcipher"
with tempfile.TemporaryDirectory(prefix="profile-store-native-") as scratch:
    build = Path(scratch)
    crypto = ["-DSQLCIPHER_CRYPTO_CC=1"] if platform.system() == "Darwin" else ["-DSQLCIPHER_CRYPTO_OPENSSL=1"]
    subprocess.run(["cc", "-c", "-O2", "-DSQLITE_HAS_CODEC=1", "-DSQLITE_EXTRA_INIT=sqlcipher_extra_init", "-DSQLITE_EXTRA_SHUTDOWN=sqlcipher_extra_shutdown", "-DSQLITE_TEMP_STORE=2", "-DSQLITE_THREADSAFE=1", "-DSQLITE_OMIT_LOAD_EXTENSION=1", *crypto, "-I", str(cipher / "PublicHeaders"), str(cipher / "Sources/sqlite3.c"), "-o", str(build / "sqlcipher.o")], check=True)
    module = build / "module.modulemap"
    module.write_text('module sqlcipher [system] { header "' + str(cipher / "PublicHeaders/sqlite3.h") + '" export * }\n')
    libraries = ["-framework", "Security"] if platform.system() == "Darwin" else ["-lcrypto", "-ldl", "-lpthread", "-lm"]
    subprocess.run([swift, "-I", str(build), str(store), str(Path(__file__).with_name("main.swift")), str(build / "sqlcipher.o"), *libraries, "-o", str(build / "test")], check=True)
    subprocess.run([str(build / "test")], check=True)
