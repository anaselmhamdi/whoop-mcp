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

## Usage

### Remote (recommended)

When deployed, the server uses FastMCP's OAuthProxy. Just add the URL to your MCP client — authentication happens automatically through WHOOP's OAuth flow.

**Claude Desktop** (`~/Library/Application Support/Claude/claude_desktop_config.json`):

```json
{
  "mcpServers": {
    "whoop": {
      "type": "http",
      "url": "https://your-app.fly.dev/mcp/"
    }
  }
}
```

On first connect, your browser will open for WHOOP login. After authorizing, the tools are available immediately.

### Local

For local development, provide a WHOOP access token via env var:

```bash
cp .env.example .env
# Fill in WHOOP_CLIENT_ID, WHOOP_CLIENT_SECRET, WHOOP_ACCESS_TOKEN
```

```bash
uv run whoop-mcp
```

**Claude Desktop** (local):

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

1. Install [flyctl](https://fly.io/docs/flyctl/install/)
2. Create the app:
   ```bash
   fly launch --no-deploy
   ```
3. Set secrets:
   ```bash
   cat .env | fly secrets import
   ```
4. Add your Fly.io app URL as a redirect URI in the [WHOOP developer dashboard](https://developer-dashboard.whoop.com):
   ```
   https://your-app.fly.dev/auth/callback
   ```
5. Deploy:
   ```bash
   fly deploy
   ```

### CI/CD

A GitHub Actions workflow (`.github/workflows/deploy.yml`) auto-deploys on push to `main`. To set it up:

1. Get a Fly.io deploy token:
   ```bash
   fly tokens create deploy -x 999999h
   ```
2. Add it as `FLY_API_TOKEN` in your GitHub repo's secrets (Settings > Secrets > Actions)

## Development

```bash
uv sync              # Install dependencies
uv run pytest        # Run tests
uv run pytest -v     # Run tests with output
```

## License

MIT
