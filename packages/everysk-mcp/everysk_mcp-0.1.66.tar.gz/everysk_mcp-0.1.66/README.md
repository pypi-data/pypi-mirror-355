### Clone and set up the MCP server

This installs the server in the Desktop. Please check folder names `mcp` and `mcp-server` are available.

```bash
cd ~/Desktop
git clone git@github.com:Everysk/mcp.git
mv mcp mcp-server
cd mcp-server
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Setup environment variables

Create a `.env` file in the `mcp-server` directory with the following content:

```
EVERYSK_API_URL_DOMAIN=dev-api-pm2pps2oia-uc.a.run.app
EVERYSK_API_SID=...
EVERYSK_API_TOKEN=...
```

If using the PROD environment, you can skip the EVERYSK_API_URL_DOMAIN.

### Configure the MCP server

Use command below or navigate to the file manually to edit the configuration.

```bash
open /Users/<USERNAME>/Library/Application\ Support/Claude/claude_desktop_config.json
```

Replace any existing content with the following configuration, ensuring to replace `{...}` with the actual path to your MCP server directory:

```json
{
  "mcpServers": {
    "Everysk MCP Server": {
      "command": "{...}/mcp-server/.venv/bin/mcp",
      "args": ["run", "{...}/mcp-server/server.py"]
    }
  }
}
```

### Debugging

```bash
mcp dev server.py
```
