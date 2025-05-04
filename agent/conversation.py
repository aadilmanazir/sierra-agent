import os
import json
from typing import List, Dict, Any, Optional, Tuple, Union
import asyncio
import re
import openai
import dotenv
from enum import Enum, auto

from agent.utils import extract_tracking_number, extract_order_number, extract_sku, extract_tags
from agent.services.products import get_all_products
from agent.services.orders import search_orders, get_order_details, track_order, format_order_info, order_status_to_readable, orders_to_context

# Load environment variables
dotenv.load_dotenv()

# Set up OpenAI API
openai.api_key = os.getenv("OPEN_AI_API_KEY")

class AgentState(Enum):
    """Enum to represent the different states of the agent."""
    WELCOME = auto()  # Initial welcome state
    INTENT_DETECTION = auto()  # Detecting user intent
    INFO_GATHERING = auto()  # Gathering info
    DATA_RETRIEVAL = auto()  # Retrieving data based on gathered info

class Intent(Enum):
    """Enum to represent the different intents a user might have."""
    NONE = auto()  # No clear intent detected
    ORDER_STATUS = auto()  # User wants to check order status + tracking link
    PRODUCT_RECOMMENDATIONS = auto()  # User wants product recommendations
    PROMOTIONS = auto()  # User wants to know about promotions

