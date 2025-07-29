import logging

from dharitrietl.cli import cli

logging.basicConfig(level=logging.INFO, format="[%(threadName)s] [%(levelname)s] [%(module)s]: %(message)s")

if __name__ == "__main__":
    cli()
