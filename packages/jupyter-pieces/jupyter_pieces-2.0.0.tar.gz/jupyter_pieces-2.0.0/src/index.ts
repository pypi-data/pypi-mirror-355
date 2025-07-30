import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin,
} from '@jupyterlab/application';
import { ICommandPalette } from '@jupyterlab/apputils';
import { showOnboarding } from './onboarding/showOnboarding';
import { PiecesView } from './ui/piecesView';
import { getStored, setStored } from './localStorageManager';
import { createCommands } from './actions/createCommands';
import * as Sentry from '@sentry/browser';
import { SentryTracking } from './analytics/SentryTracking';
import { ISettingRegistry } from '@jupyterlab/settingregistry';
import ConnectorSingleton from './connection/connectorSingleton';
import { SegmentAnalytics } from './analytics/SegmentAnalytics';
import { Heartbeat, pluginActivityCheck } from './analytics/Heartbeat';
import { IStateDB } from '@jupyterlab/statedb';
import PiecesCacheSingleton from './cache/piecesCacheSingleton';
import { stream } from './connection/streamAssets';
import CheckVersionAndConnection from './connection/checkVersionAndConnection';
import versionCheck from './connection/versionCheck';
import PiecesDB from './models/databaseModel';
import { returnedMaterial } from './models/typedefs';
import AnnotationHandler from './utils/annotationHandler';
import './globals';
import { ElementMap } from './models/ElementMap';
import ActivitySingleton from './actions/ActivitySingleton';
import { copilotParams } from './ui/views/copilot/CopilotParams';
import ApplicationStream from './connection/AppStream';
import { loadConnect } from './connection/apiWrapper';
import { PluginGlobalVars } from './PluginGlobalVars';
import { Applet } from './ui/views/shared/applet';
import { settingsAppletMessageHandler } from './ui/views/settings/messageHandler';
import { AppletWebviewMessageEnum } from './ui/views/shared/types/AppletMessageType.enum';
import { login } from './actions/login';
import Notifications from './connection/Notifications';
import { NotificationActionTypeEnum } from './ui/views/shared/types/NotificationParameters';
/**
 * Initialization data for the jupyter_pieces extension.
 */
export const pluginHeartbeat = new Heartbeat(5); // 5 minutes

const plugin: JupyterFrontEndPlugin<void> = {
  id: PluginGlobalVars.PLUGIN_ID + ':plugin',
  description:
    'Pieces for Developers is a code material management tool powered by AI.',
  autoStart: true,
  requires: [ICommandPalette, IStateDB],
  optional: [],
  deactivate: async () => {
    await Sentry.close(2000);
    pluginHeartbeat.stop();
  },
  activate: async (
    app: JupyterFrontEnd,
    palette: ICommandPalette,
    state: IStateDB
  ) => {
    createPrototypes();
    const cache = PiecesCacheSingleton.getInstance();
    versionCheck({ notify: true }); // Check for minimum version of POS

    PluginGlobalVars.theme = '';
    PluginGlobalVars.defaultApp = app;
    PluginGlobalVars.defaultState = state;

    const piecesView = new PiecesView();
    PluginGlobalVars.defaultView = piecesView;
    await piecesView.build(app);
    await loadConnect();
    createCommands({ palette });

    // Register the login handler to break circular dependency
    const notifications = Notifications.getInstance();
    notifications.registerActionHandler(
      NotificationActionTypeEnum.SIGN_IN,
      async () => {
        await login();
      }
    );

    SentryTracking.init();
    SegmentAnalytics.init();

    pluginHeartbeat.start(() => {
      pluginActivityCheck();
    });

    app.restored
      .then(async () => {
        const data = (await state.fetch(
          PluginGlobalVars.PLUGIN_ID
        )) as unknown as PiecesDB;
        if (
          //@ts-ignore this is a migration check
          data[0]?.schema ||
          !data.assets[0]?.annotations
        ) {
          return;
        }
        data?.assets?.forEach((val) => (val.created = new Date(val.created)));
        cache.store({
          assets: data.assets as unknown as returnedMaterial[],
        });
        if (data.remoteCopilotState) {
          PluginGlobalVars.copilotState = data.remoteCopilotState;
        }
        if (data.remoteSettingsState) {
          PluginGlobalVars.settingsState = data.remoteSettingsState;
        }
      })
      .finally(async () => {
        Applet.resolveDBLock();
        CheckVersionAndConnection.run().then(() => {
          AnnotationHandler.getInstance().loadAnnotations().then(stream);
        });
        if (!getStored('onBoardingShown')) {
          showOnboarding();
          setStored({ onBoardingShown: true });
          ActivitySingleton.getInstance().installed();
        }
      });

    document.body.addEventListener('click', () => {
      if (
        PluginGlobalVars.theme !==
        document.body.getAttribute('data-jp-theme-light')
      ) {
        PluginGlobalVars.theme = document.body.getAttribute(
          'data-jp-theme-light'
        )!;
      }
    });
  },
};

