import argparse
import ssl
from importlib.metadata import version
from logging import DEBUG, INFO
from npm_login import io, api, npmrc
from npm_login.logger import logger, green


def cli():
    parser = argparse.ArgumentParser(description='Login to a registry user account')
    parser.add_argument(
        '-r',
        '--registry',
        default='https://registry.npmjs.org/',
        help='the base URL of the NPM registry',
    )
    parser.add_argument('-d', '--debug', action='store_true', help='enable debugging mode')
    parser.add_argument('-v', '--version', action='version', version=version('npm-login'))
    args = parser.parse_args()
    logger.setLevel(DEBUG if args.debug else INFO)

    if args.debug:
        ssl._create_default_https_context = ssl._create_unverified_context
    if args.registry.strip() == '':
        io.error('Registry URL cannot be empty')

    BASE_URL = args.registry if args.registry.endswith('/') else f'{args.registry}/'
    logger.info(f'Log in on {green(BASE_URL)}')
    username = io.read_string('Username: ')
    io.validate_username(username)
    password = io.read_password()
    io.validate_password(password)
    data = api.login(BASE_URL, username, password)
    npmrc.write(BASE_URL, data['token'])


if __name__ == '__main__':
    cli()
