import { copilotParams } from '../copilot/CopilotParams';
import getTheme from '../shared/theme';
import { Applet } from '../shared/applet';
import { handleSettingsMessage } from './messageHandler';
import { AppletSettingsCapabilities } from '../shared/types/AppletSettingsCapabilitiesEnum';
import { PluginGlobalVars } from '../../../PluginGlobalVars';
import { AppletCapabilities } from '../shared/types/AppletCapabilitiesEnum';
import ConnectorSingleton from '../../../connection/connectorSingleton';
import { OSAppletEnum } from '@pieces.app/pieces-os-client';

export default class SettingsApplet extends Applet {
  constructor() {
    super('pieces-settings', handleSettingsMessage);
  }

  async getUrl() {
    const application = await copilotParams.getApplication();
    const baseUrl = await ConnectorSingleton.getInstance().osApi.osAppletLaunch(
      {
        inactiveOSServerApplet: {
          type: OSAppletEnum.FutureAppletModulePlaceholderA,
          parent: application,
        },
      }
    );

    const url = new URL(`http://localhost:${baseUrl.port}`);
    const theme = getTheme();

    url.searchParams.append('theme', JSON.stringify(theme));
    url.searchParams.append('application', JSON.stringify(application));
    url.searchParams.append(
      'settings',
      AppletSettingsCapabilities.savedMaterialAutoOpenDrive.toString()
    );
    url.searchParams.append(
      'capabilities',
      AppletCapabilities.openOnboarding.toString()
    );
    if (PluginGlobalVars.settingsState)
      url.searchParams.append(
        'state',
        JSON.stringify(PluginGlobalVars.settingsState)
      );
    return url;
  }
}

export const settingsApplet = new SettingsApplet();
