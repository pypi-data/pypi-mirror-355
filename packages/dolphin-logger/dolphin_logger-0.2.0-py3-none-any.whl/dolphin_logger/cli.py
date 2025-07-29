import argparse
import shutil
import importlib.resources as pkg_resources # Use importlib.resources
import os # For os.path.exists in init if needed, though Path.exists is better
from pathlib import Path # For Path object operations

# Imports from our refactored modules
from .config import load_config, get_config_path, get_config_dir # Added get_config_dir
from .server import run_server_main
from .upload import upload_logs
import json # For validate in config command

def _handle_init_command():
    """Handles the `dolphin-logger init` command."""
    print("Initializing dolphin-logger configuration...")
    config_dir = get_config_dir() # This also creates the dir if it doesn't exist
    config_file_path = get_config_path()

    if config_file_path.exists():
        print(f"Configuration file already exists at: {config_file_path}")
    else:
        try:
            # Use config.json.example from the project root as the template
            template_path = Path(__file__).parent.parent.parent / "config.json.example"
            
            if template_path.exists():
                # Ensure config_dir exists (get_config_dir should do this, but double check)
                config_dir.mkdir(parents=True, exist_ok=True)
                
                shutil.copy(template_path, config_file_path)
                print(f"Default configuration file created at: {config_file_path}")
                print("\n🎉 Configuration initialized! Next steps:")
                print("1. Set your API keys as environment variables:")
                print("   export ANTHROPIC_API_KEY=your_anthropic_key")
                print("   export OPENAI_API_KEY=your_openai_key")
                print("   export GOOGLE_API_KEY=your_google_key")
                print("2. (Optional) Edit the config file to customize models and endpoints")
                print("3. Start the server: dolphin-logger")
                print("4. Test with: curl http://localhost:5001/v1/models")
            else:
                print(f"Error: Default configuration template (config.json.example) not found.")
                print(f"Expected location: {template_path}")
                print("Please ensure the package is installed correctly and config.json.example exists in the project root.")

        except Exception as e:
            print(f"Error during configuration initialization: {e}")
            print("Please ensure the package is installed correctly and a config.json.example file is present.")

def _handle_config_command(args):
    """Handles the `dolphin-logger config` command."""
    if args.path:
        config_file_path = get_config_path()
        print(f"Expected configuration file path: {config_file_path}")
        if not config_file_path.exists():
             print(f"Note: Configuration file does not currently exist at this path. Run 'dolphin-logger init' to create it.")
    
    elif args.validate:
        config_file_path = get_config_path()
        print(f"Validating configuration at: {config_file_path}...")
        if not config_file_path.exists():
            print(f"Configuration file not found at: {config_file_path}")
            print("Run 'dolphin-logger init' to create a default configuration file.")
            return

        try:
            # load_config already prints details about API key resolution
            config_data = load_config() 
            if config_data: # load_config returns a dict
                models_loaded = len(config_data.get("models", []))
                print(f"Configuration appears valid. {models_loaded} model(s) entries found.")
                # Further validation could be added here, e.g., checking schema
            else:
                # This case might occur if load_config returns None or empty dict on some error
                # though current load_config raises exceptions or returns dict.
                print("Configuration loaded but seems empty or invalid.")
        except json.JSONDecodeError as e:
            print(f"Configuration validation failed: Invalid JSON - {e.msg} (line {e.lineno}, column {e.colno})")
        except FileNotFoundError: # Should be caught by the .exists() check, but as a safeguard
            print(f"Configuration validation failed: File not found at {config_file_path}")
        except Exception as e:
            print(f"Configuration validation failed: {e}")
            # import traceback
            # traceback.print_exc()
    else:
        # No flags given for 'config' command, print help for this subcommand
        print("Please specify an option for the 'config' command: --path or --validate.")
        # Alternatively, could show the config path by default. For now, require a flag.


def main_cli():
    """Command Line Interface entry point for Dolphin Logger."""
    parser = argparse.ArgumentParser(description="Dolphin Logger: Proxy server, log uploader, and config manager.")
    subparsers = parser.add_subparsers(dest='command', title='commands',
                                       description='Valid commands:',
                                       help="Run 'dolphin-logger <command> -h' for more information on a specific command.")
    subparsers.required = False # Make subcommands optional, so default behavior can be server

    # Server command (default if no command is specified)
    server_parser = subparsers.add_parser('server', help='Run the proxy server (default action if no command is given).')
    server_parser.add_argument('--port', type=int, default=None, help='Port to run the server on (default: 5001, or PORT environment variable)')

    # Upload command
    upload_parser = subparsers.add_parser('upload', help='Upload logs to Hugging Face Hub.')
    # upload_parser.set_defaults(func=_run_upload_command)

    # Init command
    init_parser = subparsers.add_parser('init', help='Initialize dolphin-logger configuration (create default config.json).')
    # init_parser.set_defaults(func=_handle_init_command) # Link to handler

    # Config command
    config_parser = subparsers.add_parser('config', help='Manage or inspect configuration.')
    config_parser.add_argument('--path', action='store_true', help='Show the expected path to the configuration file.')
    config_parser.add_argument('--validate', action='store_true', help='Validate the current configuration file.')
    # config_parser.set_defaults(func=_handle_config_command_with_args) # Link to handler that takes args

    args = parser.parse_args()

    # --- Command Dispatching ---
    command_to_run = args.command
    if command_to_run is None: # If no command is specified, default to 'server'
        command_to_run = 'server'

    # Initialize configuration for server and upload commands.
    # For 'init' and 'config --path', it's not strictly needed beforehand,
    # but it doesn't hurt as get_config_dir() ensures the directory exists.
    # 'config --validate' relies on load_config().
    if command_to_run in ['server', 'upload']:
        try:
            print("Initializing Dolphin Logger configuration for server/upload...")
            load_config() # Ensures config dir exists, default config is copied if needed, and ENV vars are processed for server.
            print("Configuration check/setup complete for server/upload.")
        except Exception as e:
            print(f"Error during configuration initialization for {command_to_run}: {e}")
            print("Please check your setup. Exiting.")
            return

    # Dispatch based on command
    if command_to_run == 'server':
        print("Server mode activated.")
        try:
            # Handle port argument for server command
            port = None
            if hasattr(args, 'port') and args.port is not None:
                port = args.port
            run_server_main(port=port) 
        except Exception as e:
            print(f"An error occurred while trying to start the server: {e}")
    
    elif command_to_run == 'upload':
        print("Upload mode activated.")
        try:
            upload_logs()
        except Exception as e:
            print(f"An error occurred during log upload: {e}")

    elif command_to_run == 'init':
        _handle_init_command()

    elif command_to_run == 'config':
        _handle_config_command(args) # Pass all args, handler will use relevant ones

    # No 'else' needed if subparsers.required = True or if default is set,
    # but with required = False and a default command logic, this is fine.

if __name__ == '__main__':
    main_cli()
