# Demo

This demo uses local OAuth credentials and a local MCP client. Replace paths with the folder where you cloned the repository.

## Setup

```bash
git clone https://github.com/Shaazakhtar/youtube-studio-mcp.git
cd youtube-studio-mcp
mkdir -p secrets
```

Save your Google OAuth Desktop client JSON to:

```text
secrets/client_secret.json
```

Authenticate:

```bash
python3 scripts/auth.py auth
```

Expected result:

```text
Saved OAuth token to /path/to/youtube-studio-mcp/secrets/token.json
```

## Example MCP prompt

```text
Show my YouTube channel overview and summarize the last 10 uploaded videos.
```

## Example assistant workflow

The assistant can call:

```text
youtube_auth_status
youtube_channel_overview
youtube_list_videos
```

Then it can summarize:

```text
Your channel is connected. Here are the most recent uploads, their public stats, privacy status, and metadata improvement opportunities.
```

## Safety check

Before sharing logs or screenshots, remove:

- OAuth authorization URLs
- `secrets/client_secret.json`
- `secrets/token.json`
- Channel IDs if you do not want them public
