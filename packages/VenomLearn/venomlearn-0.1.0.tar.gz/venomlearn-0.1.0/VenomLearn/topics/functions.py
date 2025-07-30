"""Functions module for VenomLearn learning package.

This module covers Python functions, parameters, return values, and scope.
"""

import time
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.markdown import Markdown
from questionary import select, text

from VenomLearn.utils.terminal_ui import TerminalUI
from VenomLearn.utils.checker import check_code, check_function

console = Console()
ui = TerminalUI()


def start_lesson():
    """Start the Functions lesson."""
    console.print("[bold cyan]Python Functions[/bold cyan]\n")
    
    # Introduction
    ui.display_section("Introduction to Functions")
    console.print("Functions are reusable blocks of code that perform a specific task.")
    console.print("They help organize code, avoid repetition, and make programs more readable.\n")
    
    # Defining Functions
    ui.display_section("Defining Functions")
    console.print("In Python, you define a function using the 'def' keyword, followed by the function name and parameters.")
    
    # Example code
    code = """
# Basic function definition
def greet():
    print("Hello, world!")

# Function with parameters
def greet_person(name):
    print(f"Hello, {name}!")

# Function with default parameter
def greet_with_time(name, time_of_day="day"):
    print(f"Good {time_of_day}, {name}!")

# Calling functions
greet()  # Output: Hello, world!
greet_person("Alice")  # Output: Hello, Alice!
greet_with_time("Bob", "morning")  # Output: Good morning, Bob!
greet_with_time("Charlie")  # Output: Good day, Charlie!
    """
    
    ui.display_code(code, "python")
    
    # Exercise 1
    ui.display_exercise("Exercise 1: Define a Function")
    console.print("Define a function called 'calculate_area' that takes the radius of a circle as a parameter and returns its area.")
    console.print("Remember that the area of a circle is π × r².\n")
    
    exercise_completed = False
    while not exercise_completed:
        user_code = ui.get_code_input()
        
        # Check if the code contains the required function
        if "def calculate_area" in user_code and "return" in user_code:
            try:
                # Test the function with some test cases
                test_cases = [
                    ((1,), {}, 3.141592653589793),  # r=1
                    ((2,), {}, 12.566370614359172),  # r=2
                    ((0,), {}, 0)  # r=0
                ]
                
                is_correct, message = check_function(user_code, "calculate_area", test_cases)
                
                if is_correct:
                    console.print("[bold green]Great job! Your function correctly calculates the area of a circle.[/bold green]\n")
                    exercise_completed = True
                else:
                    console.print(f"[bold red]{message}[/bold red]\n")
            except Exception as e:
                console.print(f"[bold red]Error in your code: {str(e)}[/bold red]\n")
        else:
            console.print("[bold red]Make sure to define a function called 'calculate_area' that returns the area of a circle.[/bold red]\n")
    
    # Return Values
    ui.display_section("Return Values")
    console.print("Functions can return values using the 'return' statement.")
    console.print("A function can return a single value, multiple values, or nothing at all.\n")
    
    # Example code
    code = """
# Function that returns a value
def square(x):
    return x * x

# Function that returns multiple values
def min_max(numbers):
    return min(numbers), max(numbers)

# Using returned values
result = square(5)  # result = 25

minimum, maximum = min_max([1, 5, 3, 9, 2])  # minimum = 1, maximum = 9
    """
    
    ui.display_code(code, "python")
    
    # Function Scope
    ui.display_section("Function Scope")
    console.print("Variables defined inside a function have local scope and are not accessible outside the function.")
    console.print("Variables defined outside functions have global scope and can be accessed inside functions (but not modified without the 'global' keyword).\n")
    
    # Example code
    code = """
# Global variable
counter = 0

def increment():
    # Local variable
    step = 1
    # Using the global keyword to modify a global variable
    global counter
    counter += step
    return counter

print(increment())  # Output: 1
print(increment())  # Output: 2

# This would cause an error because 'step' is a local variable
# print(step)  # NameError: name 'step' is not defined
    """
    
    ui.display_code(code, "python")
    
    # Exercise 2
    ui.display_exercise("Exercise 2: Function with Multiple Returns")
    console.print("Write a function called 'analyze_number' that takes a number as input and returns three values:")
    console.print("1. Whether the number is positive, negative, or zero (as a string)")
    console.print("2. Whether the number is even or odd (as a string)")
    console.print("3. The square of the number\n")
    
    exercise_completed = False
    while not exercise_completed:
        user_code = ui.get_code_input()
        
        # Check if the code contains the required function
        if "def analyze_number" in user_code and "return" in user_code:
            try:
                # Execute the code to define the function
                local_vars = {}
                exec(user_code, {}, local_vars)
                
                if "analyze_number" in local_vars and callable(local_vars["analyze_number"]):
                    # Test the function with some inputs
                    test_cases = [
                        (5,),  # Positive, odd, 25
                        (-4,),  # Negative, even, 16
                        (0,)   # Zero, even, 0
                    ]
                    
                    expected_results = [
                        ("positive", "odd", 25),
                        ("negative", "even", 16),
                        ("zero", "even", 0)
                    ]
                    
                    all_correct = True
                    for i, (args, expected) in enumerate(zip(test_cases, expected_results)):
                        result = local_vars["analyze_number"](*args)
                        
                        if not isinstance(result, tuple) or len(result) != 3:
                            console.print("[bold red]Your function should return three values as a tuple.[/bold red]\n")
                            all_correct = False
                            break
                        
                        sign, parity, square = result
                        exp_sign, exp_parity, exp_square = expected
                        
                        if sign.lower() != exp_sign or parity.lower() != exp_parity or square != exp_square:
                            console.print(f"[bold red]Test case failed for input {args[0]}.\nExpected: {expected}\nGot: {result}[/bold red]\n")
                            all_correct = False
                            break
                    
                    if all_correct:
                        console.print("[bold green]Excellent! Your function correctly analyzes numbers.[/bold green]\n")
                        exercise_completed = True
                else:
                    console.print("[bold red]Make sure to define a function called 'analyze_number'.[/bold red]\n")
            except Exception as e:
                console.print(f"[bold red]Error in your code: {str(e)}[/bold red]\n")
        else:
            console.print("[bold red]Make sure to define a function called 'analyze_number' that returns three values.[/bold red]\n")
    
    # Lambda Functions
    ui.display_section("Lambda Functions")
    console.print("Lambda functions are small, anonymous functions defined with the 'lambda' keyword.")
    console.print("They can have any number of parameters but only one expression.\n")
    
    # Example code
    code = """
# Lambda function to square a number
square = lambda x: x * x

# Lambda function with multiple parameters
sum_product = lambda a, b: (a + b, a * b)

# Using lambda with built-in functions
numbers = [1, 5, 3, 9, 2]
sorted_numbers = sorted(numbers)  # [1, 2, 3, 5, 9]
sorted_by_square = sorted(numbers, key=lambda x: x * x)  # [1, 2, 3, 5, 9]
    """
    
    ui.display_code(code, "python")
    
    # Quiz
    ui.display_section("Quiz Time!")
    
    score = 0
    
    # Question 1
    answer = select(
        "What keyword is used to define a function in Python?",
        choices=[
            "function",
            "def",  # Correct answer
            "define",
            "func"
        ]
    ).ask()
    
    if answer == "def":
        console.print("[bold green]Correct! The 'def' keyword is used to define functions in Python.[/bold green]")
        score += 1
    else:
        console.print("[bold red]Not quite. The 'def' keyword is used to define functions in Python.[/bold red]")
    
    # Question 2
    answer = select(
        "What does the following function return? \ndef mystery(x, y):\n    if x > y:\n        return x\n    else:\n        return y",
        choices=[
            "The sum of x and y",
            "The product of x and y",
            "The larger of x and y",  # Correct answer
            "The smaller of x and y"
        ]
    ).ask()
    
    if answer == "The larger of x and y":
        console.print("[bold green]Correct! This function returns the larger of the two input values.[/bold green]")
        score += 1
    else:
        console.print("[bold red]Not quite. This function returns the larger of the two input values.[/bold red]")
    
    # Question 3
    answer = select(
        "Which of the following is a valid lambda function in Python?",
        choices=[
            "lambda x: return x * 2",
            "lambda x => x * 2",
            "lambda x -> x * 2",
            "lambda x: x * 2"  # Correct answer
        ]
    ).ask()
    
    if answer == "lambda x: x * 2":
        console.print("[bold green]Correct! Lambda functions use the syntax 'lambda parameters: expression'.[/bold green]")
        score += 1
    else:
        console.print("[bold red]Not quite. Lambda functions use the syntax 'lambda parameters: expression'.[/bold red]")
    
    # Display score
    console.print(f"\n[bold]Your score: {score}/3[/bold]")
    
    if score == 3:
        console.print("[bold green]Perfect! You've mastered Python functions![/bold green]")
    elif score >= 2:
        console.print("[bold yellow]Good job! You're getting the hang of Python functions.[/bold yellow]")
    else:
        console.print("[bold]Keep practicing! Review the lesson and try again.[/bold]")
    
    # Summary
    ui.display_section("Summary")
    console.print("In this lesson, you learned about:")
    console.print("• Defining functions with the 'def' keyword")
    console.print("• Function parameters and default values")
    console.print("• Return values and returning multiple values")
    console.print("• Function scope (local and global variables)")
    console.print("• Lambda functions for small, anonymous operations\n")
    
    # Ask if user wants to continue
    continue_learning = select(
        "Have you completed this lesson?",
        choices=[
            "Yes, I've completed this lesson",
            "No, I need more time with this topic"
        ]
    ).ask()
    
    return "Yes" in continue_learning