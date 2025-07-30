import { SettingsAppletState } from '../ui/views/shared/types/SettingsAppletState';
import { returnedMaterial } from './typedefs';

export default interface PiecesDB {
  assets: returnedMaterial[];
  remoteCopilotState: string;
  remoteSettingsState: SettingsAppletState;
}
