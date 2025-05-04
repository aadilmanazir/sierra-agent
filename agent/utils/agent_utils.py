from agent.conversation import AgentState
import openai
from typing import List, Dict, Tuple
import os
import uuid
import datetime
import pytz

openai.api_key = os.getenv("OPEN_AI_API_KEY")

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

class SierraAgent:
    def _get_last_user_message(self) -> str:
        """Get the last user message from conversation history."""
        for message in reversed(self.conversation_history):
            if message["role"] == "user":
                return message["content"]
        return ""

    async def _detect_intent_llm(self) -> str:
        """
        Detect the intent of the user message using LLM
        """
        system_message = """
        Your task is to classify customer service queries into one of the following intents:
        - order_status: Questions about the status of an order or delivery
        - product_recommendations: Requests for product recommendations
        - promotions: ONLY for explicit requests for the "Early Risers Promotion" (must be specifically requesting this exact promotion)
        - none: If the query doesn't clearly fit any of the above categories

        For promotions:
        - ONLY classify as "promotions" if the user EXPLICITLY asks for the "Early Risers Promotion"
        - General questions about sales, discounts, or other promotions should be classified as "none"
        - The user must directly mention "Early Risers" or "Early Riser" promotion

        You will receive a chat history. Classify the intent of the user's most recent messages. What does the user want to know now?
        It is important to classify the intent of what the user desires now, as their intent in previous messages may be different.
        
        Return only the intent name, with no additional explanation.
        """
        
        messages = [
            {"role": "system", "content": system_message}
        ]
        
        # Add conversation history (up to last 5 exchanges)
        # Make sure the most recent user message is included
        if self.conversation_history:
            # Include up to the last 5 exchanges (10 messages, alternating between user and assistant)
            history_to_include = self.conversation_history[-10:]
            messages.extend(history_to_include)
        
        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-4o",
                messages=messages,
                max_tokens=64,
                temperature=0.3
            )
            intent = response.choices[0].message.content.strip().lower()
            
            # Validate that the intent is one of our expected values
            valid_intents = ["order_status", "product_recommendations", 
                             "promotions", "none"]
            
            if intent not in valid_intents:
                intent = "none"
                
            return intent
        except Exception as e:
            print(f"Error detecting intent: {e}")
            return "none"

    def _get_recent_conversation(self, num_messages: int = 10) -> List[Dict[str, str]]:
        """
        Get recent conversation history, limited to the specified number of messages.
        
        Args:
            num_messages: Maximum number of recent messages to return
            
        Returns:
            List of conversation messages
        """
        return self.conversation_history[-num_messages:] if len(self.conversation_history) >= num_messages else self.conversation_history
    
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