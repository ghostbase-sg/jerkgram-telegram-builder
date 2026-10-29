#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
python3 scripts/materialize_jg13.py
python3 scripts/configure_jg13.py --previous-contracts-only
python3 scripts/verify_jg13_source.py --previous-contracts-only
python3 -m unittest discover -s tests -p test_jg13_history_backend.py
python3 -m unittest discover -s tests -p test_jg131_migration.py
python3 -m unittest discover -s tests -p test_jg131_ui_repair.py
python3 -m unittest discover -s tests -p test_jg131_ui_type_compat.py
python3 tests/run_jg131_capture_repair.py
python3 tests/run_jg13_history_backend.py
xcrun swiftc -frontend -parse work/swiftgram-src/submodules/TelegramUI/Sources/ChatHistoryListNode.swift
python3 -m unittest discover -s tests -p test_jg13_stars_gift.py
python3 tests/run_jg13_stars_gift.py
python3 -m unittest discover -s tests -p test_jg13_sponsored.py
python3 -m unittest discover -s tests -p test_jg13_profile_capture.py
python3 tests/run_jg13_sponsored.py
python3 -m unittest discover -s tests -p test_jg13_download_boost.py
python3 tests/run_jg13_download_boost.py
python3 -m unittest discover -s tests -p test_jg13_premium_icons.py
python3 tests/run_jg13_premium_icons.py
python3 -m unittest discover -s tests -p test_jg13_release_ui.py
python3 tests/run_jg13_ping_policy.py
python3 -m unittest discover -s tests -p test_jg13_beta_followup.py
python3 tests/run_jg13_followup.py
python3 tests/run_jg13_performance_capture.py
python3 tests/run_jg13_secondary_timebase.py
python3 tests/run_jg13_profile_preferences.py
python3 tests/run_jg13_expanded_diagnostics.py
python3 tests/run_jg13_capture_retention.py
python3 tests/run_jg13_history_bounds.py
python3 -m unittest discover -s tests -p 'test_jg13_deleted_reply*.py'
python3 tests/run_jg13_deleted_reply.py
python3 -m unittest discover -s tests -p test_jg13_recovery_media.py
python3 -m unittest discover -s tests -p test_jg13_protected_copy.py
python3 -m unittest discover -s tests -p test_jg13_forward_routes.py
python3 -m unittest discover -s tests -p test_jg13_portable_copy_stage.py
python3 tests/run_jg13_recovery_media.py
python3 -m unittest discover -s tests -p test_jg13_recovery_cache.py
python3 tests/run_jg13_recovery_cache.py
python3 tests/run_jg13_protected_copy.py
python3 -m unittest discover -s tests -p test_jg13_package_digest.py
python3 scripts/apply_jg131_final_stages.py
python3 scripts/verify_jg13_source.py
python3 -m unittest discover -s tests -p test_jg131_profile_polish.py
python3 -m unittest discover -s tests -p test_jg131_profile_metadata_stage.py
python3 -m unittest discover -s tests -p test_jg131_profile_metadata.py
python3 -m unittest discover -s tests -p test_jg131_excluded_history_stage.py
python3 -m unittest discover -s tests -p test_jg131_excluded_history.py
python3 -m unittest discover -s tests -p test_jg131_settings_transparency_stage.py
python3 -m unittest discover -s tests -p test_jg131_settings_transparency.py
python3 -m unittest discover -s tests -p test_jg131_final_stages.py
python3 tests/run_jg131_settings_preferences.py
python3 -m unittest discover -s tests -p test_jg131_performance_followup_stage.py
python3 -m unittest discover -s tests -p test_jg131_performance_followup.py
python3 -m unittest discover -s tests -p test_jg131_chat_visit.py
python3 -m unittest discover -s tests -p test_jg131_profile_metadata_dc.py
python3 -m unittest discover -s tests -p test_jg131_settings_visual_followup.py
python3 -m unittest discover -s tests -p test_jg131_excluded_chat_interactions.py
python3 tests/run_jg131_build175_regressions.py
python3 scripts/materialize_jg131_performance_wave1.py
python3 tests/run_jg131_build176_regressions.py
python3 scripts/materialize_jg131_translation_repair.py
python3 tests/run_jg131_translation_repair.py
python3 scripts/materialize_jg131_default_folder.py
python3 tests/run_jg131_default_folder.py
python3 scripts/pin_jg13_dependencies.py
cd work/swiftgram-src
git submodule sync --recursive
git submodule update --init --recursive --depth 1
python3 ../../scripts/pin_jg13_dependencies.py --verify
python3 ../../scripts/prepare_jg13_build_rules.py
"${BAZEL_BIN:-bazelisk}" build \
  -c opt \
  --ios_multi_cpus=arm64 \
  --check_direct_dependencies=off \
  --//Telegram:disableExtensions=false \
  --//Telegram:disableProvisioningProfiles=true \
  --features=disable_legacy_signing \
  --define=buildNumber=176 \
  //Telegram:Telegram
test -f bazel-bin/Telegram/Telegram.ipa
# Inspect retained build actions without a second build or target analysis.
# Only optimization tokens are printed; complete command lines stay temporary.
optimization_query=$(mktemp)
if "${BAZEL_BIN:-bazelisk}" aquery --skyframe_state --output=textproto \
  --include_commandline --include_param_files --include_artifacts=false \
  'inputs(".*ChatTextInputPanelNode[.]swift", mnemonic("SwiftCompile"))' \
  > "$optimization_query" 2>/dev/null; then
  python3 ../../scripts/report_jg13_swift_optimization.py "$optimization_query" || true
else
  printf '%s\n' 'Swift optimization action query unavailable; no conclusion.'
fi
rm -f "$optimization_query"
cd ../..
python3 scripts/package_jg13.py work/swiftgram-src/bazel-bin/Telegram/Telegram.ipa
