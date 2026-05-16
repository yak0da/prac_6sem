"""Entry point for ``python -m mood.server``."""

import asyncio

from mood.server.app import run_server


def main():
    """Run the MOOD server."""
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
