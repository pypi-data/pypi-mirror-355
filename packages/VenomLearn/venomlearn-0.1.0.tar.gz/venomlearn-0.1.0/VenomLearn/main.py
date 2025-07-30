"""Main entry point for VenomLearn learning package."""

import os
import pyfiglet
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from questionary import select

from VenomLearn.utils.terminal_ui import TerminalUI
from VenomLearn.utils.progress_tracker import ProgressTracker
from VenomLearn.topics import (
    basics,
    control_flow,
    functions,
    data_structures,
    oop,
    modules,
    advanced
)

console = Console()
ui = TerminalUI()


def display_welcome():
    """Display welcome message with ASCII art."""
    title = pyfiglet.figlet_format("VenomLearn", font="slant")
    console.print(f"[bold cyan]{title}[/bold cyan]")
    console.print(Panel("[bold yellow]Interactive Python Learning[/bold yellow]", 
                        subtitle="[italic]Learn Python one byte at a time[/italic]"))
    console.print("\n")


def select_difficulty():
    """Ask user to select difficulty level."""
    difficulty = select(
        "Select your difficulty level:",
        choices=[
            "Beginner - New to Python",
            "Intermediate - Some Python experience",
            "Advanced - Experienced Python developer"
        ]
    ).ask()
    
    if "Beginner" in difficulty:
        return "beginner"
    elif "Intermediate" in difficulty:
        return "intermediate"
    else:
        return "advanced"


def get_topics(difficulty):
    """Get topics based on difficulty level."""
    all_topics = {
        "beginner": [
            ("Python Basics", basics),
            ("Control Flow", control_flow),
            ("Functions", functions),
        ],
        "intermediate": [
            ("Python Basics", basics),
            ("Control Flow", control_flow),
            ("Functions", functions),
            ("Data Structures", data_structures),
            ("Object-Oriented Programming", oop),
        ],
        "advanced": [
            ("Python Basics", basics),
            ("Control Flow", control_flow),
            ("Functions", functions),
            ("Data Structures", data_structures),
            ("Object-Oriented Programming", oop),
            ("Modules and Packages", modules),
            ("Advanced Topics", advanced),
        ]
    }
    
    return all_topics.get(difficulty, all_topics["beginner"])


def display_roadmap(topics):
    """Display learning roadmap."""
    console.print("[bold green]Your Learning Roadmap:[/bold green]\n")
    
    for i, (topic_name, _) in enumerate(topics, 1):
        console.print(f"[bold]{i}.[/bold] {topic_name}")
    
    console.print("\n")


def main():
    """Main function to start the learning journey."""
    # Initialize progress tracker
    progress = ProgressTracker()
    
    # Display welcome message
    display_welcome()
    
    # Select difficulty
    difficulty = select_difficulty()
    
    # Get topics based on difficulty
    topics = get_topics(difficulty)
    
    # Display roadmap
    display_roadmap(topics)
    
    # Start learning journey
    current_topic_index = progress.get_current_topic_index()
    
    while current_topic_index < len(topics):
        topic_name, topic_module = topics[current_topic_index]
        
        console.print(f"\n[bold blue]Starting Topic: {topic_name}[/bold blue]\n")
        
        # Run the topic module
        completed = topic_module.start_lesson()
        
        if completed:
            progress.mark_topic_completed(topic_name)
            current_topic_index = progress.get_current_topic_index()
            
            if current_topic_index < len(topics):
                next_topic = select(
                    "What would you like to do next?",
                    choices=[
                        f"Continue to {topics[current_topic_index][0]}",
                        "Exit for now"
                    ]
                ).ask()
                
                if "Exit" in next_topic:
                    break
        else:
            # If topic not completed, ask if user wants to try again
            retry = select(
                "Would you like to try this topic again?",
                choices=[
                    "Yes, let's try again",
                    "No, I'll come back later"
                ]
            ).ask()
            
            if "No" in retry:
                break
    
    # Show completion message if all topics are done
    if current_topic_index >= len(topics):
        console.print("\n[bold green]Congratulations! You've completed all topics![/bold green]")
        console.print("[italic]Keep coding and learning![/italic]")
    else:
        console.print("\n[bold yellow]See you next time![/bold yellow]")
        console.print(f"[italic]Your progress has been saved. You're currently at: {topics[current_topic_index][0]}[/italic]")


if __name__ == "__main__":
    main()