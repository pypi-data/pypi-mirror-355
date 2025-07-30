"""
Simplified blockchain utilities for basic chain information.
"""

from .constants import CHAIN_NAMES, EXPLORER_URLS, RPC_URLS, NATIVE_TOKENS
import httpx
import json
from typing import Optional, Dict, Any

# EVM chain IDs (all chains except Solana)
EVM_CHAINS = {"1", "56", "137", "43114", "42161", "10", "8453", "324", "59144", "5000"}

def is_evm_chain(chain_id: str) -> bool:
    """Check if a chain ID corresponds to an EVM-compatible blockchain."""
    return chain_id in EVM_CHAINS

def get_chain_name(chain_id: str) -> str:
    """Get the display name for a chain ID."""
    return CHAIN_NAMES.get(chain_id, f"Chain {chain_id}")

def get_explorer_url(chain_id: str, tx_hash: str) -> str:
    """Get the block explorer URL for a transaction."""
    base_url = EXPLORER_URLS.get(chain_id)
    if base_url:
        return f"{base_url}{tx_hash}"
    return f"Transaction: {tx_hash}"

def is_supported_chain(chain_id: str) -> bool:
    """Check if a chain ID is supported."""
    return chain_id in CHAIN_NAMES

async def get_native_balance_internal(chainIndex: str, walletAddress: str) -> str:
    """Get native token (gas) balance for a wallet address on specified chain."""
    try:
        url = "https://mcp-node-server-264441234562.us-central1.run.app/getNativeBalance"
        payload = {
            "chainIndex": chainIndex,
            "walletAddress": walletAddress
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                url,
                headers={"Content-Type": "application/json"},
                json=payload,
                timeout=15.0
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("code") == 200:
                    return result.get("data", "No data returned")
                else:
                    return f"❌ Error: {result.get('msg', 'Unknown error')}"
            else:
                return f"❌ HTTP Error {response.status_code}: {response.text}"
                
    except Exception as e:
        return f"❌ Error fetching native balance: {str(e)}"

def register_blockchain_tools(mcp):
    """Register blockchain-related MCP tools."""
    # @mcp.tool()
    # async def get_native_balance(chainIndex: str, walletAddress: str) -> str:
    #     """Get native token (gas) balance for a wallet address on specified chain."""
    #     return await get_native_balance_internal(chainIndex, walletAddress)