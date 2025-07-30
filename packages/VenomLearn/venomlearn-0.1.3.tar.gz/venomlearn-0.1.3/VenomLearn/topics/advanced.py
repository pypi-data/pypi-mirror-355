"""Advanced Python Topics module for VenomLearn learning package.

This module covers advanced Python concepts like decorators, generators, context managers, and more.
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
    """Start the Advanced Python Topics lesson."""
    console.print("[bold cyan]Advanced Python Topics[/bold cyan]\n")
    
    # Introduction
    ui.display_section("Introduction to Advanced Python")
    console.print("Python offers many advanced features that make it powerful and flexible.")
    console.print("In this lesson, we'll explore decorators, generators, context managers, and more.\n")
    
    # Decorators
    ui.display_section("Decorators")
    console.print("Decorators are a powerful way to modify or enhance functions without changing their code.")
    console.print("They are functions that take another function as an argument and extend its behavior.\n")
    
    # Example code
    code = """
# Basic decorator example
def my_decorator(func):
    def wrapper():
        print("Something is happening before the function is called.")
        func()
        print("Something is happening after the function is called.")
    return wrapper

@my_decorator
def say_hello():
    print("Hello!")

# Calling the decorated function
say_hello()

# Output:
# Something is happening before the function is called.
# Hello!
# Something is happening after the function is called.

# Decorator with arguments
def repeat(n):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for _ in range(n):
                result = func(*args, **kwargs)
            return result
        return wrapper
    return decorator

@repeat(3)
def greet(name):
    print(f"Hello, {name}!")

greet("Alice")  # Will print "Hello, Alice!" three times
    """
    
    ui.display_code(code, "python")
    
    # Exercise 1
    ui.display_exercise("Exercise 1: Create a Timing Decorator")
    console.print("Create a decorator called 'timer' that measures the time it takes for a function to execute.")
    console.print("The decorator should print the time elapsed in seconds.\n")
    
    exercise_completed = False
    while not exercise_completed:
        user_code = ui.get_code_input()
        
        # Check if the code contains the required elements
        if "def timer" in user_code and "def wrapper" in user_code and "time" in user_code:
            try:
                # Execute the code to define the decorator
                local_vars = {}
                exec(user_code, {}, local_vars)
                
                if "timer" in local_vars and callable(local_vars["timer"]):
                    console.print("[bold green]Great job! Your timer decorator looks good.[/bold green]\n")
                    exercise_completed = True
                else:
                    console.print("[bold red]Make sure to define a decorator called 'timer'.[/bold red]\n")
            except Exception as e:
                console.print(f"[bold red]Error in your code: {str(e)}[/bold red]\n")
        else:
            console.print("[bold red]Make sure to create a decorator that uses the time module to measure execution time.[/bold red]\n")
    
    # Generators
    ui.display_section("Generators")
    console.print("Generators are a simple way to create iterators using functions and the yield statement.")
    console.print("They allow you to iterate over a potentially large sequence without creating the entire sequence in memory.\n")
    
    # Example code
    code = """
# Basic generator function
def count_up_to(n):
    i = 0
    while i < n:
        yield i
        i += 1

# Using the generator
for number in count_up_to(5):
    print(number)  # Outputs: 0, 1, 2, 3, 4

# Generator expressions (similar to list comprehensions)
squares_gen = (x**2 for x in range(5))
print(list(squares_gen))  # Outputs: [0, 1, 4, 9, 16]

# Infinite sequence generator
def fibonacci():
    a, b = 0, 1
    while True:
        yield a
        a, b = b, a + b

