# pz-clean-menu

A simple, elegant Python interactive menu system using the **Rich** library, part of the **pz-** namespace.

## Features

✅ Create colorful and structured console menus  
✅ Support for nested submenus (children)  
✅ Group options for better organization  
✅ Dynamic addition of options and submenus at runtime  
✅ Breadcrumb navigation for nested menus  
✅ Support for disabled menu options  
✅ Single-key input (no need to press Enter after selecting an option)  
✅ Console helper utilities for various platforms  
✅ Geometric console utilities (boxes, tables, grids, etc.)  
✅ Powered by [Rich](https://github.com/Textualize/rich) for beautiful console output

## Installation

Install via pip (after publishing to PyPI):

```bash
pip install pz-clean-menu
```

Or for local development:

```bash
git clone https://github.com/poziel/clean-menu.git
cd clean-menu
pip install -e .
```

## Basic Usage

```python
from pz_clean_menu import CleanMenu

def hello_callback(menu):
    print("\\nHello, world!")

menu = CleanMenu(header="My Menu")
menu.Group("default", title="Options")
menu.Add("1", "Say Hello", hello_callback)
menu.Display()
```

## Advanced Usage

Submenus, dynamic options, and more!

```python
from pz_clean_menu import CleanMenu

def final_depth_action(menu):
    print("\\n[Action] You've reached the final depth! Well done!\\n")

def create_deep_child(menu, depth):
    if depth == 0:
        return final_depth_action

    def next_level_callback(inner_menu):
        next_child = inner_menu.Children(header=f"Level {depth} Menu")
        next_child.Group("deep_group", title=f"Level {depth} Options")
        next_child.Add("1", f"Go Deeper to Level {depth-1}", create_deep_child(next_child, depth - 1), group_id="deep_group")
        next_child.Display()

    return next_level_callback

if __name__ == "__main__":
    main_menu = CleanMenu(header="Infinite Depth Menu", footer="Start your journey!")
    main_menu.Group("root", title="Root Options")
    main_menu.Add("1", "Descend to Level 3", create_deep_child(main_menu, 3), group_id="root")
    main_menu.Display()
```

## Examples

Check out the `examples/` folder for:

- **basic_usage.py**: Simple menu with two actions  
- **advanced_usage.py**: Submenus and dynamic options  
- **nested_menus.py**: Deep nested menus showcasing the power of pz-clean-menu
- **feature_showcase.py**: Demonstrates all the new features (breadcrumbs, disabled options, console helpers, geometric console)

Run them with:

```bash
python examples/basic_usage.py
python examples/advanced_usage.py
python examples/nested_menus.py
python examples/feature_showcase.py
```

## Console Helpers

The package includes various console helper functions:

```python
from pz_clean_menu import clear_console, get_terminal_size, run_command, pause, print_centered, print_header

# Clear the console (works on Windows, macOS, and Linux)
clear_console()

# Get terminal dimensions
width, height = get_terminal_size()

# Run a system command
output = run_command("echo Hello World")

# Pause execution until user presses Enter
pause("Press Enter to continue...")

# Print centered text
print_centered("This text is centered")

# Print a header
print_header("My Application", style="bold blue")
```

## Geometric Console

Create beautiful geometric elements in the console:

```python
from pz_clean_menu import GeometricConsole

gc = GeometricConsole()

# Create a box with text
gc.box("This is text in a box", title="My Box")

# Create a centered box
gc.centered_box("Centered text in a box", width=50)

# Create a table
data = [
    ["Name", "Age", "City"],
    ["Alice", 30, "New York"],
    ["Bob", 25, "Los Angeles"]
]
gc.table(data[1:], headers=data[0], title="People")

# Create a progress bar
gc.progress_bar(75, 100)

# Create a grid of items
items = ["Item 1", "Item 2", "Item 3", "Item 4"]
gc.grid(items, columns=2)

# Create a divider
gc.divider()
```

## Tests

Tests are written using **pytest**:

```bash
pytest tests
```

## License

MIT License

---

Enjoy exploring with **pz-clean-menu**! 🚀
