import { JupyterFrontEnd } from '@jupyterlab/application';
import { PiecesView } from './ui/piecesView';
import { IStateDB } from '@jupyterlab/statedb';
import { ISettingRegistry } from '@jupyterlab/settingregistry';
import { SettingsAppletState } from './ui/views/shared/types/SettingsAppletState';

export class PluginGlobalVars {
  public static PLUGIN_ID = 'jupyter_pieces';
  public static defaultApp: JupyterFrontEnd;
  public static defaultView: PiecesView;
  public static theme: string;
  public static defaultState: IStateDB;
  public static pluginSettings: ISettingRegistry.ISettings;
  public static copilotState: string;
  public static settingsState: SettingsAppletState;
}
