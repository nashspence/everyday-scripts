#!/usr/bin/env zsh
set -euo pipefail

[[ $# -eq 1 ]] || { echo "usage: $0 /path/to/logfile.log" >&2; exit 1; }
LOGFILE=$1
touch "$LOGFILE" 2>/dev/null \
  || { echo "❌ Cannot write log '$LOGFILE'." >&2; exit 1; }

osascript <<EOF
tell application "Terminal"
  do script "tail -f '$LOGFILE'"
end tell
EOF