# Get first 10 Fibonacci numbers
fib_gen = fibonacci()
fib_numbers = [next(fib_gen) for _ in range(10)]
print(fib_numbers)  # Outputs: [0, 1, 1, 2, 3, 5, 8, 13, 21, 34]
    """
    
    ui.display_code(code, "python")
    
    # Exercise 2
    ui.display_exercise("Exercise 2: Create a Generator")
    console.print("Create a generator function called 'prime_numbers' that yields prime numbers up to a given limit.")
    console.print("A prime number is a natural number greater than 1 that is not divisible by any number other than 1 and itself.\n")
    
    exercise_completed = False
    while not exercise_completed:
        user_code = ui.get_code_input()
        
        # Check if the code contains the required elements
        if "def prime_numbers" in user_code and "yield" in user_code:
            try:
                # Execute the code to define the generator
                local_vars = {}
                exec(user_code, {}, local_vars)
                
                if "prime_numbers" in local_vars and callable(local_vars["prime_numbers"]):
                    # Test the generator with a small limit
                    try:
                        primes = list(local_vars["prime_numbers"](20))
                        expected = [2, 3, 5, 7, 11, 13, 17, 19]
                        
                        if primes == expected:
                            console.print("[bold green]Great job! Your prime_numbers generator works correctly.[/bold green]\n")
                            exercise_completed = True
                        else:
                            console.print(f"[bold red]Your generator doesn't produce the expected prime numbers. Expected: {expected}, Got: {primes}[/bold red]\n")
                    except Exception as e:
                        console.print(f"[bold red]Error when testing your generator: {str(e)}[/bold red]\n")
                else:
                    console.print("[bold red]Make sure to define a generator function called 'prime_numbers'.[/bold red]\n")
            except Exception as e:
                console.print(f"[bold red]Error in your code: {str(e)}[/bold red]\n")
        else:
            console.print("[bold red]Make sure to create a generator function that yields prime numbers.[/bold red]\n")
    
    # Context Managers
    ui.display_section("Context Managers")
    console.print("Context managers provide a way to allocate and release resources precisely when you want to.")
    console.print("The 'with' statement in Python is used with context managers to ensure resources are properly managed.\n")
    
    # Example code
    code = """
# Using built-in context managers
with open('example.txt', 'w') as file:
    file.write('Hello, World!')
# File is automatically closed after the with block

# Creating a context manager using a class
class Timer:
    def __enter__(self):
        import time
        self.start = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        import time
        self.end = time.time()
        print(f"Elapsed time: {self.end - self.start:.2f} seconds")

# Using our custom context manager
with Timer():
    # Code to be timed
    import time
    time.sleep(1)  # Sleep for 1 second

# Creating a context manager using contextlib
from contextlib import contextmanager

@contextmanager
def file_manager(filename, mode):
    try:
        file = open(filename, mode)
        yield file
    finally:
        file.close()

# Using the contextlib-based context manager
with file_manager('example.txt', 'r') as file:
    content = file.read()
    print(content)  # Outputs: Hello, World!
    """
    
    ui.display_code(code, "python")
    
    # Exercise 3
    ui.display_exercise("Exercise 3: Create a Context Manager")
    console.print("Create a context manager called 'Indenter' that helps with printing indented text.")
    console.print("It should have methods to increase and decrease the indentation level.\n")
    
    exercise_completed = False
    while not exercise_completed:
        user_code = ui.get_code_input()
        
        # Check if the code contains the required elements
        if "class Indenter" in user_code and "__enter__" in user_code and "__exit__" in user_code:
            try:
                # Execute the code to define the context manager
                local_vars = {}
                exec(user_code, {}, local_vars)
                
                if "Indenter" in local_vars and callable(local_vars["Indenter"]):
                    console.print("[bold green]Great job! Your Indenter context manager looks good.[/bold green]\n")
                    exercise_completed = True
                else:
                    console.print("[bold red]Make sure to define a class called 'Indenter'.[/bold red]\n")
            except Exception as e:
                console.print(f"[bold red]Error in your code: {str(e)}[/bold red]\n")
        else:
            console.print("[bold red]Make sure to create a context manager class with __enter__ and __exit__ methods.[/bold red]\n")
    
    # Metaclasses
    ui.display_section("Metaclasses")
    console.print("Metaclasses are the 'classes of classes' - they define how classes behave.")
    console.print("They're an advanced feature that allows you to customize class creation.\n")
    
    # Example code
    code = """
