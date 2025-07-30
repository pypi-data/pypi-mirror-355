import logging

gray = '\x1b[38;5;244m'
yellow = '\x1b[33;20m'
red = '\x1b[31;20m'
bold_red = '\x1b[31;1m'
reset = '\x1b[0m'


def green(string: str):
    return f'\x1b[32;20m{string}{reset}'


def format(color: str | None):
    if color:
        return f'{color}%(levelname)s: %(message)s{reset}'
    return '%(levelname)s: %(message)s'


FORMATS = {
    logging.DEBUG: format(gray),
    logging.INFO: format(None),
    logging.WARNING: format(yellow),
    logging.ERROR: format(red),
    logging.CRITICAL: format(bold_red),
}


class Formatter(logging.Formatter):
    def format(self, record):
        fmt = FORMATS.get(record.levelno)
        formatter = logging.Formatter(fmt)
        return formatter.format(record)


handler = logging.StreamHandler()
handler.setFormatter(Formatter())
logging.basicConfig(handlers=[handler])
logger = logging.getLogger('npm-login')
