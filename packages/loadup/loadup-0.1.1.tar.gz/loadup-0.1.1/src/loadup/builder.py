import subprocess
import os
import platform
from pathlib import Path

class BuildKit:
    """
    Constructs and executes a PyInstaller command based on user configuration.
    """
    def __init__(self, entry_script: str, config: dict):
        self.entry_script = Path(entry_script)
        self.config = config
        self.pyinstaller_cmd = ["pyinstaller", str(self.entry_script)]
        
        # Sensible defaults
        self.dist_path = Path(config.get("build_dir", "dist"))
        self.work_path = self.dist_path / "build"
        self.spec_path = self.dist_path

    def _prepare_command(self):
        """Assembles the full PyInstaller command from the config."""
        
        # Name
        name = self.config.get("name", self.entry_script.stem)
        self.pyinstaller_cmd.extend(["--name", name])
        
        # Bundle type
        if self.config.get("onefile", True):
            self.pyinstaller_cmd.append("--onefile")
        
        # Windowed or Console
        if self.config.get("windowed", True):
            self.pyinstaller_cmd.append("--windowed")
        else:
            self.pyinstaller_cmd.append("--console")
        
        # Icon
        if icon_path := self.config.get("icon"):
            self.pyinstaller_cmd.extend(["--icon", str(icon_path)])
            
        # Add assets
        # Automatically include the 'assets' directory if it exists
        if Path("assets").exists():
            self.pyinstaller_cmd.extend(["--add-data", f"assets{os.pathsep}assets"])
        
        # Add user-specified assets
        for asset_path in self.config.get("add_asset", []):
            dest = Path(asset_path).name
            self.pyinstaller_cmd.extend(["--add-data", f"{asset_path}{os.pathsep}{dest}"])

        # Paths
        self.pyinstaller_cmd.extend([
            "--distpath", str(self.dist_path),
            "--workpath", str(self.work_path),
            "--specpath", str(self.spec_path),
        ])
        
        # Clean build
        if self.config.get("clean", True):
            self.pyinstaller_cmd.append("--clean")
            
    def build(self):
        """Executes the PyInstaller build command."""
        self._prepare_command()
        
        print("---")
        print("Executing PyInstaller with the following command:")
        print(f"  {' '.join(self.pyinstaller_cmd)}")
        print("---")
        
        # Execute the command
        result = subprocess.run(
            self.pyinstaller_cmd, 
            capture_output=True, 
            text=True, 
            check=False
        )
        
        if result.returncode != 0:
            print("PyInstaller STDOUT:")
            print(result.stdout)
            print("PyInstaller STDERR:")
            print(result.stderr)
            raise RuntimeError("PyInstaller failed. See output above for details.")
        
        print(result.stdout) 