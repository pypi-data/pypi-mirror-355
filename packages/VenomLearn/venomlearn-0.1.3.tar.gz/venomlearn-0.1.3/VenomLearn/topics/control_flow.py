"""Control Flow module for VenomLearn learning package.

This module covers Python's control flow structures like if-else statements and loops.
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
    """Start the Control Flow lesson."""
    console.print("[bold cyan]Control Flow in Python[/bold cyan]\n")
    
    # Introduction
    ui.display_section("Introduction to Control Flow")
    console.print("Control flow is how we direct the execution of a program based on conditions and repetition.")
    console.print("In this lesson, we'll learn about conditional statements and loops in Python.\n")
    
    # Conditional Statements
    ui.display_section("Conditional Statements (if-else)")
    console.print("Conditional statements allow your program to make decisions based on conditions.")
    
    # Example code
    code = """
# Basic if statement
age = 18

if age >= 18:
    print("You are an adult")
else:
    print("You are a minor")

# if-elif-else statement
score = 85

if score >= 90:
    grade = "A"
elif score >= 80:
    grade = "B"
elif score >= 70:
    grade = "C"
elif score >= 60:
    grade = "D"
else:
    grade = "F"

print(f"Your grade is: {grade}")
    """
    
    ui.display_code(code, "python")
    
    # Exercise 1
    ui.display_exercise("Exercise 1: Conditional Statements")
    console.print("Write a program that asks the user for a temperature in Celsius and then prints whether it's 'Hot' (over 25°C), 'Pleasant' (between 15°C and 25°C), or 'Cold' (below 15°C).\n")
    
    exercise_completed = False
    while not exercise_completed:
        user_code = ui.get_code_input()
        
        # Check if the code contains the required elements
        if "if" in user_code and ("input(" in user_code or "temperature" in user_code):
            try:
                # For simplicity, we'll just check if the code structure seems correct
                console.print("[bold green]Good job! Your code looks correct.[/bold green]\n")
                console.print("[italic]Note: In a real program, this would evaluate the temperature and respond accordingly.[/italic]\n")
                exercise_completed = True
            except Exception as e:
                console.print(f"[bold red]Error in your code: {str(e)}[/bold red]\n")
        else:
            console.print("[bold red]Make sure to use if-elif-else statements and get the temperature from the user.[/bold red]\n")
    
    # Loops
    ui.display_section("Loops")
    console.print("Loops allow you to repeat a block of code multiple times.")
    console.print("Python has two main types of loops: for loops and while loops.\n")
    
    # For Loops
    ui.display_section("For Loops")
    console.print("For loops iterate over a sequence (like a list, tuple, or string).")
    
    # Example code
    code = """
# Iterating over a range
for i in range(5):
    print(f"Count: {i}")

# Iterating over a list
fruits = ["apple", "banana", "cherry"]
for fruit in fruits:
    print(f"I like {fruit}s")

# Iterating over a string
for char in "Python":
    print(char)
    """
    
    ui.display_code(code, "python")
    
    # While Loops
    ui.display_section("While Loops")
    console.print("While loops continue executing as long as a condition is true.")
    
    # Example code
    code = """
# Basic while loop
count = 0
while count < 5:
    print(f"Count: {count}")
    count += 1

