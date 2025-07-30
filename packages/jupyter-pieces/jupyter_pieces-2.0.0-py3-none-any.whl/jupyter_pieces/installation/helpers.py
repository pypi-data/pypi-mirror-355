import asyncio
import sys
import subprocess
from enum import Enum
from tempfile import gettempdir
import asyncio
import sys
import re
import time
from typing import Optional, Callable, List, Tuple
import tornado.httpclient
import tornado.ioloop
import tornado.websocket

class PlatformEnum(Enum):
    Windows = 'Windows'
    Linux = 'Linux'
    Macos = 'Macos'

class DownloadState(Enum):
    IDLE = 'IDLE'
    DOWNLOADING = 'DOWNLOADING'
    COMPLETED = 'COMPLETED'
    FAILED = 'FAILED'

class TerminalEventType(Enum):
    PROMPT = 'PROMPT'
    OUTPUT = 'OUTPUT'
    ERROR = 'ERROR'

class DownloadModel:
    def __init__(self, state: DownloadState, terminal_event: TerminalEventType , bytes_received: int = 0, total_bytes: int=0, percent: float=0):
        self.bytes_received = bytes_received
        self.total_bytes = total_bytes
        self.percent = percent
        self.state = state
        self.terminal_event = terminal_event

    def to_json(self):
        return {
            'bytes_received': self.bytes_received,
            'total_bytes': self.total_bytes,
            'percent': self.percent,
            'state': self.state.value,
            'terminal_event': self.terminal_event.value
        }

