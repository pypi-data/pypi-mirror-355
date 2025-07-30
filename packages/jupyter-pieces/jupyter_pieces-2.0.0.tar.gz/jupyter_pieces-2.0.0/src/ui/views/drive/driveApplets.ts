import { AppletCapabilities } from '../shared/types/AppletCapabilitiesEnum';
import { copilotParams } from '../copilot/CopilotParams';
import getTheme from '../shared/theme';
import { OSAppletEnum } from '@pieces.app/pieces-os-client';
import ConnectorSingleton from '../../../connection/connectorSingleton';
import { Applet } from '../shared/applet';
import { handleOnMessage } from '../messageHandler';

export default class DriveApplet extends Applet {
  constructor() {
    super('pieces-snippets', handleOnMessage);
  }

  async getUrl() {
    const application = await copilotParams.getApplication();
    const baseUrl = await ConnectorSingleton.getInstance().osApi.osAppletLaunch(
      {
        inactiveOSServerApplet: {
          type: OSAppletEnum.SavedMaterials,
          parent: application,
        },
      }
    );

    const url = new URL(`http://localhost:${baseUrl.port}`);
    const theme = getTheme();

    url.searchParams.append('theme', JSON.stringify(theme));
    url.searchParams.append('application', JSON.stringify(application));
    url.searchParams.append(
      'capabilities',
      // AppletCapabilities.insertAtCursor |
      (
        AppletCapabilities.askCopilot |
        AppletCapabilities.displayNotification |
        AppletCapabilities.persistState |
        AppletCapabilities.launchPos |
        // AppletCapabilities.corsProxy |
        AppletCapabilities.setTheme |
        AppletCapabilities.addToContext |
        AppletCapabilities.copyToClipboard |
        AppletCapabilities.loaded |
        // AppletCapabilities.previewAsset |
        AppletCapabilities.openSettings |
        AppletCapabilities.focusCopilotConversation |
        AppletCapabilities.runInTerminal
      ) // Getting type = null here which is super wired!
        .toString()
    );

    return url;
  }
}

export const driveApplet = new DriveApplet();
