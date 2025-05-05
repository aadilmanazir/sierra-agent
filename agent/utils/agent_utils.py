from agent.types import AgentState
from openai import AsyncOpenAI
from typing import List, Dict, Tuple
import os
import uuid
import datetime
import pytz 
import dotenv

dotenv.load_dotenv()

openai = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def handle_early_risers_promotion() -> str:
    """
    Handle Early Risers Promotion requests.
    Checks if current time is between 8-10 AM Pacific Time,
    and returns an appropriate response with a discount code if it is.
    
    Returns:
        A formatted response message
    """
    # Get current time in Pacific timezone
    pacific_tz = pytz.timezone('America/Los_Angeles')
    current_time = datetime.datetime.now(pacific_tz)
    
    # Check if time is between 8-10 AM
    if 8 <= current_time.hour < 10:
        # Generate unique discount code
        discount_code = f"EARLY-{uuid.uuid4().hex[:8].upper()}"
        return f"Great news! You qualify for our Early Risers Promotion ☀️. Here's your unique 10% discount code: {discount_code}\n\nThis code is valid for your next purchase. Can I help you with anything else?"
    else:
        # Not eligible for promotion
        time_str = current_time.strftime('%I:%M %p')
        return f"The Early Risers Promotion is only available between 8:00 AM and 10:00 AM Pacific Time ☀️. Current time is {time_str}. Please check back during promotion hours. Can I help you with anything else?"

def handle_other_promotion_requests() -> str:
    """
    Handle requests for discounts or promotions other than Early Risers.
    Returns a standard response informing the customer that the requested promotion doesn't exist.
    
    Returns:
        A formatted response message
    """
    return "I'm sorry, but the promotion or discount you're asking about isn't currently available. Is there something else I can help you with?"

class AgentUtilsMixin:
    def _get_last_user_message(self) -> str:
        """Get the last user message from conversation history."""
        for message in reversed(self.conversation_history):
            if message["role"] == "user":
                return message["content"]
        return ""

    async def _detect_intent_llm(self) -> str:
        """Detect the intent of the user message using LLM"""

        system_message = f"""
        You are the CORE INTENT CLASSIFIER within Sierra Outfitters' customer service AI orchestration system.
        
        YOUR ROLE: Accurately determine the customer's current intent to route the conversation to the appropriate specialized handling module.
        
        IMPORTANT CONTEXT:
        - You are the primary orchestrator for conversation flow decisions
        - Your classification directly determines which specialized AI component handles the customer's request
        - The entire customer experience depends on consistent and accurate intent classification
        - This is an ongoing conversation with context and history, not isolated messages
        
        CLASSIFICATION TASK:
        Classify the user's intent into ONE of the following categories:
        - order_status: Questions or discussions about a customer's order status or delivery
        - product_recommendations: Requests or discussions about product suggestions or information
        - promotions: ONLY for explicit requests about the "Early Risers Promotion"
        - other_discounts: Requests for ANY other mention of discount, coupon, sale, or promotion EXCEPT Early Risers. 
        - none: Only if the query doesn't fit any above categories
        
        CONVERSATION CONTEXT AWARENESS:
        - The current conversation intent is: {self.current_intent}
        - Maintain conversational coherence by preserving this intent unless there's a clear change
        - User messages are part of a continuous dialogue, not isolated requests
        - Follow-up questions, clarifications, or additional details about the same topic should maintain the current intent
        - Only change the intent when the customer explicitly shifts to a new topic
        
        SPECIFIC CLASSIFICATION GUIDELINES:
        - For "order_status": Include any questions about orders, shipping, tracking, or delivery status
        - For "product_recommendations": Include product searches, inquiries about features, availability, or comparisons
        - For "promotions": ONLY use when customer explicitly mentions "Early Risers" or "Early Riser" promotion
        - For "other_discounts": Use for ANY request about discounts, coupons, sales, or promotions EXCEPT Early Risers
        - For "none": Use only when the customer's intent truly doesn't match any of the defined categories
        
        CRITICAL REMINDER:
        - "promotions" is ONLY for the specific "Early Risers Promotion", nothing else
        - "other_discounts" covers all other discount/promotion requests
        - Your classification determines the entire conversation path, so be precise and consistent
        - When in doubt about a new topic, consider whether it relates to the current intent
        
        Return ONLY the intent name without explanations or additional text.
        """
        
        recent_conversation = self._get_recent_conversation()
        
        try:
            response = await openai.responses.create(
                model="gpt-4o",
                instructions=system_message,
                input=recent_conversation,
                max_output_tokens=16,
                temperature=0.25
            )
            intent = response.output_text.strip().lower()
            
            # Validate that the intent is one of our expected values
            valid_intents = ["order_status", "product_recommendations", 
                             "promotions", "other_discounts", "none"]
            
            if intent not in valid_intents:
                intent = "none"
                
            return intent
        except Exception as e:
            print(f"Error detecting intent: {e}")
            return "none"

    def _get_recent_conversation(self, num_messages: int = 25) -> str:
        """
        Get recent conversation history as formatted text, limited to the specified number of messages.
        
        Args:
            num_messages: Maximum number of recent messages to return
            
        Returns:
            Formatted conversation text as a string
        """
        recent_messages = self.conversation_history[-num_messages:] if len(self.conversation_history) >= num_messages else self.conversation_history
        return self._format_conversation_text(recent_messages)
    
    def _format_conversation_text(self, messages: List[Dict[str, str]]) -> str:
        """
        Format conversation messages into a readable text format.
        
        Args:
            messages: List of conversation messages
            
        Returns:
            Formatted conversation text
        """
        conversation_text = ""
        for msg in messages:
            role = "User" if msg["role"] == "user" else "Assistant"
            conversation_text += f"{role}: {msg['content']}\n"
        return conversation_text
    
    async def _send_response(self, response: str, next_state: AgentState = AgentState.INTENT_DETECTION) -> str:
        """
        Send a response to the user and update state.
        
        Args:
            response: Message to send to the user
            next_state: The state to transition to after sending the response
            
        Returns:
            The response message
        """
        self.conversation_history.append({"role": "assistant", "content": response})
        self.state = next_state
        return response