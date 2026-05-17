"""Entry point for ``python -m mood.server``."""
# если сервер не запускается: lsof -ti :1111 | xargs kill
from mood.server.app import start_server


def main():
    """Run the MOOD server."""
    start_server()


if __name__ == "__main__":
    main()
