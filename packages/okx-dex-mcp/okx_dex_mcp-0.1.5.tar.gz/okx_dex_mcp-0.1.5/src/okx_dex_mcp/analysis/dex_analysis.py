"""
DEX analysis functionality using DexScreenerTokenInfoAgent.
"""

from dotenv import load_dotenv
from ..api.mesh_api import call_mesh_api, HEURIST_API_KEY
from ..utils.constants import OKX_API_KEY, OKX_SECRET_KEY, OKX_PASSPHRASE, OKX_API_BASE
from ..api.okx_api import make_okx_request

# Load environment variables for mesh API
load_dotenv()


async def _get_specific_pair_info_internal(chain: str, pair_address: str) -> dict:
    """Get detailed information about a specific trading pair."""
    if not chain:
        raise ValueError("chain is required")
    if not pair_address:
        raise ValueError("pair_address is required")
    
    # Build request data for DexScreenerTokenInfoAgent
    request_data = {
        "agent_id": "DexScreenerTokenInfoAgent",
        "input": {
            "tool": "get_specific_pair_info",
            "tool_arguments": {
                "chain": chain,
                "pair_address": pair_address
            }
        }
    }
    
    if HEURIST_API_KEY:
        request_data["api_key"] = HEURIST_API_KEY
    
    try:
        result = await call_mesh_api("mesh_request", method="POST", json=request_data)
        return result
    except Exception as e:
        raise Exception(f"Failed to get pair info for {pair_address} on {chain}: {str(e)}")


async def _get_token_pairs_internal(chain: str, token_address: str) -> dict:
    """Get all trading pairs for a specific token."""
    if not chain:
        raise ValueError("chain is required")
    if not token_address:
        raise ValueError("token_address is required")
    
    # Build request data for DexScreenerTokenInfoAgent
    request_data = {
        "agent_id": "DexScreenerTokenInfoAgent",
        "input": {
            "tool": "get_token_pairs",
            "tool_arguments": {
                "chain": chain,
                "token_address": token_address
            }
        }
    }
    
    if HEURIST_API_KEY:
        request_data["api_key"] = HEURIST_API_KEY
    
    try:
        result = await call_mesh_api("mesh_request", method="POST", json=request_data)
        return result
    except Exception as e:
        raise Exception(f"Failed to get token pairs for {token_address} on {chain}: {str(e)}")


