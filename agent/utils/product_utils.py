from agent.services.products import get_all_products
from agent.types import AgentState
import json
from openai import AsyncOpenAI
from typing import List, Dict, Any
import os
import dotenv

dotenv.load_dotenv()

openai = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class ProductUtilsMixin:
    async def _handle_product_info_gathering(self) -> str:
            """
            Simplified product information handling process.
            1. Detects if there's a clear product question
            2. If yes, passes the question and product catalog to an LLM to generate a response
            3. If no products match, prompts user for more information
            
            Returns:
                Response message to user
            """
            # Load product catalog data from API
            try:
                product_data = await get_all_products()
                if not product_data:
                    error_msg = "I'm having trouble accessing our product information right now. Could you please try again later?"
                    return await self._send_response(error_msg, AgentState.INTENT_DETECTION)
            except Exception as e:
                print(f"Error loading product data from API: {e}")
                error_msg = "I'm having trouble accessing our product information right now. Could you please try again later?"
                return await self._send_response(error_msg, AgentState.INTENT_DETECTION)
                
            # Get recent conversation history
            recent_messages = self._get_recent_conversation()
            
            # Step 1: Detect if there's a clear product question
            has_clear_question = await self._check_for_product_question()
            
            if not has_clear_question:
                prompt_msg = "Please provide me more details about what you're looking for. I can help you find products!"
                return await self._send_response(prompt_msg, AgentState.INFO_GATHERING)
            
            # Step 2: Use LLM to match products and answer the question
            response = await self._generate_product_matching_response(product_data)

            # Step 3: If the response is empty, no products matched
            if len(response) == 0:
                no_match_msg = "I couldn't find any products matching your criteria. Could you please provide more details about what you're looking for? For example, what type of activity, features, or categories are important to you?"
                return await self._send_response(no_match_msg, AgentState.INFO_GATHERING)
            
            # Return the response with state transition to INTENT_DETECTION
            return await self._send_response(response, AgentState.INTENT_DETECTION)
    
    async def _check_for_product_question(self) -> bool:
        """
        Check if the user has asked a clear product-related question
        
        Returns:
            Boolean indicating if there's a clear product question
        """
        # Get recent conversation history
        recent_conversation = self._get_recent_conversation()
        
        system_message = """
        You are a specialized query intent classifier within Sierra Outfitters' AI customer service orchestration system.
    
        YOUR ROLE: Determine if the customer's conversation contains enough product-specific information to perform a product catalog search.
        
        IMPORTANT CONTEXT:
        - You are analyzing an ongoing conversation, not isolated queries
        - Customers may reference products mentioned earlier in the conversation
        - The conversation has contextual continuity - information builds across messages
        - Previous messages provide important context for understanding the current request
        
        CLASSIFICATION TASK:
        Determine if the conversation contains enough information to search the product catalog effectively.
        
        EXAMPLES OF SEARCHABLE QUERIES:
        - Direct product mentions: "Do you have hiking boots?"
        - Product categories: "I'm looking for camping gear"
        - Product attributes: "I need waterproof jackets"
        - Products for types of people: "Do you have products for wizards?"
        - Just product types: "protein bars"
        - Follow-up specifics: "How many are in stock?" (when previously discussing a specific product)
        - Implied references: "What other colors does it come in?" (referencing a previously mentioned product)
        
        ANSWER GUIDELINES:
        - Answer "yes" if the conversation contains information to perform a catalog search, so if the customer has mentioned a product, a category, an attribute, or a follow-up question about a previously mentioned product.
        - Answer "no" if the customer hasn't specified any product information that could be used for searching the catalog for the current request / context
        - Consider the ENTIRE conversation context, not just the latest message. But, of course, the product searching context should be relevant to the intent of the customer's current request. 
        - If the customer is asking follow-up questions about previously mentioned products, answer "yes". But, of course, the product searching context should be relevant to the intent of the customer's current request, otherwise answer "no". 
        
        Respond ONLY with "yes" or "no".
        """      
        
        try:
            response = await openai.responses.create(
                model="gpt-4o",
                instructions=system_message,
                input=recent_conversation,
                max_output_tokens=16,
                temperature=0.25
            )
            
            result = response.output_text.strip().lower()
            return result == "yes"
                
        except Exception as e:
            print(f"Error checking for product question: {e}")
            # Default to yes if there's an error
            return True
    
    async def _generate_product_matching_response(self, product_data: List[Dict[str, Any]]) -> str:
        """
        Generate a response based on matching products to the user's question.
        
        Args:
            product_data: List of products from the catalog
            
        Returns:
            Response message or empty string if no products match
        """
        # Get recent conversation history
        recent_conversation = self._get_recent_conversation()
        
        # Format product data as JSON string
        product_json = json.dumps(product_data, indent=2)
        
        model_input = f"""
        Product catalog:
        {product_json}

        Customer Conversation:
        {recent_conversation}
        """

        system_message = """
        You are the product recommendation component within Sierra Outfitters' customer service AI orchestration system.
        
        YOUR ROLE: Generate helpful, accurate product information based on the customer's needs in the context of their ongoing conversation.
        
        IMPORTANT CONTEXT:
        - You have access to the complete product catalog (provided below)
        - You are analyzing an ongoing conversation with contextual history
        - The customer may refer to information mentioned earlier in the conversation
        - Your response will be delivered directly to the customer as part of a seamless experience
        
        RESPONSE GENERATION TASK:
        1. Carefully analyze the entire conversation to understand what products the customer is interested in
        2. Match their needs against the product catalog
        3. Generate a helpful, personalized response about relevant products
        
        RESPONSE GUIDELINES:
        - IMPORTANT: If NO products in the catalog match the customer's needs, return ONLY an empty string "". Make sure to return an empty string, not a message saying that no products were found. Do not include spaces or newlines.
        - Never mention products that aren't in the provided catalog
        - Be conversational and natural - you're continuing an ongoing dialogue
        - Reference relevant details from the catalog (product names, SKUs, features, inventory)
        - Include a brief, enthusiastic outdoor-themed comment relevant to the products (e.g., "These hiking boots are perfect for conquering mountain trails!"). Add a relevant outdoor-themed emoji as well.
        - Always end by asking if they need further assistance
        - Maintain continuity with the previous conversation - acknowledge information they've already shared
        
        Product catalog is provided in JSON format with the following fields:
        - ProductName: The name of the product
        - SKU: The unique product identifier
        - Inventory: Number of items in stock
        - Description: Detailed description of the product
        - Tags: List of categories/features related to the product
        """
        
        try:
            response = await openai.responses.create(
                model="gpt-4o",
                instructions=system_message,
                input=model_input,
                max_output_tokens=512,
                temperature=0.7
            )
            
            result = response.output_text.strip()
            
            # If the result is empty, return an empty string
            if len(result) <= 2:
                return ""
                
            return result
                
        except Exception as e:
            print(f"Error generating product matching response: {e}")
            # Return an error message instead of empty string
            return "I found some products that might interest you, but I'm having trouble retrieving the details right now. Can you please try again?"