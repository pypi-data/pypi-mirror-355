"""Object-Oriented Programming module for VenomLearn learning package.

This module covers Python's object-oriented programming concepts like classes, objects, inheritance, and polymorphism.
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
    """Start the Object-Oriented Programming lesson."""
    console.print("[bold cyan]Object-Oriented Programming in Python[/bold cyan]\n")
    
    # Introduction
    ui.display_section("Introduction to OOP")
    console.print("Object-Oriented Programming (OOP) is a programming paradigm based on the concept of 'objects'.")
    console.print("Objects can contain data (attributes) and code (methods). In Python, everything is an object.\n")
    
    # Classes and Objects
    ui.display_section("Classes and Objects")
    console.print("A class is a blueprint for creating objects. An object is an instance of a class.")
    
    # Example code
    code = """
# Defining a class
class Dog:
    # Class attribute (shared by all instances)
    species = "Canis familiaris"
    
    # Initializer / Constructor
    def __init__(self, name, age):
        # Instance attributes (unique to each instance)
        self.name = name
        self.age = age
    
    # Instance method
    def bark(self):
        return f"{self.name} says Woof!"
    
    # Another instance method
    def description(self):
        return f"{self.name} is {self.age} years old"

# Creating objects (instances of the Dog class)
buddy = Dog("Buddy", 5)
max = Dog("Max", 3)

# Accessing attributes
print(buddy.name)  # Output: Buddy
print(max.age)     # Output: 3
print(buddy.species)  # Output: Canis familiaris

# Calling methods
print(buddy.bark())  # Output: Buddy says Woof!
print(max.description())  # Output: Max is 3 years old
    """
    
    ui.display_code(code, "python")
    
    # Exercise 1
    ui.display_exercise("Exercise 1: Create a Class")
    console.print("Create a class called 'Rectangle' with:")
    console.print("1. An initializer that takes width and height as parameters")
    console.print("2. A method called 'area' that returns the area of the rectangle")
    console.print("3. A method called 'perimeter' that returns the perimeter of the rectangle\n")
    
    exercise_completed = False
    while not exercise_completed:
        user_code = ui.get_code_input()
        
        # Check if the code contains the required elements
        if "class Rectangle" in user_code and "def __init__" in user_code and "def area" in user_code and "def perimeter" in user_code:
            try:
                # Execute the code to define the class
                local_vars = {}
                exec(user_code, {}, local_vars)
                
                if "Rectangle" in local_vars and callable(local_vars["Rectangle"]):
                    # Test the class with some values
                    try:
                        rect = local_vars["Rectangle"](5, 10)
                        area = rect.area()
                        perimeter = rect.perimeter()
                        
                        if area == 50 and perimeter == 30:
                            console.print("[bold green]Great job! Your Rectangle class works correctly.[/bold green]\n")
                            exercise_completed = True
                        else:
                            console.print(f"[bold red]Your calculations seem off. Area should be 50 (got {area}) and perimeter should be 30 (got {perimeter}).[/bold red]\n")
                    except Exception as e:
                        console.print(f"[bold red]Error when using your class: {str(e)}[/bold red]\n")
                else:
                    console.print("[bold red]Make sure to define a class called 'Rectangle'.[/bold red]\n")
            except Exception as e:
                console.print(f"[bold red]Error in your code: {str(e)}[/bold red]\n")
        else:
            console.print("[bold red]Make sure to create a Rectangle class with __init__, area, and perimeter methods.[/bold red]\n")
    
    # Inheritance
    ui.display_section("Inheritance")
    console.print("Inheritance allows a class to inherit attributes and methods from another class.")
    console.print("The class that inherits is called a subclass, and the class it inherits from is called a superclass.\n")
    
    # Example code
    code = """
# Base class (superclass)
class Animal:
    def __init__(self, name):
        self.name = name
    
    def speak(self):
        return "Some sound"

# Derived class (subclass)
class Cat(Animal):
    def speak(self):
        return "Meow"

# Another derived class
class Dog(Animal):
    def speak(self):
        return "Woof"

# Creating objects
animal = Animal("Generic Animal")
cat = Cat("Whiskers")
dog = Dog("Rex")

# Calling the speak method
print(animal.speak())  # Output: Some sound
print(cat.speak())     # Output: Meow
print(dog.speak())     # Output: Woof
    """
    
    ui.display_code(code, "python")
    
    # Exercise 2
    ui.display_exercise("Exercise 2: Inheritance")
    console.print("Create a base class called 'Shape' with a method 'area'.")
    console.print("Then create two subclasses: 'Circle' and 'Square' that inherit from Shape and override the area method.\n")
    
    exercise_completed = False
    while not exercise_completed:
        user_code = ui.get_code_input()
        
        # Check if the code contains the required elements
        if "class Shape" in user_code and "class Circle" in user_code and "class Square" in user_code and "def area" in user_code:
            try:
                # Execute the code to define the classes
                local_vars = {}
                exec(user_code, {}, local_vars)
                
                if all(cls in local_vars and callable(local_vars[cls]) for cls in ["Shape", "Circle", "Square"]):
                    # Test the classes
                    try:
                        # Create instances (assuming Circle takes radius and Square takes side length)
                        # This is a simplification - we're making assumptions about the constructor parameters
                        circle = None
                        square = None
                        
                        # Try different constructor signatures
                        try:
                            circle = local_vars["Circle"](5)
                        except:
                            try:
                                circle = local_vars["Circle"](5, "radius")
                            except:
                                circle = local_vars["Circle"]()
                        
                        try:
                            square = local_vars["Square"](4)
                        except:
                            try:
                                square = local_vars["Square"](4, "side")
                            except:
                                square = local_vars["Square"]()
                        
                        # Check if area methods exist
                        if hasattr(circle, "area") and callable(getattr(circle, "area")) and \
                           hasattr(square, "area") and callable(getattr(square, "area")):
                            console.print("[bold green]Good job! Your Shape, Circle, and Square classes look correct.[/bold green]\n")
                            exercise_completed = True
                        else:
                            console.print("[bold red]Make sure both Circle and Square have an area method.[/bold red]\n")
                    except Exception as e:
                        console.print(f"[bold red]Error when using your classes: {str(e)}[/bold red]\n")
                else:
                    console.print("[bold red]Make sure to define Shape, Circle, and Square classes.[/bold red]\n")
            except Exception as e:
                console.print(f"[bold red]Error in your code: {str(e)}[/bold red]\n")
        else:
            console.print("[bold red]Make sure to create Shape, Circle, and Square classes with area methods.[/bold red]\n")
    
    # Encapsulation
    ui.display_section("Encapsulation")
    console.print("Encapsulation is the bundling of data and methods that operate on that data within a single unit (class).")
    console.print("It also involves restricting direct access to some of an object's components.\n")
    
    # Example code
    code = """
