# Bruno Suite: Clicker & Link Generator

A toolset for automating workflows with the **[Bruno](https://www.usebruno.com/)** API client. 
It allows you to generate unique request links and automatically open them in the Bruno app using a custom `brunogs://` protocol.

---

## 1. Component Description

### Bruno Clicker (`bruno_clicker.py`)
The core automation agent.
- **Purpose**: Receives a URI link (`brunogs://` protocol), launches Bruno in debug mode (CDP), connects via Playwright, and automatically finds/opens the specified request in the collection.
- **Technologies**: Python, Playwright (Chromium), Windows Registry.
- **Features**: Runs in the background and automatically manages Bruno processes.

### Bruno Generator (`bruno_generator.py`)
The link creation tool.
- **Purpose**: Integrates into the Windows context menu for `.yml` files (Bruno requests). When triggered, it generates a valid link like `brunogs://Main%20Collection?path=...` and copies it to the clipboard.
- **Features**: Automatically encodes special characters (URL Encoding) to ensure path validity.

---

## 2. Executable Build (Python)

**PyInstaller** is used to compile the scripts into standalone `.exe` files. The `--onedir` mode is used to avoid issues with Playwright browser paths.

### Prerequisites
1. **Python 3.10+** installed.
2. Dependencies installed:
   ```bash
   pip install playwright pyperclip
   playwright install chromium
   ```
### Build Commands
Run the following commands in your terminal from the project folder:

1. Build Clicker:
```
pyinstaller --noconfirm --onedir --windowed --name "bruno_clicker" "bruno_clicker.py"
```

2. Build Generator:
```
pyinstaller --noconfirm --onedir --windowed --name "bruno_generator" "bruno_generator.py"
```
After building, two directories will appear in the dist/ folder. For the installer to work correctly, it is recommended to merge their contents into a single folder: dist/BrunoSuite.

3. Build Suite (via .spec file):
```
pyinstaller build.spec --noconfirm
```

## 3. Installer Build (Inno Setup)
Inno Setup 6.0.2 is used to create the installation package.

Build Steps:
Open the .iss setup script in the Inno Setup Compiler.

Ensure the [Files] section points to the correct path of the compiled Python files (dist/BrunoSuite directory).

Click Build -> Compile (or press Ctrl + F9).

What the Installer Does:
* *Auto-detection*: Automatically finds the installed Bruno.exe in the system (via Registry or standard paths).
* *Protocol Registration*: Registers the brunogs:// handler in the Registry, linking it to bruno_clicker.exe.
* *Shell Integration*: Adds "Copy Bruno Link" to the context menu for .yml files.

Maintenance Mode: Detects existing installations and offers to update or fully uninstall the program.

## 4. Usage
Right-click any Bruno request file (.yml).

Select "Copy Bruno Link".

Share the link with a colleague or use it in your documentation. Clicking the link will automatically open Bruno at the specific request.

## 5. Tools Used
* **[Bruno](https://www.usebruno.com/)**
* **[Visual studio code](https://code.visualstudio.com/)**
* **[Python 3.13](https://www.python.org/downloads/release/python-3130/)**
* **[InnoSetup](https://jrsoftware.org/isinfo.php)**
---
## 6. Acknowledgments
* **[Gemini](https://gemini.google.com)**
* **[Deepseek](https://chat.deepseek.com)**
* **[Markdown live preview](https://markdownlivepreview.com/)**
