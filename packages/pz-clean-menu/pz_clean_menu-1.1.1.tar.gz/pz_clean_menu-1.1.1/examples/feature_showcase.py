from pz_clean_menu import CleanMenu, GeometricConsole, clear_console, pause, print_header

def show_breadcrumb_navigation(menu):
    """
    Demonstrates breadcrumb navigation by creating nested menus.
    """
    submenu1 = menu.Children(header="Submenu Level 1")
    submenu1.Group("options", title="Submenu Level 1 Options")
    submenu1.Add("1", "Go to Level 2", lambda m: go_to_level_2(submenu1), group_id="options")
    submenu1.Display()

def go_to_level_2(menu):
    """
    Creates a second level submenu to demonstrate breadcrumb navigation.
    """
    submenu2 = menu.Children(header="Submenu Level 2")
    submenu2.Group("options", title="Submenu Level 2 Options")
    submenu2.Add("1", "Go to Level 3", lambda m: go_to_level_3(submenu2), group_id="options")
    submenu2.Display()

def go_to_level_3(menu):
    """
    Creates a third level submenu to demonstrate breadcrumb navigation.
    """
    submenu3 = menu.Children(header="Submenu Level 3")
    submenu3.Group("options", title="Submenu Level 3 Options")
    submenu3.Add("1", "Show Message", show_message, group_id="options")
    submenu3.Display()

def show_message(menu):
    """
    Shows a message and waits for user input.
    """
    print("\n[Action] You've navigated through multiple levels of menus!")
    print("Notice the breadcrumb navigation at the top of the menu.")
    pause()

def show_disabled_options(menu):
    """
    Demonstrates disabled menu options.
    """
    submenu = menu.Children(header="Disabled Options Demo")
    submenu.Group("options", title="Disabled Options")
    
    # Add a regular option
    submenu.Add("1", "Regular Option", lambda m: print("\n[Action] You selected a regular option!\n") or pause(), group_id="options")
    
    # Add disabled options
    submenu.Add("2", "Disabled Option", lambda m: None, group_id="options", disabled=True)
    submenu.Add("3", "Another Disabled Option", lambda m: None, group_id="options", disabled=True)
    
    submenu.Display()

def show_console_helpers(menu):
    """
    Demonstrates console helper functions.
    """
    clear_console()
    print_header("Console Helpers Demo")
    
    print("\nThis example demonstrates various console helper functions.")
    print("The console has been cleared using clear_console().")
    print("The header above was created using print_header().")
    
    pause("\nPress Enter to return to the menu...")

def show_geometric_console(menu):
    """
    Demonstrates the GeometricConsole class.
    """
    clear_console()
    gc = GeometricConsole()
    
    # Show a box
    gc.box("This is text in a box", title="Simple Box")
    print()
    
    # Show a centered box
    gc.centered_box("This is text in a centered box", title="Centered Box", width=50)
    print()
    
    # Show a table
    data = [
        ["Name", "Age", "City"],
        ["Alice", 30, "New York"],
        ["Bob", 25, "Los Angeles"],
        ["Charlie", 35, "Chicago"]
    ]
    gc.table(data[1:], headers=data[0], title="Sample Table")
    print()
    
    # Show a progress bar
    print("Progress Bar Demo:")
    gc.progress_bar(75, 100)
    print()
    
    # Show a grid
    items = ["Item 1", "Item 2", "Item 3", "Item 4", "Item 5", "Item 6"]
    print("Grid Demo:")
    gc.grid(items, columns=3)
    print()
    
    # Show a divider
    gc.divider()
    
    pause("\nPress Enter to return to the menu...")

if __name__ == "__main__":
    # Create the main menu
    main_menu = CleanMenu(header="Feature Showcase", footer="Select an option to explore new features")
    
    # Create groups
    main_menu.Group("features", title="New Features")
    
    # Add options to demonstrate new features
    main_menu.Add("1", "Breadcrumb Navigation", show_breadcrumb_navigation, group_id="features")
    main_menu.Add("2", "Disabled Menu Options", show_disabled_options, group_id="features")
    main_menu.Add("3", "Console Helpers", show_console_helpers, group_id="features")
    main_menu.Add("4", "Geometric Console", show_geometric_console, group_id="features")
    
    # Display the menu
    main_menu.Display()