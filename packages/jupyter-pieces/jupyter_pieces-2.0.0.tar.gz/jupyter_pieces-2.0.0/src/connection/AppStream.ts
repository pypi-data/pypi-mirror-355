import {
  Application,
  CapabilitiesEnum,
  StreamedIdentifiersFromJSON,
} from '@pieces.app/pieces-os-client';
import ConnectorSingleton from './connectorSingleton';
import { copilotParams } from '../ui/views/copilot/CopilotParams';
import { setStored } from '../localStorageManager';
import { PluginGlobalVars } from '../PluginGlobalVars';

export default class ApplicationStream {
  private static instance: ApplicationStream;

  private ws: WebSocket | null = null;

  /**
   * Private constructor to initialize the object and establish a connection.
   * This constructor is typically used in singleton patterns to prevent
   * external instantiation.
   */
  private constructor() {
    this.connect();
  }

  /**
   * Closes the WebSocket connection if it is open and sets the WebSocket instance to null.
   */
  public closeSocket() {
    this.ws?.close();
    this.ws = null;
  }

  /**
   * Establishes a WebSocket connection if one does not already exist.
   * Constructs the WebSocket URL based on the basePath parameter, replacing
   * the protocol with 'wss://' or 'ws://', and appending the specific path for the stream.
   * Sets up event handlers for message reception, error, and close events.
   */
  private connect() {
    if (this.ws !== null) return;
    const url =
      (
        ConnectorSingleton.getHost()
      )
        .replace('https://', 'wss://')
        .replace('http://', 'ws://') + '/applications/stream/identifiers';

    this.ws = new WebSocket(url);

    /**
     * Event handler for WebSocket 'onmessage' event.
     *
     * @param {MessageEvent} event - The message event received from the WebSocket.
     */
    this.ws.onmessage = (event) => this.updateSettings(event);

    /**
     * Refreshes the WebSocket connection.
     * If an error is provided, it logs the error to the console.
     *
     * @param {any} [error] - Optional error object to log.
     */
    const refreshSockets = (error?: any) => {
      if (error) console.error(error);
      this.ws = null;
    };
    // on error or close, reject the 'handleMessage' promise, and close the socket.
    this.ws.onerror = refreshSockets;
    this.ws.onclose = refreshSockets;
  }

  /**
   * Updates the settings based on the received message event.
   *
   * @param {MessageEvent} event - The message event containing the data to update settings.
   * @returns {Promise<void>} - A promise that resolves when the settings update is complete.
   */
  private async updateSettings(event: MessageEvent): Promise<void> {
    const identifiers = StreamedIdentifiersFromJSON(JSON.parse(event.data));

    const storedApplication = await copilotParams.getApplication();

    if (!storedApplication) return;

    if (
      !identifiers.iterable.some(
        (el) => el.application?.id === storedApplication.id
      )
    )
      return;

    const application =
      await ConnectorSingleton.getInstance().applicationsApi.applicationsSpecificApplicationSnapshot(
        { application: storedApplication.id }
      );

    this.updateCapabilties(application);
  }

  /**
   * Updates the cloud capabilities configuration for each target in the workspace.
   *
   * @param {Application} application - The application object containing the capabilities to be updated.
   * @returns {Promise<void>} - A promise that resolves when the update is complete.
   */
  private async updateCapabilties(application: Application): Promise<void> {
    const settingValue =
      application.capabilities === CapabilitiesEnum.Blended
        ? 'Blended'
        : 'Local';
    PluginGlobalVars.pluginSettings.set('Capabilities', settingValue);
    setStored({
      Capabilities: settingValue,
    });
  }

  public static getInstance() {
    return (this.instance ??= new ApplicationStream());
  }
}
