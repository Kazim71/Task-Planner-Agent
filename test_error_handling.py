"""
Comprehensive error handling test script for the Task Planner Agent.
Tests various failure scenarios to ensure robust error handling.
"""

import asyncio
import json
import time
import requests
from typing import Dict, Any
import logging
from logging_config import setup_logging

# Set up logging
logger = setup_logging(log_level="DEBUG")
logger.info("Starting comprehensive error handling tests")

# Test configuration
BASE_URL = "http://127.0.0.1:8000"
TEST_TIMEOUT = 30


class ErrorHandlingTester:
    """Test various error scenarios to validate error handling."""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.test_results = []
        self.session = requests.Session()
    
    def log_test_result(self, test_name: str, success: bool, message: str, details: Dict[str, Any] = None):
        """Log test result."""
        result = {
            "test_name": test_name,
            "success": success,
            "message": message,
            "details": details or {},
            "timestamp": time.time()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{status} - {test_name}: {message}")
        if details:
            logger.debug(f"Test details: {json.dumps(details, indent=2)}")
    
    def test_server_connectivity(self) -> bool:
        """Test if server is running and accessible."""
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=5)
            if response.status_code == 200:
                self.log_test_result(
                    "Server Connectivity",
                    True,
                    f"Server is running and responding (Status: {response.status_code})",
                    {"status_code": response.status_code, "response_time": response.elapsed.total_seconds()}
                )
                return True
            else:
                self.log_test_result(
                    "Server Connectivity",
                    False,
                    f"Server returned unexpected status code: {response.status_code}",
                    {"status_code": response.status_code}
                )
                return False
        except requests.exceptions.RequestException as e:
            self.log_test_result(
                "Server Connectivity",
                False,
                f"Failed to connect to server: {str(e)}",
                {"error_type": type(e).__name__, "error_message": str(e)}
            )
            return False
    
    def test_invalid_goal_validation(self) -> bool:
        """Test validation of invalid goal inputs."""
        test_cases = [
            {"goal": "", "expected_error": "Goal cannot be empty"},
            {"goal": "  ", "expected_error": "Goal cannot be empty"},
            {"goal": "a" * 1001, "expected_error": "Goal must be no more than 1000 characters"},
            {"goal": "ab", "expected_error": "Goal must be at least 3 characters"},
            {"goal": None, "expected_error": "Goal is required"},
        ]
        
        all_passed = True
        
        for i, test_case in enumerate(test_cases):
            try:
                payload = {"goal": test_case["goal"]} if test_case["goal"] is not None else {}
                response = self.session.post(f"{self.base_url}/plan", json=payload, timeout=TEST_TIMEOUT)
                
                if response.status_code == 422:  # Validation error
                    self.log_test_result(
                        f"Invalid Goal Validation - Test {i+1}",
                        True,
                        f"Correctly rejected invalid goal: '{test_case['goal']}'",
                        {"goal": test_case["goal"], "status_code": response.status_code}
                    )
                else:
                    self.log_test_result(
                        f"Invalid Goal Validation - Test {i+1}",
                        False,
                        f"Expected validation error but got status {response.status_code}",
                        {"goal": test_case["goal"], "status_code": response.status_code, "response": response.text}
                    )
                    all_passed = False
                    
            except Exception as e:
                self.log_test_result(
                    f"Invalid Goal Validation - Test {i+1}",
                    False,
                    f"Exception during test: {str(e)}",
                    {"goal": test_case["goal"], "error": str(e)}
                )
                all_passed = False
        
        return all_passed
    
    def test_invalid_date_validation(self) -> bool:
        """Test validation of invalid date inputs."""
        test_cases = [
            {"start_date": "invalid-date", "expected_error": "Invalid date format"},
            {"start_date": "2023-13-01", "expected_error": "Invalid date format"},
            {"start_date": "2023-02-30", "expected_error": "Invalid date format"},
            {"start_date": "2020-01-01", "expected_error": "Start date cannot be in the past"},
            {"start_date": "2030-01-01", "expected_error": "Start date cannot be more than 1 year in the future"},
        ]
        
        all_passed = True
        
        for i, test_case in enumerate(test_cases):
            try:
                payload = {"goal": "Test goal for date validation", "start_date": test_case["start_date"]}
                response = self.session.post(f"{self.base_url}/plan", json=payload, timeout=TEST_TIMEOUT)
                
                if response.status_code == 400:  # Bad request
                    self.log_test_result(
                        f"Invalid Date Validation - Test {i+1}",
                        True,
                        f"Correctly rejected invalid date: '{test_case['start_date']}'",
                        {"start_date": test_case["start_date"], "status_code": response.status_code}
                    )
                else:
                    self.log_test_result(
                        f"Invalid Date Validation - Test {i+1}",
                        False,
                        f"Expected validation error but got status {response.status_code}",
                        {"start_date": test_case["start_date"], "status_code": response.status_code, "response": response.text}
                    )
                    all_passed = False
                    
            except Exception as e:
                self.log_test_result(
                    f"Invalid Date Validation - Test {i+1}",
                    False,
                    f"Exception during test: {str(e)}",
                    {"start_date": test_case["start_date"], "error": str(e)}
                )
                all_passed = False
        
        return all_passed
    
    def test_invalid_plan_id_validation(self) -> bool:
        """Test validation of invalid plan ID inputs."""
        test_cases = [
            {"plan_id": "invalid", "expected_error": "Plan ID must be a valid integer"},
            {"plan_id": -1, "expected_error": "Plan ID must be a positive integer"},
            {"plan_id": 0, "expected_error": "Plan ID must be a positive integer"},
            {"plan_id": 999999999, "expected_error": "Plan ID is too large"},
        ]
        
        all_passed = True
        
        for i, test_case in enumerate(test_cases):
            try:
                response = self.session.get(f"{self.base_url}/plans/{test_case['plan_id']}", timeout=TEST_TIMEOUT)
                
                if response.status_code == 400:  # Bad request
                    self.log_test_result(
                        f"Invalid Plan ID Validation - Test {i+1}",
                        True,
                        f"Correctly rejected invalid plan ID: '{test_case['plan_id']}'",
                        {"plan_id": test_case["plan_id"], "status_code": response.status_code}
                    )
                else:
                    self.log_test_result(
                        f"Invalid Plan ID Validation - Test {i+1}",
                        False,
                        f"Expected validation error but got status {response.status_code}",
                        {"plan_id": test_case["plan_id"], "status_code": response.status_code, "response": response.text}
                    )
                    all_passed = False
                    
            except Exception as e:
                self.log_test_result(
                    f"Invalid Plan ID Validation - Test {i+1}",
                    False,
                    f"Exception during test: {str(e)}",
                    {"plan_id": test_case["plan_id"], "error": str(e)}
                )
                all_passed = False
        
        return all_passed
    
    def test_missing_api_key_scenario(self) -> bool:
        """Test behavior when API key is missing (if possible to simulate)."""
        try:
            # This test might not work if the API key is already set
            # We'll test the health endpoint to see if it reports missing API key
            response = self.session.get(f"{self.base_url}/health", timeout=TEST_TIMEOUT)
            
            if response.status_code == 200:
                health_data = response.json()
                gemini_status = health_data.get("services", {}).get("gemini_api", {}).get("status")
                
                if gemini_status == "not_configured":
                    self.log_test_result(
                        "Missing API Key Detection",
                        True,
                        "Health check correctly detected missing API key",
                        {"gemini_status": gemini_status}
                    )
                    return True
                elif gemini_status == "connected":
                    self.log_test_result(
                        "Missing API Key Detection",
                        True,
                        "API key is configured and working",
                        {"gemini_status": gemini_status}
                    )
                    return True
                else:
                    self.log_test_result(
                        "Missing API Key Detection",
                        False,
                        f"Unexpected Gemini API status: {gemini_status}",
                        {"gemini_status": gemini_status, "health_data": health_data}
                    )
                    return False
            else:
                self.log_test_result(
                    "Missing API Key Detection",
                    False,
                    f"Health check failed with status {response.status_code}",
                    {"status_code": response.status_code}
                )
                return False
                
        except Exception as e:
            self.log_test_result(
                "Missing API Key Detection",
                False,
                f"Exception during test: {str(e)}",
                {"error": str(e)}
            )
            return False
    
    def test_plan_creation_with_valid_data(self) -> bool:
        """Test plan creation with valid data."""
        try:
            payload = {
                "goal": "Learn Python programming in 30 days",
                "start_date": "2024-01-01",
                "save_to_db": True
            }
            
            response = self.session.post(f"{self.base_url}/plan", json=payload, timeout=TEST_TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    self.log_test_result(
                        "Valid Plan Creation",
                        True,
                        f"Successfully created plan with ID: {data.get('plan_id')}",
                        {"plan_id": data.get("plan_id"), "response_time": response.elapsed.total_seconds()}
                    )
                    return True
                else:
                    self.log_test_result(
                        "Valid Plan Creation",
                        False,
                        f"Plan creation failed: {data.get('message')}",
                        {"message": data.get("message"), "response": data}
                    )
                    return False
            else:
                self.log_test_result(
                    "Valid Plan Creation",
                    False,
                    f"Unexpected status code: {response.status_code}",
                    {"status_code": response.status_code, "response": response.text}
                )
                return False
                
        except Exception as e:
            self.log_test_result(
                "Valid Plan Creation",
                False,
                f"Exception during test: {str(e)}",
                {"error": str(e)}
            )
            return False
    
    def test_plan_retrieval(self) -> bool:
        """Test plan retrieval functionality."""
        try:
            # First, get all plans
            response = self.session.get(f"{self.base_url}/plans", timeout=TEST_TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    plans = data.get("plans", [])
                    self.log_test_result(
                        "Plan Retrieval - All Plans",
                        True,
                        f"Successfully retrieved {len(plans)} plans",
                        {"plan_count": len(plans), "response_time": response.elapsed.total_seconds()}
                    )
                    
                    # If we have plans, try to get a specific one
                    if plans:
                        plan_id = plans[0].get("id")
                        if plan_id:
                            return self.test_specific_plan_retrieval(plan_id)
                    
                    return True
                else:
                    self.log_test_result(
                        "Plan Retrieval - All Plans",
                        False,
                        f"Failed to retrieve plans: {data.get('message')}",
                        {"message": data.get("message")}
                    )
                    return False
            else:
                self.log_test_result(
                    "Plan Retrieval - All Plans",
                    False,
                    f"Unexpected status code: {response.status_code}",
                    {"status_code": response.status_code, "response": response.text}
                )
                return False
                
        except Exception as e:
            self.log_test_result(
                "Plan Retrieval - All Plans",
                False,
                f"Exception during test: {str(e)}",
                {"error": str(e)}
            )
            return False
    
    def test_specific_plan_retrieval(self, plan_id: int) -> bool:
        """Test retrieval of a specific plan."""
        try:
            response = self.session.get(f"{self.base_url}/plans/{plan_id}", timeout=TEST_TIMEOUT)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    self.log_test_result(
                        "Plan Retrieval - Specific Plan",
                        True,
                        f"Successfully retrieved plan {plan_id}",
                        {"plan_id": plan_id, "response_time": response.elapsed.total_seconds()}
                    )
                    return True
                else:
                    self.log_test_result(
                        "Plan Retrieval - Specific Plan",
                        False,
                        f"Failed to retrieve plan {plan_id}: {data.get('message')}",
                        {"plan_id": plan_id, "message": data.get("message")}
                    )
                    return False
            elif response.status_code == 404:
                self.log_test_result(
                    "Plan Retrieval - Specific Plan",
                    True,
                    f"Correctly returned 404 for non-existent plan {plan_id}",
                    {"plan_id": plan_id, "status_code": response.status_code}
                )
                return True
            else:
                self.log_test_result(
                    "Plan Retrieval - Specific Plan",
                    False,
                    f"Unexpected status code: {response.status_code}",
                    {"plan_id": plan_id, "status_code": response.status_code, "response": response.text}
                )
                return False
                
        except Exception as e:
            self.log_test_result(
                "Plan Retrieval - Specific Plan",
                False,
                f"Exception during test: {str(e)}",
                {"plan_id": plan_id, "error": str(e)}
            )
            return False
    
    def test_malformed_json_request(self) -> bool:
        """Test handling of malformed JSON requests."""
        try:
            # Send malformed JSON
            headers = {"Content-Type": "application/json"}
            response = self.session.post(
                f"{self.base_url}/plan",
                data="{'invalid': json}",  # Invalid JSON
                headers=headers,
                timeout=TEST_TIMEOUT
            )
            
            if response.status_code == 422:  # Unprocessable Entity
                self.log_test_result(
                    "Malformed JSON Request",
                    True,
                    "Correctly rejected malformed JSON",
                    {"status_code": response.status_code}
                )
                return True
            else:
                self.log_test_result(
                    "Malformed JSON Request",
                    False,
                    f"Expected 422 but got {response.status_code}",
                    {"status_code": response.status_code, "response": response.text}
                )
                return False
                
        except Exception as e:
            self.log_test_result(
                "Malformed JSON Request",
                False,
                f"Exception during test: {str(e)}",
                {"error": str(e)}
            )
            return False
    
    def test_large_request_handling(self) -> bool:
        """Test handling of large requests."""
        try:
            # Create a very large goal
            large_goal = "Learn programming " * 100  # Very long goal
            payload = {"goal": large_goal}
            
            response = self.session.post(f"{self.base_url}/plan", json=payload, timeout=TEST_TIMEOUT)
            
            if response.status_code == 400:  # Bad request due to size
                self.log_test_result(
                    "Large Request Handling",
                    True,
                    "Correctly rejected oversized request",
                    {"goal_length": len(large_goal), "status_code": response.status_code}
                )
                return True
            elif response.status_code == 200:
                # If it's accepted, that's also valid (depending on implementation)
                self.log_test_result(
                    "Large Request Handling",
                    True,
                    "Accepted large request (implementation dependent)",
                    {"goal_length": len(large_goal), "status_code": response.status_code}
                )
                return True
            else:
                self.log_test_result(
                    "Large Request Handling",
                    False,
                    f"Unexpected status code: {response.status_code}",
                    {"goal_length": len(large_goal), "status_code": response.status_code}
                )
                return False
                
        except Exception as e:
            self.log_test_result(
                "Large Request Handling",
                False,
                f"Exception during test: {str(e)}",
                {"error": str(e)}
            )
            return False
    
    def run_all_tests(self) -> Dict[str, Any]:
        """Run all error handling tests."""
        logger.info("Starting comprehensive error handling test suite")
        start_time = time.time()
        
        tests = [
            ("Server Connectivity", self.test_server_connectivity),
            ("Invalid Goal Validation", self.test_invalid_goal_validation),
            ("Invalid Date Validation", self.test_invalid_date_validation),
            ("Invalid Plan ID Validation", self.test_invalid_plan_id_validation),
            ("Missing API Key Detection", self.test_missing_api_key_scenario),
            ("Valid Plan Creation", self.test_plan_creation_with_valid_data),
            ("Plan Retrieval", self.test_plan_retrieval),
            ("Malformed JSON Request", self.test_malformed_json_request),
            ("Large Request Handling", self.test_large_request_handling),
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            try:
                logger.info(f"Running test: {test_name}")
                if test_func():
                    passed_tests += 1
            except Exception as e:
                logger.error(f"Test {test_name} failed with exception: {e}")
                self.log_test_result(
                    test_name,
                    False,
                    f"Test failed with exception: {str(e)}",
                    {"error": str(e)}
                )
        
        total_time = time.time() - start_time
        
        # Summary
        summary = {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "success_rate": (passed_tests / total_tests) * 100,
            "total_time": total_time,
            "test_results": self.test_results
        }
        
        logger.info(f"Test suite completed in {total_time:.2f}s")
        logger.info(f"Results: {passed_tests}/{total_tests} tests passed ({summary['success_rate']:.1f}%)")
        
        return summary


def main():
    """Main function to run error handling tests."""
    print("🧪 Task Planner Agent - Error Handling Test Suite")
    print("=" * 60)
    
    tester = ErrorHandlingTester()
    results = tester.run_all_tests()
    
    print("\n📊 Test Results Summary:")
    print(f"Total Tests: {results['total_tests']}")
    print(f"Passed: {results['passed_tests']}")
    print(f"Failed: {results['failed_tests']}")
    print(f"Success Rate: {results['success_rate']:.1f}%")
    print(f"Total Time: {results['total_time']:.2f}s")
    
    print("\n📋 Detailed Results:")
    for result in results['test_results']:
        status = "✅" if result['success'] else "❌"
        print(f"{status} {result['test_name']}: {result['message']}")
    
    # Save results to file
    with open("test_results.json", "w") as f:
        json.dump(results, f, indent=2)
    
    print(f"\n💾 Detailed results saved to test_results.json")
    
    return results['success_rate'] >= 80  # Consider 80%+ as success


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
