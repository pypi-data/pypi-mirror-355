# Time and Date MCP Server

[![PyPI](https://img.shields.io/pypi/v/casual-mcp-server-time.svg)](https://pypi.org/project/casual-mcp-server-time/)
[![License](https://img.shields.io/github/license/casualgenius/mcp-servers)](https://github.com/casualgenius/mcp-servers/blob/main/LICENSE)

> An MCP server providing time and date tools for LLMs.

---

## Overview

The Time and Date MCP Server provides date and time utilities for language models and AI assistants. It allows tools like `current_time`, `time_since`, `date_diff` to be called programmatically via Stdio or Streamable HTTP.

---

## Tools

The tools exposed by the MCP server include:

- **current_time** - Get the current time in a given timezone.
- **time_since** - Human readable time elapsed since a given date.
- **add_days** - Add days to today and return the future date.
- **subtract_days** - Subtract days from today and return the past date.
- **date_diff** - Number of days between two dates.
- **next_weekday** - Date of the next occurrence of a weekday.
- **is_leap_year** - Check if a year is a leap year.
- **week_number** - ISO week number for a date.
- **parse_human_date** - Parse a natural language date description.

---

## Configuration

### Local Time Zone

The local time zone can be set using the environmental variable `LOCAL_TIME_ZONE`.

It takes a [IANA Timezone](https://nodatime.org/TimeZones), if not given it will default to `Etc/UTC`.

---

## 🛠️ Installation

### Local Development (via `uv`)

From this directory:

```bash
uv sync --locked
uv tool install .
```

### Docker Build

From the root of the repository:

```bash
docker build -f servers/time/Dockerfile -t casual-mcp-server-time .
```

---

## ▶️ Running the Server

### ➤ Stdio Mode

#### From Source

Install for local development and then configure:

```json
{
  "mcpServers": {
    "time": {
      "command": "uv",
      "args": ["tool", "run", "casual-mcp-server-time"],
      "env": {
        "LOCAL_TIME_ZONE": "Asia/Bangkok"
      }
    }
  }
}
```

#### Using `uvx`

```json
{
  "mcpServers": {
    "time": {
      "command": "uvx",
      "args": ["casual-mcp-server-time"],
      "env": {
        "LOCAL_TIME_ZONE": "Asia/Bangkok"
      }
    }
  }
}
```

#### Docker

```json
{
  "mcpServers": {
    "time": {
      "command": "docker",
      "args": ["run", "--rm", "casual-mcp-server-time"],
      "env": {
        "LOCAL_TIME_ZONE": "Asia/Bangkok"
      }
    }
  }
}
```

---

### ➤ Streamable HTTP Mode

#### From Source

```bash
uv run casual-mcp-server-time --transport streamable-http
```

With port/host overrides:

```bash
uv run casual-mcp-server-time --transport streamable-http --port 9000 --host 0.0.0.0
```

#### Using `uvx`

```bash
uvx casual-mcp-server-time --transport streamable-http
```

You can use the same port/host overrides as above

#### Docker

```bash
docker run -e MCP_TRANSPORT=streamable-http -e MCP_PORT=9000 -p 9000:9000 casual-mcp-server-time
```

##### Configuration

```json
{
  "mcpServers": {
    "time": {
      "type": "streamable-http",
      "url": "http://localhost:9000"
    }
  }
}
```

---

## 📜 License

MIT – [LICENSE](https://github.com/casualgenius/mcp-servers/blob/main/LICENSE)

---

## 📦 PyPI

Published at: [https://pypi.org/project/casual-mcp-server-time/](https://pypi.org/project/casual-mcp-server-time/)