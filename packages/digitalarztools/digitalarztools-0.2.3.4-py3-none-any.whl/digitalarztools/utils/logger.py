import logging
from colorama import Fore

class CustomFormatter(logging.Formatter):
    format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s (%(filename)s:%(lineno)d)"

    FORMATS = {
        logging.DEBUG: Fore.WHITE + format + Fore.RESET,
        logging.INFO: Fore.CYAN + format + Fore.RESET,
        logging.WARNING: Fore.YELLOW + format + Fore.RESET,
        logging.ERROR: Fore.RED + format + Fore.RESET,
        logging.CRITICAL: Fore.MAGENTA + format + Fore.RESET,
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        return logging.Formatter(log_fmt, "%Y-%m-%d %H:%M:%S").format(record)

def get_da_logger(name="DigitalArz", level=logging.DEBUG):
    logger = logging.getLogger(name)
    logger.setLevel(level)  # 👈 Set log level here

    if not logger.handlers:
        ch = logging.StreamHandler()
        ch.setLevel(level)
        ch.setFormatter(CustomFormatter())
        logger.addHandler(ch)

    logger.propagate = False  # prevent double logging
    return logger

da_logger = get_da_logger()

da_logger.info("Logger is working!")  # ✅ Will show colored output in PyCharm