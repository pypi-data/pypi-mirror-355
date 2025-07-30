"""
Account and wallet analysis functionality using ZerionWalletAnalysisAgent and direct Solana RPC.
"""

import asyncio
import json
import aiohttp
from typing import Dict, Any, List
from ..api.mesh_api import call_mesh_api, HEURIST_API_KEY


async def _fetch_evm_wallet_tokens_internal(wallet_address: str) -> Dict[str, Any]:
    """Fetch token holdings of an EVM wallet."""
    if not wallet_address:
        raise ValueError("wallet_address is required")
    
    request_data = {
        "agent_id": "ZerionWalletAnalysisAgent",
        "input": {
            "tool": "fetch_wallet_tokens",
            "tool_arguments": {
                "wallet_address": wallet_address
            }
        }
    }
    
    if HEURIST_API_KEY:
        request_data["api_key"] = HEURIST_API_KEY
    
    try:
        result = await call_mesh_api("mesh_request", method="POST", json=request_data)
        return result
    except Exception as e:
        raise Exception(f"Failed to fetch EVM wallet tokens: {str(e)}")


async def _fetch_solana_wallet_assets_internal(owner_address: str) -> Dict[str, Any]:
    """Fetch token holdings of a Solana wallet using direct RPC calls with retry logic."""
    if not owner_address:
        raise ValueError("owner_address is required")
    
    endpoint = "https://api.mainnet-beta.solana.com"
    headers = {"Content-Type": "application/json"}
    
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "getTokenAccountsByOwner",
        "params": [
            owner_address,
            {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"},
            {"encoding": "jsonParsed"}
        ]
    }
    
    max_retries = 3
    base_delay = 1  # Base delay in seconds
    
    for attempt in range(max_retries):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(endpoint, headers=headers, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        
                        # Check for RPC error
                        if "error" in data:
                            raise Exception(f"Solana RPC error: {data['error']}")
                        
                        # Parse results
                        tokens = []
                        total_tokens = 0
                        
                        if "result" in data and "value" in data["result"]:
                            for token_account in data["result"]["value"]:
                                try:
                                    info = token_account["account"]["data"]["parsed"]["info"]
                                    token_address = info.get("mint")
                                    amount = info.get("tokenAmount", {}).get("uiAmount")
                                    decimals = info.get("tokenAmount", {}).get("decimals")
                                    raw_amount = info.get("tokenAmount", {}).get("amount")
                                    
                                    # Ensure we have valid data
                                    if token_address and decimals is not None:
                                        # Include all tokens, even those with 0 balance for completeness
                                        tokens.append({
                                            "token_address": token_address,
                                            "balance": amount or 0,
                                            "decimals": decimals,
                                            "raw_amount": raw_amount or "0"
                                        })
                                        
                                        # Only count tokens with positive balance
                                        if amount and amount > 0:
                                            total_tokens += 1
                                            
                                except (KeyError, TypeError, AttributeError) as e:
                                    # Skip malformed token accounts
                                    print(f"Warning: Skipping malformed token account: {e}")
                                    continue
                        
                        return {
                            "owner_address": owner_address,
                            "total_tokens": total_tokens,
                            "tokens": tokens,
                            "status": "success",
                            "source": "direct_solana_rpc"
                        }
                    else:
                        raise Exception(f"HTTP {response.status}: {await response.text()}")
                        
        except Exception as e:
            if attempt == max_retries - 1:  # Last attempt
                raise Exception(f"Failed to fetch Solana wallet assets after {max_retries} attempts: {str(e)}")
            
            # Exponential backoff with jitter
            delay = base_delay * (2 ** attempt) + (0.1 * attempt)  # Add small jitter
            print(f"Attempt {attempt + 1} failed: {str(e)}. Retrying in {delay:.1f} seconds...")
            await asyncio.sleep(delay)


def _detect_wallet_type(address: str) -> str:
    """Detect wallet type based on address format."""
    if not address or address == "":
        raise ValueError("Address cannot be empty")
    
    # EVM addresses: start with 0x and are 42 characters long
    if address.startswith("0x") and len(address) == 42:
        return "evm"
    
    # Solana addresses: typically 32-44 characters, base58 encoded, no 0x prefix
    if not address.startswith("0x") and 32 <= len(address) <= 44:
        # Basic check for base58 characters (simplified)
        base58_chars = set("123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz")
        if all(c in base58_chars for c in address):
            return "solana"
    
    # If we can't determine, return unknown
    return "unknown"


async def _fetch_wallet_balance_internal(wallet_address: str, wallet_type: str = "") -> Dict[str, Any]:
    """Fetch wallet balance for both EVM and Solana wallets with auto-detection."""
    
    # Auto-detect wallet type if not provided
    if not wallet_type:
        wallet_type = _detect_wallet_type(wallet_address)
    
    combined_results = {
        "wallet_address": wallet_address,
        "detected_type": wallet_type,
        "analysis_metadata": {
            "total_sources": 0,
            "successful_sources": 0,
            "analysis_types": []
        },
        "evm_results": None,
        "solana_results": None,
        "summary": {
            "total_evm_tokens": 0,
            "total_solana_tokens": 0,
            "supported_chains": []
        }
    }
    
    # Try EVM analysis if detected as EVM or unknown
    if wallet_type in ["evm", "unknown"]:
        combined_results["analysis_metadata"]["analysis_types"].append("EVM")
        combined_results["analysis_metadata"]["total_sources"] += 1
        try:
            evm_results = await _fetch_evm_wallet_tokens_internal(wallet_address)
            combined_results["evm_results"] = evm_results
            combined_results["analysis_metadata"]["successful_sources"] += 1
            
            # Update summary from EVM results
            if evm_results and isinstance(evm_results, dict):
                # Try to extract token count from various possible result structures
                if "tokens" in evm_results:
                    combined_results["summary"]["total_evm_tokens"] = len(evm_results["tokens"])
                elif "data" in evm_results and isinstance(evm_results["data"], list):
                    combined_results["summary"]["total_evm_tokens"] = len(evm_results["data"])
                
        except Exception as e:
            combined_results["evm_results"] = {"error": f"EVM wallet analysis failed: {str(e)}"}
    
    # Try Solana analysis if detected as Solana or unknown
    if wallet_type in ["solana", "unknown"]:
        combined_results["analysis_metadata"]["analysis_types"].append("Solana")
        combined_results["analysis_metadata"]["total_sources"] += 1
        try:
            solana_results = await _fetch_solana_wallet_assets_internal(wallet_address)
            combined_results["solana_results"] = solana_results
            combined_results["analysis_metadata"]["successful_sources"] += 1
            
            # Update summary from Solana results
            if solana_results and solana_results.get("total_tokens"):
                combined_results["summary"]["total_solana_tokens"] = solana_results["total_tokens"]
                
        except Exception as e:
            combined_results["solana_results"] = {"error": f"Solana wallet analysis failed: {str(e)}"}
    
    # If wallet type is unknown and both failed, provide guidance
    if wallet_type == "unknown" and combined_results["analysis_metadata"]["successful_sources"] == 0:
        combined_results["guidance"] = {
            "message": "Unable to determine wallet type from address format",
            "evm_format": "EVM addresses start with 0x and are 42 characters long",
            "solana_format": "Solana addresses are 32-44 characters, base58 encoded, no 0x prefix",
            "suggestion": "Please verify the wallet address format"
        }
    
    return combined_results


def register_account_tools(mcp):
    """Register account-related MCP tools."""
    
    @mcp.tool()
    async def fetch_wallet_balance(wallet_address: str, wallet_type: str = "") -> str:
        """
        Fetch token holdings and balances for both EVM and Solana wallets with automatic wallet type detection.
        
        This comprehensive wallet analysis tool supports multiple blockchain ecosystems:
        
        **EVM Wallet Analysis (Ethereum, Polygon, BSC, etc.):**
        - Uses ZerionWalletAnalysisAgent for comprehensive multi-chain analysis
        - Token symbols, names, and balances across all supported EVM chains
        - USD values and portfolio percentages
        - 24-hour price changes and market data
        - Contract addresses and chain information
        - Total portfolio value calculation
        
        **Solana Wallet Analysis:**
        - Direct Solana RPC integration for real-time data
        - All SPL token holdings and balances
        - Token contract addresses (mint addresses)
        - Token decimals and raw amounts
        - Built-in retry logic for maximum reliability
        
        **Auto-Detection Features:**
        - Automatically detects wallet type based on address format
        - EVM: Addresses starting with 0x (42 characters)
        - Solana: Base58 encoded addresses (32-44 characters)
        - Attempts analysis on both chains if type is uncertain
        
        **Combined Results Include:**
        - Unified response format with results from both ecosystems
        - Analysis metadata showing which methods were successful
        - Summary statistics for total tokens across chains
        - Error handling and guidance for unsupported formats
        
        Perfect for:
        - Multi-chain portfolio analysis and tracking
        - Cross-ecosystem wallet comparison
        - Comprehensive asset discovery
        - DeFi position monitoring across chains
        - Automated wallet type detection and analysis
        
        Args:
            wallet_address: The wallet address to analyze (EVM: 0x... or Solana: base58)
            wallet_type: Optional wallet type ("evm" or "solana"). If not provided, auto-detection is used
        """
        try:
            result = await _fetch_wallet_balance_internal(wallet_address, wallet_type)
            return str(result)
        except Exception as e:
            return f"Error: {str(e)}" 