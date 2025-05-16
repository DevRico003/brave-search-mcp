# Brave Search MCP

MCP server for integrating Brave Search API into AI agents.

## Features

This MCP provides two tools for accessing Brave Search APIs:

1. **brave_web_search** - Performs a web search using the Brave Search API
2. **brave_local_search** - Searches for local businesses and places using Brave's Local Search API

## Prerequisites

- Python 3.12+
- Docker if running the MCP server as a container (recommended)
- Brave Search API key

## Installation

### Using uv

1. Install uv if you don't have it:
   ```bash
   pip install uv
   ```

2. Clone this repository and change to its directory

3. Install dependencies:
   ```bash
   uv pip install -e .
   ```

4. Create a `.env` file based on `.env.example`:
   ```bash
   cp .env.example .env
   ```

5. Configure your environment variables in the `.env` file

### Using Docker (Recommended)

1. Build the Docker image:
   ```bash
   docker build -t brave-search-mcp --build-arg PORT=8053 .
   ```

2. Create a `.env` file based on `.env.example` and configure your environment variables

## Configuration

The following environment variables can be configured in your `.env` file:

| Variable | Description | Example |
|----------|-------------|----------|
| `BRAVE_API_KEY` | Your Brave Search API key (required) | `bsc_...` |
| `TRANSPORT` | Transport protocol (sse or stdio) | `sse` |
| `HOST` | Host to bind to when using SSE transport | `0.0.0.0` |
| `PORT` | Port to listen on when using SSE transport | `8053` |

## Running the Server

### Using uv

#### SSE Transport

```bash
# Set TRANSPORT=sse in .env then:
uv run src/main.py
```

The MCP server will run as an API endpoint that you can connect to with the configuration shown below.

#### Stdio Transport

With stdio, the MCP client itself can spin up the MCP server, so nothing to run at this point.

### Using Docker

#### SSE Transport

```bash
docker run --env-file .env -p 8053:8053 brave-search-mcp
```

The MCP server will run as an API endpoint within the container that you can connect to with the configuration shown below.

#### Stdio Transport

With stdio, the MCP client itself can spin up the MCP server container, so nothing to run at this point.

## Integration with MCP Clients

### SSE Configuration

Once you have the server running with SSE transport, you can connect to it using this configuration:

```json
{
  "mcpServers": {
    "brave-search": {
      "transport": "sse",
      "url": "http://localhost:8053/sse"
    }
  }
}
```

> **Note for Windsurf users**: Use `serverUrl` instead of `url` in your configuration:
> ```json
> {
>   "mcpServers": {
>     "brave-search": {
>       "transport": "sse",
>       "serverUrl": "http://localhost:8053/sse"
>     }
>   }
> }
> ```

> **Note for n8n users**: Use host.docker.internal instead of localhost since n8n has to reach outside of its own container to the host machine:
> 
> So the full URL in the MCP node would be: http://host.docker.internal:8053/sse

Make sure to update the port if you are using a value other than the default 8053.

### Python with Stdio Configuration

Add this server to your MCP configuration for Claude Desktop, Windsurf, or any other MCP client:

```json
{
  "mcpServers": {
    "brave-search": {
      "command": "your/path/to/brave-search/.venv/Scripts/python.exe",
      "args": ["your/path/to/brave-search/src/main.py"],
      "env": {
        "TRANSPORT": "stdio",
        "BRAVE_API_KEY": "YOUR-API-KEY"
      }
    }
  }
}
```

### Docker with Stdio Configuration

```json
{
  "mcpServers": {
    "brave-search": {
      "command": "docker",
      "args": ["run", "--rm", "-i", 
               "-e", "TRANSPORT", 
               "-e", "BRAVE_API_KEY", 
               "brave-search-mcp"],
      "env": {
        "TRANSPORT": "stdio",
        "BRAVE_API_KEY": "YOUR-API-KEY"
      }
    }
  }
}
```

## API Tools

### brave_web_search

Performs a web search using the Brave Search API.

- **Required Parameters**:
  - `query`: Search query (max 400 chars, 50 words)
  
- **Optional Parameters**:
  - `count`: Number of results (1-20, default 10)
  - `offset`: Pagination offset (max 9, default 0)

### brave_local_search

Searches for local businesses and places using Brave's Local Search API.

- **Required Parameters**:
  - `query`: Local search query (e.g. 'pizza near Central Park')
  
- **Optional Parameters**:
  - `count`: Number of results (1-20, default 5)

## Rate Limits

The Brave Search API has the following rate limits:

- 1 request per second
- 15,000 requests per month

## License

MIT