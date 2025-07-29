import os
import sys

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

import asyncio
import argparse
import json
from .server import main
from .scheduler.schedule import scheduler_main

# Path to your config file (adjust as needed)
CONFIG_PATH = os.path.join(os.path.dirname(__file__),"Agent", "config", "mcp_servers_config.json")

# Load environment variables from the config file
def load_env_from_json(json_path):
    with open(json_path, 'r') as f:
        config = json.load(f)
    for key, value in config.items():
        os.environ[key] = str(value)
    return config
 
def main():
    """Synchronous entry point for console scripts"""
    from .server import main as server_main
    asyncio.run(server_main())



# async def run_concurrently():
    
#     # Step 1: Create parser for mode
#     parser = argparse.ArgumentParser(description="Run MCP services")
#     parser.add_argument(
#         "mode",
#         choices=["server", "scheduler", "both"],
#         default="server",
#         nargs="?",
#         help="Select which component to run"
#     )

#     # Step 2: Parse known args
#     args, remaining_args = parser.parse_known_args()

#     # Step 3: Override sys.argv so any other config parsing still works
#     sys.argv = [sys.argv[0]] + remaining_args
#     print("running with args:", args)

#     # Step 4: Dispatch
#     if args.mode == "scheduler":
#         print("Running scheduler...")
#         await scheduler_main()
#     else:
#         print("Running main server...")
#         main()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run MCP services")
    parser.add_argument(
        "mode",
        choices=["server", "scheduler", "both"],
        default="server",
        nargs="?",
        help="Select which component to run"
    )

    # Step 2: Parse known args
    args, remaining_args = parser.parse_known_args()

    # Step 3: Override sys.argv so any other config parsing still works
    sys.argv = [sys.argv[0]] + remaining_args
    print("running with args:", args)

    # Step 4: Dispatch
    if args.mode == "scheduler":
        print("Running scheduler...")
        asyncio.run(scheduler_main())
    else:
        print("Running main server...")
        main()

    


