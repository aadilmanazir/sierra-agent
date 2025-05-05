from agent.services.orders import search_orders, get_order_details, track_order, format_order_info, order_status_to_readable, orders_to_context
from agent.types import AgentState
import json
from openai import AsyncOpenAI
import os
from typing import List, Dict, Any, Optional
import dotenv
from pydantic import BaseModel

dotenv.load_dotenv()

openai = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class OrderDetails(BaseModel):
    order_number: Optional[str] = None
    email: Optional[str] = None

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
        You are a specialized information extraction component within a larger customer service AI orchestration system for Sierra Outfitters.
    
        YOUR ROLE: Extract key order identification details from an ongoing customer service conversation to facilitate order lookups.
        
        IMPORTANT CONTEXT:
        - You are analyzing a real conversation between a customer and our service agent
        - The conversation is ongoing and may contain corrections, changes, or updates to previously provided information
        - Customers may provide partial information, correct previous information, or refer to information from earlier in the conversation
        - Always prioritize the most recently provided information when there are contradictions
        
        EXTRACTION TASK:
        Look for the following specific details:
        1. Order number (format: #W followed by digits, e.g., #W001, #W123)
        2. Customer email address
        
        EXTRACTION GUIDELINES:
        - If multiple order numbers are mentioned, use the most recently mentioned one
        - If multiple email addresses are mentioned, use the most recently mentioned one
        - The customer may have corrected a typo or provided updated information - always use their most recent statement
        - If the information is not present in the conversation, return null
        
        Return your findings in this JSON format:
        {
            "order_number": "the order number or null if not found",
            "email": "the email address or null if not found"
        }
        
        Only return the JSON object, nothing else.
        """
        
        try:
            response = await openai.responses.parse(
                model="gpt-4o",
                instructions=system_message,
                input=recent_conversation,
                max_output_tokens=256,
                temperature=0.3,
                text_format=OrderDetails
            )
            
            # Access the parsed Pydantic model directly
            parsed_response = response.output_parsed
            
            # Create the order details dictionary from the Pydantic model
            order_details = {
                "order_number": parsed_response.order_number,
                "email": parsed_response.email
            }
            
            return order_details
            
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
