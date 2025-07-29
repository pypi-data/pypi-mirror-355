import urllib.error
import fileinput
import argparse
import json
import re
import ssl
from pathlib import Path
from urllib import request, parse
from getpass import getpass
from datetime import datetime, timezone
from typing import NoReturn


def error(message, exit_code=1) -> NoReturn:
    print(f'\033[91mERROR: {message}\033[0m')
    exit(exit_code)


def info(message):
    print(f'INFO: {message}')


def green(string):
    return f'\033[92m{string}\033[0m'


def read_value(prompt):
    try:
        return input(prompt)
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


def create_request(url, data):
    try:
        body = json.dumps(data).encode('utf-8')
        return request.Request(
            url,
            data=body,
            method='PUT',
            headers={
                'content-type': 'application/json',
                'npm-auth-type': 'legacy',
                'npm-command': 'login',
                'npm-otp': '321004',
            },
        )
    except ValueError as e:
        error(e)


def send_request(req: request.Request):
    try:
        with request.urlopen(req) as resp:
            response = resp.read().decode('utf-8')
            return json.loads(response)
    except urllib.error.HTTPError as e:
        if e.code == 401 and not req.get_header('npm-otp'):
            otp = read_value('Enter OTP: ')
            validate_otp(otp)
            req.add_header('npm-otp', otp)
            return send_request(req)
        else:
            error(f'{e.code} {e.reason}')
    except urllib.error.URLError as e:
        error(e.reason)


def write_npmrc(url, token):
    url_object = parse.urlparse(url)
    url_without_scheme = url.removeprefix(f'{url_object.scheme}:')
    search = f'//{url_object.netloc}'
    content = f'{url_without_scheme}:_authToken={token}'
    file_path = Path.home() / '.npmrc'
    is_written = False
    if file_path.exists():
        with fileinput.input(file_path, inplace=True) as file:
            for line in file:
                if line.startswith(search):
                    print(content)
                    is_written = True
                else:
                    print(line, end='')
    if not is_written:
        with open(file_path, 'a') as file:
            file.write(f'{content}\n')
    info(f'{green(file_path)} updated successfully')


def main():
    parser = argparse.ArgumentParser(description='Login to a registry user account')
    parser.add_argument(
        '--registry', default='https://registry.npmjs.org/', help='the base URL of the npm registry'
    )
    parser.add_argument('--debug', action='store_false', help='enable debugging mode')
    args = parser.parse_args()
    if args.debug:
        ssl._create_default_https_context = ssl._create_unverified_context
    if args.registry.strip() == '':
        error('Registry URL cannot be empty')

    URL = args.registry if args.registry.endswith('/') else f'{args.registry}/'
    info(f'Log in on {green(URL)}')
    username = read_value('Username: ')
    validate_username(username)
    password = read_password()
    validate_password(password)

    path = f'-/user/org.couchdb.user:{parse.quote(username)}'
    url = parse.urljoin(URL, path)
    data = {
        '_id': f'org.couchdb.user:{username}',
        'name': username,
        'password': password,
        'type': 'user',
        'roles': [],
        'date': datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z'),
    }
    req = create_request(url, data)
    data = send_request(req)
    write_npmrc(URL, data['token'])


if __name__ == '__main__':
    main()
