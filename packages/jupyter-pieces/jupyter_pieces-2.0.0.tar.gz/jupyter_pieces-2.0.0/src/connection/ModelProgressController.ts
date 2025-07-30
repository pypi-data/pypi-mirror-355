import {
  Model,
  ModelDownloadProgressFromJSON,
  ModelDownloadProgressStatusEnum,
  ModelFoundationEnum,
  Models,
} from '@pieces.app/pieces-os-client';
import ConnectorSingleton from './connectorSingleton';
import Notifications from './Notifications';

export default class ModelProgressController {
  private static instance: ModelProgressController;

  public modelDownloadStatus = new Map<
    string,
    ModelDownloadProgressStatusEnum
  >(); // status of all relevant model downloads

  public models: Promise<Models>; // models snapshot

  private callbacks: Array<() => void> = new Array<() => void>(); // all callbacks to be ran from a websocket event

  private sockets: { [key: string]: WebSocket } = {}; // model id -> its download socket

  /**
   * Initializes the sockets
   */
  private constructor() {
    const config = ConnectorSingleton.getInstance();
    this.models = config.modelsApi.modelsSnapshot();
    this.models.then((models) => {
      this.initSockets(
        models.iterable.filter(
          (el: Model) =>
            el.foundation === ModelFoundationEnum.Llama27B &&
            el.unique !== 'llama-2-7b-chat.ggmlv3.q4_K_M'
        )
      );
    });
  }

  /**
   * Registering a callback here will allow that callback to be executed during stream events
   * i.e refresh the LLMConfigModal once a download finishes
   * @param cb call back to be registered
   */
  public registerCallback(cb: () => void) {
    this.callbacks.push(cb);
  }

  /**
   * This will remove the callback from the list of registered callbacks
   * @param cb the call back to be deregistered
   */
  public deregisterCallback(cb: () => void) {
    this.callbacks = this.callbacks.filter((el) => el != cb);
  }

  /**
   * Cleanup function to close all sockets
   */
  public closeSockets() {
    for (const socket of Object.values(this.sockets)) {
      socket.close();
    }
  }

  /**
   * Opens all sockets for models that currently don't have a socket open
   * This is used to refresh sockets that had an error in connection
   * @param models all of the models to open a socket for progress
   */
  public openSockets(models: Model[]) {
    for (const model of models) {
      if (!this.sockets[model.id]) {
        this.connect(model);
      }
    }
  }

  /**
   * This opens all sockets via the constructor
   * @param models all models to initialize the sockets
   */
  private initSockets(models: Model[]) {
    for (const model of models) {
      this.connect(model);
    }
  }

  /**
   * This opens a socket, and handles all messaging / error handling needs for that model's socket
   * @param model The model to connect a socket
   */
  private connect(model: Model) {
    const ws: WebSocket = new WebSocket(
      (
				ConnectorSingleton.getHost()
			)
				.replace('https://', 'wss://')
				.replace('http://', 'ws://') + "/model/${model.id}/download/progress"
    );
    this.sockets[model.id] = ws;
    ws.onmessage = (evt) => {
      const event = ModelDownloadProgressFromJSON(JSON.parse(evt.data));

      const oldStatus = this.modelDownloadStatus.get(model.id);
      this.modelDownloadStatus.set(
        model.id,
        event.status ?? ModelDownloadProgressStatusEnum.Failed
      );

      // if the new status is the same as the status we have saved, or either of them are undefined, do nothing.
      if (
        oldStatus === event.status ||
        oldStatus === undefined ||
        event.status === undefined
      )
        return;

      if (event.status !== 'COMPLETED') return;

      if (event.status === 'COMPLETED') {
        model.downloaded = true;
        Notifications.getInstance().information({
          message: 'Model download success!',
        });
      }
      /**
       * Execute all callbacks that are registered
       */
      for (const cb of this.callbacks) {
        cb();
      }
    };

    const handleLostConnection = () => {
      delete this.sockets[model.id];

      if (ws.readyState !== ws.CLOSED && ws.readyState !== ws.CLOSING) {
        ws.close();
      }
    };
    /**
     * remove the socket from the current list of sockets if there is an error,
     * and make sure the socket is closed.
     */
    ws.onerror = handleLostConnection;
    ws.onclose = handleLostConnection;
  }

  public static getInstance() {
    return (this.instance ??= new ModelProgressController());
  }
}
