"""
DEX quote operations.
Supports both same-chain and cross-chain quotes with operation type control.
"""

import aiohttp
import json
from ..utils.formatters import convert_decimal_to_minimal_units


async def get_quote_internal(
    from_token: str, 
    to_token: str, 
    from_chain: str,
    to_chain: str = None,
    decimal_amount: str = None,
    amount: str = None,
    is_cross_chain: bool = False,
    from_token_decimals: int = None,
    slippage: str = "1",
    slippage_mode: str = "percentage"
) -> str:
    """Get a DEX trading quote supporting both same-chain and cross-chain operations.
    
    Args:
        from_token: From token contract address
        to_token: To token contract address
        from_chain: Source chain ID (e.g., "1" for Ethereum, "56" for BSC)
        to_chain: Destination chain ID (required for cross-chain, ignored for same-chain)
        decimal_amount: Decimal amount (e.g., "0.1" for 0.1 tokens)
        amount: Amount in minimal units (alternative to decimal_amount)
        is_cross_chain: Whether this is a cross-chain quote (default: False)
        from_token_decimals: Required when using decimal_amount
        slippage: Allowed slippage value (default: "1")
        slippage_mode: Mode of slippage value - "percentage" or "float" (default: "percentage")
    """
    
    # Validate parameters based on operation type
    if is_cross_chain:
        if not to_chain:
            return "❌ to_chain is required for cross-chain quotes."
        if from_chain == to_chain:
            return "❌ Cross-chain quote requires different source and destination chains."
    else:
        # For same-chain quotes, to_chain equals from_chain
        to_chain = from_chain
    
    # Handle amount conversion
    if decimal_amount:
        if from_token_decimals is None:
            return "❌ from_token_decimals is required when using decimal_amount parameter."
        try:
            amount = convert_decimal_to_minimal_units(decimal_amount, from_token_decimals)
        except ValueError as e:
            return f"❌ Error converting decimal amount: {str(e)}"
    elif not amount:
        return "❌ Either decimal_amount or amount parameter is required."
    
    # Handle slippage - convert to float format for both endpoints
    try:
        slippage_float = float(slippage)
        if slippage_mode == "percentage":
            if slippage_float < 0 or slippage_float > 100:
                return "❌ Invalid slippage percentage. Must be between 0 and 100."
            # Convert percentage to float (e.g., 1% -> 0.01)
            slippage_float = slippage_float / 100
        elif slippage_mode == "float":
            if slippage_float < 0 or slippage_float > 1:
                return "❌ Invalid slippage float. Must be between 0 and 1."
        else:
            return "❌ Invalid slippage_mode. Must be either 'percentage' or 'float'."
    except ValueError:
        return "❌ Invalid slippage value. Must be a valid number."
    
    # Determine endpoint and payload based on operation type
    if is_cross_chain:
        # Cross-chain quote using new crossChainQuote_v2 endpoint
        endpoint = "https://mcp-server-264441234562.us-central1.run.app/crossChainQuote_v2"
        payload = {
            "fromTokenAddress": from_token,
            "toTokenAddress": to_token,
            "fromChainIndex": from_chain,
            "amount": amount,
            "toChainIndex": to_chain,
            "slippage": str(slippage_float)  # Convert to string for API
        }
    else:
        # Same-chain quote using quote_v2 endpoint
        endpoint = "https://mcp-server-264441234562.us-central1.run.app/quote_v2"
        payload = {
            "fromTokenAddress": from_token,
            "toTokenAddress": to_token,
            "chainIndex": from_chain,
            "amount": amount
        }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(endpoint, json=payload) as response:
                if response.status != 200:
                    operation_desc = "cross-chain" if is_cross_chain else "same-chain"
                    return f"❌ API Error: HTTP {response.status} for {operation_desc} quote"
                
                data = await response.json()
                
                if not data:
                    return "❌ No data received from API"
                
                if "error" in data:
                    return f"❌ API Error: {data['error']}"
                
                # Format response based on operation type
                if is_cross_chain:
                    result = f"""✅ CROSS-CHAIN DEX QUOTE FOUND

=== ROUTE DETAILS ===
From Chain: {from_chain}
To Chain: {to_chain}

=== TOKEN DETAILS ===
From Token Address: {from_token}
To Token Address: {to_token}

=== TRANSACTION DETAILS ===
Amount: {amount}
Slippage: {slippage} ({slippage_mode}) -> {slippage_float} (float)

=== API RESPONSE ===
{json.dumps(data, indent=2)}

💡 This quote is for cross-chain swapping. Please verify all details before proceeding.
"""
                    return result
                else:
                    # Same-chain quote - show API response directly
                    result = f"""✅ SAME-CHAIN DEX QUOTE FOUND

=== ROUTE DETAILS ===
Chain: {from_chain}

=== TOKEN DETAILS ===
From Token Address: {from_token}
To Token Address: {to_token}

=== TRANSACTION DETAILS ===
Amount: {amount}

=== API RESPONSE ===
{json.dumps(data, indent=2)}

💡 This quote is for same-chain swapping. Please verify all details before proceeding.
"""
                    return result
                
    except Exception as e:
        operation_desc = "cross-chain" if is_cross_chain else "same-chain"
        return f"""❌ ERROR FETCHING {operation_desc.upper()} QUOTE

Error details: {str(e)}

Please verify:
• All addresses are valid
• Chain IDs are supported
• Amount is in correct format
• Network connection is stable
"""


