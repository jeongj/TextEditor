
# **Simple Text Editor**

A lightweight, cross-platform text editor built with Python and Tkinter. This application is designed to be a simple yet powerful tool for basic text editing, featuring a clean user interface, multi-window support, and extensive customization options.

## **Features**

* **Cross-Platform:** Works on Windows, macOS, and Linux.  
* **Multi-Window Support:** Open and edit multiple files in separate windows simultaneously.  
* **Full Customization:**  
  * Change font family and size.  
  * Select custom colors for the font and background.  
* **Session Persistence:** The editor remembers your font, color, and window settings for the next session.  
* **Recent Files:** Quickly access your last 5 opened files from the menu.  
* **Autosave:** Automatically saves your work every 30 seconds to prevent data loss (can be toggled on/off).  
* **Status Bar:** Get real-time feedback on font size and **character count**.  
* **Standard Editing Tools:** Includes Undo, Redo, Cut, Copy, and Paste.  
* **Platform-Aware Shortcuts:** Uses Cmd on macOS and Ctrl on Windows/Linux for a native feel.

## **Technology Stack**

* **Language:** Python 3  
* **GUI Framework:** Tkinter (Python's standard library)

## **Getting Started**

There are two ways to use this application: by running the pre-built executable or by running the script from the source.

### **1\. Running the Executable**

This is the easiest way to get started.

1. Go to the **Releases** section of this GitHub repository.  
2. Download the appropriate executable for your operating system (Text Editor.exe for Windows, Text Editor.app for macOS).  
3. Double-click the file to run the application. No installation is needed\!

### **2\. Running from Source**

If you are a developer and want to run the application from the source code, follow these steps:

1. **Prerequisites:** Ensure you have Python 3 installed on your system.  
2. **Clone the repository:**  
   git clone \[https://github.com/your-username/simple-text-editor.git\](https://github.com/your-username/simple-text-editor.git)  
   cd simple-text-editor

3. **Run the script:**  
   python text\_editor.py

## **How to Build Your Own Executable**

You can package the script into a standalone executable using **PyInstaller**.

1. **Install PyInstaller:**  
   pip install pyinstaller

2. **Create an Icon (Optional):**  
   * Create a square PNG image for your icon (e.g., icon.png).  
   * Convert it to .ico for Windows or .icns for macOS using an online converter.  
3. **Run the PyInstaller command:**  
   * **For Windows (.exe):**  
     pyinstaller \--onefile \--windowed \--icon="your\_icon.ico" \--name="Text Editor" text\_editor.py

   * **For macOS (.app):**  
     pyinstaller \--onefile \--windowed \--icon="your\_icon.icns" \--name="Text Editor" text\_editor.py

4. **Find your application:** The final executable will be located in the dist folder.

## **License**

This project is licensed under the MIT License \- see the LICENSE.md file for details.
