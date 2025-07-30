"""Python Basics module for VenomLearn learning package.

This module covers fundamental Python concepts like variables, data types, and basic input/output.
"""

import time
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.markdown import Markdown
from questionary import select, text

from VenomLearn.utils.terminal_ui import TerminalUI
from VenomLearn.utils.checker import check_code

console = Console()
ui = TerminalUI()


def start_lesson():
    """Start the Python Basics lesson."""
    console.print("[bold cyan]Python Basics[/bold cyan]\n")
    
    # Introduction
    ui.display_section("Introduction to Python")
    console.print("Python is a high-level, interpreted programming language known for its simplicity and readability.")
    console.print("In this lesson, we'll learn about variables, data types, and basic input/output operations.\n")
    
    # Variables and Data Types
    ui.display_section("Variables and Data Types")
    console.print("Variables are used to store data in a program. In Python, you don't need to declare a variable's type.")
    
    # Example code
    code = """
# Integer
age = 25

# Float
height = 5.9

# String
name = "Python Learner"

# Boolean
is_student = True

# Print variables
print(f"Name: {name}, Age: {age}, Height: {height}, Student: {is_student}")
    """
    
    ui.display_code(code, "python")
    
    # Exercise 1
    ui.display_exercise("Exercise 1: Create Variables")
    console.print("Create a variable called 'favorite_language' and assign it the value 'Python'.")
    console.print("Then create a variable called 'year' and assign it the current year.\n")
    
    exercise_completed = False
    while not exercise_completed:
        user_code = ui.get_code_input()
        
        # Check if the code contains the required variables
        if "favorite_language" in user_code and "year" in user_code:
            try:
                # Execute user code in a safe environment
                local_vars = {}
                exec(user_code, {}, local_vars)
                
                if local_vars.get("favorite_language") == "Python" and isinstance(local_vars.get("year"), int):
                    console.print("[bold green]Great job! You've created the variables correctly.[/bold green]\n")
                    exercise_completed = True
                else:
                    console.print("[bold red]Almost there! Make sure 'favorite_language' is 'Python' and 'year' is a number.[/bold red]\n")
            except Exception as e:
                console.print(f"[bold red]Error in your code: {str(e)}[/bold red]\n")
        else:
            console.print("[bold red]Make sure to create both 'favorite_language' and 'year' variables.[/bold red]\n")
    
    # Input and Output
    ui.display_section("Input and Output")
    console.print("Python provides functions for getting input from users and displaying output.")
    
    # Example code
    code = """
# Getting input from the user
user_name = input("Enter your name: ")

# Converting input to different types
user_age = int(input("Enter your age: "))

# Displaying output
print(f"Hello, {user_name}! In 10 years, you'll be {user_age + 10} years old.")
    """
    
    ui.display_code(code, "python")
    
    # Exercise 2
    ui.display_exercise("Exercise 2: Input and Output")
    console.print("Write code that asks the user for their favorite color and then prints a message saying that's a great color.\n")
    
    exercise_completed = False
    while not exercise_completed:
        user_code = ui.get_code_input()
        
        # Check if the code contains input and print
        if "input(" in user_code and "print(" in user_code:
            try:
                # This is a bit tricky to test since we can't easily simulate user input
                # For simplicity, we'll just check if the code structure seems correct
                console.print("[bold green]Good job! Your code looks correct.[/bold green]\n")
                console.print("[italic]Note: In a real program, this would ask for user input and respond accordingly.[/italic]\n")
                exercise_completed = True
            except Exception as e:
                console.print(f"[bold red]Error in your code: {str(e)}[/bold red]\n")
        else:
            console.print("[bold red]Make sure to use the input() function to get the user's favorite color and print() to respond.[/bold red]\n")
    
    # Quiz
    ui.display_section("Quiz Time!")
    
    score = 0
    
    # Question 1
    answer = select(
        "Which of the following is NOT a built-in data type in Python?",
        choices=[
            "Integer",
            "Float",
            "Character",  # This is the correct answer (Python has strings, not char)
            "Boolean"
        ]
    ).ask()
    
    if answer == "Character":
        console.print("[bold green]Correct! Python doesn't have a separate character type - it uses strings instead.[/bold green]")
        score += 1
    else:
        console.print("[bold red]Not quite. Python doesn't have a separate character type - it uses strings instead.[/bold red]")
    
    # Question 2
    answer = select(
        "What function is used to get input from the user in Python?",
        choices=[
            "get()",
            "input()",  # Correct answer
            "read()",
            "scan()"
        ]
    ).ask()
    
    if answer == "input()":
        console.print("[bold green]Correct! The input() function is used to get user input in Python.[/bold green]")
        score += 1
    else:
        console.print("[bold red]Not quite. The input() function is used to get user input in Python.[/bold red]")
    
    # Question 3
    answer = select(
        "What will the following code print? x = 5; y = '3'; print(x + y)",
        choices=[
            "8",
            "53",
            "5 + 3",
            "Error"  # Correct answer
        ]
    ).ask()
    
    if answer == "Error":
        console.print("[bold green]Correct! You can't add an integer and a string in Python without converting one of them.[/bold green]")
        score += 1
    else:
        console.print("[bold red]Not quite. You can't add an integer and a string in Python without converting one of them.[/bold red]")
    
    # Display score
    console.print(f"\n[bold]Your score: {score}/3[/bold]")
    
    if score == 3:
        console.print("[bold green]Perfect! You've mastered Python basics![/bold green]")
    elif score >= 2:
        console.print("[bold yellow]Good job! You're getting the hang of Python basics.[/bold yellow]")
    else:
        console.print("[bold]Keep practicing! Review the lesson and try again.[/bold]")
    
    # Summary
    ui.display_section("Summary")
    console.print("In this lesson, you learned about:")
    console.print("• Variables and how to create them")
    console.print("• Basic data types: integers, floats, strings, and booleans")
    console.print("• Getting input from users with the input() function")
    console.print("• Displaying output with the print() function\n")
    
    # Ask if user wants to continue
    continue_learning = select(
        "Have you completed this lesson?",
        choices=[
            "Yes, I've completed this lesson",
            "No, I need more time with this topic"
        ]
    ).ask()
    
    return "Yes" in continue_learning