async def _search_erc20_tokens_internal(token_name: str, chain_name: str = "") -> dict:
    """Search for ERC-20 tokens by name or symbol using both DexScreener and OKX API."""
    # Build search term by concatenating token name and chain name if provided
    search_term = token_name
    if chain_name:
        search_term = f"{token_name} {chain_name}"
    
    results = {
        "dexscreener_results": None,
        "okx_results": None,
        "combined_summary": {
            "search_term": search_term,
            "chain_name": chain_name,
            "total_sources": 2,
            "successful_sources": 0
        }
    }
    
    # Call DexScreenerTokenInfoAgent
    try:
        request_data = {
            "agent_id": "DexScreenerTokenInfoAgent",
            "input": {
                "tool": "search_pairs",
                "tool_arguments": {
                    "search_term": search_term
                }
            }
        }
        if HEURIST_API_KEY:
            request_data["api_key"] = HEURIST_API_KEY
        
        dexscreener_result = await call_mesh_api("mesh_request", method="POST", json=request_data)
        results["dexscreener_results"] = dexscreener_result
        results["combined_summary"]["successful_sources"] += 1
    except Exception as e:
        results["dexscreener_results"] = {"error": f"DexScreener search failed: {str(e)}"}
    
    # Call OKX API for tokens
    try:
        if not all([OKX_API_KEY, OKX_SECRET_KEY, OKX_PASSPHRASE]):
            results["okx_results"] = {"error": "OKX API credentials not configured"}
        else:
            # Map common chain names to chainId values
            chain_id_mapping = {
                "ethereum": "1",
                "bsc": "56", 
                "binance smart chain": "56",
                "polygon": "137",
                "avalanche": "43114",
                "arbitrum": "42161",
                "optimism": "10",
                "fantom": "250",
                "solana": "501"
            }
            
            target_chain_id = None
            matched_chain_name = None
            
            if chain_name:
                # Try to find chainId from mapping first
                chain_lower = chain_name.lower()
                for name, chain_id in chain_id_mapping.items():
                    if chain_lower in name or name in chain_lower:
                        target_chain_id = chain_id
                        matched_chain_name = chain_name
                        break
                
                # If not found in mapping, try the supported chains API
                if not target_chain_id:
                    chains_url = f"{OKX_API_BASE}/api/v5/dex/aggregator/supported/chain"
                    chains_data = await make_okx_request(chains_url)
                    
                    if chains_data and chains_data.get("data"):
                        for chain in chains_data["data"]:
                            chain_name_api = chain.get("chainName", "").lower()
                            if chain_name.lower() in chain_name_api or chain_name_api in chain_name.lower():
                                # Try to get chainId from the chain data, fallback to chainIndex
                                target_chain_id = chain.get("chainId") or chain.get("chainIndex")
                                matched_chain_name = chain.get("chainName")
                                break
                
                if target_chain_id:
                    results["combined_summary"]["mapped_chain_id"] = target_chain_id
                    results["combined_summary"]["mapped_chain_name"] = matched_chain_name
            
            # Try to get tokens - use chainId parameter if we have one
            filtered_tokens = []
            search_lower = token_name.lower()
            
            if target_chain_id:
                # Search specific chain
                tokens_url = f"{OKX_API_BASE}/api/v5/dex/aggregator/all-tokens?chainId={target_chain_id}&limit=100"
                tokens_data = await make_okx_request(tokens_url)
            else:
                # Search popular chains
                chains_to_search = ["1", "56", "137", "43114", "501"]  # ETH, BSC, Polygon, Avalanche, Solana
                all_chain_tokens = []
                
                for chain_id in chains_to_search:
                    chain_url = f"{OKX_API_BASE}/api/v5/dex/aggregator/all-tokens?chainId={chain_id}&limit=100"
                    chain_data = await make_okx_request(chain_url)
                    
                    if chain_data and chain_data.get("code") == "0" and chain_data.get("data"):
                        # Add chainId to each token
                        for token in chain_data["data"]:
                            token["chainId"] = chain_id
                        all_chain_tokens.extend(chain_data["data"])
                
                # Create a mock response structure
                tokens_data = {
                    "code": "0",
                    "msg": "Success",
                    "data": all_chain_tokens
                }
            
            if tokens_data and tokens_data.get("code") == "0" and tokens_data.get("data"):
                # Filter tokens that match the search term
                for token in tokens_data["data"]:
                    token_symbol = token.get("tokenSymbol", "").lower()
                    token_name_api = token.get("tokenName", "").lower()
                    
                    # Match by symbol or name
                    if (search_lower in token_symbol or 
                        search_lower in token_name_api or
                        token_symbol.startswith(search_lower) or
                        token_name_api.startswith(search_lower)):
                        
                        # Add chain information to token data if we have it
                        token_with_chain = token.copy()
                        if target_chain_id and matched_chain_name:
                            token_with_chain["chainId"] = target_chain_id
                            token_with_chain["chainName"] = matched_chain_name
                        filtered_tokens.append(token_with_chain)
                
                # Remove duplicates based on contract address
                unique_tokens = []
                seen_addresses = set()
                for token in filtered_tokens:
                    addr = token.get('tokenContractAddress', '')
                    if addr not in seen_addresses:
                        seen_addresses.add(addr)
                        unique_tokens.append(token)
                
                results["okx_results"] = {
                    "code": tokens_data.get("code", "0"),
                    "msg": tokens_data.get("msg", "Success"),
                    "data": unique_tokens,
                    "total_matches": len(unique_tokens),
                    "chain_filter_applied": target_chain_id is not None,
                    "target_chain_id": target_chain_id,
                    "target_chain_name": matched_chain_name
                }
                results["combined_summary"]["successful_sources"] += 1
            else:
                error_msg = "OKX API returned no data"
                if tokens_data and tokens_data.get("msg"):
                    error_msg = f"OKX API error: {tokens_data.get('msg')}"
                results["okx_results"] = {"error": error_msg, "raw_response": tokens_data}
    except Exception as e:
        results["okx_results"] = {"error": f"OKX API search failed: {str(e)}"}
    
    return results





