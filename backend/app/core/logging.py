import logging


def configure_logging() -> None:
    """Configure simple application logging without logging secrets or submitted content."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