def register_quote_tools(mcp):
    """Register quote related MCP tools."""
    
    @mcp.tool()
    async def get_quote(
        from_token: str, 
        to_token: str, 
        from_chain: str,
        decimal_amount: str = None,
        amount: str = None,
        to_chain: str = None,
        is_cross_chain: bool = False,
        from_token_decimals: int = None,
        slippage: str = "1",
        slippage_mode: str = "percentage"
    ) -> str:
        """Get a unified DEX trading quote supporting both same-chain and cross-chain operations.
        
        This unified function can handle both same-chain and cross-chain quotes based on the is_cross_chain parameter.
        Both quote types have been simplified and no longer require wallet addresses.
        
        **Same-Chain Quotes (is_cross_chain=False):**
        - Uses the quote_v2 endpoint 
        - Only requires from_token, to_token, from_chain, and amount/decimal_amount
        - No wallet address required
        
        **Cross-Chain Quotes (is_cross_chain=True):**
        - Uses the crossChainQuote_v2 endpoint
        - Requires to_chain parameter
        - Supports slippage configuration
        - No wallet addresses required

        Args:
            from_token: From token contract address
            to_token: To token contract address
            from_chain: Source chain ID (e.g., "1" for Ethereum, "56" for BSC)
            decimal_amount: Decimal amount (e.g., "0.1" for 0.1 tokens)
            amount: Amount in minimal units (alternative to decimal_amount)
            to_chain: Destination chain ID (required only for cross-chain quotes)
            is_cross_chain: Whether this is a cross-chain quote (default: False)
            from_token_decimals: Required when using decimal_amount
            slippage: Allowed slippage value (default: "1")
            slippage_mode: Mode of slippage value - "percentage" or "float" (default: "percentage")
        """
        # Validate required parameters
        if not decimal_amount and not amount:
            return "❌ Either decimal_amount or amount parameter is required."
        
        if decimal_amount and from_token_decimals is None:
            return "❌ from_token_decimals is required when using decimal_amount parameter."
        
        return await get_quote_internal(
            from_token=from_token, 
            to_token=to_token, 
            from_chain=from_chain,
            to_chain=to_chain,
            decimal_amount=decimal_amount,
            amount=amount,
            is_cross_chain=is_cross_chain,
            from_token_decimals=from_token_decimals,
            slippage=slippage,
            slippage_mode=slippage_mode
        ) 