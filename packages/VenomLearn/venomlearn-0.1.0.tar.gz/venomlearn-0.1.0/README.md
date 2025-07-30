# VenomLearn: Interactive Python Learning

VenomLearn is an interactive Python learning package designed to make learning Python fun, engaging, and accessible for beginners and intermediate learners. The package provides a terminal-based interface with colorful visuals, interactive exercises, and progress tracking.

## Features

- 🎯 **Progressive Learning Path**: From beginner to advanced Python concepts
- 🧩 **Interactive Exercises**: Practice what you learn with hands-on coding challenges
- 📊 **Progress Tracking**: Keep track of your learning journey
- 🎮 **Gamified Experience**: Earn badges and achievements as you learn
- 🎨 **Rich Terminal UI**: Colorful and engaging interface

## Installation

```bash
# Install from PyPI
pip install VenomLearn

# Or install from source
git clone https://github.com/VenomLearn/VenomLearn.git
cd VenomLearn
pip install -e .
```

## Requirements

VenomLearn requires Python 3.7 or higher and the following packages:

- rich>=10.0.0
- questionary>=1.10.0
- pyfiglet>=0.8.post1
- tqdm>=4.62.0

## Usage

After installing VenomLearn, you can start the interactive learning tool in two ways:

### 1. Launch from the Terminal (if installed as a script)
```bash
venomlearn
```

### 2. Run as a Python Module
```bash
python -m VenomLearn.main
```

Both commands will launch the interactive terminal UI where you can select your difficulty level, view your learning roadmap, and begin your Python journey.

### 3. Import and Use Programmatically (Advanced)
You can also import specific modules from the package in your own Python scripts:
```python
from VenomLearn.topics import basics, advanced

# Start a lesson directly
basics.start_lesson()
advanced.start_lesson()
```

For most users, launching from the terminal or as a module is recommended.

## Topics Covered

- **Python Basics**: Variables, data types, input/output operations
- **Control Flow**: If-else statements, loops, conditional expressions
- **Functions**: Function definitions, parameters, return values, scope
- **Data Structures**: Lists, dictionaries, sets, tuples, comprehensions
- **Object-Oriented Programming**: Classes, objects, inheritance, encapsulation
- **Modules and Packages**: Importing, creating modules, package structure
- **Advanced Topics**: Decorators, generators, context managers, error handling

## Project Structure

```
bytebybyte/
├── __init__.py
├── config.py          # Configuration settings
├── main.py            # Main entry point
├── data/              # Data files (progress tracking)
├── topics/            # Learning topics modules
└── utils/             # Utility modules
    ├── checker.py     # Code checking utilities
    ├── progress_tracker.py  # Progress tracking
    └── terminal_ui.py  # Terminal UI utilities
```

## Learning Path

VenomLearn offers three difficulty levels:

1. **Beginner**: For those new to Python programming
2. **Intermediate**: For those with some Python experience
3. **Advanced**: For experienced Python developers looking to master advanced concepts

Each topic includes:
- Explanations with examples
- Interactive coding exercises
- Quizzes to test understanding
- Progress tracking

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [Rich](https://github.com/Textualize/rich) for the beautiful terminal UI
- [Questionary](https://github.com/tmbo/questionary) for interactive prompts
- [Pyfiglet](https://github.com/pwaller/pyfiglet) for ASCII art text