# Basic metaclass example
class Meta(type):
    def __new__(cls, name, bases, attrs):
        # Add a new attribute to the class
        attrs['added_by_meta'] = 'This attribute was added by the metaclass'
        return super().__new__(cls, name, bases, attrs)

# Using the metaclass
class MyClass(metaclass=Meta):
    pass

# The attribute added by the metaclass is available
print(MyClass.added_by_meta)  # Outputs: This attribute was added by the metaclass

# More practical example: Singleton metaclass
class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

# Using the Singleton metaclass
class Logger(metaclass=Singleton):
    def __init__(self):
        self.logs = []
    
    def log(self, message):
        self.logs.append(message)

# Creating multiple instances actually returns the same instance
logger1 = Logger()
logger2 = Logger()

logger1.log("First message")
logger2.log("Second message")

print(logger1.logs)  # Outputs: ['First message', 'Second message']
print(logger1 is logger2)  # Outputs: True (they are the same object)
    """
    
    ui.display_code(code, "python")
    
    # Quiz
    ui.display_section("Quiz Time!")
    
    score = 0
    
    # Question 1
    answer = select(
        "What is the primary purpose of a decorator in Python?",
        choices=[
            "To add visual elements to the Python console",
            "To modify or enhance functions without changing their code",  # Correct answer
            "To create new classes from existing ones",
            "To optimize code execution speed"
        ]
    ).ask()
    
    if answer == "To modify or enhance functions without changing their code":
        console.print("[bold green]Correct! Decorators allow you to modify functions without changing their implementation.[/bold green]")
        score += 1
    else:
        console.print("[bold red]Not quite. Decorators are used to modify or enhance functions without changing their code.[/bold red]")
    
    # Question 2
    answer = select(
        "What is the main advantage of generators over regular functions that return lists?",
        choices=[
            "Generators are always faster",
            "Generators can only be used once",
            "Generators use less memory by yielding items one at a time",  # Correct answer
            "Generators can return multiple values simultaneously"
        ]
    ).ask()
    
    if answer == "Generators use less memory by yielding items one at a time":
        console.print("[bold green]Correct! Generators are memory-efficient because they yield items one at a time.[/bold green]")
        score += 1
    else:
        console.print("[bold red]Not quite. Generators use less memory by yielding items one at a time rather than creating the entire sequence at once.[/bold red]")
    
    # Question 3
    answer = select(
        "Which statement is used with context managers in Python?",
        choices=[
            "using",
            "with",  # Correct answer
            "context",
            "manage"
        ]
    ).ask()
    
    if answer == "with":
        console.print("[bold green]Correct! The 'with' statement is used with context managers in Python.[/bold green]")
        score += 1
    else:
        console.print("[bold red]Not quite. The 'with' statement is used with context managers in Python.[/bold red]")
    
    # Display score
    console.print(f"\n[bold]Your score: {score}/3[/bold]")
    
    if score == 3:
        console.print("[bold green]Perfect! You've mastered advanced Python concepts![/bold green]")
    elif score >= 2:
        console.print("[bold yellow]Good job! You're getting the hang of advanced Python concepts.[/bold yellow]")
    else:
        console.print("[bold]Keep practicing! Review the lesson and try again.[/bold]")
    
    # Summary
    ui.display_section("Summary")
    console.print("In this lesson, you learned about:")
    console.print("• Decorators for modifying function behavior")
    console.print("• Generators for memory-efficient iteration")
    console.print("• Context managers for resource management")
    console.print("• Metaclasses for customizing class creation\n")
    
    # Ask if user wants to continue
    continue_learning = select(
        "Have you completed this lesson?",
        choices=[
            "Yes, I've completed this lesson",
            "No, I need more time with this topic"
        ]
    ).ask()
    
    return "Yes" in continue_learning