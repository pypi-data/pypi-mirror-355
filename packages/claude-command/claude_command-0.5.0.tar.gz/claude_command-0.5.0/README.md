# Claude Command MCP Server

Real-time AI command center for Claude Code CLI with dynamic multi-provider support.

> [!IMPORTANT]
> **System Prompt**: Development standards and procedures are documented in `.air/prompts/system.prompt.md` - this is the most important file for understanding how to work with this codebase.

## Overview

Claude Command is an MCP (Model Context Protocol) server that enables live three-way conversations between Claude Code CLI, multiple AI providers, and human developers. Built with fastMCP, it supports dynamic provider switching and real-time streaming conversations.

## Features

- **Multi-Provider Support**: Gemini, OpenAI, and Anthropic models
- **Dynamic Provider Switching**: Call any AI provider on-demand
- **Real-Time Streaming**: Watch conversations unfold live via `tail -f`
- **Context Preservation**: Full conversation history maintained across providers
- **Background Processing**: Non-blocking AI calls with threading
- **Session Management**: Persistent conversation storage in JSON format

## Architecture

Built using fastMCP framework with modular client architecture and mission-based execution:

```flowchart
Claude Code CLI (Hub) ↔ fastMCP Server ↔ Mission System ↔ [Gemini ↔ OpenAI ↔ Anthropic]
                                        ↓
                        [Query | Review | Brainstorm | Conversation | Recon]
                                        ↓
                           [Streaming | Sessions | File Management]
```

### Mission-Based Architecture

The core functionality is organized into specialized **missions** that handle different types of AI interactions:

- **Query Mission**: Multi-provider intelligence gathering with independent responses
- **Review Mission**: Code inspection across multiple AI providers with focus areas
- **Brainstorm Mission**: Creative collaboration with multiple providers simultaneously
- **Conversation Mission**: Live conversations with context preservation and history
- **Recon Mission**: Independent reconnaissance for unbiased comparative analysis

## Installation

### Prerequisites

