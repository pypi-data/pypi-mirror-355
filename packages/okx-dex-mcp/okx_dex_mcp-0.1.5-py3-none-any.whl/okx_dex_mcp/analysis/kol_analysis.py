"""
KOL (Key Opinion Leader) and blockchain intelligence analysis functionality using MindAiKolAgent and ArkhamIntelligenceAgent.
"""

from typing import Optional
from ..api.mesh_api import call_mesh_api, HEURIST_API_KEY


async def _get_best_initial_calls_internal(
    period: int = 168,
    token_category: Optional[str] = None,
    kol_name: Optional[str] = None,
    token_symbol: Optional[str] = None
) -> dict:
    """Get the best initial calls for a specific token or from a specific KOL."""
    # Build tool arguments
    tool_arguments = {"period": period}
    
    if token_category:
        if token_category not in ["top100", "top500", "lowRank"]:
            raise ValueError("token_category must be one of: top100, top500, lowRank")
        tool_arguments["token_category"] = token_category
    
    if kol_name:
        tool_arguments["kol_name"] = kol_name
    
    if token_symbol:
        tool_arguments["token_symbol"] = token_symbol
    
    # Build request data for MindAiKolAgent
    request_data = {
        "agent_id": "MindAiKolAgent",
        "input": {
            "tool": "get_best_initial_calls",
            "tool_arguments": tool_arguments
        }
    }
    
    if HEURIST_API_KEY:
        request_data["api_key"] = HEURIST_API_KEY
    
    try:
        result = await call_mesh_api("mesh_request", method="POST", json=request_data)
        return result
    except Exception as e:
        raise Exception(f"Failed to get best initial calls: {str(e)}")


async def _get_kol_statistics_internal(period: int = 168, kol_name: Optional[str] = None) -> dict:
    """Get performance statistics for KOLs."""
    # Build tool arguments
    tool_arguments = {"period": period}
    
    if kol_name:
        tool_arguments["kol_name"] = kol_name
    
    # Build request data for MindAiKolAgent
    request_data = {
        "agent_id": "MindAiKolAgent",
        "input": {
            "tool": "get_kol_statistics",
            "tool_arguments": tool_arguments
        }
    }
    
    if HEURIST_API_KEY:
        request_data["api_key"] = HEURIST_API_KEY
    
    try:
        result = await call_mesh_api("mesh_request", method="POST", json=request_data)
        return result
    except Exception as e:
        raise Exception(f"Failed to get KOL statistics: {str(e)}")


async def _get_token_statistics_internal(token_symbol: str, period: int = 168) -> dict:
    """Get performance statistics for tokens."""
    if not token_symbol:
        raise ValueError("token_symbol is required")
    
    # Build request data for MindAiKolAgent
    request_data = {
        "agent_id": "MindAiKolAgent",
        "input": {
            "tool": "get_token_statistics",
            "tool_arguments": {
                "token_symbol": token_symbol,
                "period": period
            }
        }
    }
    
    if HEURIST_API_KEY:
        request_data["api_key"] = HEURIST_API_KEY
    
    try:
        result = await call_mesh_api("mesh_request", method="POST", json=request_data)
        return result
    except Exception as e:
        raise Exception(f"Failed to get token statistics: {str(e)}")


async def _get_top_gainers_internal(
    period: int = 168,
    token_category: str = "top100",
    tokens_amount: int = 5,
    kols_amount: int = 3
) -> dict:
    """Get top gaining tokens and the KOLs who called them."""
    # Validate parameters
    if token_category not in ["top100", "top500", "lowRank"]:
        raise ValueError("token_category must be one of: top100, top500, lowRank")
    
    if not (1 <= tokens_amount <= 10):
        raise ValueError("tokens_amount must be between 1 and 10")
    
    if not (3 <= kols_amount <= 10):
        raise ValueError("kols_amount must be between 3 and 10")
    
    # Build request data for MindAiKolAgent
    request_data = {
        "agent_id": "MindAiKolAgent",
        "input": {
            "tool": "get_top_gainers",
            "tool_arguments": {
                "period": period,
                "token_category": token_category,
                "tokens_amount": tokens_amount,
                "kols_amount": kols_amount
            }
        }
    }
    
    if HEURIST_API_KEY:
        request_data["api_key"] = HEURIST_API_KEY
    
    try:
        result = await call_mesh_api("mesh_request", method="POST", json=request_data)
        return result
    except Exception as e:
        raise Exception(f"Failed to get top gainers: {str(e)}")


