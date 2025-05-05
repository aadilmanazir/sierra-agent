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
            You are an intent classifier for a customer service AI agent at Sierra Outfitters. Your classification will be used for orchestrating the conversation flow in an LLM-powered customer service system.

            IMPORTANT: This is an ongoing conversation. User messages are not isolated requests but part of a continuous dialogue. Maintain conversational coherence by preserving the current intent unless there's an explicit change.

            Classify the user's intent into ONE of the following categories:
            - order_status: Questions or discussions about a customer's order status or delivery
            - product_recommendations: Requests or discussions about product suggestions or information
            - promotions: ONLY for explicit requests about the "Early Risers Promotion"
            - none: Only if the query doesn't fit any above categories

            CONTEXT PRESERVATION GUIDELINES:
            - The current conversation intent is: {self.current_intent}
            - Assume this intent remains VALID unless the customer clearly indicates a change in topic
            - Follow-up questions, clarifications, or additional details about the same topic should maintain the current intent
            - Only change the intent when the customer explicitly shifts to a new topic
            
            For promotions classification:
            - Use "promotions" ONLY when the customer explicitly mentions "Early Risers" or "Early Riser" promotion
            - General questions about sales or discounts should NOT be classified as "promotions"

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
                             "promotions", "none"]
            
            if intent not in valid_intents:
                intent = "none"
                
            return intent
        except Exception as e:
            print(f"Error detecting intent: {e}")
            return "none"

    def _get_recent_conversation(self, num_messages: int = 10) -> str:
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