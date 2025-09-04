# =====================================================================================
#  Simple Text Editor
#  Author: Gemini
#  Version: 1.1 (Cross-platform)
#
#  A feature-rich, multi-window text editor built with Python's Tkinter library.
#  Now with platform-aware shortcuts (Cmd on macOS, Ctrl on Windows/Linux).
#
#  Features:
#  - Multiple independent editor windows
#  - File operations: New, Open, Save, Save As
#  - Session persistence: Remembers font, colors, and recent files
#  - Customizable formatting: Font family, size, and colors
#  - Autosave functionality
#  - Status bar with character count and font information
#  - Standard text editing: Undo, Redo, Cut, Copy, Paste
# =====================================================================================

import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox, font, colorchooser
import json
import os
import sys

# --- Constants ---
SETTINGS_FILE = "editor_settings.json"

# --- Platform-specific Configuration ---
# Detect if the OS is macOS to use 'Command' key instead of 'Control'.
IS_MAC = sys.platform == 'darwin'
ACCELERATOR_MODIFIER = "Cmd" if IS_MAC else "Ctrl"
BINDING_MODIFIER = "Command" if IS_MAC else "Control"


class TextEditor:
    """
    Manages a single, independent text editor window.

    Each instance of this class is a complete editor with its own text area,
    menu bar, and state (e.g., current file path, unsaved changes).
    """

    def __init__(self, master_window, app_controller):
        """
        Initializes a new TextEditor instance.

        Args:
            master_window (tk.Toplevel): The Tkinter Toplevel window for this editor.
            app_controller (AppController): The main controller managing all editor instances.
        """
        self.root = master_window
        self.controller = app_controller
        self.file_path = None
        self.is_dirty = False  # Tracks if there are unsaved changes.

        # Load shared settings from the controller.
        self.load_settings()
        # Build the UI components for this window.
        self.setup_ui()

        # Set the behavior for when the window's close button is clicked.
        self.root.protocol("WM_DELETE_WINDOW", self.close_window)
        # Start the periodic autosave check.
        self.start_autosave_loop()

    # --- Setup and Configuration ---

    def load_settings(self):
        """Loads configuration from the central controller's settings dictionary."""
        settings = self.controller.settings
        self.font_size = settings.get("font_size", 12)
        self.font_family = settings.get("font_family", "Consolas")
        self.font_color = settings.get("font_color", "black")
        self.bg_color = settings.get("bg_color", "white")
        self.autosave_enabled = settings.get("autosave_enabled", True)
        self.autosave_interval = settings.get("autosave_interval", 30000)  # 30 seconds in ms

    def setup_ui(self):
        """Constructs and lays out all the widgets for this editor window."""
        self.root.title("Untitled - Simple Text Editor")
        self.root.geometry("800x600")

        # The font object is configured once and can be updated later.
        self.editor_font = font.Font(family=self.font_family, size=self.font_size)

        # --- Main Text Widget ---
        # ScrolledText is a convenient wrapper around the Text widget that includes a scrollbar.
        self.text_area = scrolledtext.ScrolledText(
            self.root,
            wrap=tk.WORD,
            undo=True,  # This enables the undo/redo stack.
            font=self.editor_font,
            fg=self.font_color,
            bg=self.bg_color,
            insertbackground=self.font_color  # Sets the cursor color to match the font.
        )
        self.text_area.pack(expand=True, fill='both')
        self.text_area.focus_set()  # Place the cursor in the text area on launch.

        # --- Status Bar ---
        self.status_bar = tk.Label(self.root, text="Ready", anchor='w', bd=1, relief=tk.SUNKEN)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # --- Menu Bar ---
        self.autosave_enabled_var = tk.BooleanVar(value=self.autosave_enabled)
        self.create_menu_bar()

        # --- Event Bindings ---
        # The <<Modified>> virtual event is triggered whenever the text content changes.
        self.text_area.bind("<<Modified>>", self.on_text_modified)
        self.bind_shortcuts()

        self.update_status_bar()

    def create_menu_bar(self):
        """Creates and configures the menu bar for this window."""
        menu_bar = tk.Menu(self.root)
        self.root.config(menu=menu_bar)

        # --- File Menu ---
        file_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="New File", accelerator=f"{ACCELERATOR_MODIFIER}+N", command=self.new_file)
        file_menu.add_command(label="New Window", accelerator=f"{ACCELERATOR_MODIFIER}+Shift+N",
                              command=self.controller.create_new_window)
        file_menu.add_command(label="Open...", accelerator=f"{ACCELERATOR_MODIFIER}+O", command=self.open_file_dialog)

        self.recent_menu = tk.Menu(file_menu, tearoff=0)
        file_menu.add_cascade(label="Recent Files", menu=self.recent_menu)
        self.controller.update_all_recent_files_menus()

        file_menu.add_separator()
        file_menu.add_command(label="Save", accelerator=f"{ACCELERATOR_MODIFIER}+S", command=self.save_file)
        file_menu.add_command(label="Save As...", accelerator=f"{ACCELERATOR_MODIFIER}+Shift+S",
                              command=self.save_as_file)
        file_menu.add_separator()
        file_menu.add_checkbutton(label="Autosave", onvalue=True, offvalue=False, variable=self.autosave_enabled_var)
        file_menu.add_separator()
        file_menu.add_command(label="Close Window", command=self.close_window)

        # --- Edit, Format, and View Menus ---
        self._create_edit_format_view_menus(menu_bar)

    def _create_edit_format_view_menus(self, menu_bar):
        """Helper function to create the non-File menus."""
        # --- Edit Menu ---
        edit_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Undo", accelerator=f"{ACCELERATOR_MODIFIER}+Z", command=self.text_area.edit_undo)
        edit_menu.add_command(label="Redo", accelerator=f"{ACCELERATOR_MODIFIER}+Y", command=self.text_area.edit_redo)
        edit_menu.add_separator()
        edit_menu.add_command(label="Cut", accelerator=f"{ACCELERATOR_MODIFIER}+X",
                              command=lambda: self.text_area.event_generate("<<Cut>>"))
        edit_menu.add_command(label="Copy", accelerator=f"{ACCELERATOR_MODIFIER}+C",
                              command=lambda: self.text_area.event_generate("<<Copy>>"))
        edit_menu.add_command(label="Paste", accelerator=f"{ACCELERATOR_MODIFIER}+V",
                              command=lambda: self.text_area.event_generate("<<Paste>>"))

        # --- Format Menu ---
        format_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Format", menu=format_menu)
        format_menu.add_command(label="Change Font...", command=self.change_font)
        format_menu.add_command(label="Change Font Color...", command=self.change_font_color)
        format_menu.add_command(label="Change Background Color...", command=self.change_bg_color)

        # --- View Menu ---
        view_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Increase Font Size", accelerator=f"{ACCELERATOR_MODIFIER}++",
                              command=self.increase_font_size)
        view_menu.add_command(label="Decrease Font Size", accelerator=f"{ACCELERATOR_MODIFIER}+-",
                              command=self.decrease_font_size)

    def bind_shortcuts(self):
        """Binds keyboard shortcuts to their respective functions using the correct modifier."""
        self.root.bind(f"<{BINDING_MODIFIER}-n>", self.new_file)
        self.root.bind(f"<{BINDING_MODIFIER}-N>", self.controller.create_new_window)
        self.root.bind(f"<{BINDING_MODIFIER}-o>", self.open_file_dialog)
        self.root.bind(f"<{BINDING_MODIFIER}-s>", self.save_file)
        self.root.bind(f"<{BINDING_MODIFIER}-S>", self.save_as_file)  # Capital 'S' for Shift+s
        self.root.bind(f"<{BINDING_MODIFIER}-plus>", self.increase_font_size)
        self.root.bind(f"<{BINDING_MODIFIER}-equal>", self.increase_font_size)
        self.root.bind(f"<{BINDING_MODIFIER}-minus>", self.decrease_font_size)
        # Note: Undo/Redo/Cut/Copy/Paste are often handled by the OS/Tkinter,
        # but explicit bindings can be added here if they feel inconsistent on any platform.
        # e.g., self.root.bind(f"<{BINDING_MODIFIER}-z>", lambda e: self.text_area.edit_undo())

    # --- Core Functionality ---

    def new_file(self, event=None):
        """Clears the text area to start a new file."""
        if self._check_unsaved_changes():
            self.file_path = None
            self.text_area.delete(1.0, tk.END)
            self.text_area.edit_reset()  # Clears the undo/redo stack.
            self.is_dirty = False
            self.update_title()
            self.update_status_bar()

    def open_file_dialog(self, event=None):
        """Shows the OS 'Open File' dialog and opens the selected file."""
        if not self._check_unsaved_changes():
            return

        path = filedialog.askopenfilename(
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if path:
            self._open_file_at_path(path)

    def _open_file_at_path(self, path):
        """Helper function to load content from a given file path."""
        try:
            with open(path, 'r', encoding='utf-8') as file:
                content = file.read()

            self.text_area.delete(1.0, tk.END)
            self.text_area.insert(tk.END, content)

            self.file_path = path
            self.is_dirty = False
            self.text_area.edit_reset()
            self.update_title()
            self.update_status_bar()
            self.controller.add_to_recent_files(path)
        except Exception as e:
            messagebox.showerror("Error", f"Could not open file:\n{e}", master=self.root)

    def save_file(self, event=None):
        """Saves the current file to its existing path, or prompts for a new path."""
        # If no path exists, this is the same as "Save As".
        if not self.file_path:
            return self.save_as_file()

        try:
            content = self.text_area.get(1.0, "end-1c")  # Get all text minus the trailing newline.
            with open(self.file_path, 'w', encoding='utf-8') as file:
                file.write(content)

            self.is_dirty = False
            self.update_title()
            self.controller.add_to_recent_files(self.file_path)
            return True  # Indicate success.
        except Exception as e:
            messagebox.showerror("Error", f"Could not save file:\n{e}", master=self.root)
            return False  # Indicate failure.

    def save_as_file(self, event=None):
        """Shows the OS 'Save File' dialog and saves the content to a new path."""
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")]
        )
        if path:
            self.file_path = path
            return self.save_file()
        return False  # User cancelled the dialog.

    def close_window(self):
        """Handles the logic for closing this editor window."""
        if self._check_unsaved_changes():
            # If confirmed, proceed with closing.
            self.controller.on_window_close(self)
            self.root.destroy()

    # --- Event Handlers and Updates ---

    def on_text_modified(self, event=None):
        """
        Callback function for when the text area content is changed.
        The <<Modified>> virtual event requires the flag to be manually reset.
        """
        if self.text_area.edit_modified():
            self.is_dirty = True
            self.update_title()
            self.update_status_bar()
            # We must reset the flag, otherwise this event won't fire again
            # until the text area is cleared and re-inserted.
            self.text_area.edit_modified(False)

    def update_title(self):
        """Updates the window title, adding a '*' if the file is dirty (unsaved)."""
        base_name = os.path.basename(self.file_path) if self.file_path else "Untitled"
        dirty_marker = "*" if self.is_dirty else ""
        self.root.title(f"{dirty_marker}{base_name} - Simple Text Editor")

    def update_status_bar(self, event=None):
        """Updates the status bar with current font size and character count."""
        char_count = len(self.text_area.get(1.0, "end-1c"))
        status_text = f"Font: {self.font_family} {self.font_size}    |    Characters: {char_count}"
        self.status_bar.config(text=status_text)

    def start_autosave_loop(self):
        """The recurring function that performs the autosave check."""
        # Only save if autosave is enabled, the file has a path, and has been modified.
        if self.autosave_enabled_var.get() and self.is_dirty and self.file_path:
            self.save_file()

        # Schedule this function to run again after the specified interval.
        self.root.after(self.autosave_interval, self.start_autosave_loop)

    # --- Formatting Options ---

    def increase_font_size(self, event=None):
        """Increases the font size by 1 point."""
        self.font_size += 1
        self.editor_font.configure(size=self.font_size)
        self.update_status_bar()
        return "break"  # Prevents the event from propagating further.

    def decrease_font_size(self, event=None):
        """Decreases the font size by 1 point, with a minimum size of 4."""
        if self.font_size > 4:
            self.font_size -= 1
            self.editor_font.configure(size=self.font_size)
            self.update_status_bar()
        return "break"

    def change_font(self):
        """Opens a simple dialog to choose a new font family."""
        # A more complex, native font chooser could be implemented here.
        # This is a simple listbox for demonstration.
        win = tk.Toplevel(self.root)
        win.title("Choose Font")
        listbox = tk.Listbox(win)
        listbox.pack(expand=True, fill='both', padx=10, pady=10)

        fonts = sorted(font.families())
        for f in fonts:
            listbox.insert(tk.END, f)

        def on_select(evt):
            selection = listbox.get(listbox.curselection())
            self.font_family = selection
            self.editor_font.configure(family=self.font_family)
            self.update_status_bar()
            win.destroy()

        listbox.bind("<<ListboxSelect>>", on_select)

    def change_font_color(self):
        """Opens a color picker to change the text color."""
        color = colorchooser.askcolor(title="Choose Font Color", initialcolor=self.font_color)
        if color and color[1]:
            self.font_color = color[1]
            self.text_area.config(fg=self.font_color, insertbackground=self.font_color)

    def change_bg_color(self):
        """Opens a color picker to change the background color."""
        color = colorchooser.askcolor(title="Choose Background Color", initialcolor=self.bg_color)
        if color and color[1]:
            self.bg_color = color[1]
            self.text_area.config(bg=self.bg_color)

    # --- Utility Methods ---

    def _check_unsaved_changes(self):
        """
        Checks for unsaved changes and prompts the user to save if necessary.
        Returns True if the action should proceed (user saved, discarded, or no changes),
        and False if the action should be cancelled.
        """
        if not self.is_dirty:
            return True

        response = messagebox.askyesnocancel(
            "Unsaved Changes",
            "You have unsaved changes. Do you want to save them?",
            master=self.root
        )

        if response is True:  # Yes, save
            return self.save_file()
        elif response is False:  # No, discard
            return True
        else:  # Cancel
            return False


