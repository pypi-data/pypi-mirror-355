import re
from getpass import getpass
from typing import NoReturn
from npm_login.logger import logger


def error(message, exit_code=1) -> NoReturn:
    logger.error(message)
    exit(exit_code)


def read_string(value):
    try:
        return input(value)
    except (EOFError, KeyboardInterrupt):
        exit()


def read_password():
    try:
        return getpass()
    except (EOFError, KeyboardInterrupt):
        exit()


def validate_username(value):
    if value == '':
        error('Username cannot be empty')
    if re.search(r'\s', value):
        error('Username cannot contain whitespace characters')


def validate_password(value):
    if value == '':
        error('Password cannot be empty')
    if value.strip() == '':
        error('Password cannot contain only whitespace characters')


def validate_otp(value):
    if len(value) != 6:
        error('OTP is invalid')