class SierraAgent:
    welcome_msg = "Welcome, I am Sierra Outfitters agent. You can ask about the status of an order, product recommendations, or potential promotions. What would you like to request?"

    def __init__(self):
        self.conversation_history = []
        self.product_context = {}
        self.order_context = {}
        self.state = AgentState.WELCOME
        self.current_intent = Intent.NONE
        self.collected_info = {}
        
    async def process_message(self, user_message: str) -> str:
        """Process user message based on current state and return response."""
        # Handle welcome state (first message)
        if self.state == AgentState.WELCOME:
            self.state = AgentState.INTENT_DETECTION
            return await self._send_response(self.welcome_msg, AgentState.INTENT_DETECTION)
        
        # Add user message to history (skip if empty - happens on initialization)
        if user_message:
            self.conversation_history.append({"role": "user", "content": user_message})
            
        # Process based on current state
        if self.state == AgentState.INTENT_DETECTION:
            return await self._handle_intent_detection()
        elif self.state == AgentState.INFO_GATHERING:
            return await self._handle_info_gathering()
            
        # Default fallback response
        return "I'm sorry, I'm having trouble understanding. Could you please try again?"
    
    async def _handle_intent_detection(self) -> str:
        """Handle the intent detection state."""
        # First, check if we might have a new intent
        intent_result = await self._detect_intent_llm()
        
        # Check if we have a clear intent
        if intent_result == "none":
            # No clear intent detected, ask for clarification
            clarification_msg = "I'm not quite sure what you would like me to help with. You can ask about the status of an order, product recommendations, or potential promotions. What would you like to request?"
            return await self._send_response(clarification_msg, AgentState.INTENT_DETECTION)
        
        # Map string intent to enum
        intent_mapping = {
            "order_status": Intent.ORDER_STATUS,
            "product_recommendations": Intent.PRODUCT_RECOMMENDATIONS,
            "promotions": Intent.PROMOTIONS
        }
        self.current_intent = intent_mapping.get(intent_result, Intent.NONE)
        
        # Reset collected info for new intent
        self.collected_info = {}
        
        # Transition to the appropriate info gathering state based on intent
        if self.current_intent == Intent.ORDER_STATUS:
            # Use the consolidated order info gathering helper
            return await self._handle_order_info_gathering()
            
        elif self.current_intent == Intent.PRODUCT_RECOMMENDATIONS:
            # Use the consolidated product info gathering helper
            return await self._handle_product_info_gathering()
            
        elif self.current_intent == Intent.PROMOTIONS:
            promotions_msg = "We currently have several promotions running. Would you like to hear about seasonal discounts, member-only offers, or bundle deals?"
            return await self._send_response(promotions_msg, AgentState.INTENT_DETECTION)
        
        # Fallback for unhandled intents
        self.state = AgentState.INTENT_DETECTION
        fallback_msg = "I understand you're interested in something, but I'm not sure what specifically. You can ask about the status of an order, product recommendations, or potential promotions. What would you like to request?"
        return await self._send_response(fallback_msg, AgentState.INTENT_DETECTION)
    
    async def _handle_info_gathering(self) -> str:
        """Handle gathering information based on intent."""
        # First check if the user changed intent
        intent_result = await self._detect_intent_llm()
        intent_mapping = {
            "order_status": Intent.ORDER_STATUS,
            "product_recommendations": Intent.PRODUCT_RECOMMENDATIONS,
            "promotions": Intent.PROMOTIONS
        }
        detected_intent = intent_mapping.get(intent_result, Intent.NONE)
        
        # If intent changed, reset and go back to intent detection
        if detected_intent != Intent.NONE and detected_intent != self.current_intent:
            self.current_intent = detected_intent
            self.collected_info = {}
            self.state = AgentState.INTENT_DETECTION
            return await self._handle_intent_detection()
        
        # Handle based on current intent
        if self.current_intent == Intent.ORDER_STATUS:
            # Use the consolidated order info gathering helper
            return await self._handle_order_info_gathering()
            
        elif self.current_intent == Intent.PRODUCT_RECOMMENDATIONS:
            # Use the consolidated product info gathering helper
            return await self._handle_product_info_gathering()
            
        # Default case (should rarely happen)
        fallback_msg = "I'm not sure what information I need. Let's start over. What would you like help with?"
        self.conversation_history.append({"role": "assistant", "content": fallback_msg})
        self.state = AgentState.INTENT_DETECTION
        return fallback_msg
    
    async def _handle_data_retrieval(self) -> str:
        """Handle retrieving data based on collected information."""
        try:
            if self.current_intent == Intent.ORDER_STATUS:
                # Try to get order data
                order_number = self.collected_info.get("order_number")
                email = self.collected_info.get("email")
                
                if order_number and email:
                    try:
                        order = await get_order_details(order_number=order_number, customer_email=email)
                        context = format_order_info(order)
                        status_text = order_status_to_readable(order["Status"])
                        tracking_info = ""
                        if order.get("TrackingNumber"):
                            tracking_info = f" Your package is being tracked with number {order['TrackingNumber']}."
                            
                        response = f"Here's the information for your order {order_number}.{tracking_info} {status_text}.\n\n{context}\n\nCan I help you with anything else?"
                        return await self._send_response(response, AgentState.INTENT_DETECTION)
                    except Exception as e:
                        error_msg = f"Sorry, I couldn't find an order with number {order_number} for email {email}. Please double check and try again."
                        # Reset collected info and stay in order info gathering
                        self.collected_info = {}
                        return await self._send_response(error_msg, AgentState.INFO_GATHERING)
                else:
                    missing_info_msg = "I'm missing some necessary information to check your order. Let's start over. Please provide your order number and email address."
                    return await self._send_response(missing_info_msg, AgentState.INFO_GATHERING)
            
            elif self.current_intent == Intent.PRODUCT_RECOMMENDATIONS:
                # Product recommendations are now handled by _handle_product_info_gathering
                # Just in case we ended up here, redirect to the proper function
                return await self._handle_product_info_gathering()
            
            # Handle promotions or other intents
            elif self.current_intent == Intent.PROMOTIONS:
                promo_msg = "We have several promotions running this month! Enjoy 20% off all hiking gear, free shipping on orders over $75, and buy-one-get-one 50% off on select clothing items. Would you like more information on any of these promotions?"
                return await self._send_response(promo_msg, AgentState.INTENT_DETECTION)
        
            # Default case
            fallback_msg = "I'm sorry, I wasn't able to retrieve the information you requested. Let's try something else. What would you like to know about?"
            return await self._send_response(fallback_msg, AgentState.INTENT_DETECTION)
            
        except Exception as e:
            # General error handling
            error_msg = "I apologize, but I encountered an error while trying to retrieve your information. Let's try again. What would you like to know about?"
            return await self._send_response(error_msg, AgentState.INTENT_DETECTION)
    