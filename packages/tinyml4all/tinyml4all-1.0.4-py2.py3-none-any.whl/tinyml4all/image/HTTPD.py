import os.path
import http.server
import socketserver
import time
import webbrowser
from threading import Thread
from urllib.parse import urlparse

from ulid import ULID

from tinyml4all.support import asset


class HTTPD(http.server.SimpleHTTPRequestHandler):
    """
    Request handler for capturing images
    """

    save_to = None
    tmpfile = None
    on_capture = None

    def do_GET(self):
        """
        Handle GET request
        :return:
        """
        url = urlparse(self.path)

        if url.path == "/" or url.path == "/":
            self.send_response(200)
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(asset("capture_image.html").encode())
        elif self.path.endswith(".jpg"):
            self.send_response(200)
            self.send_header("Content-type", "image/jpeg")
            self.end_headers()

            if not os.path.exists(self.tmpfile):
                # todo: display 404 image
                pass
            else:
                with open(self.tmpfile, "rb") as f:
                    self.wfile.write(f.read())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        """
        Handle POST request
        :return:
        """
        dest_name = os.path.join(self.save_to, f"{int(time.time() * 100)}.jpg")

        with open(dest_name, "wb") as dest:
            with open(self.tmpfile, "rb") as src:
                dest.write(src.read())

        self.send_response(200)
        self.end_headers()
        self.wfile.write(f"Saved to {dest_name}".encode())

        if self.on_capture:
            self.on_capture()

    def log_message(self, format, *args):
        pass


# Enable TCP server to handle requests in separate threads
class ThreadedHTTPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    daemon_threads = True
    allow_reuse_address = True


def httpd_factory(**kwargs) -> type:
    """
    Configure HTTPD class
    :return:
    """
    return type(f"HTTPD_{ULID()}", (HTTPD,), kwargs)


def httpd_start(
    save_to: str, tmpfile, on_capture: callable = None
) -> ThreadedHTTPServer:
    """
    Start HTTPD
    :return:
    """
    httpd_class = httpd_factory(save_to=save_to, tmpfile=tmpfile, on_capture=on_capture)

    for port in range(8000, 8010):
        try:
            httpd = ThreadedHTTPServer(("127.0.0.1", port), httpd_class)
            thread = Thread(target=httpd.serve_forever)
            thread.daemon = True
            thread.start()
            print(f"HTTP server listening at port {port}")
            webbrowser.open_new_tab(f"http://127.0.0.1:{port}")

            return httpd
        except (PermissionError, OSError) as e:
            pass
