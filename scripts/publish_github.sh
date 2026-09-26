#!/usr/bin/env bash

set -euo pipefail

OWNER="${1:-Shaazakhtar}"
REPO="${2:-youtube-studio-mcp}"
DESCRIPTION="Local MCP server for YouTube metadata, thumbnails, comments, and analytics."
TOPICS="mcp,model-context-protocol,youtube,youtube-api,youtube-analytics,youtube-studio,ai-tools,creator-tools,python"

if ! command -v gh >/dev/null 2>&1; then
  echo "GitHub CLI is required. Install it from https://cli.github.com/."
  exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "GitHub CLI is not authenticated. Run: gh auth login --hostname github.com --git-protocol https --web --scopes repo"
  exit 1
fi

git remote remove origin >/dev/null 2>&1 || true

if gh repo view "${OWNER}/${REPO}" >/dev/null 2>&1; then
  echo "Repository already exists: ${OWNER}/${REPO}"
else
  gh repo create "${OWNER}/${REPO}" \
    --public \
    --description "${DESCRIPTION}" \
    --source . \
    --remote origin
fi

git remote set-url origin "https://github.com/${OWNER}/${REPO}.git"
git push -u origin main

gh repo edit "${OWNER}/${REPO}" \
  --description "${DESCRIPTION}" \
  --homepage "https://github.com/${OWNER}/${REPO}" \
  --add-topic "${TOPICS}"

echo "Published: https://github.com/${OWNER}/${REPO}"
