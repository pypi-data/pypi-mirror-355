"""Data Structures module for VenomLearn learning package.

This module covers Python's data structures like lists, dictionaries, sets, and tuples.
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
    """Start the Data Structures lesson."""
    console.print("[bold cyan]Python Data Structures[/bold cyan]\n")
    
    # Introduction
    ui.display_section("Introduction to Data Structures")
    console.print("Data structures are containers that organize and store data in specific formats.")
    console.print("Python has several built-in data structures that make it powerful and flexible.\n")
    
    # Lists
    ui.display_section("Lists")
    console.print("Lists are ordered, mutable collections that can contain items of different types.")
    
    # Example code
    code = """
# Creating a list
fruits = ["apple", "banana", "cherry"]

# Accessing elements (indexing starts at 0)
print(fruits[0])  # Output: apple

# Modifying elements
fruits[1] = "blueberry"
print(fruits)  # Output: ['apple', 'blueberry', 'cherry']

# Adding elements
fruits.append("dragonfruit")
print(fruits)  # Output: ['apple', 'blueberry', 'cherry', 'dragonfruit']

# List methods
fruits.insert(1, "apricot")  # Insert at specific position
print(fruits)  # Output: ['apple', 'apricot', 'blueberry', 'cherry', 'dragonfruit']

fruits.remove("cherry")  # Remove by value
print(fruits)  # Output: ['apple', 'apricot', 'blueberry', 'dragonfruit']

popped = fruits.pop()  # Remove and return the last item
print(popped)  # Output: dragonfruit
print(fruits)  # Output: ['apple', 'apricot', 'blueberry']

# List operations
numbers = [1, 2, 3]
more_numbers = [4, 5, 6]
combined = numbers + more_numbers  # Concatenation
print(combined)  # Output: [1, 2, 3, 4, 5, 6]

duplicated = numbers * 3  # Repetition
print(duplicated)  # Output: [1, 2, 3, 1, 2, 3, 1, 2, 3]

# List comprehensions
squares = [x**2 for x in range(1, 6)]
print(squares)  # Output: [1, 4, 9, 16, 25]
    """
    
    ui.display_code(code, "python")
    
    # Exercise 1
    ui.display_exercise("Exercise 1: List Operations")
    console.print("Create a list of numbers from 1 to 5, then write code to:")
    console.print("1. Add the number 6 to the end of the list")
    console.print("2. Insert the number 0 at the beginning of the list")
    console.print("3. Remove the number 3 from the list")
    console.print("4. Print the final list\n")
    
    exercise_completed = False
    while not exercise_completed:
        user_code = ui.get_code_input()
        
        # Check if the code contains the required operations
        if "append" in user_code or "+= [6]" in user_code or ".extend" in user_code:
            if "insert" in user_code or "[0] +" in user_code:
                if "remove" in user_code or "pop" in user_code:
                    if "print" in user_code:
                        try:
                            # Execute the code to see if it works
                            local_vars = {}
                            exec(user_code, {}, local_vars)
                            console.print("[bold green]Great job! Your list operations work correctly.[/bold green]\n")
                            exercise_completed = True
                        except Exception as e:
                            console.print(f"[bold red]Error in your code: {str(e)}[/bold red]\n")
                    else:
                        console.print("[bold red]Make sure to print the final list.[/bold red]\n")
                else:
                    console.print("[bold red]Make sure to remove the number 3 from the list.[/bold red]\n")
            else:
                console.print("[bold red]Make sure to insert the number 0 at the beginning of the list.[/bold red]\n")
        else:
            console.print("[bold red]Make sure to create a list and add the number 6 to the end.[/bold red]\n")
    
    # Dictionaries
    ui.display_section("Dictionaries")
    console.print("Dictionaries are unordered collections of key-value pairs.")
    console.print("They are mutable and keys must be unique and immutable (strings, numbers, tuples).\n")
    
    # Example code
    code = """
# Creating a dictionary
person = {
    "name": "Alice",
    "age": 30,
    "city": "New York"
}

# Accessing values
print(person["name"])  # Output: Alice

# Alternative way to access values (safer)
print(person.get("age"))  # Output: 30
print(person.get("country", "Unknown"))  # Output: Unknown (default value if key doesn't exist)

# Modifying values
person["age"] = 31
print(person)  # Output: {'name': 'Alice', 'age': 31, 'city': 'New York'}

# Adding new key-value pairs
person["job"] = "Engineer"
print(person)  # Output: {'name': 'Alice', 'age': 31, 'city': 'New York', 'job': 'Engineer'}

# Removing key-value pairs
del person["city"]
print(person)  # Output: {'name': 'Alice', 'age': 31, 'job': 'Engineer'}

