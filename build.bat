rem Build Clicker
rem pyinstaller --onedir --noconsole --hidden-import=playwright --collect-all playwright src\bruno_clicker.py

rem Build Generator
rem pyinstaller --onedir --noconsole --hidden-import=playwright --collect-all playwright src\bruno_generator.py

rem Build Suite
pyinstaller build.spec --noconfirm