async def _search_native_tokens_internal(chain_name: str = "", filter_symbol: str = "") -> dict:
    """Search and retrieve information about native tokens across supported chains."""
    from ..utils.constants import NATIVE_TOKENS, CHAIN_NAMES, BRIDGE_TOKENS
    
    native_tokens_info = []
    
    # If chain_name is provided, filter by it
    if chain_name:
        # Find matching chain ID
        target_chain_id = None
        chain_lower = chain_name.lower()
        
        for chain_id, name in CHAIN_NAMES.items():
            if chain_lower in name.lower() or name.lower() in chain_lower:
                target_chain_id = chain_id
                break
        
        if target_chain_id:
            chain_ids_to_check = [target_chain_id]
        else:
            chain_ids_to_check = []
    else:
        chain_ids_to_check = list(NATIVE_TOKENS.keys())
    
    for chain_id in chain_ids_to_check:
        if chain_id in NATIVE_TOKENS and chain_id in CHAIN_NAMES:
            native_address = NATIVE_TOKENS[chain_id]
            chain_name_display = CHAIN_NAMES[chain_id]
            
            # Determine native token symbol based on chain
            if chain_id == "1" or chain_id == "42161" or chain_id == "10" or chain_id == "8453":  # Ethereum chains
                symbol = "ETH"
                name = "Ethereum"
            elif chain_id == "56":  # BSC
                symbol = "BNB"
                name = "Binance Coin"
            elif chain_id == "137":  # Polygon
                symbol = "MATIC"
                name = "Polygon"
            elif chain_id == "43114":  # Avalanche
                symbol = "AVAX"
                name = "Avalanche"
            elif chain_id == "501":  # Solana
                symbol = "SOL"
                name = "Solana"
            else:
                symbol = "NATIVE"
                name = "Native Token"
            
            # Apply symbol filter if provided
            if filter_symbol and filter_symbol.upper() not in symbol.upper():
                continue
                
            token_info = {
                "symbol": symbol,
                "name": name,
                "chainId": chain_id,
                "chainName": chain_name_display,
                "nativeAddress": native_address,
                "isNative": True,
                "tokenType": "Native",
                "bridgeTokens": BRIDGE_TOKENS.get(chain_id, {})
            }
            
            native_tokens_info.append(token_info)
    
    return {
        "native_tokens": native_tokens_info,
        "total_chains": len(native_tokens_info),
        "search_filters": {
            "chain_name": chain_name,
            "symbol_filter": filter_symbol
        },
        "available_chains": list(CHAIN_NAMES.values())
    }


