from typing import List, Dict, Any, Tuple
import re
import json
import asyncio
from agent.conversation import SierraAgent, AgentState
from evals.test_cases import get_test_cases

class AgentEvaluator:
    def __init__(self):
        self.agent = SierraAgent()
        self.results = {}
        # Initialize agent and skip welcome message
        asyncio.create_task(self._initialize_agent())
    
    async def _initialize_agent(self):
        """Initialize agent and skip the welcome message"""
        # This processes the welcome message and moves to intent detection
        await self.agent.process_message("")
        # Ensure agent is in INTENT_DETECTION state
        self.agent.state = AgentState.INTENT_DETECTION
    
    async def evaluate_single_turn(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate a single-turn test case
        """
        # Create a fresh agent for each test case so we can test independently
        self.agent = SierraAgent()
        await self._initialize_agent()
        
        test_id = test_case["id"]
        query = test_case["query"]
        
        # Process the query
        response = await self.agent.process_message(query)
        
        # Evaluate success criteria
        criteria_results = []
        for criterion in test_case["success_criteria"]:
            criterion_met = self._evaluate_criterion(criterion, response)
            criteria_results.append({
                "criterion": criterion,
                "met": criterion_met
            })
        
        success_percentage = sum(1 for cr in criteria_results if cr["met"]) / len(criteria_results) * 100
        
        result = {
            "test_id": test_id,
            "query": query,
            "response": response,
            "criteria_results": criteria_results,
            "success_percentage": success_percentage,
            "passed": success_percentage >= 75  # Consider a test passed if it meets at least 75% of criteria
        }
        
        self.results[test_id] = result
        return result
    
    async def evaluate_multi_turn(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate a multi-turn test case
        """
        test_id = test_case["id"]
        conversation = test_case["conversation"]
        
        # Reset agent for this test
        self.agent = SierraAgent()
        await self._initialize_agent()
        
        # Process each turn in the conversation
        responses = []
        for turn in conversation:
            query = turn["query"]
            response = await self.agent.process_message(query)
            responses.append({
                "query": query,
                "response": response
            })
        
        # Evaluate success criteria
        criteria_results = []
        for criterion in test_case["success_criteria"]:
            # For multi-turn, check criterion against all responses
            all_responses = " ".join([r["response"] for r in responses])
            criterion_met = self._evaluate_criterion(criterion, all_responses)
            criteria_results.append({
                "criterion": criterion,
                "met": criterion_met
            })
        
        success_percentage = sum(1 for cr in criteria_results if cr["met"]) / len(criteria_results) * 100
        
        result = {
            "test_id": test_id,
            "conversation": conversation,
            "responses": responses,
            "criteria_results": criteria_results,
            "success_percentage": success_percentage,
            "passed": success_percentage >= 75  # Consider a test passed if it meets at least 75% of criteria
        }
        
        self.results[test_id] = result
        return result
    
    def _evaluate_criterion(self, criterion: str, response: str) -> bool:
        """
        Evaluate if a criterion is met in the response
        """
        response_lower = response.lower()
        
        if criterion.startswith("should mention "):
            term = criterion[15:].lower()
            return term in response_lower
        
        if criterion.startswith("should include "):
            term = criterion[15:].lower()
            return term in response_lower
        
        if criterion.startswith("should not "):
            term = criterion[11:].lower()
            return term not in response_lower
        
        if criterion.startswith("should ask "):
            # Look for question marks
            return "?" in response
        
        if criterion == "should keep context between messages":
            # This is a heuristic - look for references to previous messages
            context_terms = ["you mentioned", "earlier", "previously", "that one", "as i said"]
            return any(term in response_lower for term in context_terms)
        
        if criterion == "should offer assistance":
            assistance_terms = ["help", "assist", "support", "resolve", "contact"]
            return any(term in response_lower for term in assistance_terms)
        
        # Default to False for unrecognized criteria
        return False
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """
        Run all tests and return results
        """
        all_test_cases = get_test_cases()
        
        for test_case in all_test_cases:
            if test_case["category"] == "multi_turn":
                await self.evaluate_multi_turn(test_case)
            else:
                await self.evaluate_single_turn(test_case)
        
        # Calculate overall metrics
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results.values() if r["passed"])
        overall_success_rate = passed_tests / total_tests * 100 if total_tests > 0 else 0
        
        category_metrics = {}
        for category in ["product_search", "product_details", "order_search", "order_details", "track_order", "multi_turn", "edge_case"]:
            category_test_cases = get_test_cases(category)
            category_test_ids = [tc["id"] for tc in category_test_cases]
            category_results = [r for test_id, r in self.results.items() if test_id in category_test_ids]
            
            if category_results:
                category_passed = sum(1 for r in category_results if r["passed"])
                category_success_rate = category_passed / len(category_results) * 100
                category_metrics[category] = {
                    "total_tests": len(category_results),
                    "passed_tests": category_passed,
                    "success_rate": category_success_rate
                }
        
        return {
            "overall_metrics": {
                "total_tests": total_tests,
                "passed_tests": passed_tests,
                "success_rate": overall_success_rate
            },
            "category_metrics": category_metrics,
            "detailed_results": self.results
        }
    
    def save_results(self, filename: str = "evaluation_results.json") -> None:
        """
        Save evaluation results to a JSON file
        """
        with open(filename, "w") as f:
            json.dump(self.results, f, indent=2)

async def run_evaluation():
    """
    Run the evaluation and print results
    """
    evaluator = AgentEvaluator()
    results = await evaluator.run_all_tests()
    
    # Print overall metrics
    overall = results["overall_metrics"]
    print(f"\n=== OVERALL EVALUATION RESULTS ===")
    print(f"Total tests: {overall['total_tests']}")
    print(f"Passed tests: {overall['passed_tests']}")
    print(f"Success rate: {overall['success_rate']:.2f}%")
    
    # Print category metrics
    print(f"\n=== CATEGORY RESULTS ===")
    for category, metrics in results["category_metrics"].items():
        print(f"{category.upper()}: {metrics['success_rate']:.2f}% ({metrics['passed_tests']}/{metrics['total_tests']} tests passed)")
    
    # Save detailed results
    evaluator.save_results()
    print(f"\nDetailed results saved to evaluation_results.json")
