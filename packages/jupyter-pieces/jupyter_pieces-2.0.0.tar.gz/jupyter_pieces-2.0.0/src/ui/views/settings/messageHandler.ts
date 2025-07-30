import { PluginGlobalVars } from '../../../PluginGlobalVars';
import { Applet } from '../shared/applet';
import { AppletMessageData } from '../shared/types/AppletMessageData';
import { AppletWebviewMessageEnum } from '../shared/types/AppletMessageType.enum';
import { settingsApplet } from './settingsApplet';
import { SettingsAppletMessageHandler } from './settingsAppletMessageHandler';
import PiecesDatabase from '../../../database/PiecesDatabase';
import { SettingsAppletState } from '../shared/types/SettingsAppletState';
import DevLogger from '../../../dev/DevLogger';
import { showOnboarding } from '../../../onboarding/showOnboarding';

export const settingsAppletMessageHandler = new SettingsAppletMessageHandler();

const messageTypeToFunction = {
  applicationReq: settingsAppletMessageHandler.handleGetApplication,
  getStateReq: settingsAppletMessageHandler.handleGetState,
  setStateReq: settingsAppletMessageHandler.handleSetState,
  loaded: settingsAppletMessageHandler.handleLoaded,
};

/**
  Handles all incoming messages from the front end
    - acts as the backend for the Settings webview.
  @param event: the message sent from the front end of type {@link AppletMessageData}.
*/
export async function handleSettingsMessage(event: MessageEvent) {
  if (event.data.destination !== 'extension') {
    return;
  }
  DevLogger.log('Settings Applet', event.data);

  const message = event.data as
    | AppletMessageData<AppletWebviewMessageEnum>
    | {
        type:
          | 'loaded'
          | 'launchPos'
          | 'openSettings'
          | 'installPos'
          | 'onboardingOpen';
      }
    | { type: 'persistState'; data: SettingsAppletState };
  if (message.type === 'launchPos') {
    Applet.launchPos();
    return;
  }
  if (message.type === 'loaded') {
    Applet.resolveLoading();
    return;
  }

  // TODO: install POS
  if (message.type === 'installPos') {
    return;
  }

  if (message.type === 'onboardingOpen') {
    showOnboarding();
    return;
  }

  if (message.type === 'persistState') {
    const newState = message.data;
    PluginGlobalVars.settingsState = newState;
    PluginGlobalVars.pluginSettings.set(
      'AutoOpen',
      newState.savedMaterials.autoOpen
    );
    PiecesDatabase.writeDB();
    const msg: AppletMessageData<AppletWebviewMessageEnum.SetStateReq> = {
      type: AppletWebviewMessageEnum.SetStateReq,
      data: { state: JSON.stringify(newState) },
    };

    settingsApplet.postToFrame(msg);

    return;
  }
  const messageType = message.type; // Asserting the type here
  const handlerFunction =
    // @ts-ignore
    messageTypeToFunction[messageType] ||
    settingsAppletMessageHandler.handleDefault;
  // eslint-disable-next-line @typescript-eslint/ban-ts-comment
  //@ts-ignore i spent one hour trying to get rid of this type error this is due to be refactored to not be such a confusing time sink anyways
  settingsAppletMessageHandler.handlerWrapper(message, handlerFunction, (msg) =>
    settingsApplet.postToFrame(msg)
  );
}