async def _get_token_holders_internal(chain: str, address: str, groupByEntity: bool = True) -> dict:
    """Get the top holders of a specific token, including their balances, USD values, and percentage of total supply."""
    if not chain:
        raise ValueError("chain is required")
    if not address:
        raise ValueError("address is required")
    
    # Build request data for ArkhamIntelligenceAgent
    request_data = {
        "agent_id": "ArkhamIntelligenceAgent",
        "input": {
            "tool": "get_token_holders",
            "tool_arguments": {
                "chain": chain,
                "address": address,
                "groupByEntity": groupByEntity
            }
        }
    }
    
    if HEURIST_API_KEY:
        request_data["api_key"] = HEURIST_API_KEY
    
    try:
        result = await call_mesh_api("mesh_request", method="POST", json=request_data)
        return result
    except Exception as e:
        raise Exception(f"Failed to get token holders for {address} on {chain}: {str(e)}")


def register_kol_analysis_tools(mcp):
    """Register KOL analysis and blockchain intelligence related MCP tools."""
    
    @mcp.tool()
    async def get_best_initial_calls(
        period: int = 168,
        token_category: Optional[str] = None,
        kol_name: Optional[str] = None,
        token_symbol: Optional[str] = None
    ) -> str:
        """
        Get the best initial calls for a specific token or from a specific KOL.
        
        This tool analyzes KOL (Key Opinion Leader) performance and identifies the most successful
        early token calls. ROA (Return on Assets) measures the performance of a token call by a KOL,
        showing how profitable their recommendations have been over time.
        
        Perfect for:
        - Identifying top-performing KOLs and their successful calls
        - Finding which KOLs made the best early calls on specific tokens
        - Analyzing ROA performance across different time periods
        - Discovering successful token recommendations by category
        
        The analysis includes:
        - KOL names and their call performance
        - Token symbols and call timing
        - ROA metrics and return percentages
        - Call success rates and timing analysis
        - Category-based performance filtering
        
        Args:
            period: Time period in hours to look back (default: 168 hours/7 days)
            token_category: Optional category filter - 'top100', 'top500', or 'lowRank'
            kol_name: Optional KOL name filter (e.g., '@agentcookiefun')
            token_symbol: Optional token symbol filter (e.g., 'BTC', 'ETH')
        """
        try:
            result = await _get_best_initial_calls_internal(period, token_category, kol_name, token_symbol)
            return str(result)
        except Exception as e:
            return f"Error: {str(e)}"
    
    @mcp.tool()
    async def get_kol_statistics(period: int = 168, kol_name: Optional[str] = None) -> str:
        """
        Get comprehensive performance statistics for KOLs.
        
        This tool provides detailed analytics on KOL performance across multiple tokens and time periods.
        ROA (Return on Assets) measures the overall performance of token calls made by KOLs,
        helping identify the most successful and consistent performers in the space.
        
        Perfect for:
        - Evaluating KOL track records and reliability
        - Comparing performance across different KOLs
        - Understanding call success rates and timing
        - Analyzing consistent performers over time
        
        The statistics include:
        - Overall ROA performance metrics
        - Number of successful vs unsuccessful calls
        - Average return percentages and timing
        - Call frequency and consistency analysis
        - Performance trends over different periods
        - Success rate comparisons and rankings
        
        Args:
            period: Time period in hours to look back (default: 168 hours/7 days)
            kol_name: Optional specific KOL name to analyze (e.g., '@agentcookiefun')
        """
        try:
            result = await _get_kol_statistics_internal(period, kol_name)
            return str(result)
        except Exception as e:
            return f"Error: {str(e)}"
    
    @mcp.tool()
    async def get_token_statistics(token_symbol: str, period: int = 168) -> str:
        """
        Get comprehensive performance statistics for tokens.
        
        This tool analyzes token performance and identifies which KOLs have called them,
        providing insights into token momentum and KOL influence. ROA (Return on Assets)
        measures token performance after being called by various KOLs.
        
        Perfect for:
        - Understanding token performance after KOL calls
        - Identifying which KOLs have influence on specific tokens
        - Analyzing token momentum and call impact
        - Tracking token performance across different timeframes
        
        The analysis includes:
        - Token ROA performance metrics
        - List of KOLs who have called the token
        - Call timing and impact analysis
        - Performance comparisons across calls
        - Success rates of different KOL calls
        - Token momentum and trend analysis
        
        Args:
            token_symbol: Symbol of the token to analyze (e.g., 'BTC', 'ETH', 'DOGE')
            period: Time period in hours to look back (default: 168 hours/7 days)
        """
        try:
            result = await _get_token_statistics_internal(token_symbol, period)
            return str(result)
        except Exception as e:
            return f"Error: {str(e)}"
    
    @mcp.tool()
    async def get_top_gainers(
        period: int = 168,
        token_category: str = "top100",
        tokens_amount: int = 5,
        kols_amount: int = 3
    ) -> str:
        """
        Get top gaining tokens and the KOLs who called them.
        
        This powerful tool identifies the best performing tokens and reveals which KOLs made
        successful calls on them. ROA (Return on Assets) measures token performance after
        KOL calls, helping identify both winning tokens and successful KOL recommendations.
        
        Perfect for:
        - Discovering trending and high-performing tokens
        - Finding KOLs who consistently call winners
        - Analyzing market momentum and KOL influence
        - Identifying successful token categories and patterns
        
        The analysis includes:
        - Top gaining tokens by performance metrics
        - KOLs who made successful calls on each token
        - ROA performance and return percentages
        - Call timing and impact analysis
        - Category-based performance insights
        - KOL success rate rankings per token
        
        Args:
            period: Time period in hours to look back (default: 168 hours/7 days)
            token_category: Category filter - 'top100', 'top500', or 'lowRank' (default: 'top100')
            tokens_amount: Number of top tokens to return, 1-10 (default: 5)
            kols_amount: Number of KOLs to return per token, 3-10 (default: 3)
        """
        try:
            result = await _get_top_gainers_internal(period, token_category, tokens_amount, kols_amount)
            return str(result)
        except Exception as e:
            return f"Error: {str(e)}"
    
    @mcp.tool()
    async def get_token_holders(chain: str, address: str, groupByEntity: bool = True) -> str:
        """
        Get the top holders of a specific token, including their balances, USD values, and percentage of total supply.
        
        This comprehensive on-chain analysis tool provides detailed insights into token distribution
        and holder composition using Arkham Intelligence's advanced blockchain analytics platform.
        Perfect for understanding token ownership patterns, identifying major stakeholders, and
        analyzing concentration risks in any cryptocurrency project.
        
        Key Features:
        - Complete token holder breakdown and rankings
        - Real-time balance tracking and USD valuations
        - Percentage ownership of total token supply
        - Entity grouping and institutional identification
        - Exchange and whale wallet detection
        - Historical holder analysis and trends
        
        Detailed Analysis Provided:
        - Top token holders ranked by balance size
        - Individual wallet addresses and their holdings
        - USD value calculations at current market prices
        - Percentage of total supply held by each address
        - Known entity identification (exchanges, institutions, DAOs)
        - Wallet categorization and labeling
        - Distribution metrics and concentration analysis
        
        Entity Grouping Benefits:
        - Aggregates holdings by known organizations
        - Identifies exchange wallets and hot/cold storage
        - Groups institutional investors and funds
        - Reveals DAO treasury holdings and governance tokens
        - Consolidates multi-signature wallet holdings
        - Provides cleaner, more meaningful data insights
        
        Strategic Applications:
        - Investment due diligence and risk assessment
        - Token distribution analysis for new projects
        - Whale watching and large holder monitoring
        - Concentration risk evaluation for portfolios
        - Market manipulation risk assessment
        - Governance token voting power analysis
        - Exchange reserve monitoring and tracking
        
        Risk Analysis Features:
        - Concentration risk metrics (how many holders control majority)
        - Exchange exposure and liquidity risks
        - Single points of failure identification
        - Whale accumulation and distribution patterns
        - Token unlock and vesting schedule impacts
        - Market maker and liquidity provider identification
        
        Perfect for traders, analysts, researchers, and institutions who need comprehensive
        on-chain intelligence about token ownership and distribution patterns.
        
        Args:
            chain: The blockchain network where the token exists (e.g., 'ethereum', 'polygon', 'bsc', 'arbitrum')
            address: The token contract address to analyze
            groupByEntity: Whether to group holders by known entities like exchanges and institutions (default: True)
        """
        try:
            result = await _get_token_holders_internal(chain, address, groupByEntity)
            return str(result)
        except Exception as e:
            return f"Error: {str(e)}" 