# Dictionary methods
keys = person.keys()  # Get all keys
values = person.values()  # Get all values
items = person.items()  # Get all key-value pairs as tuples

print(list(keys))  # Output: ['name', 'age', 'job']
print(list(values))  # Output: ['Alice', 31, 'Engineer']
print(list(items))  # Output: [('name', 'Alice'), ('age', 31), ('job', 'Engineer')]

# Dictionary comprehensions
squares_dict = {x: x**2 for x in range(1, 6)}
print(squares_dict)  # Output: {1: 1, 2: 4, 3: 9, 4: 16, 5: 25}
    """
    
    ui.display_code(code, "python")
    
    # Exercise 2
    ui.display_exercise("Exercise 2: Dictionary Operations")
    console.print("Create a dictionary representing a book with keys for 'title', 'author', and 'year'.")
    console.print("Then write code to:")
    console.print("1. Add a new key 'genre' with an appropriate value")
    console.print("2. Update the 'year' value")
    console.print("3. Print all the keys and values in the format 'Key: Value'\n")
    
    exercise_completed = False
    while not exercise_completed:
        user_code = ui.get_code_input()
        
        # Check if the code contains the required elements
        if "title" in user_code and "author" in user_code and "year" in user_code:
            if "genre" in user_code:
                if "print" in user_code and ("items()" in user_code or "keys()" in user_code or "values()" in user_code or "for" in user_code):
                    try:
                        # Execute the code to see if it works
                        local_vars = {}
                        exec(user_code, {}, local_vars)
                        console.print("[bold green]Great job! Your dictionary operations work correctly.[/bold green]\n")
                        exercise_completed = True
                    except Exception as e:
                        console.print(f"[bold red]Error in your code: {str(e)}[/bold red]\n")
                else:
                    console.print("[bold red]Make sure to print all keys and values in the format 'Key: Value'.[/bold red]\n")
            else:
                console.print("[bold red]Make sure to add a 'genre' key with an appropriate value.[/bold red]\n")
        else:
            console.print("[bold red]Make sure to create a dictionary with 'title', 'author', and 'year' keys.[/bold red]\n")
    
    # Tuples
    ui.display_section("Tuples")
    console.print("Tuples are ordered, immutable collections that can contain items of different types.")
    console.print("They are similar to lists but cannot be modified after creation.\n")
    
    # Example code
    code = """
# Creating a tuple
coordinates = (10, 20)

# Accessing elements
print(coordinates[0])  # Output: 10

# Tuples are immutable
# This would cause an error: coordinates[0] = 15

# Tuple packing and unpacking
person = ("Alice", 30, "New York")
name, age, city = person  # Unpacking
print(name)  # Output: Alice
print(age)   # Output: 30
print(city)  # Output: New York

# Tuple methods
colors = ("red", "green", "blue", "green", "red")
print(colors.count("red"))  # Output: 2 (number of occurrences)
print(colors.index("blue"))  # Output: 2 (index of first occurrence)

# Tuples as dictionary keys (since they're immutable)
point_values = {(0, 0): "origin", (1, 0): "unit x", (0, 1): "unit y"}
print(point_values[(0, 0)])  # Output: origin
    """
    
    ui.display_code(code, "python")
    
    # Sets
    ui.display_section("Sets")
    console.print("Sets are unordered collections of unique elements.")
    console.print("They are useful for membership testing and eliminating duplicate entries.\n")
    
    # Example code
    code = """
# Creating a set
fruits = {"apple", "banana", "cherry"}

# Creating a set from a list (removes duplicates)
numbers = set([1, 2, 2, 3, 3, 3, 4])
print(numbers)  # Output: {1, 2, 3, 4}

# Adding elements
fruits.add("dragonfruit")
print(fruits)  # Output might be: {'cherry', 'dragonfruit', 'banana', 'apple'} (order not guaranteed)

# Removing elements
fruits.remove("banana")  # Raises an error if the element doesn't exist
fruits.discard("elderberry")  # No error if the element doesn't exist

# Set operations
set1 = {1, 2, 3, 4, 5}
set2 = {4, 5, 6, 7, 8}

union = set1 | set2  # or set1.union(set2)
print(union)  # Output: {1, 2, 3, 4, 5, 6, 7, 8}

intersection = set1 & set2  # or set1.intersection(set2)
print(intersection)  # Output: {4, 5}

difference = set1 - set2  # or set1.difference(set2)
print(difference)  # Output: {1, 2, 3}

symmetric_difference = set1 ^ set2  # or set1.symmetric_difference(set2)
print(symmetric_difference)  # Output: {1, 2, 3, 6, 7, 8}

