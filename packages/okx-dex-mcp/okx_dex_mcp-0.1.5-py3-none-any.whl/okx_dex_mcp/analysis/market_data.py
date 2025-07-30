"""
Market data and token information from OKX DEX API.
"""

from ..utils.constants import OKX_API_KEY, OKX_SECRET_KEY, OKX_PASSPHRASE, OKX_API_BASE
from ..api.okx_api import make_okx_request


async def _get_chain_top_tokens_internal(chain_id: str, limit: int = 20) -> dict:
    """Get top tokens by market cap on a specific chain."""
    if not all([OKX_API_KEY, OKX_SECRET_KEY, OKX_PASSPHRASE]):
        raise Exception("OKX API credentials not configured. Please set OKX_API_KEY, OKX_SECRET_KEY, and OKX_PASSPHRASE in .env file.")
    
    if limit > 50:
        limit = 50
        
    url = f"{OKX_API_BASE}/api/v5/dex/aggregator/all-tokens?chainId={chain_id}&limit={limit}"
    data = await make_okx_request(url)
    
    if not data:
        raise Exception(f"Unable to fetch top tokens for chain {chain_id}.")
    
    return data


def register_market_data_tools(mcp):
    """Register market data related MCP tools."""
    
    @mcp.tool()
    async def get_chain_top_tokens(chain_id: str, limit: int = 20) -> str:
        """Get top tokens by market cap on a specific chain.
        
        This tool retrieves the most valuable and actively traded tokens on a specific blockchain network
        ranked by market capitalization and trading volume. It provides comprehensive token information
        including prices, market metrics, contract addresses, and trading statistics.
        
        The analysis includes:
        - Token symbols, names, and contract addresses
        - Current prices and market capitalizations
        - 24-hour trading volumes and price changes
        - Liquidity information and trading pairs
        - Token decimals and technical details
        - DEX trading statistics and availability
        
        Perfect for discovering top-performing tokens on specific chains, market analysis,
        portfolio research, and identifying trending cryptocurrencies by blockchain network.

        Args:
            chain_id: Chain ID (e.g., "1" for Ethereum, "56" for BSC, "137" for Polygon)
            limit: Number of tokens to return (maximum 50, default: 20)
        """
        try:
            result = await _get_chain_top_tokens_internal(chain_id, limit)
            return str(result)
        except Exception as e:
            return f"Error: {str(e)}" 