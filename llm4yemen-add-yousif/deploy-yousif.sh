#!/bin/bash
# LLM4Yemen -- Add Dr. Yousif Alyousifi to teaching team
# Usage: bash deploy-yousif.sh /path/to/repo

REPO=${1:-"/path/to/llm4yemen-repo"}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "=== LLM4Yemen Team Update ==="

for f in team.html curriculum.html index.html; do
  cp "$SCRIPT_DIR/$f" "$REPO/$f"
  echo "  Copied: $f"
done

cd "$REPO"
git add team.html curriculum.html index.html
git commit -m "Add Dr. Yousif Alyousifi to teaching team + assign instructors to all weeks/books"
git push

echo "=== Done! ==="
