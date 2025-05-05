from agent.services.orders import search_orders, get_order_details, track_order, format_order_info, order_status_to_readable, orders_to_context
from agent.types import AgentState
import json
from openai import AsyncOpenAI
import os
from typing import List, Dict, Any, Optional
import dotenv

dotenv.load_dotenv()

openai = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class OrderUtilsMixin:
    async def _extract_order_details_with_llm(self) -> Dict[str, Optional[str]]:
        """
        Extract order number and email from conversation history using LLM.
        Looks at multiple messages in conversation history to find this information.
            
        Returns:
            Dict with keys 'order_number' and 'email', values can be None if not found
        """
        # Get recent conversation
        recent_conversation = self._get_recent_conversation()
        
        system_message = """
        Your task is to extract order details from a conversation between a customer and a customer service agent.
        
        Look for:
        1. Order number (format: #W followed by digits, e.g., #W001, #W123)
        2. Customer email address
        
        Important: The information might not be present in the conversation. 
        If you can't find an order number or email, it's okay to return null.
        
        Return your findings in this JSON format:
        {
            "order_number": "the order number or null if not found",
            "email": "the email address or null if not found"
        }
        
        Only return the JSON object, nothing else.
        """
        
        try:
            response = await openai.responses.create(
                model="gpt-4o",
                instructions=system_message,
                input=recent_conversation,
                max_output_tokens=256,
                temperature=0.3
            )
            
            result_text = response.output_text.strip()
            
            # Try to parse the JSON response
            try:
                result = json.loads(result_text)
                # Normalize the results
                order_details = {
                    "order_number": result.get("order_number") if result.get("order_number") and result.get("order_number") != "null" else None,
                    "email": result.get("email") if result.get("email") and result.get("email") != "null" else None
                }
                return order_details
            except json.JSONDecodeError: # TODO: Fallback to regex extraction
                print(f"Error parsing JSON response: {result_text}")
                return {
                    "order_number": None,
                    "email": None
                }
            
        except Exception as e:
            print(f"Error extracting order details: {e}")
            return {
                "order_number": None,
                "email": None
            }

    async def _handle_order_info_gathering(self) -> str:
        """
        Handle order information gathering process.
        This function:
        1. Extracts order details using LLM
        2. Updates collected_info
        3. Manages state transitions
        4. Returns appropriate response messages
        
        Returns:
            Response message to user
        """
        # Extract order details from conversation history
        order_details = await self._extract_order_details_with_llm()
        
        # Update collected info with any new information found
        if order_details["order_number"]:
            self.collected_info["order_number"] = order_details["order_number"]
        if order_details["email"]:
            self.collected_info["email"] = order_details["email"]
        
        # Get the current state of order details
        order_number = self.collected_info.get("order_number")
        email = self.collected_info.get("email")
        
        # If we have enough info, move to data retrieval
        if order_number and email:
            self.state = AgentState.DATA_RETRIEVAL
            return await self._handle_data_retrieval()
        
        # Otherwise, ask for the missing info
        if not order_number and not email:
            info_request_msg = "To check your order status, I'll need your order number and email address. Can you please provide this information?"
            return await self._send_response(info_request_msg, AgentState.INFO_GATHERING)
        elif not order_number:
            info_request_msg = f"I have your email address ({email}), but I still need your order number (starts with #W). Could you please provide it?"
            return await self._send_response(info_request_msg, AgentState.INFO_GATHERING)
        elif not email:
            info_request_msg = f"I have your order number ({order_number}), but I still need the email address associated with this order. Could you please provide it?"
            return await self._send_response(info_request_msg, AgentState.INFO_GATHERING)
        
        # This should never happen, but just in case
        return await self._send_response("I need some more information to check your order status. Could you provide both your order number and email address?", AgentState.INFO_GATHERING)