# Class with encapsulation
class BankAccount:
    def __init__(self, account_number, balance):
        self._account_number = account_number  # Protected attribute (convention)
        self.__balance = balance  # Private attribute
    
    # Getter method
    def get_balance(self):
        return self.__balance
    
    # Setter method
    def set_balance(self, amount):
        if amount >= 0:
            self.__balance = amount
        else:
            print("Balance cannot be negative")
    
    # Method to deposit money
    def deposit(self, amount):
        if amount > 0:
            self.__balance += amount
            return True
        return False
    
    # Method to withdraw money
    def withdraw(self, amount):
        if 0 < amount <= self.__balance:
            self.__balance -= amount
            return True
        return False

# Creating an account
account = BankAccount("123456", 1000)

# Using methods to interact with the account
print(account.get_balance())  # Output: 1000
account.deposit(500)
print(account.get_balance())  # Output: 1500
account.withdraw(200)
print(account.get_balance())  # Output: 1300

# Direct access to private attribute will fail
# print(account.__balance)  # AttributeError
    """
    
    ui.display_code(code, "python")
    
    # Polymorphism
    ui.display_section("Polymorphism")
    console.print("Polymorphism allows objects of different classes to be treated as objects of a common superclass.")
    console.print("It's often achieved through method overriding, as seen in the inheritance example.\n")
    
    # Example code
    code = """
# Polymorphism example
def make_sound(animal):
    return animal.speak()

# Using the Animal, Cat, and Dog classes from earlier
animal = Animal("Generic Animal")
cat = Cat("Whiskers")
dog = Dog("Rex")

# The same function works for different types of objects
print(make_sound(animal))  # Output: Some sound
print(make_sound(cat))     # Output: Meow
print(make_sound(dog))     # Output: Woof
    """
    
    ui.display_code(code, "python")
    
    # Quiz
    ui.display_section("Quiz Time!")
    
    score = 0
    
    # Question 1
    answer = select(
        "What is the special method that is called when a new object is created?",
        choices=[
            "__new__()",
            "__init__()",  # Correct answer
            "__call__()",
            "__create__()"
        ]
    ).ask()
    
    if answer == "__init__()":
        console.print("[bold green]Correct! __init__() is the constructor method in Python classes.[/bold green]")
        score += 1
    else:
        console.print("[bold red]Not quite. __init__() is the constructor method in Python classes.[/bold red]")
    
    # Question 2
    answer = select(
        "Which of the following is NOT a principle of Object-Oriented Programming?",
        choices=[
            "Encapsulation",
            "Inheritance",
            "Polymorphism",
            "Compilation"  # Correct answer
        ]
    ).ask()
    
    if answer == "Compilation":
        console.print("[bold green]Correct! Compilation is not a principle of OOP. The main principles are Encapsulation, Inheritance, Polymorphism, and Abstraction.[/bold green]")
        score += 1
    else:
        console.print("[bold red]Not quite. Compilation is not a principle of OOP. The main principles are Encapsulation, Inheritance, Polymorphism, and Abstraction.[/bold red]")
    
    # Question 3
    answer = select(
        "In Python, what does the 'self' parameter in a method refer to?",
        choices=[
            "The class itself",
            "The instance of the class",  # Correct answer
            "The parent class",
            "The method itself"
        ]
    ).ask()
    
    if answer == "The instance of the class":
        console.print("[bold green]Correct! 'self' refers to the instance of the class on which the method is being called.[/bold green]")
        score += 1
    else:
        console.print("[bold red]Not quite. 'self' refers to the instance of the class on which the method is being called.[/bold red]")
    
    # Display score
    console.print(f"\n[bold]Your score: {score}/3[/bold]")
    
    if score == 3:
        console.print("[bold green]Perfect! You've mastered Object-Oriented Programming in Python![/bold green]")
    elif score >= 2:
        console.print("[bold yellow]Good job! You're getting the hang of OOP in Python.[/bold yellow]")
    else:
        console.print("[bold]Keep practicing! Review the lesson and try again.[/bold]")
    
    # Summary
    ui.display_section("Summary")
    console.print("In this lesson, you learned about:")
    console.print("• Classes and Objects: The building blocks of OOP")
    console.print("• Inheritance: Creating new classes based on existing ones")
    console.print("• Encapsulation: Bundling data and methods together")
    console.print("• Polymorphism: Treating objects of different classes as objects of a common superclass")
    
    return True