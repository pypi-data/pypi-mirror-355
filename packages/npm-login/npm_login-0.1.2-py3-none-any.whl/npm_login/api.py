import json
from urllib.error import HTTPError, URLError
from urllib import request, parse
from npm_login import io, utils

NPM_OTP_HEADER = 'Npm-otp'


def send_request(req):
    try:
        with request.urlopen(req) as resp:
            response = resp.read().decode('utf-8')
            return json.loads(response)
    except HTTPError as e:
        if e.code == 401 and not req.get_header(NPM_OTP_HEADER):
            otp = io.read_string('Enter OTP: ')
            io.validate_otp(otp)
            req.add_header(NPM_OTP_HEADER, otp)
            return send_request(req)
        else:
            io.error(f'{e.code} {e.reason}')
    except URLError as e:
        io.error(e.reason)


def login(base_url, username, password):
    path = f'-/user/org.couchdb.user:{parse.quote(username)}'
    url = parse.urljoin(base_url, path)
    data = {
        '_id': f'org.couchdb.user:{username}',
        'name': username,
        'password': password,
        'type': 'user',
        'roles': [],
        'date': utils.now(),
    }
    try:
        body = json.dumps(data).encode('utf-8')
        req = request.Request(
            url,
            data=body,
            method='PUT',
            headers={
                'content-type': 'application/json',
                'npm-auth-type': 'legacy',
                'npm-command': 'login',
            },
        )
        return send_request(req)
    except ValueError as e:
        io.error(e)
