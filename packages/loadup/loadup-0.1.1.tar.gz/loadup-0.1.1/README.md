# LoadUp 📦

**The official bundler for WinUp applications.**

LoadUp is a smart build tool that wraps the power of PyInstaller in a simple and intuitive command-line interface. It's designed with sensible defaults for WinUp projects, allowing you to go from a Python script to a distributable executable with a single command.

---

## Why use LoadUp?

PyInstaller is incredibly powerful, but its command-line options can be overwhelming. LoadUp simplifies this process by:

*   **Providing a cleaner CLI:** Uses simple flags like `--onefile` and `--windowed`.
*   **Using a config file:** Reads a `loadup.config.json` for project-specific settings.
*   **Including sensible defaults:** Automatically finds and includes your `assets` directory and sets other options ideal for GUI applications.

---

## Installation

LoadUp is installed as part of the `winup init` process if you choose to include it. If you need to install it manually into your project's environment, you can install it from its directory:

```bash
# From the project root where the 'loadup' folder is
pip install loadup
```

---

## Usage

The primary command is `loadup build`.

```bash
loadup build <path_to_main_script> [OPTIONS]
```

This command will bundle your application and place the final executable and any associated files into a `dist` directory (or the directory specified in your `loadup.config.json`).

### Example

```bash
# Build the main.py script from a generated project
loadup build src/app/main.py --name "MyCoolApp" --onefile
```

---

## Configuration

You can configure the build process in two ways:

1.  **Command-Line Options (Highest Priority):** Flags you pass to the `build` command will always override the config file.
2.  **`loadup.config.json`:** For settings that don't change often, you can create this file in your project's root directory.

**Example `loadup.config.json`:**
```json
{
    "build_dir": "release",
    "name": "MyAwesomeApp",
    "icon": "assets/icon.ico"
}
```

### All Build Options

*   `filename`: (Required) The path to your main Python script.
*   `--name`: The name of the final executable file. (Default: the script's name)
*   `--icon`: Path to an application icon file (`.ico` on Windows, `.icns` on Mac).
*   `--onefile` / `--onedir`: Package your app into a single executable or a directory with dependencies. (Default: `--onefile`)
*   `--windowed` / `--console`: Choose whether to show a console window in the background. For GUI apps, `--windowed` is recommended. (Default: `--windowed`)
*   `--add-asset`: Specify an additional file or folder to include in the build. Can be used multiple times.
*   `--clean`: Force a clean build by removing PyInstaller's cache. (Default: on)

LoadUp provides a streamlined path from development to distribution, letting you focus on your code, not your build commands. 