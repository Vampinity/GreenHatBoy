#!/bin/sh
# ingest.sh RUN_FOLDER RUN_ID [--expect-build 01.219.911] [--notes "what you saw"] [--build-tag t120-gbb4]
#
# After copying a run off the console: check it, pack it into the shared repo, write its report and rebuild the
# index. Stops at the check if anything is wrong. Commit and push are left to you (or your agent).
# REPO defaults to the shared repo clone; set REPO=/path to override.
set -eu
here=$(cd "$(dirname "$0")" && pwd)
run=${1:?run folder}; id=${2:?run id}; shift 2
expect=""; notes=""; tag=""
while [ $# -gt 0 ]; do
  case "$1" in
    --expect-build) expect=$2; shift 2 ;;
    --notes) notes=$2; shift 2 ;;
    --build-tag) tag=$2; shift 2 ;;
    *) echo "unknown option $1"; exit 2 ;;
  esac
done
REPO=${REPO:?set REPO to the shared repo clone}
if [ -n "$expect" ]; then python3 "$here/checkrun.py" "$run" --expect-build "$expect"; else python3 "$here/checkrun.py" "$run"; fi
set -- "$REPO" "$run" --id "$id"
[ -n "$notes" ] && set -- "$@" --notes "$notes"
[ -n "$tag" ] && set -- "$@" --build-tag "$tag"
out=$(python3 "$REPO/tools/GrowingBlackBeans/pack-gbb.py" "$@")
echo "$out"
dir="$REPO/runs/GrowingBlackBeans/$(echo "$out" | awk '{print $1}')"
python3 "$here/runreport.py" "$dir" --out "$dir/report.md"
python3 "$REPO/tools/make-index.py" "$REPO"
python3 "$here/index-gbb.py" "$REPO"
echo "packed: $dir (report.md written). Review, then commit and push."
