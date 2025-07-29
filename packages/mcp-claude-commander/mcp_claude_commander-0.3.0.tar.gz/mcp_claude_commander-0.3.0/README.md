# mcp-claude-commander

This is a namespace alias for the main [`claude-command`](https://pypi.org/project/claude-command/) package.

## Installation

```bash
uv tool install claude-command
```

Then configure with Claude CLI:
```bash
claude mcp add claude-command claude-command \
  -e GEMINI_API_KEY="$GEMINI_API_KEY" \
  -e CLAUDE_COMMAND_OPENAI_API_KEY="$OPENAI_API_KEY" \
  -e CLAUDE_COMMAND_ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
  --scope user
```

This package automatically installs and re-exports the main `claude-command` package. All functionality is identical.

## Why This Package Exists

This package exists to secure the `mcp-claude-commander` namespace and redirect users to the canonical `claude-command` package.

## Usage

See the main [claude-command documentation](https://github.com/shaneholloman/mcp-claude-command) for usage instructions.