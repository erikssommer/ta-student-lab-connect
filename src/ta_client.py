import logging
from components.ta_component import TaClientComponent


if __name__ == '__main__':
    # logging.DEBUG: Most fine-grained logging, printing everything
    # logging.INFO:  Only the most important informational log items
    # logging.WARN:  Show only warnings and errors.
    # logging.ERROR: Show only error messages.
    debug_level = logging.INFO
    logger = logging.getLogger(__name__)
    logger.setLevel(debug_level)
    ch = logging.StreamHandler()
    ch.setLevel(debug_level)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)-12s - %(levelname)-8s - %(message)s')
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    # Create a new instance of the TA client component
    client = TaClientComponent(logger)
