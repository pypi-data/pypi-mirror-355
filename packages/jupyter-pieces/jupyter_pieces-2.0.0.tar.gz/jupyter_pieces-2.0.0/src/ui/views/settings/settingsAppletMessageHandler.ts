import DevLogger from '../../../dev/DevLogger';
import { settingsApplet } from './settingsApplet';
import { PluginGlobalVars } from '../../../PluginGlobalVars';
import { AppletWebviewMessageEnum } from '../shared/types/AppletMessageType.enum';
import { AppletMessageHandler } from '../shared/types/AppletMessageHandler';
import { AppletMessageData } from '../shared/types/AppletMessageData';

export class SettingsAppletMessageHandler extends AppletMessageHandler {
  handleLoaded() {
    DevLogger.log('Settings webview loaded');
  }
  handleSetState(
    message: AppletMessageData<AppletWebviewMessageEnum.SetStateReq>
  ) {
    const msg = {
      type: 'persistState',
      data: JSON.parse(message.data.state),
    };
    DevLogger.log(JSON.stringify(msg));

    settingsApplet.postToFrame(msg);
  }

  handleGetState() {
    return {
      state: JSON.stringify(PluginGlobalVars.settingsState),
    };
  }
}
