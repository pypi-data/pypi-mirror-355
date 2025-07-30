"""Modules and Packages module for VenomLearn learning package.

This module covers Python's module system, importing, and creating packages.
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
    """Start the Modules and Packages lesson."""
    console.print("[bold cyan]Python Modules and Packages[/bold cyan]\n")
    
    # Introduction
    ui.display_section("Introduction to Modules")
    console.print("A module is a file containing Python definitions and statements.")
    console.print("Modules help organize code into reusable, logical units.\n")
    
    # Importing Modules
    ui.display_section("Importing Modules")
    console.print("Python has many built-in modules that you can import and use in your programs.")
    
    # Example code
    code = """
# Importing an entire module
import math
print(math.pi)  # Output: 3.141592653589793
print(math.sqrt(16))  # Output: 4.0

# Importing specific items from a module
from random import randint, choice
print(randint(1, 10))  # Output: Random integer between 1 and 10
print(choice(['apple', 'banana', 'cherry']))  # Output: Random item from the list

# Importing with an alias
import datetime as dt
now = dt.datetime.now()
print(now)  # Output: Current date and time

# Importing all items from a module (not recommended in production code)
from math import *
print(sin(0))  # Output: 0.0
print(cos(0))  # Output: 1.0
    """
    
    ui.display_code(code, "python")
    
    # Exercise 1
    ui.display_exercise("Exercise 1: Using Built-in Modules")
    console.print("Write code that uses the 'random' module to:")
    console.print("1. Generate a random number between 1 and 100")
    console.print("2. Shuffle a list of the numbers 1 through 5")
    console.print("3. Print both results\n")
    
    exercise_completed = False
    while not exercise_completed:
        user_code = ui.get_code_input()
        
        # Check if the code contains the required elements
        if "import random" in user_code or "from random import" in user_code:
            if ("randint" in user_code or "randrange" in user_code or "random()" in user_code) and "shuffle" in user_code:
                if "print" in user_code:
                    try:
                        # Execute the code to see if it works
                        local_vars = {}
                        exec(user_code, {}, local_vars)
                        console.print("[bold green]Great job! Your code correctly uses the random module.[/bold green]\n")
                        exercise_completed = True
                    except Exception as e:
                        console.print(f"[bold red]Error in your code: {str(e)}[/bold red]\n")
                else:
                    console.print("[bold red]Make sure to print both results.[/bold red]\n")
            else:
                console.print("[bold red]Make sure to generate a random number and shuffle a list.[/bold red]\n")
        else:
            console.print("[bold red]Make sure to import the random module.[/bold red]\n")
    
    # Creating Modules
    ui.display_section("Creating Your Own Modules")
    console.print("You can create your own modules by saving Python code in a .py file.")
    console.print("Then you can import and use that code in other Python files.\n")
    
    # Example code
    code = """
# File: mymath.py
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b

def multiply(a, b):
    return a * b

def divide(a, b):
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

PI = 3.14159

# In another file, you can import and use this module:
# import mymath
# print(mymath.add(5, 3))  # Output: 8
# print(mymath.PI)  # Output: 3.14159
    """
    
    ui.display_code(code, "python")
    
    # Module Search Path
    ui.display_section("Module Search Path")
    console.print("When you import a module, Python searches for it in several locations:")
    console.print("1. The directory containing the script being run")
    console.print("2. The Python standard library directories")
    console.print("3. Third-party package directories (site-packages)")
    console.print("4. Directories listed in the PYTHONPATH environment variable\n")
    
    # Example code
    code = """
# Viewing the module search path
import sys
print(sys.path)  # List of directories Python searches for modules

# Adding a directory to the search path
sys.path.append('/path/to/my/modules')
    """
    
    ui.display_code(code, "python")
    
    # Packages
    ui.display_section("Python Packages")
    console.print("A package is a directory containing multiple module files and a special __init__.py file.")
    console.print("Packages help organize related modules into a hierarchy.\n")
    
    # Example code
    code = """
# Package structure example:
# mypackage/
# ├── __init__.py
# ├── module1.py
# ├── module2.py
# └── subpackage/
#     ├── __init__.py
#     └── module3.py

# Importing from a package
import mypackage.module1
from mypackage import module2
from mypackage.subpackage import module3

# Using the imported modules
mypackage.module1.function1()
module2.function2()
module3.function3()
    """
    
    ui.display_code(code, "python")
    
    # The __init__.py File
    ui.display_section("The __init__.py File")
    console.print("The __init__.py file makes Python treat a directory as a package.")
    console.print("It can be empty or contain initialization code for the package.\n")
    
    # Example code
    code = """
# Example __init__.py file for a package

# Import commonly used modules to make them available directly from the package
from .module1 import function1, Class1
from .module2 import function2

# Define package-level variables
__version__ = '1.0.0'
__author__ = 'Your Name'

