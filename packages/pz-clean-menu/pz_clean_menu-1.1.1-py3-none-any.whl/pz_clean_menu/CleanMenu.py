from rich.panel import Panel
from rich.console import Console
from rich.prompt import Confirm
from .Console import Clean, GetKey, Pause
import time

class CleanMenu:
    """
    CleanMenu is a simple console-based menu system using the 'rich' library.
    It allows for adding multiple menu options with callbacks and provides a user-friendly
    interface to navigate these options.
    """

    def __init__(self, main_menu=None, parent_menu=None, header=None, footer=None, clear_console=True,
                 header_color="blue", option_color="cyan", quit_color="red", disabled_color="grey50"):
        """
        Initializes the CleanMenu instance, setting up the console for output,
        initializing the choice dictionary, and line storage.

        Args:
            main_menu: Reference to the main menu CleanMenu instance if this is a submenu.
            parent_menu: Reference to the immediate parent menu CleanMenu instance.
            header: The text to display at the top of the menu.
            footer: The text to display at the bottom of the menu.
            clear_console: Whether to clear the console before displaying the menu.
            header_color: Color of the header text.
            option_color: Color of the menu options.
            quit_color: Color of the quit text.
            disabled_color: Color of disabled menu options.
        """
        self.console = Console()
        self.choices = {}
        self.groups = {}  # To hold groups of options by group ID
        self.header = header
        self.footer = footer
        self.clear_console = clear_console
        self.header_color = header_color
        self.option_color = option_color
        self.quit_color = quit_color
        self.disabled_color = disabled_color
        self.main_menu = main_menu
        self.parent_menu = parent_menu
        self.menu_path = []  # To track the navigation path for breadcrumbs

    def Group(self, group, title=None):
        """
        Adds a new group of menu options.

        Args:
            group: The unique identifier for the group.
            title: An optional title for the group.
        Raises:
            ValueError: If the group ID already exists.
        """
        if group in self.groups:
            raise ValueError(f"Group '{group}' already exists. Please choose a unique group ID.")
        self.groups[group] = {'title': title, 'options': []}

    def Add(self, key, description, callback, group_id=None, visible=True, disabled=False):
        """
        Adds a new choice to the specified group or to the default group if none is specified.

        Args:
            key: The key the user will press to select this option (e.g., '1', '2', '3').
            description: The description of the action.
            callback: The function to call when this option is selected.
            group_id: The group ID to add the choice to. If None, it will add to a default group.
            visible: Determines if the option should be visible in the menu.
            disabled: Determines if the option should be disabled (greyed out and unusable).
        Raises:
            ValueError: If the key already exists.
        """
        key = key.strip().lower()
        if key in self.choices:
            raise ValueError(f"Key '{key}' already exists. Please choose a unique key.")
        if visible:
            self.choices[key] = {'description': description, 'callback': callback, 'disabled': disabled}
            if group_id is None:
                group_id = 'default'
            if group_id not in self.groups:
                self.Group(group_id)
            self.groups[group_id]['options'].append((key, description, disabled))

    def Display(self):
        """
        Displays the interactive menu, handles user input, and executes corresponding callbacks.
        It continues to prompt until the user chooses to quit.
        """
        while True:

            # Clear the console if specified
            if self.clear_console:
                Clean()

            # Display the menu header if set
            if self.main_menu is None and self.header:
                self.console.print(
                    Panel(f"[bold {self.header_color}]{self.header}[/bold {self.header_color}]", title="Main Menu",
                          padding=1))
                self.console.print("")
            elif self.header:
                self.console.print(f"[bold {self.header_color}]{self.header}[/bold {self.header_color}]\n")

            # Display breadcrumb navigation if in a submenu
            if self.menu_path and len(self.menu_path) > 0:
                breadcrumb = " > ".join(self.menu_path)
                self.console.print(f"[{self.header_color}]Navigation: {breadcrumb}[/{self.header_color}]\n")

            # Display Main Menu options if applicable
            if self.main_menu:
                self.console.print(f"[{self.option_color}]M.[/{self.option_color}] Main Menu\n")

            # Display the menu options grouped by group ID
            for group_id, group_data in self.groups.items():
                if group_data['title']:
                    self.console.print(f"[bold {self.header_color}]{group_data['title']}[/bold {self.header_color}]")
                for key, description, disabled in group_data['options']:
                    if disabled:
                        self.console.print(
                            f"[{self.disabled_color}]{key}. {description} (Disabled)[/{self.disabled_color}]")
                    else:
                        self.console.print(f"[{self.option_color}]{key}.[/{self.option_color}] {description}")
                self.console.print("")  # Add line break between groups

            # Display Back or Quit options if applicable
            if self.parent_menu:
                self.console.print(f"[{self.option_color}]B.[/{self.option_color}] Back")
            else:
                self.console.print(f"[{self.quit_color}]Q.[/{self.quit_color}] Quit")

            # Display the footer if set
            if self.footer:
                self.console.print(f"\n[bold {self.header_color}]{self.footer}[/bold {self.header_color}]\n")

            # Prompt the user for input
            self.console.print("\n[bold yellow]Please press a key to select an option[/bold yellow]")
            user_input = GetKey()
            self.console.print(f"\nYou selected: {user_input}\n")

            # Handle Back, Main Menu, and Quit options
            if user_input == 'b' and self.parent_menu:
                self.parent_menu.Display()
                break
            elif user_input == 'm' and self.main_menu:
                self.main_menu.Display()
                break
            elif user_input in ['q', 'quit', 'exit', 'void', 'escape', 'esc', 'x']:
                quit()

            # Execute the corresponding callback if it exists and not disabled
            if user_input in self.choices:
                if self.choices[user_input].get('disabled', False):
                    self.console.print("[bold red]This option is disabled.[/bold red]")
                    time.sleep(1.5)
                else:
                    callback = self.choices[user_input]['callback']
                    callback(self)
            else:
                self.console.print("[bold red]Invalid option, please try again.[/bold red]")
                time.sleep(1.5)

    def Children(self, header=None, footer=None, clear_console=True, header_color="blue", option_color="cyan",
                 quit_color="red", disabled_color="grey50"):
        """
        Creates and returns a child menu (submenu) instance.

        Args:
            header: The text to display at the top of the submenu.
            footer: The text to display at the bottom of the submenu.
            clear_console: Whether to clear the console before displaying the submenu.
            header_color: Color of the header text in the submenu.
            option_color: Color of the menu options in the submenu.
            quit_color: Color of the quit text in the submenu.
            disabled_color: Color of disabled menu options in the submenu.
        Returns:
            CleanMenu: A new CleanMenu instance representing the child menu.
        """
        mm = self if self.main_menu is None else self.main_menu
        child_menu = CleanMenu(mm, self, header, footer, clear_console, header_color, option_color, quit_color,
                               disabled_color)

        # Set up the menu path for breadcrumbs
        if self.header:
            child_menu.menu_path = self.menu_path.copy() if self.menu_path else []
            child_menu.menu_path.append(self.header)

        return child_menu
