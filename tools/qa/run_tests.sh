#!/usr/bin/env bash
# Runs every test suite. The tests that read the disc need `tools/build/build.sh` to have run once
# (it fills build/orig and build/work/script_orig); the ones on the translation store need nothing.
#
#   tools/qa/run_tests.sh
set -uo pipefail
cd "$(dirname "$0")/../.."
fail=0
run() { echo "== $*"; "$@" >build/test.log 2>&1 && echo "   PASS" || { echo "   FAIL (build/test.log)"; tail -5 build/test.log; fail=1; }; }
mkdir -p build
py=python3; command -v python3 >/dev/null || py=python
run $py tools/qa/test_translation_store.py
run $py tools/qa/test_check_translation.py
if [[ -d build/work/script_orig && -f build/orig/SCRIPT.IMG ]]; then
  run $py tools/qa/test_scfasm_roundtrip.py build/work/script_orig
  run $py tools/qa/test_scfvm.py build/work/script_orig
  run $py tools/qa/test_patches_jp.py build/work/script_orig
  run $py tools/qa/test_text_roundtrip.py build/orig/SCRIPT.IMG
  run $py tools/qa/test_graph0_textures.py build/orig/GRAPH/GRAPH0.ARC
  run $py tools/qa/test_graph_overrides.py build/orig/GRAPH
else
  echo "(disc tests skipped: run tools/build/build.sh once first)"
fi
exit $fail