# Membership testing
print("apple" in fruits)  # Output: True
print("banana" in fruits)  # Output: False (we removed it earlier)
    """
    
    ui.display_code(code, "python")
    
    # Exercise 3
    ui.display_exercise("Exercise 3: Set Operations")
    console.print("Create two sets: one with even numbers from 2 to 10, and another with multiples of 3 from 3 to 12.")
    console.print("Then write code to find:")
    console.print("1. The union of the two sets")
    console.print("2. The intersection of the two sets")
    console.print("3. The elements that are in the first set but not in the second")
    console.print("4. Print all results\n")
    
    exercise_completed = False
    while not exercise_completed:
        user_code = ui.get_code_input()
        
        # Check if the code contains the required elements
        if "set" in user_code and ("range" in user_code or "2, 4, 6, 8, 10" in user_code or "[2, 4, 6, 8, 10]" in user_code):
            if "3, 6, 9, 12" in user_code or "[3, 6, 9, 12]" in user_code or ("range" in user_code and "3" in user_code):
                if ("union" in user_code or "|" in user_code) and ("intersection" in user_code or "&" in user_code) and ("difference" in user_code or "-" in user_code):
                    if "print" in user_code:
                        try:
                            # Execute the code to see if it works
                            local_vars = {}
                            exec(user_code, {}, local_vars)
                            console.print("[bold green]Great job! Your set operations work correctly.[/bold green]\n")
                            exercise_completed = True
                        except Exception as e:
                            console.print(f"[bold red]Error in your code: {str(e)}[/bold red]\n")
                    else:
                        console.print("[bold red]Make sure to print all results.[/bold red]\n")
                else:
                    console.print("[bold red]Make sure to find the union, intersection, and difference of the sets.[/bold red]\n")
            else:
                console.print("[bold red]Make sure to create a set with multiples of 3 from 3 to 12.[/bold red]\n")
        else:
            console.print("[bold red]Make sure to create a set with even numbers from 2 to 10.[/bold red]\n")
    
    # Quiz
    ui.display_section("Quiz Time!")
    
    score = 0
    
    # Question 1
    answer = select(
        "Which of the following data structures is mutable?",
        choices=[
            "Tuple",
            "String",
            "List",  # Correct answer
            "Frozen set"
        ]
    ).ask()
    
    if answer == "List":
        console.print("[bold green]Correct! Lists are mutable, meaning they can be modified after creation.[/bold green]")
        score += 1
    else:
        console.print("[bold red]Not quite. Lists are mutable, while tuples, strings, and frozen sets are immutable.[/bold red]")
    
    # Question 2
    answer = select(
        "What will the following code output? \nprint(set([1, 2, 2, 3, 3, 3]))",
        choices=[
            "{1, 2, 2, 3, 3, 3}",
            "{1, 2, 3}",  # Correct answer
            "[1, 2, 3]",
            "Error"
        ]
    ).ask()
    
    if answer == "{1, 2, 3}":
        console.print("[bold green]Correct! Sets automatically remove duplicate elements.[/bold green]")
        score += 1
    else:
        console.print("[bold red]Not quite. Sets automatically remove duplicate elements, so the output would be {1, 2, 3}.[/bold red]")
    
    # Question 3
    answer = select(
        "Which data structure would be most appropriate for storing a collection of unique user IDs?",
        choices=[
            "List",
            "Dictionary",
            "Set",  # Correct answer
            "Tuple"
        ]
    ).ask()
    
    if answer == "Set":
        console.print("[bold green]Correct! Sets are ideal for storing unique values and performing fast membership tests.[/bold green]")
        score += 1
    else:
        console.print("[bold red]Not quite. Sets are ideal for storing unique values and performing fast membership tests.[/bold red]")
    
    # Display score
    console.print(f"\n[bold]Your score: {score}/3[/bold]")
    
    if score == 3:
        console.print("[bold green]Perfect! You've mastered Python data structures![/bold green]")
    elif score >= 2:
        console.print("[bold yellow]Good job! You're getting the hang of Python data structures.[/bold yellow]")
    else:
        console.print("[bold]Keep practicing! Review the lesson and try again.[/bold]")
    
    # Summary
    ui.display_section("Summary")
    console.print("In this lesson, you learned about:")
    console.print("• Lists: Ordered, mutable collections for storing sequences of items")
    console.print("• Dictionaries: Key-value pairs for mapping relationships")
    console.print("• Tuples: Ordered, immutable collections for fixed data")
    console.print("• Sets: Unordered collections of unique elements for membership operations\n")
    
    # Ask if user wants to continue
    continue_learning = select(
        "Have you completed this lesson?",
        choices=[
            "Yes, I've completed this lesson",
            "No, I need more time with this topic"
        ]
    ).ask()
    
    return "Yes" in continue_learning