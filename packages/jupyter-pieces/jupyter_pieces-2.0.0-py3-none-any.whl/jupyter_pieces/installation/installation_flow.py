
import json
from jupyter_server.utils import url_path_join
from tornado import web
from tornado.websocket import WebSocketHandler

from .helpers import PosDownloader, DownloadModel

class MessageModel:
    """Model for messages sent between the frontend and backend."""

    def __init__(self, download: bool):
        self.download = download

    def to_json(self) -> str:
        """Returns the message as a JSON string."""
        return json.dumps({
            "download": self.download
        })
    
    @staticmethod
    def from_json(json_string: str):
        """Converts a JSON string to a MessageModel object."""
        data = json.loads(json_string)
        return MessageModel(download=data["download"])


class InstallationHandler(WebSocketHandler):
    """Handles websocket messages for the jupyterlab-pieces extension."""

    def open(self):
        """Called when a new connection is established."""
        self.downloader = PosDownloader(self.send_data)

    def on_message(self, message):
        """Handles incoming messages."""
        print(f"Received message: {message}")
        try:
            m = MessageModel.from_json(message)
        except json.JSONDecodeError:
            self.write_message("Invalid JSON message")
            self.close(500)
            return
        if m.download:
            self.downloader.start_download()
        else:
            self.downloader.cancel_download()

    def on_close(self):
        """Called when the connection is closed."""
        self.downloader.cancel_download() # Clean ups
        print("Connection closed.")

    def send_data(self, data: DownloadModel):
        """Sends data to the client."""
        self.write_message(data.to_json())

class HealthHandler(web.RequestHandler):
    """Handles the /try endpoint."""
    def get(self):
        """Handles GET requests."""
        self.write("jupyterlab-pieces is installed correctly.")


def setup_handlers(web_app: web.Application):
    host_pattern = ".*$"

    base_url = web_app.settings["base_url"]

    route_pattern = url_path_join(base_url, "jupyter-pieces", "install", "ws")
    handlers = [(route_pattern, InstallationHandler)]
    web_app.add_handlers(host_pattern, handlers)


    try_url = url_path_join(base_url, "jupyter-pieces", "check")
    handlers = [(try_url, HealthHandler)]
    web_app.add_handlers(host_pattern, handlers)