async def _search_all_tokens_internal(token_name: str, chain_name: str = "", filter_symbol: str = "") -> dict:
    """Search for both ERC-20/SPL tokens and native tokens, returning combined results."""
    
    # Determine which search to perform based on filter_symbol
    native_token_symbols = {"ETH", "BNB", "MATIC", "AVAX", "SOL"}
    search_native = True
    search_erc20 = True
    
    # If filter_symbol is provided and it's a known native token, prioritize native search
    if filter_symbol and filter_symbol.upper() in native_token_symbols:
        # Still search both, but native will likely have better results
        pass
    
    # If token_name matches a native token symbol, include native search
    if token_name.upper() in native_token_symbols:
        # Still search both for comprehensive results
        pass
    
    combined_results = {
        "search_metadata": {
            "query": {
                "token_name": token_name,
                "chain_name": chain_name,
                "filter_symbol": filter_symbol
            },
            "search_types": [],
            "successful_searches": 0,
            "total_searches": 0
        },
        "erc20_results": None,
        "native_results": None,
        "summary": {
            "total_erc20_sources": 0,
            "successful_erc20_sources": 0,
            "total_native_tokens": 0,
            "matching_chains": []
        }
    }
    
    # Search ERC-20/SPL tokens
    if search_erc20:
        combined_results["search_metadata"]["search_types"].append("ERC20/SPL")
        combined_results["search_metadata"]["total_searches"] += 1
        try:
            erc20_results = await _search_erc20_tokens_internal(token_name, chain_name)
            combined_results["erc20_results"] = erc20_results
            
            # Update summary from ERC-20 results
            if erc20_results and erc20_results.get("combined_summary"):
                combined_results["summary"]["total_erc20_sources"] = erc20_results["combined_summary"].get("total_sources", 0)
                combined_results["summary"]["successful_erc20_sources"] = erc20_results["combined_summary"].get("successful_sources", 0)
            
            combined_results["search_metadata"]["successful_searches"] += 1
        except Exception as e:
            combined_results["erc20_results"] = {"error": f"ERC-20 search failed: {str(e)}"}
    
    # Search native tokens
    if search_native:
        combined_results["search_metadata"]["search_types"].append("Native")
        combined_results["search_metadata"]["total_searches"] += 1
        try:
            # Use token_name as filter_symbol if no specific filter_symbol provided
            native_filter = filter_symbol if filter_symbol else token_name
            native_results = await _search_native_tokens_internal(chain_name, native_filter)
            combined_results["native_results"] = native_results
            
            # Update summary from native results
            if native_results:
                combined_results["summary"]["total_native_tokens"] = native_results.get("total_chains", 0)
                if native_results.get("native_tokens"):
                    combined_results["summary"]["matching_chains"] = [
                        token["chainName"] for token in native_results["native_tokens"]
                    ]
            
            combined_results["search_metadata"]["successful_searches"] += 1
        except Exception as e:
            combined_results["native_results"] = {"error": f"Native token search failed: {str(e)}"}
    
    return combined_results


