import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(funcName)s(): - %(message)s",
    handlers=[logging.StreamHandler()]
)