import json
import logging
import os
import requests
from websockets import Origin
from websockets.sync.client import connect
import tomllib
from urllib.parse import urlparse


DEFAULT_CONFIG_PATH = "~/.config/hubkit/config.toml"
CONFIG_PATH_ENV_VAR = "HUBKIT_CONFIG_PATH"


if CONFIG_PATH_ENV_VAR in os.environ:
    DEFAULT_CONFIG_PATH = os.environ[CONFIG_PATH_ENV_VAR]

if not os.path.exists(os.path.expanduser(DEFAULT_CONFIG_PATH)):
    logging.error(f"Config file not found at {DEFAULT_CONFIG_PATH}. Please create it with the required settings.")
    exit(1)

with open(os.path.expanduser(DEFAULT_CONFIG_PATH), "rb") as f:
    try:
        config = tomllib.load(f)
    except tomllib.TOMLDecodeError as e:
        exit(1)



server_url = config.get('server', {}).get('url')
requestbin_app = config.get('requestbin', {}).get('app')
access_token = config.get('requestbin', {}).get('access_token')

if server_url is None or requestbin_app is None or access_token is None:
    exit(1)




class requestbin:
    def __init__(self, requestbin_id: int, logging_level=logging.WARN):
        logging.basicConfig(format="%(asctime)s %(message)s", level=logging_level)
        self.requestbin_id = requestbin_id
        self.websocket = None

    def __enter__(self):
        self.websocket = connect(uri=f"wss://{urlparse(server_url)._replace(schema='wss').geturl()}/app/{requestbin_app}?protocol=7&client=js&version=8.4.0&flash=false",
                                 origin=Origin(server_url))

        socket_id = json.loads(json.loads(self.websocket.recv())['data'])['socket_id']

        response = requests.post(f"{server_url}/api/broadcasting/auth",
                                 data={"socket_id": socket_id, "channel_name": f"private-requestbin.{self.requestbin_id}.events"},
                                 headers={"Authorization": f"Bearer {access_token}"},
                                 allow_redirects=False)

        if response.status_code != 200:
            logging.error(f"Failed to authenticate socket: {response.status_code} - {response.text}")

        auth = response.json()['auth']

        self.websocket.send(json.dumps({"event": "pusher:subscribe", "data": {"auth": auth,
                                                                              "channel": f"private-requestbin.{self.requestbin_id}.events"}}))

        message = json.loads(self.websocket.recv())
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.websocket:
            self.websocket.close()

    def recv(self, timeout: int = None):
        if self.websocket:
            data = json.loads(json.loads(self.websocket.recv(timeout=timeout, ))['data'])['event']

            class RequestResponse:
                def __init__(self, data):
                    self.id = data['id']
                    self.created_at = data['created_at']
                    self.url = data['url']
                    self.method = data['method']
                    self.body = data['body']
                    self.headers = data['headers']

                def __str__(self):
                    return f"RequestResponse(id={self.id}, created_at={self.created_at}, url={self.url}, method={self.method}, body={self.body}, headers={self.headers})"

            return RequestResponse(data)
        return None