def register_dex_analysis_tools(mcp):
    """Register DEX analysis related MCP tools."""
    
    # @mcp.tool()
    # async def get_specific_pair_info(chain: str, pair_address: str) -> str:
    #     """Get detailed information about a specific trading pair on a decentralized exchange by chain and pair address.
        
    #     This comprehensive tool provides real-time data about a specific DEX trading pair using DexScreener data.
    #     Perfect for analyzing specific liquidity pools, tracking pair performance, and making informed trading decisions.
        
    #     Key Features:
    #     - Real-time price and volume data from DexScreener
    #     - Comprehensive liquidity pool analysis
    #     - 24-hour trading metrics and price changes
    #     - Historical trading patterns and trends
    #     - Exchange-specific pair information
    #     - Token pair composition and ratios
        
    #     Trading Insights Provided:
    #     - Current token prices and exchange rates
    #     - 24-hour volume and trading activity
    #     - Total value locked (TVL) in the liquidity pool
    #     - Price change percentages (1h, 24h, 7d)
    #     - Bid/ask spreads and market depth
    #     - Recent trading history and patterns
    #     - Liquidity provider metrics
    #     - Fee structures and APY calculations
        
    #     Use Cases:
    #     - Analyzing specific liquidity pools before trading
    #     - Monitoring pair performance and volatility
    #     - Researching arbitrage opportunities between pairs
    #     - Tracking liquidity changes and market depth
    #     - Evaluating trading costs and slippage potential
    #     - Comparing pair metrics across different DEXes
        
    #     Important: The pair_address must be the LP (liquidity pool) contract address,
    #     not the individual token contract address. This address represents the
    #     specific trading pair on the decentralized exchange.

    #     Args:
    #         chain: Blockchain identifier (e.g., 'solana', 'bsc', 'ethereum', 'base', 'polygon', 'arbitrum')
    #         pair_address: The LP contract address of the trading pair to analyze
    #     """
    #     try:
    #         result = await _get_specific_pair_info_internal(chain, pair_address)
    #         return str(result)
    #     except Exception as e:
    #         return f"Error: {str(e)}"
    
    # @mcp.tool()
    # async def get_token_pairs(chain: str, token_address: str) -> str:
    #     """Get all trading pairs for a specific token across decentralized exchanges by chain and token address.
        
    #     This powerful discovery tool retrieves a comprehensive list of all DEX pairs where the specified token
    #     is actively traded on a particular blockchain. Essential for finding the best trading venues,
    #     comparing liquidity across exchanges, and identifying arbitrage opportunities.
        
    #     Key Features:
    #     - Complete pair discovery across all major DEXes
    #     - Real-time liquidity and volume comparisons
    #     - Cross-exchange trading analysis
    #     - Multi-DEX pair performance metrics
    #     - Comprehensive market coverage
        
    #     Trading Data Provided:
    #     - All available trading pairs for the token
    #     - Exchange platforms and DEX protocols
    #     - Paired tokens and their contract addresses
    #     - Current prices across different pairs
    #     - 24-hour volume for each trading pair
    #     - Liquidity depth and TVL metrics
    #     - Price differences between exchanges
    #     - Trading fees and transaction costs
        
    #     Market Analysis Features:
    #     - Liquidity concentration analysis
    #     - Volume distribution across pairs
    #     - Price discovery and arbitrage opportunities
    #     - Market maker activity patterns
    #     - Trading pair popularity rankings
    #     - Cross-exchange price comparisons
        
    #     Strategic Applications:
    #     - Finding the most liquid trading venues
    #     - Identifying arbitrage opportunities between DEXes
    #     - Analyzing token distribution and market structure
    #     - Optimizing trade execution across multiple pairs
    #     - Monitoring market fragmentation and concentration
    #     - Discovering new trading opportunities and venues
        
    #     Perfect for traders, arbitrageurs, and analysts who need comprehensive
    #     market intelligence about a specific token's trading landscape.

    #     Args:
    #         chain: Blockchain identifier (e.g., 'solana', 'bsc', 'ethereum', 'base', 'polygon', 'arbitrum')
    #         token_address: The contract address of the token to find all trading pairs for
    #     """
    #     try:
    #         result = await _get_token_pairs_internal(chain, token_address)
    #         return str(result)
    #     except Exception as e:
    #         return f"Error: {str(e)}"
    
    @mcp.tool()
    async def search_tokens(token_name: str, chain_name: str = "", filter_symbol: str = "") -> str:
        """Search for all types of tokens (both ERC-20/SPL and native tokens) by name or symbol.
        
        This comprehensive search tool combines results from multiple token search methods:
        1. **ERC-20/SPL Token Search**: Uses DexScreener and OKX DEX Aggregator to find contract-based tokens
        2. **Native Token Search**: Searches built-in native token database for ETH, BNB, MATIC, AVAX, SOL
        
        The unified search provides:
        
        **ERC-20/SPL Token Results:**
        - Token symbols, names, and contract addresses from DexScreener and OKX
        - Available trading pairs and DEX platforms
        - Current prices and market data
        - Liquidity pools and volume information
        - Multi-chain token availability
        - Cross-platform token verification
        
        **Native Token Results:**
        - Native token symbols (ETH, BNB, MATIC, AVAX, SOL) and names
        - Chain IDs and network names where they're native
        - Native token addresses (used for DEX operations)
        - Available bridge tokens on each chain
        - Token type classification and metadata
        
        **Combined Analysis:**
        - Comprehensive token discovery across all types
        - Both contract-based and native token information
        - Cross-chain availability and deployment analysis
        - Complete market coverage and trading venue discovery
        - Unified results for better decision making
        
        Perfect for:
        - Complete token research and discovery
        - Finding all available forms of a token (native vs contract)
        - Cross-chain token analysis and comparison
        - Comprehensive market intelligence gathering
        - One-stop token information lookup
        - Planning multi-chain trading strategies
        
        Use this tool when you want the most comprehensive token search results,
        combining both contract-based tokens and native blockchain tokens.

        Args:
            token_name: Token name or symbol to search for (e.g., "ETH", "USDC", "Uniswap")
            chain_name: Optional chain name to include in search (e.g., "Ethereum", "Polygon", "BSC")
            filter_symbol: Optional symbol filter for more precise native token matching (e.g., "ETH", "BNB")
        """
        try:
            result = await _search_all_tokens_internal(token_name, chain_name, filter_symbol)
            return str(result)
        except Exception as e:
            return f"Error: {str(e)}"
    

    
 