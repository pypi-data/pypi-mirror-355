# Project Intelligence Control

This directory follows the universal .air standard for AI intelligence control.

> *Where .git gives us version control, .air gives us intelligence control.*

## The Five Core AI Management Primitives

### 1. Rules
AI behavior guidelines, coding standards, domain constraints

### 2. Prompts
Specific instructions and templates for AI interactions

### 3. Workflows
Process documentation, memory systems, project context

### 4. Frameworks
Project management patterns and organizational methodologies

### 5. Tools
Scripts, MCP configurations, automation, domain-specific utilities

## Structure

- `rules/` - Project-level rules across all domains
- `prompts/` - Project-level prompts across all domains
- `workflows/` - Project-level workflows across all domains
- `frameworks/` - Project-level framework definitions
- `tools/` - Project-level tools, scripts, MCP configurations
- `domains/` - Domain-specific intelligence organization
- `context/` - Project session state (not synced to vendors)

## Getting Started

1. Add your AI rules to `rules/index.md`
2. Create reusable prompts in `prompts/index.md`
3. Configure workflows in `workflows/index.md`
4. Explore domain-specific organization in `domains/`

## Configuration Hierarchy

Settings are applied in this order (later overrides earlier):

1. **Global Base**: `~/.air/` provides universal foundation
2. **Domain Specific**: `~/.air/domains/{domain}/` adds domain expertise
3. **Project Base**: `/project/.air/` adds project-specific context (this directory)
4. **Project Domain**: `/project/.air/domains/{domain}/` provides final overrides





For more information, see: https://github.com/shaneholloman/airpilot