class PosDownloader:
    def __init__(self, callback: Optional[Callable[[DownloadModel], None]]):
        self.platform = self.detect_platform()
        self.download_process = None
        self.progress_update_callback = callback
        self.state = DownloadState.IDLE
        self.terminal_event = TerminalEventType.PROMPT
        self.stop = False
        self.last_progress_update = time.time()
        self.file = None

    async def update_progress(self, bytes_received: int = 0, total_bytes: int = 0, force=False):
        now = time.time()

        if (now - self.last_progress_update) < 0.5 and force==False: # Only update every 0.5 seconds
            return
        self.last_progress_update = now
        if self.progress_update_callback:
            if total_bytes == 0:
                percent = 0
            else:
                percent = (bytes_received / total_bytes) * 100
            progress = DownloadModel(self.state, self.terminal_event, bytes_received, total_bytes, percent)
            try:
                self.progress_update_callback(progress)
            except tornado.websocket.WebSocketClosedError:
                await self.cancel_download()

    @staticmethod
    def detect_platform() -> PlatformEnum:
        if sys.platform == 'win32':
            return PlatformEnum.Windows
        elif sys.platform == 'linux':
            return PlatformEnum.Linux
        else:
            return PlatformEnum.Macos

    def start_download(self) -> bool:
        if self.state == DownloadState.DOWNLOADING:
            return False

        self.state = DownloadState.DOWNLOADING

        tornado.ioloop.IOLoop.current().add_callback(self._start_download)

        return True

    async def _start_download(self):
        await self.update_progress()

        self.stop = False
        try:
            if self.platform == PlatformEnum.Windows:
                await self.download_windows()
            elif self.platform == PlatformEnum.Linux:
                await self.download_linux()
            elif self.platform == PlatformEnum.Macos:
                await self.download_macos()
        except Exception as e:
            print(f"Error: {e}")
            self.state = DownloadState.FAILED
            await self.update_progress()

    async def download_linux(self):
        self.print('Starting POS download for Linux.')
        command = '''
            if command -v pkexec >/dev/null 2>&1; then
              pkexec snap install pieces-os && \
              pkexec snap connect pieces-os:process-control :process-control && \
              pieces-os
            else
              echo "Error: pkexec is not available. Exiting." >&2
              exit 1
            fi
        '''
        await self.execute_command('bash', '-c', [command], self.extract_linux_regex)

    def extract_linux_regex(self, line) -> Optional[Tuple[int, int]]:
        pattern = r"(\d+)%\s+([\d.]+)MB/s\s+([\dms.]+)"

        match = re.search(pattern, line)

        if match:
            percentage = match.group(1)
            download_speed = match.group(2)
            time_remaining = match.group(3)
            total_bytes = int(download_speed) * int(time_remaining)
            bytes_downloaded = (int(percentage) / 100) * total_bytes

            return bytes_downloaded, total_bytes

    async def download_macos(self):
        self.print('Starting POS download for Macos.')
        
        arch = 'arm64' if sys.maxsize > 2**32 else 'x86_64'
        pkg_url = f'https://builds.pieces.app/stages/production/macos_packaging/pkg-pos-launch-only-{arch}/download?product=JUPYTER_LAB&download=true'
        tmp_pkg_path = "/tmp/Pieces-OS-Launch.pkg"
        await self.install_using_web(pkg_url, tmp_pkg_path)

    async def download_windows(self):
        self.print('Starting POS download for Windows.')
        pkg_url = 'https://builds.pieces.app/stages/production/os_server/windows-exe/download?download=true&product=JUPYTER_LAB'
        tmp_pkg_path = f"{gettempdir()}\\Pieces-OS.exe"
        await self.install_using_web(pkg_url, tmp_pkg_path)

    def on_chunk(self, chunk):
        if not chunk:
            return self.on_done()
        if self.stop:
            print("Download stopped by user.")
            self.state = DownloadState.IDLE
            self.http_client.close()
            tornado.ioloop.IOLoop.current().add_callback(self.update_progress)
            raise TimeoutError("Closed closed by the user")

        self.file.write(chunk)
        self.downloaded_size += len(chunk)

        tornado.ioloop.IOLoop.current().add_callback(lambda: self.update_progress(self.downloaded_size, self.file_size))
        self.print(f'Downloaded {self.downloaded_size} of {self.file_size}')
        if self.downloaded_size == self.file_size:
            self.on_done()
    
    def on_done(self):
        self.file.close()
        self.state = DownloadState.COMPLETED
        tornado.ioloop.IOLoop.current().add_callback(lambda: self.update_progress(force=True))

        self.print(f'Download completed. Opening {self.tmp_pkg_path}.')

        if sys.platform == 'win32':
            subprocess.run(['start', self.tmp_pkg_path], shell=True)
        else:
            subprocess.run(['open', self.tmp_pkg_path])

    def update_header(self, header):
        if 'Content-Length' in header:
            self.file_size = int(header.split(':')[1].strip())

    async def install_using_web(self, pkg_url: str, tmp_pkg_path: str):
        try:
            self.http_client = tornado.httpclient.AsyncHTTPClient(force_instance=True, max_body_size=1000000000)
            self.tmp_pkg_path = tmp_pkg_path
            if self.file:
                self.file.close()
            self.file = open(tmp_pkg_path, 'wb')
            self.downloaded_size = 0
            self.file_size = 0
            self.request = tornado.httpclient.HTTPRequest(pkg_url, headers={'Accept': '*/*'}, streaming_callback=self.on_chunk, header_callback=self.update_header, request_timeout=0)
            await self.http_client.fetch(self.request)

        except Exception as e:
            self.state = DownloadState.FAILED
            await self.update_progress()
            self.print(f'Unexpected error during download: {e}')
            return False


    async def execute_command(self, shell: str, command: str, args: List[str], callback: Optional[Callable[[str], Tuple[int, int]]]) -> bool:
        try:
            self.print(f'Spawning process: {shell} {command} {args}')
            self.download_process = subprocess.Popen(
                [shell, command] + args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            while True:
                out = self.download_process.stdout.readline()
                err = self.download_process.stderr.readline()

                if out:
                    self.state = DownloadState.DOWNLOADING
                    self.terminal_event = TerminalEventType.OUTPUT
                    try:
                        bytes_received, total_bytes = callback(out.decode('utf-8'))
                        await self.update_progress(bytes_received, total_bytes)
                    except Exception as e:
                        self.print(f"Could not match pattern: {e}", file=sys.stderr)

                if err:
                    self.terminal_event = TerminalEventType.ERROR
                    await self.update_progress(bytes_received=0, total_bytes=0)
                    self.print(err.decode('utf-8'), file=sys.stderr)

                if self.download_process.poll() is not None:
                    break

            self.download_process.wait()
            self.print('Process completed.')
            return self.download_process.returncode == 0
        except Exception as e:
            self.print(f'Error executing command: {e}')
            self.state = DownloadState.FAILED
            await self.update_progress()
            return False

    def cancel_download(self) -> None:
        self.stop = True
        if self.state == DownloadState.DOWNLOADING:
            if self.download_process:
                self.download_process.kill()
                tornado.ioloop.IOLoop.current().add_callback(self.update_progress_stop)
            else:
                self.file.close()

    async def update_progress_stop(self) -> None:
        self.state = DownloadState.IDLE
        self.terminal_event = TerminalEventType.OUTPUT
        await self.update_progress()
        self.print('Download canceled.')

    def print(self, message, file=sys.stdout):
        print(message, file=file)
