#!/usr/bin/env bash
set -euo pipefail

export USE_BAZEL_VERSION="${USE_BAZEL_VERSION:-7.6.1}"
BAZEL_BIN="${BAZEL_BIN:-bazelisk}"

SIGN_DIR="$RUNNER_TEMP/signing"
mkdir -p "$SIGN_DIR"

cd work/swiftgram-src

echo "== bazelisk / bazel =="
which "$BAZEL_BIN"
"$BAZEL_BIN" --version || true

echo
echo "== init bazel rule submodules =="
git submodule sync --recursive
git submodule update --init --recursive --depth 1 \
  build-system/bazel-rules/apple_support \
  build-system/bazel-rules/rules_apple \
  build-system/bazel-rules/rules_swift \
  build-system/bazel-rules/rules_xcodeproj \
  build-system/bazel-rules/sourcekit-bazel-bsp

echo
echo "== create build configuration repo =="
rm -rf build-input/configuration-repository
mkdir -p build-input
cp -R build-system/example-configuration build-input/configuration-repository

printf '%s\n' 'module(name = "build_configuration", version = "0.0.0")' \
  > build-input/configuration-repository/MODULE.bazel

cat >> build-input/configuration-repository/variables.bzl <<'EOF'

# Added by GhostBase builder
telegram_bazel_path = "."
telegram_use_xcode_managed_codesigning = False

# Swiftgram config placeholder for BuildConfig
sg_config = "{}"
EOF

echo
echo "== decode provisioning profile =="
PROFILE="$SIGN_DIR/Telegram.mobileprovision"
PROFILE_PLIST="$SIGN_DIR/profile.plist"

printf "%s" "$PROF_B64" | base64 -D > "$PROFILE"
security cms -D -i "$PROFILE" > "$PROFILE_PLIST"

UUID=$(/usr/libexec/PlistBuddy -c "Print UUID" "$PROFILE_PLIST")

mkdir -p "$HOME/Library/MobileDevice/Provisioning Profiles"
cp "$PROFILE" "$HOME/Library/MobileDevice/Provisioning Profiles/$UUID.mobileprovision"

cp "$PROFILE" build-input/configuration-repository/provisioning/Telegram.mobileprovision
cp "$PROFILE" build-system/example-configuration/provisioning/Telegram.mobileprovision

echo "== profile =="
wc -c "$PROFILE"
shasum -a 256 "$PROFILE"
/usr/libexec/PlistBuddy -c "Print Entitlements:application-identifier" "$PROFILE_PLIST"
/usr/libexec/PlistBuddy -c "Print Entitlements:aps-environment" "$PROFILE_PLIST"

echo
echo "== decode repack import p12 =="
ORIG="$SIGN_DIR/original.p12"
PEM="$SIGN_DIR/exported.pem"
APPLE_P12="$SIGN_DIR/apple-compatible.p12"
KEYCHAIN="$RUNNER_TEMP/gb.keychain-db"

printf "%s" "$CERT_B64" | base64 -D > "$ORIG"

openssl pkcs12 \
  -in "$ORIG" \
  -nodes \
  -passin pass:"$P12_PASSWORD" \
  -out "$PEM"

openssl pkcs12 \
  -export \
  -in "$PEM" \
  -out "$APPLE_P12" \
  -passout pass:"$P12_PASSWORD" \
  -certpbe PBE-SHA1-3DES \
  -keypbe PBE-SHA1-3DES \
  -macalg sha1

security create-keychain -p "$KEYCHAIN_PASSWORD" "$KEYCHAIN"
security unlock-keychain -p "$KEYCHAIN_PASSWORD" "$KEYCHAIN"
security set-keychain-settings -lut 21600 "$KEYCHAIN"

security import "$APPLE_P12" \
  -k "$KEYCHAIN" \
  -P "$P12_PASSWORD" \
  -A \
  -f pkcs12

security list-keychains -d user -s "$KEYCHAIN"
security set-key-partition-list -S apple-tool:,apple:,codesign: -s -k "$KEYCHAIN_PASSWORD" "$KEYCHAIN"

echo "== identities =="
security find-identity -v -p codesigning "$KEYCHAIN"

echo
echo
echo "== patch AsyncDisplayKit cxxopts safely =="
python3 - <<'PY2'
from pathlib import Path
import re

p = Path("submodules/AsyncDisplayKit/BUILD")
s = p.read_text()

# Если уже есть copts, удалить весь cxxopts-блок.
if "copts =" in s and "cxxopts =" in s:
    s = re.sub(
        r'\n\s*cxxopts\s*=\s*\[[\s\S]*?\],',
        '',
        s,
        count=1
    )
else:
    s = s.replace("cxxopts =", "copts =")

p.write_text(s)

print("== AsyncDisplayKit BUILD head ==")
print("\n".join(s.splitlines()[:35]))
PY2

echo "== build analysis probe =="
"$BAZEL_BIN" build --nobuild //Telegram:Swiftgram

echo
echo "== build analysis probe OK =="
