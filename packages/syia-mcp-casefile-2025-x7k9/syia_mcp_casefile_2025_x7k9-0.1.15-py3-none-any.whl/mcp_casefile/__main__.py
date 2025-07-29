import asyncio

def main():
    """Synchronous entry point for console scripts"""
    from .server import main as server_main
    asyncio.run(server_main())

if __name__ == "__main__":
    main()