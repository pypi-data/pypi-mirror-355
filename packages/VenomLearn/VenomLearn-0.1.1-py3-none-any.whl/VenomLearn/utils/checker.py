"""Code checker module for VenomLearn learning package.

This module provides functions to check and validate user code submissions.
"""

import ast
import sys
from io import StringIO
from contextlib import redirect_stdout


def check_code(code, expected_output=None, expected_variables=None, check_syntax_only=False):
    """Check user code against expected output or variables.
    
    Args:
        code (str): The user's code to check
        expected_output (str, optional): Expected output of the code
        expected_variables (dict, optional): Expected variables and their values
        check_syntax_only (bool, optional): Only check syntax, not execution
        
    Returns:
        tuple: (is_correct, message)
    """
    # Check syntax
    try:
        ast.parse(code)
    except SyntaxError as e:
        return False, f"Syntax error: {str(e)}"
    
    if check_syntax_only:
        return True, "Syntax is correct!"
    
    # Execute code and check results
    local_vars = {}
    captured_output = StringIO()
    
    try:
        with redirect_stdout(captured_output):
            exec(code, {}, local_vars)
        
        output = captured_output.getvalue().strip()
        
        # Check expected output
        if expected_output is not None and output != expected_output:
            return False, f"Output doesn't match expected result.\nExpected: {expected_output}\nGot: {output}"
        
        # Check expected variables
        if expected_variables is not None:
            for var_name, expected_value in expected_variables.items():
                if var_name not in local_vars:
                    return False, f"Variable '{var_name}' is missing."
                
                if local_vars[var_name] != expected_value:
                    return False, f"Variable '{var_name}' has incorrect value.\nExpected: {expected_value}\nGot: {local_vars[var_name]}"
        
        return True, "Code is correct!"
    
    except Exception as e:
        return False, f"Error executing code: {str(e)}"


def check_function(code, function_name, test_cases):
    """Check if a function works correctly with test cases.
    
    Args:
        code (str): The user's code containing the function
        function_name (str): The name of the function to test
        test_cases (list): List of tuples (args, kwargs, expected_output)
        
    Returns:
        tuple: (is_correct, message)
    """
    # Check syntax
    try:
        ast.parse(code)
    except SyntaxError as e:
        return False, f"Syntax error: {str(e)}"
    
    # Execute code to define the function
    local_vars = {}
    
    try:
        exec(code, {}, local_vars)
        
        if function_name not in local_vars:
            return False, f"Function '{function_name}' is not defined."
        
        if not callable(local_vars[function_name]):
            return False, f"'{function_name}' is not a function."
        
        # Test the function with test cases
        for i, (args, kwargs, expected) in enumerate(test_cases, 1):
            result = local_vars[function_name](*args, **kwargs)
            
            if result != expected:
                return False, f"Test case {i} failed.\nInput: args={args}, kwargs={kwargs}\nExpected: {expected}\nGot: {result}"
        
        return True, "All test cases passed!"
    
    except Exception as e:
        return False, f"Error executing code: {str(e)}"