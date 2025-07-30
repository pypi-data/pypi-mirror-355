import click
import json
import os
from pathlib import Path
from .builder import BuildKit

@click.group()
def main():
    """
    LoadUp: The official bundler for WinUp applications.
    
    This tool is a friendly wrapper around PyInstaller, configured with
    sensible defaults for WinUp projects.
    """
    pass

@main.command()
@click.argument('filename', type=click.Path(exists=True))
@click.option('--name', default=None, help="Name for the final executable.")
@click.option('--icon', type=click.Path(exists=True), default=None, help="Path to an application icon (.ico, .icns).")
@click.option('--onefile/--onedir', is_flag=True, default=True, help="Create a single-file or one-dir bundle.")
@click.option('--windowed/--console', is_flag=True, default=True, help="Run without a console window (GUI only).")
@click.option('--add-asset', multiple=True, type=click.Path(exists=True), help="Path to an additional asset or directory to bundle.")
@click.option('--clean', is_flag=True, default=True, help="Clean PyInstaller cache before building.")
def build(filename, **kwargs):
    """Packages your WinUp application into an executable."""
    click.secho("🚀 Starting LoadUp build process...", fg="cyan")
    
    config_path = Path("loadup.config.json")
    config = {}
    if config_path.exists():
        click.echo(f"  -> Found '{config_path}', loading configuration.")
        config = json.loads(config_path.read_text())
    
    # CLI options override config file options
    for key, value in kwargs.items():
        if value is not None:
            config[key] = value

    try:
        builder = BuildKit(filename, config)
        builder.build()
        click.secho("✅ Build successful!", fg="green")
        click.echo(f"   -> Your application is ready in the '{builder.dist_path}' directory.")
    except Exception as e:
        click.secho(f"🔥 Build failed: {e}", fg="red")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 