const createPrototypes = () => {
  /**
   * Array Prototype extensions
   */
  Array.prototype.remove = function <T>(element: T) {
    const idx = this.indexOf(element);
    if (idx === -1) return;
    this.splice(idx, 1);
  };

  /**=
   * HTMLElement Prototype extensions
   */
  HTMLElement.prototype.createEl = function <T extends keyof ElementMap>(
    type: T
  ) {
    const el = document.createElement(type);
    this.appendChild(el);
    return el as ElementMap[T];
  };

  HTMLElement.prototype.createDiv = function (className?: string) {
    const div = document.createElement('div');
    if (className) div.classList.add(className);
    this.appendChild(div);
    return div;
  };

  HTMLElement.prototype.addClass = function (className: string) {
    this.classList.add(className);
  };

  HTMLElement.prototype.addClasses = function (classNames: string[]) {
    for (let i = 0; i < classNames.length; i++) {
      this.classList.add(classNames[i]);
    }
  };

  HTMLElement.prototype.setText = function (text: string) {
    this.innerText = text;
  };

  HTMLElement.prototype.empty = function () {
    this.innerHTML = '';
  };
};

// Getting rid of stupid TS squiggles that aren't actually issues
const settings: JupyterFrontEndPlugin<void> = {
  id: PluginGlobalVars.PLUGIN_ID + ':pieces-settings',
  description:
    'Pieces for Developers is a code material management tool powered by AI.',
  autoStart: true,
  requires: [ISettingRegistry],
  optional: [],
  activate: async (app: JupyterFrontEnd, settings: ISettingRegistry) => {
    const config: ConnectorSingleton = ConnectorSingleton.getInstance();
    function onSettingsChange(settings: ISettingRegistry.ISettings): void {
      // Read the settings and convert to the correct type
      if (
        getStored('AutoOpen') !==
        (settings.get('AutoOpen').composite as boolean)
      ) {
        PluginGlobalVars.settingsState.savedMaterials.autoOpen = settings.get(
          'AutoOpen'
        ).composite as boolean;
        updateApplet();
        setStored({
          AutoOpen: settings.get('AutoOpen').composite as boolean,
        });
      }
      if (
        getStored('Capabilities') !==
        (settings.get('Capabilities').composite as string)
      ) {
        switch (settings.get('Capabilities').composite as string) {
          case 'Local':
            setStored({
              Capabilities: 'Local',
            });
            break;
          case 'Blended':
            setStored({
              Capabilities: 'Blended',
            });
            break;
          case 'Cloud':
            setStored({
              Capabilities: 'Cloud',
            });
            break;
          default:
            setStored({
              Capabilities: 'Blended',
            });
            break;
        }
        copilotParams.getApplication().then((application) => {
          if (!application) return;
          application.capabilities = getStored('Capabilities').toUpperCase();
          copilotParams.updateApplication(application);
        });

        config.application.capabilities =
          getStored('Capabilities').toUpperCase();
      }
    }

    // Wait for the application to be restored and
    // for the settings for this plugin to be loaded
    Promise.all([
      app.restored,
      settings.load(PluginGlobalVars.PLUGIN_ID + ':pieces-settings'),
    ])
      .then(([, settings]) => {
        // Read the settings
        if (settings) {
          PluginGlobalVars.pluginSettings = settings;
          onSettingsChange(settings);
        }

        // Listen for your plugin setting changes using Signal
        settings.changed.connect(onSettingsChange);

        ApplicationStream.getInstance();
      })
      .catch((reason) => {
        console.error(
          `Something went wrong when reading the settings.\n${reason}`
        );
      });
  },
};

function updateApplet() {
  settingsAppletMessageHandler.handleSetState({
    type: AppletWebviewMessageEnum.SetStateReq,
    data: {
      state: JSON.stringify(PluginGlobalVars.settingsState),
    },
  });
}
export default [settings, plugin];
