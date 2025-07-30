"""
Twitter intelligence functions using ElfaTwitterIntelligenceAgent and CookieProjectInfoAgent.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from ..api.mesh_api import call_mesh_api, HEURIST_API_KEY

logger = logging.getLogger(__name__)


class TwitterIntelligenceError(Exception):
    """Custom exception for Twitter intelligence errors."""
    pass


async def _search_mentions_internal(keywords: List[str], days_ago: int = 20, limit: int = 20) -> Dict[str, Any]:
    """Search for mentions of specific tokens or topics on Twitter."""
    if not keywords:
        raise TwitterIntelligenceError("Keywords list cannot be empty")
    
    if len(keywords) > 5:
        raise TwitterIntelligenceError("Maximum of 5 keywords are allowed")
    
    if limit < 20:
        limit = 20
    elif limit > 30:
        limit = 30
    
    request_data = {
        "agent_id": "ElfaTwitterIntelligenceAgent",
        "input": {
            "tool": "search_mentions",
            "tool_arguments": {
                "keywords": keywords,
                "days_ago": days_ago,
                "limit": limit
            }
        }
    }
    
    if HEURIST_API_KEY:
        request_data["api_key"] = HEURIST_API_KEY
    
    try:
        result = await call_mesh_api("mesh_request", method="POST", json=request_data)
        return result
    except Exception as e:
        logger.error(f"Error searching Twitter mentions for keywords {keywords}: {str(e)}")
        raise TwitterIntelligenceError(f"Failed to search Twitter mentions: {str(e)}")


async def _search_account_internal(username: str, days_ago: int = 30, limit: int = 20) -> Dict[str, Any]:
    """Search for a Twitter account with both mention search and account statistics."""
    if not username:
        raise TwitterIntelligenceError("Username cannot be empty")
    
    username = username.lstrip('@')
    
    request_data = {
        "agent_id": "ElfaTwitterIntelligenceAgent",
        "input": {
            "tool": "search_account",
            "tool_arguments": {
                "username": username,
                "days_ago": days_ago,
                "limit": limit
            }
        }
    }
    
    if HEURIST_API_KEY:
        request_data["api_key"] = HEURIST_API_KEY
    
    try:
        result = await call_mesh_api("mesh_request", method="POST", json=request_data)
        return result
    except Exception as e:
        logger.error(f"Error analyzing Twitter account {username}: {str(e)}")
        raise TwitterIntelligenceError(f"Failed to analyze Twitter account: {str(e)}")


async def _get_trending_tokens_internal(time_window: str = "24h") -> Dict[str, Any]:
    """Get current trending tokens on Twitter."""
    request_data = {
        "agent_id": "ElfaTwitterIntelligenceAgent",
        "input": {
            "tool": "get_trending_tokens",
            "tool_arguments": {
                "time_window": time_window
            }
        }
    }
    
    if HEURIST_API_KEY:
        request_data["api_key"] = HEURIST_API_KEY
    
    try:
        result = await call_mesh_api("mesh_request", method="POST", json=request_data)
        return result
    except Exception as e:
        logger.error(f"Error getting trending tokens: {str(e)}")
        raise TwitterIntelligenceError(f"Failed to get trending tokens: {str(e)}")


async def _get_project_by_twitter_username_internal(twitter_username: str, interval: str = "_7Days") -> Dict[str, Any]:
    """Get comprehensive information about a crypto project by its Twitter username."""
    if not twitter_username:
        raise TwitterIntelligenceError("Twitter username cannot be empty")
    
    twitter_username = twitter_username.lstrip('@')
    
    if interval not in ["_3Days", "_7Days"]:
        interval = "_7Days"
    
    request_data = {
        "agent_id": "CookieProjectInfoAgent",
        "input": {
            "tool": "get_project_by_twitter_username",
            "tool_arguments": {
                "twitter_username": twitter_username,
                "interval": interval
            }
        }
    }
    
    if HEURIST_API_KEY:
        request_data["api_key"] = HEURIST_API_KEY
    
    try:
        result = await call_mesh_api("mesh_request", method="POST", json=request_data)
        return result
    except Exception as e:
        logger.error(f"Error getting project info for Twitter username {twitter_username}: {str(e)}")
        raise TwitterIntelligenceError(f"Failed to get project information: {str(e)}")


async def _get_project_by_contract_address_internal(contract_address: str, interval: str = "_7Days") -> Dict[str, Any]:
    """Get comprehensive information about a crypto project by its contract address."""
    if not contract_address:
        raise TwitterIntelligenceError("Contract address cannot be empty")
    
    if interval not in ["_3Days", "_7Days"]:
        interval = "_7Days"
    
    request_data = {
        "agent_id": "CookieProjectInfoAgent",
        "input": {
            "tool": "get_project_by_contract_address",
            "tool_arguments": {
                "contract_address": contract_address,
                "interval": interval
            }
        }
    }
    
    if HEURIST_API_KEY:
        request_data["api_key"] = HEURIST_API_KEY
    
    try:
        result = await call_mesh_api("mesh_request", method="POST", json=request_data)
        return result
    except Exception as e:
        logger.error(f"Error getting project info for contract address {contract_address}: {str(e)}")
        raise TwitterIntelligenceError(f"Failed to get project information: {str(e)}")


def _detect_identifier_type(identifier: str) -> str:
    """Detect whether the identifier is a contract address or Twitter username."""
    clean_identifier = identifier.lstrip('@')
    
    if (identifier.startswith('0x') and len(identifier) == 42) or \
       (len(identifier) > 20 and all(c.isalnum() for c in identifier)):
        return "contract"
    else:
        return "twitter"


def register_twitter_intelligence_tools(mcp):
    """Register Twitter intelligence related MCP tools."""
    
    @mcp.tool()
    async def search_twitter_mentions(keywords: List[str], days_ago: int = 20, limit: int = 20) -> str:
        """Search for mentions of specific tokens or topics on Twitter.
        
        This tool finds discussions about cryptocurrencies, blockchain projects, or other topics of interest.
        It provides the tweets and mentions of smart accounts (only influential ones) and does not contain all tweets.
        Use this when you want to understand what influential people are saying about a particular token or topic on Twitter.
        Each of the search keywords should be one word or phrase. A maximum of 5 keywords are allowed.
        One key word should be one concept. Never use long sentences or phrases as keywords.

        Args:
            keywords: List of keywords to search for (maximum 5 keywords)
            days_ago: Number of days to look back (default: 20)
            limit: Maximum number of results (minimum: 20, maximum: 30, default: 20)
        """
        try:
            result = await _search_mentions_internal(keywords, days_ago, limit)
            return str(result)
        except Exception as e:
            return f"Error: {str(e)}"
    
    @mcp.tool()
    async def search_twitter_account(username: str, days_ago: int = 30, limit: int = 20) -> str:
        """Search for a Twitter account with both mention search and account statistics.
        
        This tool provides engagement metrics, follower growth, and mentions by smart users.
        It does not contain all tweets, but only those of influential users. It also identifies
        the topics and cryptocurrencies they frequently discuss. Data comes from ELFA API
        and can analyze several weeks of historical activity.

        Args:
            username: Twitter username to analyze (without @)
            days_ago: Number of days to look back for mentions (default: 30)
            limit: Maximum number of mention results (default: 20)
        """
        try:
            result = await _search_account_internal(username, days_ago, limit)
            return str(result)
        except Exception as e:
            return f"Error: {str(e)}"
    
    @mcp.tool()
    async def get_twitter_trending_tokens(time_window: str = "24h") -> str:
        """Get current trending tokens on Twitter.
        
        This tool identifies which cryptocurrencies and tokens are generating the most buzz on Twitter right now.
        The results include token names, their relative popularity, and sentiment indicators.
        Use this when you want to discover which cryptocurrencies are currently being discussed
        most actively on social media. Data comes from ELFA API and represents real-time trends.

        Args:
            time_window: Time window to analyze (default: "24h")
        """
        try:
            result = await _get_trending_tokens_internal(time_window)
            return str(result)
        except Exception as e:
            return f"Error: {str(e)}"
    
    # @mcp.tool()
    # async def get_crypto_project_info(identifier: str, interval: str = "_7Days") -> str:
    #     """Get comprehensive information about a crypto project by Twitter username OR contract address.
        
    #     This unified tool automatically detects whether you're providing a Twitter username or contract address
    #     and returns detailed market metrics (market cap, price, 24h volume, liquidity, holder counts), 
    #     performance trends with percentage changes, Twitter engagement statistics (follower counts, 
    #     average impressions, engagement rates), and top engaging tweets with smart engagement points 
    #     and impression counts. Perfect for analyzing a project's market performance, social media 
    #     reach, and community engagement.
        
    #     Examples:
    #     - Twitter username: "elonmusk" or "@elonmusk"
    #     - Contract address: "0x1234567890123456789012345678901234567890"

    #     Args:
    #         identifier: Either a Twitter username (with or without @) or token contract address
    #         interval: Time interval for the data (_3Days, _7Days, default: _7Days)
    #     """
    #     try:
    #         identifier_type = _detect_identifier_type(identifier)
            
    #         if identifier_type == "twitter":
    #             result = await _get_project_by_twitter_username_internal(identifier, interval)
    #         else:
    #             result = await _get_project_by_contract_address_internal(identifier, interval)
            
    #         return str(result)
    #     except Exception as e:
    #         return f"Error: {str(e)}"
 