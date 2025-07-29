"""Main entry point for Claude Command MCP Server"""

import argparse
import sys

from .server import mcp
from .settings import settings


def main():
    """Main entry point with CLI argument parsing"""
    parser = argparse.ArgumentParser(description="Claude Command MCP Server")
    parser.add_argument("--gemini-api-key", help="Google Gemini API key")
    parser.add_argument("--openai-api-key", help="OpenAI API key")
    parser.add_argument(
        "--conversations-dir", help="Directory for conversation storage"
    )
    parser.add_argument("--temperature", type=float, help="Default temperature")

    args = parser.parse_args()

    # Override settings with CLI arguments
    if args.gemini_api_key:
        settings.gemini_api_key = args.gemini_api_key
    if args.openai_api_key:
        settings.openai_api_key = args.openai_api_key
    if args.conversations_dir:
        settings.conversations_dir = args.conversations_dir
    if args.temperature:
        settings.default_temperature = args.temperature

    # Check if we have at least one API key
    if not settings.has_valid_api_key():
        print(
            "Error: No API keys configured. Please provide at least one:",
            file=sys.stderr,
        )
        print("  --gemini-api-key YOUR_KEY", file=sys.stderr)
        print("  --openai-api-key YOUR_KEY", file=sys.stderr)
        print("Or set environment variables:", file=sys.stderr)
        print("  CLAUDE_COMMAND_GEMINI_API_KEY=your_key", file=sys.stderr)
        print("  CLAUDE_COMMAND_OPENAI_API_KEY=your_key", file=sys.stderr)
        sys.exit(1)

    # Run the MCP server
    mcp.run()


if __name__ == "__main__":
    main()
