# Words MCP Server

[![PyPI](https://img.shields.io/pypi/v/casual-mcp-server-words.svg)](https://pypi.org/project/casual-mcp-server-words/)
[![License](https://img.shields.io/github/license/casualgenius/mcp-servers)](https://github.com/casualgenius/mcp-servers/blob/main/LICENSE)
[![Build](https://img.shields.io/github/actions/workflow/status/casualgenius/mcp-servers/ci.yml?branch=main)](https://github.com/casualgenius/mcp-servers/actions)

> An MCP server providing dictionary and thesaurus tools for LLMs using the Free Dictionary API.

---

## Overview

The Words MCP Server provides natural language utilities for language models and AI assistants. It allows tools like `define`, `synonyms`, and `example_usage` to be called programmatically via FastMCP.

---

## 🔧 Tools

- **define** – Retrieve definitions of an English word.
- **example_usage** – Get example usage sentences for a word.
- **synonyms** – Get synonyms for a word.

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
docker build -f servers/words/Dockerfile -t casual-mcp-server-words .
```

---

## ▶️ Running the Server

### ➤ Stdio Mode

#### From Source

Install for local development and then configure:

```json
{
  "mcpServers": {
    "words": {
      "command": "uv",
      "args": ["tool", "run", "casual-mcp-server-words"]
    }
  }
}
```

#### Using `uvx`

```json
{
  "mcpServers": {
    "words": {
      "command": "uvx",
      "args": ["casual-mcp-server-words"]
    }
  }
}
```

#### Docker

```json
{
  "mcpServers": {
    "words": {
      "command": "docker",
      "args": ["run", "--rm", "casual-mcp-server-words"]
    }
  }
}
```

---

### ➤ Streamable HTTP Mode

#### From Source

```bash
uv run casual-mcp-server-words --transport streamable-http
```

With port/host overrides:

```bash
uv run casual-mcp-server-words --transport streamable-http --port 9000 --host 0.0.0.0
```

#### Using `uvx`

```bash
uvx casual-mcp-server-words --transport streamable-http
```

You can use the same port/host overrides as above

#### Docker

```bash
docker run -e MCP_TRANSPORT=streamable-http -e MCP_PORT=9000 -p 9000:9000 casual-mcp-server-words
```

##### Configuration

```json
{
  "mcpServers": {
    "words": {
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

Published at: [https://pypi.org/project/casual-mcp-server-words/](https://pypi.org/project/casual-mcp-server-words/)