- [Claude Code CLI](https://claude.ai/code)
- Python 3.10+
- API keys for desired providers

### Install Dependencies

```bash
git clone https://github.com/shaneholloman/mcp-claude-command
cd mcp-claude-command
uv sync
```

### Configure API Keys

Set environment variables:

```bash
export GEMINI_API_KEY="your_gemini_key"
export OPENAI_API_KEY="your_openai_key"
export ANTHROPIC_API_KEY="your_anthropic_key"
```

Or use command line arguments:

```bash
uv run python -m claude_command \
  --gemini-api-key YOUR_GEMINI_KEY \
  --openai-api-key YOUR_OPENAI_KEY \
  --anthropic-api-key YOUR_ANTHROPIC_KEY
```

### Add to Claude Code

Install as a global UV tool and configure with Claude CLI:

```bash
# Install claude-command globally
uv tool install .

# Configure with Claude CLI (includes all API keys for multi-provider support)
# Option 1: Using environment variables (if you have them set)
claude mcp add claude-command claude-command \
  -e GEMINI_API_KEY="$GEMINI_API_KEY" \
  -e CLAUDE_COMMAND_OPENAI_API_KEY="$OPENAI_API_KEY" \
  -e CLAUDE_COMMAND_ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY" \
  --scope user

# Option 2: Using your actual API keys directly (replace with your real keys)
claude mcp add claude-command claude-command \
  -e GEMINI_API_KEY="AIzaSyBxxxxxxxxxxxxxxxxxxxxxxx" \
  -e CLAUDE_COMMAND_OPENAI_API_KEY="sk-proj-xxxxxxxxxxxxxxxxxxxxxxx" \
  -e CLAUDE_COMMAND_ANTHROPIC_API_KEY="sk-ant-api03-xxxxxxxxxxxxxxx" \
  --scope user

# Verify configuration
claude mcp list
claude mcp get claude-command

# Verify API keys are properly configured (incontrovertible proof)
claude mcp get claude-command | grep -A 10 "Environment:"
```

> > [!IMPORTANT]
> Now, restart Claude's CLI. This is important.

## Usage

### Available Tools

| Tool | Description | Parameters |
|------|-------------|------------|
| `claude_command_query` | Interactive conversation or multi-provider query | `prompt`, `conversation_id`, `temperature`, `provider`, `providers` |
| `claude_command_review` | Code review by single or multiple AI providers | `code`, `focus`, `provider`, `providers`, `temperature` |
| `claude_command_brainstorm` | Creative brainstorming with single or multiple providers | `topic`, `context`, `provider`, `providers`, `temperature` |
| `claude_command_recon` | Independent reconnaissance across multiple providers | `survey_prompt`, `providers`, `temperature` |
| `claude_command_conversation_history` | Retrieve conversation history | `conversation_id` |
| `claude_command_status` | Server health and configuration | - |
| `claude_command_conversations_list` | List all conversation files | - |
| `claude_command_conversations_cleanup` | Clean up old conversations | `keep_count` |

### Provider Selection

Specify AI provider for any tool:

```bash
# Use default provider (first available)
claude_command_query prompt="Hello!"

# Use specific provider
claude_command_query prompt="Hello!" provider="gemini"
claude_command_query prompt="What do you think?" provider="openai"
claude_command_query prompt="Your perspective?" provider="anthropic"
```

### Live Streaming

Watch conversations in real-time:

```bash
tail -f ~/claude-command/live_stream.txt
```

### Multi-AI Conversations

Create conversations between multiple AI providers:

1. Start conversation with one provider
2. Use different providers for follow-up responses
3. Each AI sees full conversation context
4. Watch live streaming for real-time collaboration

## Mission System

The Claude Command server is built around a **mission-based architecture** where each mission type handles specific AI interaction patterns. This system provides specialized functionality while maintaining consistent streaming, session management, and multi-provider support.

### Mission Types

#### 1. Query Mission (`claude_command_query` with `providers` parameter)

**Purpose**: Multi-provider intelligence gathering with independent, unbiased responses.

**Key Features**:

- Each provider receives identical prompts with zero context
- Parallel execution with real-time streaming
- Independent responses prevent cross-contamination
- Ideal for comparative analysis and diverse perspectives

**Usage**:

```bash
# Query all providers
claude_command_query prompt="What are the pros and cons of microservices?" providers="gemini,openai,anthropic"

# Query specific providers
claude_command_query prompt="Best practices for API design" providers="gemini,openai"
```

**Output Structure**:

- Individual provider stream files: `query-TIMESTAMP-PROVIDER.md`
- Consolidated summary file: `query-TIMESTAMP-summary.md`
- JSON results: `~/claude-command/queries/query-TIMESTAMP.json`

#### 2. Review Mission (`claude_command_review`)

**Purpose**: Code inspection across multiple AI providers with structured focus areas.

**Key Features**:

- Specialized code analysis prompts
- Multiple focus areas: general, security, performance, best practices
- Multi-provider or single-provider modes
- Formatted code review output

**Usage**:

```bash
# Multi-provider code review
claude_command_review code="def process_data(data): return [x*2 for x in data]" focus="performance" providers="gemini,openai,anthropic"

# Single provider review
claude_command_review code="..." focus="security" provider="anthropic"
```

**Focus Areas**:

- `general`: Overall code quality and structure
- `security`: Security vulnerabilities and best practices
- `performance`: Optimization opportunities and bottlenecks
- `readability`: Code clarity and maintainability
- `testing`: Test coverage and testability

#### 3. Brainstorm Mission (`claude_command_brainstorm`)

**Purpose**: Creative collaboration with multiple AI providers for diverse problem-solving perspectives.

**Key Features**:

- Higher temperature settings for creativity
- Context-aware brainstorming
- Independent ideation across providers
- Collaborative problem-solving approach

**Usage**:

```bash
# Multi-provider brainstorming
claude_command_brainstorm topic="Improving user onboarding" context="SaaS application with 10k users" providers="gemini,openai,anthropic"

# Single provider brainstorming
claude_command_brainstorm topic="Cost optimization strategies" provider="gemini"
```

#### 4. Conversation Mission (`claude_command_query` without `providers` parameter)

**Purpose**: Live conversations with context preservation and full conversation history.

**Key Features**:

- Maintains conversation context across exchanges
- Session-based conversation management
- Single provider focus for consistency
- Real-time streaming with history preservation

**Usage**:

```bash
# Continue existing conversation
claude_command_query prompt="Can you elaborate on that?" conversation_id="session_2025-06-15_12-30-45_abc123def"

# Start new conversation
claude_command_query prompt="Help me understand microservices architecture" provider="anthropic"
```

#### 5. Recon Mission (`claude_command_recon`)

**Purpose**: Independent reconnaissance for unbiased comparative intelligence gathering.

**Key Features**:

- Each provider maintains separate conversation history
- Prevents cross-contamination between providers
- Specialized for reconnaissance and surveying
- Individual provider conversation context

**Usage**:

```bash
# Survey all providers independently
claude_command_recon survey_prompt="What are emerging trends in AI development?" providers="gemini,openai,anthropic"

# Targeted recon with specific providers
claude_command_recon survey_prompt="Current state of quantum computing" providers="openai,anthropic"
```

### Mission Execution Flow

1. **Mission Selection**: Based on tool called and parameters provided
2. **Provider Determination**: Single provider vs. multi-provider execution
3. **Parallel Processing**: Multi-threaded execution for multi-provider missions
4. **Real-time Streaming**: Live output to provider-specific stream files
5. **Result Compilation**: Aggregated results with metadata and file references
6. **Session Management**: Conversation history and file organization

### Streaming Infrastructure

Each mission utilizes the comprehensive streaming system:

**File Structure**:

```tree
~/claude-command/
├── live-streams/           # Real-time streaming files
│   ├── query-TIMESTAMP-gemini.md
│   ├── query-TIMESTAMP-openai.md
│   ├── query-TIMESTAMP-anthropic.md
│   └── query-TIMESTAMP-summary.md
├── conversations/          # Conversation sessions
├── queries/               # Query mission results
├── reviews/               # Code review results
├── brainstorm/           # Brainstorming sessions
└── recon/                # Reconnaissance results
    └── conversations/    # Provider-specific recon history
```

**Live Streaming Features**:

- Word-by-word streaming simulation
- Provider-specific stream files with metadata
- YAML front matter with operation details
- Tmux multi-pane viewing commands
- Thread-safe file operations

### Provider Management

**Dynamic Provider Selection**:

- `provider="gemini"` - Single provider execution
- `providers="gemini,openai"` - Multi-provider execution
- Default: All available providers

**Provider Fallback**:

- Automatic fallback to available providers
- Error handling for unavailable providers
- Provider-specific error reporting

### File Organization

**Directory Structure**:

- `conversations/`: Live conversation sessions
- `queries/`: Multi-provider query results
- `reviews/`: Code review analyses
- `brainstorm/`: Creative brainstorming sessions
- `recon/`: Independent reconnaissance data
- `live-streams/`: Real-time streaming files

**File Naming Convention**:

- `MISSION-TIMESTAMP-PROVIDER.md` - Individual provider streams
- `MISSION-TIMESTAMP-summary.md` - Consolidated summaries
- `MISSION-TIMESTAMP.json` - Structured result data

## File Locations

All data organized in mission-specific directories under `~/claude-command/`:

### Mission Data Structure

- **Live Streams**: `live-streams/` - Real-time streaming files for all missions
- **Conversations**: `conversations/` - Live conversation sessions with history
- **Queries**: `queries/` - Multi-provider query results and analysis
- **Reviews**: `reviews/` - Code review outputs and analysis
- **Brainstorm**: `brainstorm/` - Creative brainstorming session results
- **Recon**: `recon/` - Independent reconnaissance data and provider histories

### File Types

- **Stream Files**: `MISSION-TIMESTAMP-PROVIDER.md` - Real-time provider outputs
- **Summary Files**: `MISSION-TIMESTAMP-summary.md` - Consolidated mission summaries
- **Result Files**: `MISSION-TIMESTAMP.json` - Structured mission results
- **Session Files**: `session_YYYY-MM-DD_HH-MM-SS_XXXXXXXX.json` - Conversation sessions
- **Recon History**: `recon/conversations/recon-PROVIDER-conversation.json` - Provider-specific histories

## Configuration

### Settings

Configure via environment variables or command line:

- `GEMINI_API_KEY` / `--gemini-api-key`
- `OPENAI_API_KEY` / `--openai-api-key`
- `ANTHROPIC_API_KEY` / `--anthropic-api-key`
- `CONVERSATIONS_DIR` / `--conversations-dir` (default: `~/claude-command`)
- `DEFAULT_TEMPERATURE` / `--temperature` (default: 0.7)

### Models

Default models by provider:

- **Gemini**: `gemini-2.0-flash-exp`
- **OpenAI**: `gpt-4`
- **Anthropic**: `claude-3-5-sonnet-20241022`

## Development

### Project Structure

```tree
src/claude_command/
├── server.py              # Main MCP server with fastMCP tools
├── settings.py            # Configuration management
├── sessions.py            # Session and file management
├── streaming.py           # Multi-file streaming infrastructure
├── missions/              # Mission-based execution system
│   ├── __init__.py       # Mission module exports
│   ├── query.py          # Multi-provider intelligence gathering
│   ├── review.py         # Code inspection across providers
│   ├── brainstorm.py     # Creative collaboration system
│   ├── conversation.py   # Live conversations with history
│   └── recon.py          # Independent reconnaissance missions
└── clients/              # AI provider implementations
    ├── interface.py       # AI client interface
    ├── gemini.py         # Gemini implementation
    ├── openai.py         # OpenAI implementation
    ├── anthropic.py      # Anthropic implementation
    └── factory.py        # Client factory and management
```

### Local Development

```bash
git clone https://github.com/shaneholloman/mcp-claude-command
cd mcp-claude-command
uv sync
uv run python -m claude_command --gemini-api-key YOUR_KEY
```

## Requirements

- Claude Code CLI (will NOT work with Claude Desktop)
- At least one API key (Gemini, OpenAI, or Anthropic)
- Python 3.10+
- uv package manager

## License

MIT License - see [LICENSE](LICENSE) for details.
