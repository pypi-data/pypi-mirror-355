import { URLExt } from '@jupyterlab/coreutils';

import { ServerConnection } from '@jupyterlab/services';

export enum DownloadState {
  IDLE = 'IDLE',
  DOWNLOADING = 'DOWNLOADING',
  COMPLETED = 'COMPLETED',
  FAILED = 'FAILED',
}

export enum TerminalEventType {
  PROMPT = 'PROMPT',
  OUTPUT = 'OUTPUT',
  ERROR = 'ERROR',
}

export type DownloadModel = {
  state: DownloadState;
  terminalEvent: TerminalEventType;
  bytesReceived: number;
  totalBytes: number;
  percent: number;
};

export class POSDownloader {
  private ws: WebSocket | null;
  private oldState: DownloadState | null = null;
  private oldPercent: number = -1;
  private onStateChange: (state: DownloadState) => void;
  private onProgressChange: (progress: number) => void;

  constructor(
    onStateChange: (state: DownloadState) => void,
    onProgressChange: (progress: number) => void
  ) {
    this.ws = null;
    this.onStateChange = onStateChange;
    this.onProgressChange = onProgressChange;
  }

  public connect() {
    if (this.ws) return;
    const settings = ServerConnection.makeSettings();
    const requestUrl = URLExt.join(
      settings.baseUrl
        .replace('http://', 'ws://')
        .replace('https://', 'wss://'),
      '/jupyter-pieces/install/ws'
    );
    this.ws = new WebSocket(requestUrl);
    this.ws.onopen = () => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send('{"download": "True"}');
      }
    };
    this.ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as DownloadModel;
        if (data.state !== this.oldState) {
          this.onStateChange(data.state);
          this.oldState = data.state;
        }
        if (data.percent !== this.oldPercent && data.state === DownloadState.DOWNLOADING) {
          this.onProgressChange(data.percent);
          this.oldPercent = data.percent;
        }
        console.log('websocket message:', data);
      } catch (e) {
        console.log('websocket message error:', e);
      }
    };
    this.ws.onclose = () => {
      console.log('websocket closed');
      this.ws = null;
    };
    this.ws.onerror = (event) => {
      console.log('websocket error:', event);
      this.onStateChange(DownloadState.FAILED);
      this.ws = null;
    };
  }
  public cancel() {
    if (this.ws) {
      this.ws.send('{"download": "False"}');
      this.ws.close();
      this.ws = null;
    }
  }
}
