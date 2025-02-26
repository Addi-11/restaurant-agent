import logging


def setup_logging():
    logging.basicConfig(
        format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO
    )
    return logging.getLogger("RestaurantAssistant")


# Initialize logger
logger = setup_logging()
