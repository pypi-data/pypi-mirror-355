import {
  AnchorsApi,
  ApplicationNameEnum,
  ApplicationsApi,
  CapabilitiesEnum,
  Configuration,
  ConfigurationParameters,
  ConnectorApi,
  Context,
  ConversationApi,
  PlatformEnum,
  SeededConnectorConnection,
  SeededConnectorTracking,
  SeededTrackedApplication,
  TrackRequest,
  AllocationsApi,
  ApplicationApi,
  AssetApi,
  AssetsApi,
  Configuration as CoreConfig,
  FormatApi,
  LinkifyApi,
  SearchApi,
  OSApi,
  UserApi,
  WellKnownApi,
  DiscoveryApi,
  QGPTApi,
  AnnotationApi,
  AnnotationsApi,
  ActivityApi,
  ActivitiesApi,
  ModelApi,
  ModelsApi,
} from '@pieces.app/pieces-os-client';
import Notifications from './Notifications';
import Constants from '../const';
import { getStored } from '../localStorageManager';

export default class ConnectorSingleton {
  private static instance: ConnectorSingleton;
  private _platform = process.platform;
  private _platformMap: { [key: string]: PlatformEnum } = {
    win32: PlatformEnum.Windows,
    darwin: PlatformEnum.Macos,
    linux: PlatformEnum.Linux,
  };

  public static _port: string | null = null;

  private constructor() {
    this.createApis();
  }

  public static getPort(): string {
    if (ConnectorSingleton.port !== '' && ConnectorSingleton.port !== null) {
      return ConnectorSingleton.port;
    }
    return this.portScanning();
  }

  static portScanning(): string {
    const numPorts = 34;
    const batchSize = 5; // Check 5 ports concurrently
    const ports = Array.from({ length: numPorts }, (_, i) => 39300 + i);

    // Split ports into batches
    for (let i = 0; i < ports.length; i += batchSize) {
      const batch = ports.slice(i, i + batchSize);
      const xhrRequests = batch.map((port) => {
        const xhr = new XMLHttpRequest();
        xhr.open('GET', `http://localhost:${port}/.well-known/health`, false);
        return { xhr, port };
      });

      // Execute batch concurrently
      for (const { xhr, port } of xhrRequests) {
        try {
          xhr.send();
          if (xhr.status === 200) {
            ConnectorSingleton.port = port.toString();
            return port.toString();
          }
        } catch {
          continue;
        }
      }
    }

    throw new Error('PiecesOS is not running');
  }

  private static set port(port: string | null) {
    if (port == ConnectorSingleton._port && port != null) return;

    // Update all sockets on Port changing
    ConnectorSingleton._port = port;
    ConnectorSingleton.getInstance().createApis();
  }

  private static get port() {
    return ConnectorSingleton._port;
  }

  public static getHost() {
    return `http://localhost:${ConnectorSingleton.getPort()}`;
  }

  public get parameters(): ConfigurationParameters {
    let host;
    try {
      host = ConnectorSingleton.getHost();
    } catch {
      host = 'http://localhost:39300';
    }
    return {
      basePath: host,
      fetchApi: fetch,
    };
  }

  public context!: Context;
  public configuration: Configuration = new Configuration(this.parameters);
  public api!: ConnectorApi;
  public conversationApi!: ConversationApi;
  public anchorsApi!: AnchorsApi;
  public modelApi!: ModelApi;
  public modelsApi!: ModelsApi;
  public searchApi!: SearchApi;
  public allocationsApi!: AllocationsApi;
  public applicationApi!: ApplicationApi;
  public applicationsApi!: ApplicationsApi;
  public linkifyApi!: LinkifyApi;
  public assetsApi!: AssetsApi;
  public formatApi!: FormatApi;
  public userApi!: UserApi;
  public osApi!: OSApi;
  public assetApi!: AssetApi;
  public DiscoveryApi!: DiscoveryApi;
  public wellKnownApi!: WellKnownApi;
  public QGPTApi!: QGPTApi;
  public annotationsApi!: AnnotationsApi;
  public annotationApi!: AnnotationApi;
  public activityApi!: ActivityApi;
  public activitiesApi!: ActivitiesApi;

  addHeader(application: string) {
    this.createApis(application);
  }

  private createApis(application?: string) {
    if (application) {
      (this.parameters.headers ??= {})['application'] = application;
    }

    this.configuration = new Configuration(this.parameters);

    const coreConfig = new CoreConfig({
      fetchApi: fetch,
      basePath: this.parameters.basePath,
      headers: this.parameters.headers,
    });

    this.api = new ConnectorApi(this.configuration);
    this.conversationApi = new ConversationApi(coreConfig);
    this.anchorsApi = new AnchorsApi(coreConfig);
    this.modelApi = new ModelApi(coreConfig);
    this.modelsApi = new ModelsApi(coreConfig);
    this.searchApi = new SearchApi(coreConfig);
    this.allocationsApi = new AllocationsApi(coreConfig);
    this.applicationApi = new ApplicationApi(coreConfig);
    this.applicationsApi = new ApplicationsApi(coreConfig);
    this.linkifyApi = new LinkifyApi(coreConfig);
    this.assetsApi = new AssetsApi(coreConfig);
    this.formatApi = new FormatApi(coreConfig);
    this.userApi = new UserApi(coreConfig);
    this.osApi = new OSApi(coreConfig);
    this.assetApi = new AssetApi(coreConfig);
    this.DiscoveryApi = new DiscoveryApi(coreConfig);
    this.wellKnownApi = new WellKnownApi(coreConfig);
    this.QGPTApi = new QGPTApi(coreConfig);
    this.annotationsApi = new AnnotationsApi(coreConfig);
    this.annotationApi = new AnnotationApi(coreConfig);
    this.activityApi = new ActivityApi(coreConfig);
    this.activitiesApi = new ActivitiesApi(coreConfig);
  }

  public application: SeededTrackedApplication = {
    name: ApplicationNameEnum.JupyterHub,
    version: Constants.PLUGIN_VERSION,
    platform: this._platformMap[this._platform] || PlatformEnum.Unknown,
    capabilities: getStored('Capabilities')
      ? getStored('Capabilities')
      : CapabilitiesEnum.Blended,
  };

  public seeded: SeededConnectorConnection = {
    application: this.application,
  };

  public static getInstance(): ConnectorSingleton {
    if (!ConnectorSingleton.instance) {
      ConnectorSingleton.instance = new ConnectorSingleton();
    }

    return ConnectorSingleton.instance;
  }

  public static async checkConnection({
    notification = true,
  }: {
    notification?: boolean;
  }): Promise<boolean> {
    try {
      await fetch(
        `http://localhost:${ConnectorSingleton.port}/.well-known/health`
      );
      return true;
    } catch (e) {
      const notifications = Notifications.getInstance();
      // if notification is set to false we will ignore and just return false.
      if (notification) {
        notifications.information({
          message: Constants.CORE_PLATFORM_MSG,
        });
      }
      return false;
    }
  }

  public async track(event: SeededConnectorTracking): Promise<boolean> {
    const { context, api } = this;

    if (!context) {
      throw new Error('Application context could not be found when calling');
    }

    const seededConnectorTracking: SeededConnectorTracking = { ...event };

    const seed: TrackRequest = {
      application: context.application.id,
      seededConnectorTracking,
    };
    return api
      .track(seed)
      .then((_) => true)
      .catch((error) => {
        // TODO send this to sentry. and extract the actual error from the error.(ie error.message)
        console.log(`Error from api.track Error: ${error}`);
        return false;
      });
  }
}
