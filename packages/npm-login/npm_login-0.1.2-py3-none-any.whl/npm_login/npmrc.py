import fileinput
from pathlib import Path
from urllib import parse
from npm_login.logger import logger, green

CONFIG_PATH = Path.home() / '.npmrc'


def write(base_url, token):
    url = parse.urlparse(base_url)
    url_without_scheme = base_url.removeprefix(f'{url.scheme}:')
    search = f'//{url.netloc}'
    content = f'{url_without_scheme}:_authToken={token}'
    is_written = False
    if CONFIG_PATH.exists():
        with fileinput.input(CONFIG_PATH, inplace=True) as file:
            for line in file:
                if not is_written and line.startswith(search):
                    print(content)
                    is_written = True
                else:
                    print(line, end='')
    if not is_written:
        with open(CONFIG_PATH, 'a') as file:
            file.write(f'{content}\n')
    logger.info(f'{green(str(CONFIG_PATH))} updated successfully')
