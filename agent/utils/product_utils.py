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
                prompt_msg = "I can help you find products. What specific items or categories are you interested in?"
                return await self._send_response(prompt_msg, AgentState.INFO_GATHERING)
            
            # Step 2: Use LLM to match products and answer the question
            response = await self._generate_product_matching_response(product_data)
            
            # Step 3: If the response is empty, no products matched
            if not response:
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
        You are a customer service agent for Sierra Outfitters, an outdoor gear company.
        Your task is to determine if the customer has asked a clear product-related question.
        A clear product question is any query where the customer is asking about products, such as:
        - Questions about specific products
        - Requests for product recommendations
        - Questions about product categories, features, or availability
        - Questions about a product type

        Basically, the customer needs to give you info to search the catalog for relevant products.
        You should understand that this is a conversation and the customer may reference previous information in their query.

        For example, they may first ask for protein bars, and then ask for how many are left in stock.
        Essentially, return no when the customer hasn't given you info to search the catalog, and yes if the customer is / still is asking questions about products.
        
        Only respond with "yes" if it is clear that the customer has given info for you to search for relevant products in the catalog. Otherwise, answer "no".
        Pay special attention to the most recent customer messages. You respond with "yes" if the customer wants an answer to a question about products and has given you info to search the catalog.
        If the customer hasn't given you info to search the catalog, respond with "no".
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
        You are a helpful customer service agent for Sierra Outfitters, an outdoor gear company.
        Your task is to answer customer questions about products based on the product catalog provided.
        
        Review the customer's questions and the product catalog, then:
        1. Identify which products (if any) match what the customer is looking for
        2. Generate a helpful response about those products
        
        Guidelines:
        - If NO products match the customer's query, return only an empty string ""
        - Otherwise, provide a helpful response that addresses their specific question
        - Be friendly, concise, and thorough when describing matching products
        - Include relevant details from the product catalog (names, SKUs, features)
        - Always ask if they need further assistance
        - Make a reference to the outdoors at the end of your response, but before asking if they need further assistance. Ideally, it should relevant to the product. Make it enthusiastic and fun.
        
        Product catalog is provided in JSON format with the following fields:
        - ProductName: The name of the product
        - SKU: The unique product identifier
        - Inventory: Number of items in stock
        - Description: Detailed description of the product
        - Tags: List of categories/features related to the product

        DO NOT include any products that do not exist in the catalog.

        You should understand that this is a conversation and the customer may reference previous information in their query.
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
            
            # If the result is empty or just whitespace, return empty string
            if not result or result.isspace():
                return ""
                
            return result
                
        except Exception as e:
            print(f"Error generating product matching response: {e}")
            # Return an error message instead of empty string
            return "I found some products that might interest you, but I'm having trouble retrieving the details right now. Can you please try again?"