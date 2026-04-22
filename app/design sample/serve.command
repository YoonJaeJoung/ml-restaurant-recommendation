#!/bin/bash
# Double-click this file to view the FML design canvas + prototype in your browser.
# Reason: Babel Standalone can't fetch external .jsx files over file:// — needs http://.

cd "$(dirname "$0")"

PORT=8765
while lsof -i :$PORT >/dev/null 2>&1; do
  PORT=$((PORT + 1))
done

open "http://localhost:$PORT/FML%20Design%20Canvas.html"
open "http://localhost:$PORT/FML%20Prototype.html"

echo "Serving on http://localhost:$PORT — press Ctrl-C in this window to stop."
exec python3 -m http.server $PORT
