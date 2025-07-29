import os
import platform
import subprocess
import sys
from rich.console import Console

# For Windows
if platform.system().lower() == 'windows':
    import msvcrt
# For Unix-based systems (macOS and Linux)
else:
    try:
        import termios
        import tty
    except ImportError:
        # Fallback for systems without termios
        pass

def Clean():
    """
    Clears the console screen based on the operating system.
    Works on Windows, macOS, and Linux.
    """
    system = platform.system().lower()

    if system == 'windows':
        os.system('cls')
    elif system in ['darwin', 'linux']:
        os.system('clear')
    else:
        # Fallback for other systems - print newlines
        print('\n' * 100)

def GetTerminalSize():
    """
    Returns the current terminal size as (width, height).
    """
    try:
        return os.get_terminal_size()
    except (AttributeError, OSError):
        # Fallback values if unable to determine
        return 80, 24

def RunCommand(command):
    """
    Runs a system command and returns the output.

    Args:
        command (str): The command to run.

    Returns:
        str: The command output.
    """
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            check=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr}"

def Pause(message="Press Enter to continue..."):
    """
    Pauses execution until the user presses Enter.

    Args:
        message (str): The message to display.
    """
    input(message)

def PrintCentered(text, console=None):
    """
    Prints text centered in the terminal.

    Args:
        text (str): The text to print.
        console (rich.console.Console, optional): A Rich console instance.
    """
    if console is None:
        console = Console()

    width, _ = GetTerminalSize()
    padding = max(0, (width - len(text)) // 2)
    console.print(" " * padding + text)

def PrintHeader(text, console=None, style="bold blue"):
    """
    Prints a header with the given text.

    Args:
        text (str): The header text.
        console (rich.console.Console, optional): A Rich console instance.
        style (str): The style to apply to the header.
    """
    if console is None:
        console = Console()

    width, _ = GetTerminalSize()
    console.print("=" * width, style=style)
    PrintCentered(text, console)
    console.print("=" * width, style=style)

def GetKey():
    """
    Gets a single keypress from the user without requiring Enter to be pressed.
    Works cross-platform on Windows, macOS, and Linux.

    Returns:
        str: The character corresponding to the key pressed.
    """
    system = platform.system().lower()

    if system == 'windows':
        # Windows implementation using msvcrt
        return msvcrt.getch().decode('utf-8', errors='ignore').lower()
    else:
        # Unix implementation using termios and tty
        try:
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                tty.setraw(fd)
                ch = sys.stdin.read(1)
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
            return ch.lower()
        except (ImportError, AttributeError, termios.error):
            # Fallback for systems without termios or if there's an error
            return input().strip().lower()[0:1] or ' '
