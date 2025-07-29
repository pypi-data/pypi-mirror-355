from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.box import Box, ROUNDED, SIMPLE, DOUBLE, HEAVY, ASCII
from rich.align import Align
from rich.padding import Padding
from rich.style import Style

class GeometricConsole:
    """
    A class that provides geometric and visual utilities for console output.
    Uses the rich library for enhanced terminal rendering.
    """
    
    def __init__(self, console=None):
        """
        Initialize the GeometricConsole with a rich console instance.
        
        Args:
            console (rich.console.Console, optional): A Rich console instance.
        """
        self.console = console if console else Console()
    
    def Box(self, text, title=None, padding=(1, 2), style="blue", box_type=ROUNDED):
        """
        Renders text inside a box.
        
        Args:
            text (str): The text to display inside the box.
            title (str, optional): The title of the box.
            padding (tuple, optional): Padding inside the box (vertical, horizontal).
            style (str, optional): The style to apply to the box.
            box_type (rich.box.Box, optional): The type of box to use.
            
        Returns:
            None: The box is printed directly to the console.
        """
        panel = Panel(
            text,
            title=title,
            padding=padding,
            style=style,
            box=box_type
        )
        self.console.print(panel)
    
    def CenteredBox(self, text, title=None, width=None, padding=(1, 2), style="blue", box_type=ROUNDED):
        """
        Renders text inside a centered box.
        
        Args:
            text (str): The text to display inside the box.
            title (str, optional): The title of the box.
            width (int, optional): The width of the box. If None, auto-sized.
            padding (tuple, optional): Padding inside the box (vertical, horizontal).
            style (str, optional): The style to apply to the box.
            box_type (rich.box.Box, optional): The type of box to use.
            
        Returns:
            None: The box is printed directly to the console.
        """
        panel = Panel(
            text,
            title=title,
            padding=padding,
            style=style,
            box=box_type,
            width=width
        )
        self.console.print(Align.center(panel))
    
    def Table(self, data, headers=None, title=None, style="blue", box_type=SIMPLE):
        """
        Renders a table from a 2D array of data.
        
        Args:
            data (list): A 2D array of data to display in the table.
            headers (list, optional): Column headers for the table.
            title (str, optional): The title of the table.
            style (str, optional): The style to apply to the table.
            box_type (rich.box.Box, optional): The type of box to use for the table.
            
        Returns:
            None: The table is printed directly to the console.
        """
        table = Table(title=title, box=box_type, style=style)
        
        # Add headers if provided
        if headers:
            for header in headers:
                table.add_column(header)
        else:
            # Add default headers based on the number of columns in the first row
            if data and len(data) > 0:
                for i in range(len(data[0])):
                    table.add_column(f"Column {i+1}")
        
        # Add rows
        for row in data:
            table.add_row(*[str(cell) for cell in row])
        
        self.console.print(table)
    
    def ProgressBar(self, value, total, width=40, filled_char="█", empty_char="░", style="blue"):
        """
        Renders a simple progress bar.
        
        Args:
            value (int): Current progress value.
            total (int): Total value (100%).
            width (int, optional): Width of the progress bar in characters.
            filled_char (str, optional): Character to use for filled portion.
            empty_char (str, optional): Character to use for empty portion.
            style (str, optional): The style to apply to the progress bar.
            
        Returns:
            None: The progress bar is printed directly to the console.
        """
        progress = min(1.0, max(0.0, value / total))
        filled_width = int(width * progress)
        empty_width = width - filled_width
        
        bar = filled_char * filled_width + empty_char * empty_width
        percentage = int(progress * 100)
        
        self.console.print(f"[{style}]{bar}[/{style}] {percentage}%")
    
    def Grid(self, items, columns=3, padding=(0, 1), style="blue"):
        """
        Renders items in a grid layout.
        
        Args:
            items (list): List of items to display in the grid.
            columns (int, optional): Number of columns in the grid.
            padding (tuple, optional): Padding between items (vertical, horizontal).
            style (str, optional): The style to apply to the grid.
            
        Returns:
            None: The grid is printed directly to the console.
        """
        if not items:
            return
        
        # Calculate the number of rows needed
        rows = (len(items) + columns - 1) // columns
        
        # Create a table with the specified number of columns
        table = Table.grid(padding=padding)
        for _ in range(columns):
            table.add_column()
        
        # Add items to the table
        row_items = []
        for i, item in enumerate(items):
            row_items.append(f"[{style}]{item}[/{style}]")
            if (i + 1) % columns == 0 or i == len(items) - 1:
                # Pad the row if needed
                while len(row_items) < columns:
                    row_items.append("")
                table.add_row(*row_items)
                row_items = []
        
        self.console.print(table)
    
    def Divider(self, character="─", style="blue"):
        """
        Renders a divider line across the console width.
        
        Args:
            character (str, optional): Character to use for the divider.
            style (str, optional): The style to apply to the divider.
            
        Returns:
            None: The divider is printed directly to the console.
        """
        width = self.console.width
        self.console.print(character * width, style=style)