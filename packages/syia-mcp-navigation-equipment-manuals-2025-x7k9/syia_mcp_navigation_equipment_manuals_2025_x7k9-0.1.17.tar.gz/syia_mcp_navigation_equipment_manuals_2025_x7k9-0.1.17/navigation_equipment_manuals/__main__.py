import asyncio
import os
import sys

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def main():
    """Synchronous entry point for console scripts"""
    from .server import main as server_main
    asyncio.run(server_main())

if __name__ == "__main__":
    main()