class AppController:
    """
    Manages the overall application lifecycle and shared state.
    This includes settings and the list of open editor windows.
    """

    def __init__(self, root):
        """
        Initializes the AppController.

        Args:
            root (tk.Tk): The main, hidden root window of the application.
        """
        self.root = root
        self.editor_instances = []
        self.load_settings()

    def load_settings(self):
        """Loads settings from the JSON file or uses defaults."""
        try:
            with open(SETTINGS_FILE, 'r') as f:
                self.settings = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self.settings = {}

    def save_settings(self):
        """Saves the current settings to the JSON file."""
        # Get the settings from the last active window as the source of truth.
        if self.editor_instances:
            last_editor = self.editor_instances[-1]
            self.settings["font_size"] = last_editor.font_size
            self.settings["font_family"] = last_editor.font_family
            self.settings["font_color"] = last_editor.font_color
            self.settings["bg_color"] = last_editor.bg_color
            self.settings["autosave_enabled"] = last_editor.autosave_enabled_var.get()

        with open(SETTINGS_FILE, 'w') as f:
            json.dump(self.settings, f, indent=4)

    def create_new_window(self, event=None):
        """Creates a new Toplevel window and initializes a TextEditor instance in it."""
        editor_window = tk.Toplevel(self.root)
        editor = TextEditor(editor_window, self)
        self.editor_instances.append(editor)

    def on_window_close(self, editor_instance):
        """Handles cleanup when an editor window is closed."""
        if editor_instance in self.editor_instances:
            self.editor_instances.remove(editor_instance)

        # If the last window is closed, save settings and exit the app.
        if not self.editor_instances:
            self.save_settings()
            self.root.quit()

    def add_to_recent_files(self, path):
        """Adds a file path to the list of recent files and updates all open windows."""
        recent_files = self.settings.get("recent_files", [])
        if path in recent_files:
            recent_files.remove(path)
        recent_files.insert(0, path)
        self.settings["recent_files"] = recent_files[:5]  # Keep the last 5 files.
        self.update_all_recent_files_menus()

    def update_all_recent_files_menus(self):
        """Updates the 'Recent Files' menu in all open editor windows."""
        recent_files = self.settings.get("recent_files", [])
        for editor in self.editor_instances:
            editor.recent_menu.delete(0, tk.END)
            for path in recent_files:
                # Use a lambda with a default argument to capture the correct path.
                editor.recent_menu.add_command(
                    label=os.path.basename(path),
                    command=lambda p=path: editor._open_file_at_path(p)
                )


def main():
    """The main entry point for the application."""
    # Create the main root window. This window will be hidden and will act
    # as the parent for all other windows and the controller for the event loop.
    root = tk.Tk()
    root.withdraw()  # Hide the main window.

    # Initialize the application controller.
    app_controller = AppController(root)

    # Create the first editor window on startup.
    app_controller.create_new_window()

    # Start the Tkinter event loop.
    root.mainloop()


if __name__ == "__main__":
    main()

