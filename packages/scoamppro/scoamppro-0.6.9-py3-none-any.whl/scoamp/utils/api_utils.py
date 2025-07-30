import json
import hmac
import base64
import requests
import platform
from enum import Enum
from requests import PreparedRequest
from hashlib import sha256
from wsgiref.handlers import format_date_time
from datetime import datetime
from time import mktime
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Union

# from scoamp import __version__
from .helper import get_session
from .error import NotLoginError

# import http
# import logging
# logging.basicConfig()
# logging.getLogger().setLevel(logging.DEBUG)
# requests_log = logging.getLogger("requests.packages.urllib3")
# requests_log.setLevel(logging.DEBUG)
# requests_log.propagate = True
# http.client.HTTPConnection.debuglevel = 1


DEFAULT_ENDPOINT = "https://amp.sensecoreapi.cn"
TECH_ENDPOINT = "https://amp.sensecoreapi.tech"
DEV_ENDPOINT = "https://amp.sensecoreapi.dev"

PROTO = "HTTP/1.1"
PATH_PREFIX = "/studio/amp/data"

CACHE_ROOT = Path("~/.cache/scoamp").expanduser()
CACHE_ROOT.mkdir(parents=True, exist_ok=True)
ENV_PATH = CACHE_ROOT / "env.json"

PAGE_MAX = 200


class ApiEnv(str, Enum):
    standard = "standard"
    tech = "tech"
    dev = "dev"
    custom = "custom"

    def endpoint(self):
        if self is ApiEnv.standard:
            return DEFAULT_ENDPOINT
        elif self is ApiEnv.tech:
            return TECH_ENDPOINT
        elif self is ApiEnv.dev:
            return DEV_ENDPOINT
        else:
            return None


@dataclass
class AuthInfo:
    endpoint: str
    access_key: str
    secret_key: str
    path_prefix: bool

    def asdict(self):
        return asdict(self)


def amp_api_path(path: str, path_prefix: bool):
    if path_prefix:
        return PATH_PREFIX + path
    else:
        return path


def _request_line(method: str, path_url: str):
    return " ".join((method, path_url, PROTO))


def _gen_signature(data: str, key: str):
    key = key.encode("utf-8")
    data = data.encode("utf-8")
    sign = base64.b64encode(hmac.new(key, data, digestmod=sha256).digest())
    sign = str(sign, "utf-8")
    return sign


def _http_timeformat_now():
    return format_date_time(mktime(datetime.now().timetuple()))


def sign_req(prepped: PreparedRequest, access_key: str, secret_key: str):
    method, path_url = prepped.method, prepped.path_url
    req_line = _request_line(method, path_url)
    xdate = _http_timeformat_now()
    xdate_str = f"date: {xdate}"

    sign_data = "\n".join((xdate_str, req_line))
    sign = _gen_signature(sign_data, secret_key)
    auth = f'hmac accesskey="{access_key}", algorithm="hmac-sha256", headers="date request-line", signature="{sign}"'

    prepped.headers["Date"] = xdate
    prepped.headers["Authorization"] = auth


def get_env_cfg():
    with open(ENV_PATH) as f:
        return json.load(f)


def _persist_env(env_cfg):
    with open(ENV_PATH, "w") as f:
        json.dump(env_cfg, f, indent=4)


def switch_env(env_name: str):
    env_cfg = get_env_cfg()

    if env_name not in env_cfg["envs"]:
        raise Exception("invalid env name")

    env_cfg["use"] = env_name
    _persist_env(env_cfg)


def save_auth(
    env_name: str, endpoint: str, access_key: str, secret_key: str, path_prefix: bool
):
    env_cfg = {"use": "", "envs": {}}
    if ENV_PATH.exists():
        try:
            env_cfg = get_env_cfg()
        except json.decoder.JSONDecodeError:
            print("WARNING: invalid env cache, will be overrided")
    env_cfg["envs"][env_name] = {
        "endpoint": endpoint,
        "access_key": access_key,
        "secret_key": secret_key,
        "path_prefix": path_prefix,
    }
    env_cfg["use"] = env_name
    _persist_env(env_cfg)


def load_auth(env: str = None) -> AuthInfo:
    try:
        env_cfg = get_env_cfg()
        if not env:
            env = env_cfg["use"]
        return AuthInfo(**env_cfg["envs"][env])
    except (FileNotFoundError, KeyError):
        raise NotLoginError


def make_request(
    access_key,
    secret_key,
    method,
    url,
    params=None,
    json=None,
    headers=None,
    stream=False,
    allow_redirects=True,
    timeout=None,
):
    assert (
        access_key and secret_key
    ), "'access_key' and 'secret_key' should not be empty"
    sess = get_session()
    req = requests.Request(method=method, url=url, params=params, json=json)
    req = sess.prepare_request(req)
    sign_req(req, access_key, secret_key)
    if headers:
        req.headers.update(headers)

    kwargs = {
        "stream": stream,
        "allow_redirects": allow_redirects,
    }
    if timeout:
        kwargs["timeout"] = timeout

    return sess.send(req, **kwargs)


def get_user_agent(
    user_agent: Union[dict, str, None] = None,
) -> str:
    """Formats a user-agent string with basic info about a request.

    Args:
        user_agent (`str`, `dict`, *optional*):
            The user agent info in the form of a dictionary or a single string.

    Returns:
        The formatted user-agent string.
    """

    ua = "python/%s; platform/%s; processor/%s" % (
        platform.python_version(),
        platform.platform(),
        platform.processor(),
    )
    if isinstance(user_agent, dict):
        ua += "; " + "; ".join(f"{k}/{v}" for k, v in user_agent.items())
    elif isinstance(user_agent, str):
        ua += "; " + user_agent
    return ua
