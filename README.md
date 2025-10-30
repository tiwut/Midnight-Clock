# Midnight Clock

![Midnight Clock Screenshot](https://raw.githubusercontent.com/username/repo/main/screenshot.png) <!-- **Action Required:** Replace this with a real screenshot URL -->

A modern, feature-rich, dark-themed clock application for Linux desktops, built with Python and PyQt6. Designed to be both beautiful and functional, it provides all the essential time-keeping tools in one place.

The application remains active in the system tray when closed, ensuring your alarms and timers are never missed.

## Features

-   **Sleek Dark Interface**: A visually appealing dark theme that's easy on the eyes.
-   **Main Digital Clock**: A large, clear display of the current time and date.
-   **World Clock**:
    -   Browse and search a complete list of all available timezones.
    -   **Pin** your favorite timezones for quick access.
    -   Pinned clocks are saved and loaded automatically.
-   **Alarm**:
    -   Set multiple alarms with custom messages.
    -   Receive a desktop notification and sound alert when an alarm triggers.
-   **Timer**: A simple countdown timer that alerts you when time is up.
-   **Stopwatch**:
    -   Precise stopwatch with millisecond accuracy.
    -   **Lap** functionality to record split times.
-   **System Tray Integration**:
    -   Minimizes to the system tray instead of closing, keeping alarms active in the background.
    -   Restore or quit the application directly from the tray icon menu.

## Requirements

This application is designed for Debian-based Linux distributions (like Ubuntu, Linux Mint, etc.). You will need the following packages installed:

-   Python 3
-   PyQt6 for the graphical interface
-   Pygame for sound playback

## Installation & Usage

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/midnight-clock.git
    cd midnight-clock
    ```

2.  **Install dependencies:**
    Use `apt` to install the required libraries from your distribution's official repositories.
    ```bash
    sudo apt update
    sudo apt install python3-pyqt6 python3-pygame
    ```

3.  **Place Asset Files:**
    For full functionality, make sure the following files are in the project's root directory:
    -   `icon.png`: The icon used for the window and system tray. A default 128x128 icon is recommended.
    -   `alarm.wav`: The sound file to be played for alarms and timers.

4.  **Run the application:**
    ```bash
    python3 midnight-clock.py
    ```
    The application will start, and a `midnight_clock_config.json` file will be created automatically to store your pinned world clocks.

## Building the Debian Package (`.deb`)

If you wish to package the application for easier installation and distribution, you can follow these steps.

1.  **Create the directory structure:**
    ```bash
    mkdir -p package/DEBIAN
    mkdir -p package/usr/bin
    mkdir -p package/usr/share/applications
    mkdir -p package/usr/share/icons/hicolor/128x128/apps
    ```

2.  **Create the `control` file:**
    Create a file named `control` inside `package/DEBIAN/` with the following content:
    ```
    Package: midnight-clock
    Version: 1.0.0
    Section: utils
    Priority: optional
    Architecture: all
    Depends: python3, python3-pyqt6, python3-pygame
    Maintainer: Your Name <your.email@example.com>
    Description: A modern and cool clock application for Linux.
     A graphical clock application featuring a digital clock, alarms,
     a timer, a stopwatch, and world clocks, all with a sleek dark interface.
    ```

3.  **Copy the application files:**
    ```bash
    # Copy the main script and make it executable
    cp midnight-clock.py package/usr/bin/midnight-clock
    chmod +x package/usr/bin/midnight-clock

    # Copy the icon
    cp icon.png package/usr/share/icons/hicolor/128x128/apps/midnight-clock.png
    
    # Copy the sound file (optional, but recommended to bundle it)
    # Note: The script currently looks for the sound in its local directory.
    # For a system-wide install, you would modify the script to look in /usr/share/midnight-clock/
    # cp alarm.wav package/usr/share/midnight-clock/alarm.wav 
    ```

4.  **Create the `.desktop` file:**
    Create a file named `midnight-clock.desktop` in `package/usr/share/applications/`:
    ```ini
    [Desktop Entry]
    Name=Midnight Clock
    Comment=A modern and cool clock application
    Exec=midnight-clock
    Icon=midnight-clock
    Terminal=false
    Type=Application
    Categories=Utility;
    ```

5.  **Build the package:**
    ```bash
    dpkg-deb --build package
    ```
    This will create a `package.deb` file, which can be installed with `sudo apt install ./package.deb`.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