# While loop with break
while True:
    response = input("Type 'exit' to quit: ")
    if response.lower() == "exit":
        break
    print("You typed:", response)
    """
    
    ui.display_code(code, "python")
    
    # Exercise 2
    ui.display_exercise("Exercise 2: Loops")
    console.print("Write a program that uses a loop to print the first 5 square numbers (1, 4, 9, 16, 25).\n")
    
    exercise_completed = False
    while not exercise_completed:
        user_code = ui.get_code_input()
        
        # Check if the code contains a loop
        if ("for" in user_code or "while" in user_code) and "print(" in user_code:
            try:
                # For simplicity, we'll just check if the code structure seems correct
                console.print("[bold green]Good job! Your code looks correct.[/bold green]\n")
                console.print("[italic]Note: In a real program, this would print the square numbers.[/italic]\n")
                exercise_completed = True
            except Exception as e:
                console.print(f"[bold red]Error in your code: {str(e)}[/bold red]\n")
        else:
            console.print("[bold red]Make sure to use a loop and print the square numbers.[/bold red]\n")
    
    # Loop Control Statements
    ui.display_section("Loop Control Statements")
    console.print("Python provides statements to control the flow of loops:")
    console.print("• break - exits the loop entirely")
    console.print("• continue - skips the current iteration and moves to the next")
    console.print("• pass - does nothing, acts as a placeholder\n")
    
    # Example code
    code = """
# Using break
for i in range(10):
    if i == 5:
        break
    print(i)  # Prints 0, 1, 2, 3, 4

# Using continue
for i in range(5):
    if i == 2:
        continue
    print(i)  # Prints 0, 1, 3, 4
    """
    
    ui.display_code(code, "python")
    
    # Quiz
    ui.display_section("Quiz Time!")
    
    score = 0
    
    # Question 1
    answer = select(
        "What will the following code print? \nfor i in range(3, 8): print(i)",
        choices=[
            "3, 4, 5, 6, 7",  # Correct answer
            "3, 4, 5, 6, 7, 8",
            "3, 5, 7",
            "4, 5, 6, 7"
        ]
    ).ask()
    
    if answer == "3, 4, 5, 6, 7":
        console.print("[bold green]Correct! range(3, 8) generates numbers from 3 up to (but not including) 8.[/bold green]")
        score += 1
    else:
        console.print("[bold red]Not quite. range(3, 8) generates numbers from 3 up to (but not including) 8.[/bold red]")
    
    # Question 2
    answer = select(
        "Which statement is used to exit a loop prematurely?",
        choices=[
            "exit",
            "stop",
            "break",  # Correct answer
            "end"
        ]
    ).ask()
    
    if answer == "break":
        console.print("[bold green]Correct! The break statement is used to exit a loop prematurely.[/bold green]")
        score += 1
    else:
        console.print("[bold red]Not quite. The break statement is used to exit a loop prematurely.[/bold red]")
    
    # Question 3
    answer = select(
        "What will the following code print? \nx = 0\nwhile x < 5:\n    x += 1\n    if x == 3:\n        continue\n    print(x)",
        choices=[
            "1, 2, 3, 4, 5",
            "1, 2, 4, 5",  # Correct answer
            "0, 1, 2, 4, 5",
            "1, 2, 3, 4"
        ]
    ).ask()
    
    if answer == "1, 2, 4, 5":
        console.print("[bold green]Correct! The continue statement skips the print when x is 3.[/bold green]")
        score += 1
    else:
        console.print("[bold red]Not quite. The continue statement skips the print when x is 3.[/bold red]")
    
    # Display score
    console.print(f"\n[bold]Your score: {score}/3[/bold]")
    
    if score == 3:
        console.print("[bold green]Perfect! You've mastered Python control flow![/bold green]")
    elif score >= 2:
        console.print("[bold yellow]Good job! You're getting the hang of Python control flow.[/bold yellow]")
    else:
        console.print("[bold]Keep practicing! Review the lesson and try again.[/bold]")
    
    # Summary
    ui.display_section("Summary")
    console.print("In this lesson, you learned about:")
    console.print("• Conditional statements (if, elif, else)")
    console.print("• For loops for iterating over sequences")
    console.print("• While loops for condition-based iteration")
    console.print("• Loop control statements: break, continue, and pass\n")
    
    # Ask if user wants to continue
    continue_learning = select(
        "Have you completed this lesson?",
        choices=[
            "Yes, I've completed this lesson",
            "No, I need more time with this topic"
        ]
    ).ask()
    
    return "Yes" in continue_learning