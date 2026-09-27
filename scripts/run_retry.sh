#!/usr/bin/env bash
# eval-retry logs that stopped early (402 out of credit, Claude session limit,
# a harness crash fixed since), one at a time. Only unfinished samples rerun.
#
#   scripts/run_retry.sh [-w PATTERN] LOG.eval...    # retry these logs
#   scripts/run_retry.sh [-w PATTERN] -e DIR...      # newest log per model in
#                                                    # each DIR, if it errored
#
#   -w PATTERN   wait until no process matches PATTERN (pgrep -f) first
#
# The retry writes a new log into the same directory as the old one. Retry
# the NEWEST errored log for a model: an earlier retry that also died leaves
# a newer errored log carrying its finished samples. Rerunnable: with -e it
# picks up whatever is still errored. Rhino/Fusion retries wait for any other
# eval using that app.
set -euo pipefail
usage() { sed -n '2,/^set -euo/p' "$0" | sed '$d'; exit 2; }

WAIT="" ERRORED=0
while getopts "w:eh" opt; do
    case "$opt" in
        w) WAIT=$OPTARG ;;
        e) ERRORED=1 ;;
        *) usage ;;
    esac
done
shift $((OPTIND - 1))
(( $# )) || usage

# shellcheck source=scripts/_common.sh
source "$(dirname "$0")/_common.sh"

if (( ERRORED )); then
    LOGS=()   # macOS ships bash 3.2: no mapfile
    while IFS= read -r f; do LOGS+=("$f"); done < <(.venv/bin/python - "$@" <<'PY'
import glob, sys
from inspect_ai.log import read_eval_log
for d in sys.argv[1:]:
    latest = {}
    for f in sorted(glob.glob(f"{d}/*.eval")):  # timestamped names: newest last
        h = read_eval_log(f, header_only=True)
        latest[h.eval.model] = (f, h.status)
    for f, status in latest.values():
        if status == "error":
            print(f)
PY
)
else
    LOGS=("$@")
fi
(( ${#LOGS[@]} )) || { echo "nothing to retry"; exit 0; }

if [[ -n "$WAIT" ]]; then
    while pgrep -f "$WAIT" >/dev/null; do sleep 30; done
fi

for log in "${LOGS[@]}"; do
    dir=$(dirname "$log")
    lang=${dir##*/}; lang=${lang#*-}; lang=${lang%%-*}   # logs/trackc-rhino -> rhino
    wait_for_app "$lang"
    echo "=== retry $log $(date +%H:%M)"
    # no connection override: eval-retry keeps the original run's settings
    inspect_run eval-retry "$log" --log-dir "$dir"
done
echo "RETRY DONE $(date)"
