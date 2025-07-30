#!/usr/bin/env python3
"""
OKX DEX Trading MCP Server
Main entry point for the Model Context Protocol server providing DEX trading capabilities.
"""

from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize FastMCP server
mcp = FastMCP("okx-dex-quotes")

# Import and register tools
from .analysis.market_data import register_market_data_tools
from .analysis.twitter_intelligence import register_twitter_intelligence_tools
from .analysis.kol_analysis import register_kol_analysis_tools
from .analysis.dex_analysis import register_dex_analysis_tools
from .swap.quotes import register_quote_tools
from .swap.swaps import register_swap_tools
from .utils.blockchain import register_blockchain_tools
from .analysis.account import register_account_tools


def register_all_tools():
    """Register all MCP tools with the server."""
    # register_market_data_tools(mcp)
    register_twitter_intelligence_tools(mcp)
    # register_kol_analysis_tools(mcp)
    register_dex_analysis_tools(mcp)

    register_quote_tools(mcp)
    register_swap_tools(mcp)
    register_blockchain_tools(mcp)
    register_account_tools(mcp)

def main():
    """Main entry point for the MCP server."""
    print("🚀 Starting OKX DEX Trading MCP Server...")
    
    # Register all tools
    register_all_tools()
    
    # Start MCP server
    print("📡 MCP server running on stdio transport...")
    mcp.run(transport='stdio')

if __name__ == "__main__":
    main() 