# With this __init__.py, users can do:
# from mypackage import function1, function2, Class1
    """
    
    ui.display_code(code, "python")
    
    # Exercise 2
    ui.display_exercise("Exercise 2: Package Structure")
    console.print("Describe the structure of a Python package called 'calculator' that has:")
    console.print("1. Basic operations in a module called 'basic.py'")
    console.print("2. Advanced operations in a module called 'advanced.py'")
    console.print("3. A subpackage called 'scientific' with a module 'trigonometry.py'")
    console.print("4. Appropriate __init__.py files\n")
    
    exercise_completed = False
    while not exercise_completed:
        user_code = ui.get_code_input()
        
        # This is more of a conceptual exercise, so we'll just check for keywords
        if "calculator" in user_code and "basic.py" in user_code and "advanced.py" in user_code:
            if "scientific" in user_code and "trigonometry.py" in user_code:
                if "__init__.py" in user_code:
                    console.print("[bold green]Great job! Your package structure looks correct.[/bold green]\n")
                    exercise_completed = True
                else:
                    console.print("[bold red]Make sure to include __init__.py files in your package structure.[/bold red]\n")
            else:
                console.print("[bold red]Make sure to include the scientific subpackage with trigonometry.py.[/bold red]\n")
        else:
            console.print("[bold red]Make sure to describe the calculator package with basic.py and advanced.py modules.[/bold red]\n")
    
    # Standard Library
    ui.display_section("Python Standard Library")
    console.print("Python comes with a rich standard library of modules for various tasks.")
    console.print("Here are some commonly used standard library modules:\n")
    
    # Example code
    code = """
# os - Operating system interface
import os
print(os.getcwd())  # Current working directory
os.mkdir('new_directory')  # Create a directory

# datetime - Date and time handling
from datetime import datetime, timedelta
now = datetime.now()
one_week_ago = now - timedelta(days=7)

# json - JSON encoding and decoding
import json
data = {'name': 'Alice', 'age': 30}
json_string = json.dumps(data)
parsed_data = json.loads(json_string)

# re - Regular expressions
import re
pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
email = 'user@example.com'
is_valid = re.match(pattern, email) is not None

# collections - Specialized container datatypes
from collections import Counter
words = ['apple', 'banana', 'apple', 'orange', 'banana', 'apple']
word_counts = Counter(words)  # Counter({'apple': 3, 'banana': 2, 'orange': 1})
    """
    
    ui.display_code(code, "python")
    
    # Quiz
    ui.display_section("Quiz Time!")
    
    score = 0
    
    # Question 1
    answer = select(
        "What is the correct way to import the 'random' module and use its 'randint' function?",
        choices=[
            "import random.randint; random.randint(1, 10)",
            "import random; random.randint(1, 10)",  # Correct answer
            "from random import randint(); randint(1, 10)",
            "import randint from random; randint(1, 10)"
        ]
    ).ask()
    
    if answer == "import random; random.randint(1, 10)":
        console.print("[bold green]Correct! This properly imports the random module and accesses its randint function.[/bold green]")
        score += 1
    else:
        console.print("[bold red]Not quite. The correct way is: import random; random.randint(1, 10)[/bold red]")
    
    # Question 2
    answer = select(
        "What is the purpose of the __init__.py file in a package?",
        choices=[
            "It initializes all variables in the package",
            "It's required to make Python treat the directory as a package",  # Correct answer
            "It's where you must define all functions used in the package",
            "It's only needed for backward compatibility with Python 2"
        ]
    ).ask()
    
    if answer == "It's required to make Python treat the directory as a package":
        console.print("[bold green]Correct! The __init__.py file makes Python treat a directory as a package.[/bold green]")
        score += 1
    else:
        console.print("[bold red]Not quite. The __init__.py file is required to make Python treat a directory as a package.[/bold red]")
    
    # Question 3
    answer = select(
        "Which of the following is NOT a module in the Python standard library?",
        choices=[
            "os",
            "datetime",
            "requests",  # Correct answer (requests is a popular third-party package)
            "json"
        ]
    ).ask()
    
    if answer == "requests":
        console.print("[bold green]Correct! The 'requests' module is a popular third-party package, not part of the standard library.[/bold green]")
        score += 1
    else:
        console.print("[bold red]Not quite. The 'requests' module is a popular third-party package, not part of the standard library.[/bold red]")
    
    # Display score
    console.print(f"\n[bold]Your score: {score}/3[/bold]")
    
    if score == 3:
        console.print("[bold green]Perfect! You've mastered Python modules and packages![/bold green]")
    elif score >= 2:
        console.print("[bold yellow]Good job! You're getting the hang of Python modules and packages.[/bold yellow]")
    else:
        console.print("[bold]Keep practicing! Review the lesson and try again.[/bold]")
    
    # Summary
    ui.display_section("Summary")
    console.print("In this lesson, you learned about:")
    console.print("• Importing and using modules from the Python standard library")
    console.print("• Creating your own modules to organize code")
    console.print("• How Python searches for modules")
    console.print("• Creating packages to organize related modules")
    console.print("• The role of the __init__.py file in packages")
    console.print("• Some commonly used modules from the standard library\n")
    
    # Ask if user wants to continue
    continue_learning = select(
        "Have you completed this lesson?",
        choices=[
            "Yes, I've completed this lesson",
            "No, I need more time with this topic"
        ]
    ).ask()
    
    return "Yes" in continue_learning