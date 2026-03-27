# whoop-mcp

An MCP server that connects LLMs to your [WHOOP](https://www.whoop.com/) data — recovery, sleep, workouts, strain, and more.

Built with [FastMCP](https://gofastmcp.com/) and the [WHOOP API v2](https://developer.whoop.com/api).

> **Note**: WHOOP developer apps are limited to 10 authorized users.

## Prerequisites

1. A WHOOP membership with data on your account
2. A WHOOP developer application — create one at [developer-dashboard.whoop.com](https://developer-dashboard.whoop.com)
3. Python 3.10+ and [uv](https://docs.astral.sh/uv/)

## Installation

```bash
git clone https://github.com/anaselmhamdi/whoop-mcp.git
cd whoop-mcp
uv sync
```

## Configuration

Copy `.env.example` to `.env` and fill in your WHOOP app credentials:

```bash
cp .env.example .env
```

```env
WHOOP_CLIENT_ID=your_client_id
WHOOP_CLIENT_SECRET=your_client_secret
WHOOP_ACCESS_TOKEN=your_access_token
WHOOP_REFRESH_TOKEN=your_refresh_token
```

The server automatically refreshes expired access tokens using your refresh token.

### Getting Tokens

There are two ways to obtain your OAuth tokens:

**Option A: Via the deployed server (easiest)**

If the server is deployed (see [Deployment](#deployment)), visit `/login` in your browser. This will walk you through WHOOP's OAuth flow and store the tokens automatically.

**Option B: Manual OAuth flow**

1. Go to [developer-dashboard.whoop.com](https://developer-dashboard.whoop.com) and create an app
2. Set your redirect URI (e.g. `https://localhost`)
3. Open the authorization URL in your browser:
   ```
   https://api.prod.whoop.com/oauth/oauth2/auth?client_id=YOUR_CLIENT_ID&redirect_uri=YOUR_REDIRECT_URI&response_type=code&scope=read:profile read:body_measurement read:cycles read:recovery read:sleep read:workout offline&state=whoopauth1
   ```
4. After authorizing, grab the `code` from the redirect URL and exchange it:
   ```bash
   curl -X POST https://api.prod.whoop.com/oauth/oauth2/token \
     -d grant_type=authorization_code \
     -d code=AUTH_CODE \
     -d client_id=YOUR_CLIENT_ID \
     -d client_secret=YOUR_CLIENT_SECRET \
     -d redirect_uri=YOUR_REDIRECT_URI
   ```
5. Add the returned `access_token` and `refresh_token` to your `.env`

## Usage

### Run locally

```bash
uv run whoop-mcp
```

### Connect to Claude Desktop (local)

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "whoop": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/whoop-mcp", "whoop-mcp"],
      "env": {
        "WHOOP_CLIENT_ID": "your_client_id",
        "WHOOP_CLIENT_SECRET": "your_client_secret",
        "WHOOP_ACCESS_TOKEN": "your_access_token",
        "WHOOP_REFRESH_TOKEN": "your_refresh_token"
      }
    }
  }
}
```

### Connect to Claude Desktop (remote)

If deployed to Fly.io, point Claude Desktop at the remote URL:

```json
{
  "mcpServers": {
    "whoop": {
      "type": "url",
      "url": "https://your-app.fly.dev/mcp/"
    }
  }
}
```

### Connect to Claude Code

Add to `.claude/settings.json`:

```json
{
  "mcpServers": {
    "whoop": {
      "command": "uv",
      "args": ["run", "--directory", "/path/to/whoop-mcp", "whoop-mcp"]
    }
  }
}
```

### Test with MCP Inspector

```bash
uv run fastmcp dev src/whoop_mcp/server.py
```

## Available Tools

| Tool | Description |
|------|-------------|
| `get_profile` | Get user profile (name, email) |
| `get_body_measurement` | Get body measurements (height, weight, max HR) |
| `get_cycles` | List physiological cycles with strain and heart rate |
| `get_cycle_by_id` | Get a single cycle by ID |
| `get_recovery_collection` | List recovery scores (recovery %, HRV, RHR, SpO2) |
| `get_recovery_by_id` | Get a single recovery record |
| `get_sleep_collection` | List sleep records (stages, performance, respiratory rate) |
| `get_sleep_by_id` | Get a single sleep record |
| `get_workout_collection` | List workouts (strain, HR zones, distance) |
| `get_workout_by_id` | Get a single workout |

List tools accept optional parameters:
- `start` — ISO-8601 datetime to filter from (e.g. `2024-01-01T00:00:00.000Z`)
- `end` — ISO-8601 datetime to filter until
- `limit` — max records to return

## Deployment

### Fly.io

The server supports remote deployment with HTTP transport.

1. Install [flyctl](https://fly.io/docs/flyctl/install/)
2. Create the app:
   ```bash
   fly launch --no-deploy
   ```
3. Set secrets from your `.env`:
   ```bash
   cat .env | fly secrets import
   ```
4. Add your Fly.io app URL as a redirect URI in the [WHOOP developer dashboard](https://developer-dashboard.whoop.com):
   ```
   https://your-app.fly.dev/callback
   ```
5. Deploy:
   ```bash
   fly deploy
   ```
6. Visit `https://your-app.fly.dev/login` to authenticate with WHOOP

### CI/CD

A GitHub Actions workflow (`.github/workflows/deploy.yml`) auto-deploys on push to `main`. To set it up:

1. Get a Fly.io deploy token:
   ```bash
   fly tokens create deploy -x 999999h
   ```
2. Add it as `FLY_API_TOKEN` in your GitHub repo's secrets (Settings > Secrets > Actions)

## Refreshing Tokens

The server auto-refreshes tokens during use. To manually refresh:

```bash
uv run python scripts/refresh_token.py
```

## Development

```bash
uv sync              # Install dependencies
uv run pytest        # Run tests
uv run pytest -v     # Run tests with output
```

## License

MIT
