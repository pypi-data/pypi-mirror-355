import { QGPTPromptPipeline } from '@pieces.app/pieces-os-client';
import { AppletAnalytics } from './AppletAnalytics.enum';
import { AppletAssetSeed } from './EditorSeed';
import { AppletRange } from './range';

/**
 * These messages only go one way, front end -> backend or backend -> front end
 */

export type AskAboutFileInput = { paths: string[]; parent: string };
export type AppletUnidirectionalMessage = {
  performQuery: {
    query: string;
    relevant?: AppletAssetSeed;
    files?: AskAboutFileInput;
    snippet?: { id: string };
    replaceable?: {
      rangeToReplace: AppletRange;
      filePath: string;
    };
    pipeline?: QGPTPromptPipeline;
    conversation?: string;
    folders?: Array<string>;
  };
  openFile: { path: string };
  displayNotification: { 
		type: "success"| "warning"| "information"
		message: string,
		actions: undefined,
		title:string
	};
  track: AppletAnalytics; // TODO implement tracking
  loadContext: { paths: string[] };
  downloadModel: { id: string };
  openLink: { link: string };
  cancelDownload: { id: string };
  addAssetToContext: { conversation: string };
  addFileToContext: { conversation: string };
  addFolderToContext: { conversation: string };
  runInTerminal: { command: string, classification?: string };
  insertAtCursor: { text: string };
  focusCopilotConversation: string;
	copyToClipboard: string;
  acceptChanges: {
    rangeToReplace: AppletRange;
    filePath: string;
    replacement: string;
  };
  setStateReq: {
    state: string;
  };
};
