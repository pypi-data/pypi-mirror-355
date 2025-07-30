import {
  AnchorTypeEnum,
  CapabilitiesEnum,
  SeedTypeEnum,
} from '@pieces.app/pieces-os-client';
import { loadConnect } from '../../../connection/apiWrapper';
import ConnectorSingleton from '../../../connection/connectorSingleton';
import ShareableLinksService from '../../../connection/shareableLink';
import copyToClipboard from '../../utils/copyToClipboard';
import langExtToClassificationSpecificEnum from '../../utils/langExtToClassificationSpecificEnum';
import AddSnippetToContextModal from '../../modals/AddSnippetToContextModal';
import PiecesDatabase from '../../../database/PiecesDatabase';
import Notifications from '../../../connection/Notifications';
import { SegmentAnalytics } from '../../../analytics/SegmentAnalytics';
import { TerminalManager } from '@jupyterlab/services';
import { setStored } from '../../../localStorageManager';
import { AppletParams } from '../shared/types/AppletParams';
import {
  NotificationAction,
  NotificationActionTypeEnum,
} from '../shared/types/NotificationParameters';
import { AppletAnalytics } from '../shared/types/AppletAnalytics.enum';
import { CopilotState } from '../shared/types/ConversationState';
import { SavedMaterialsState } from '../shared/types/SavedMaterialsState';
import { copilotApplet } from './copilotApplet';
import { AppletMessageData } from '../shared/types/AppletMessageData';
import { AppletWebviewMessageEnum } from '../shared/types/AppletMessageType.enum';
import { PluginGlobalVars } from '../../../PluginGlobalVars';
import BrowserUrl from '../../../utils/browserUrl';

const getApplication = async () => {
  if (!ConnectorSingleton.getInstance().context) await loadConnect();
  return ConnectorSingleton.getInstance().context.application;
};

export const copilotParams: AppletParams = {
  async updateApplication(application) {
    await ConnectorSingleton.getInstance().applicationApi.applicationUpdate({
      application,
    });
    const settingValue =
      application.capabilities === CapabilitiesEnum.Blended
        ? 'Blended'
        : 'Local';
    PluginGlobalVars.pluginSettings.set('Capabilities', settingValue);
    setStored({
      Capabilities: settingValue,
    });
  },
  runInTerminal(command) {
    const terminal = new TerminalManager();
    terminal.startNew().then(async (session) => {
      await PluginGlobalVars.defaultApp.commands.execute('terminal:open', {
        name: session.name,
      });
      session.send({
        type: 'stdin',
        content: [command],
      });
    });
  },
  async getRecentFiles() {
    return { paths: [] };
  },
  async getWorkspacePaths() {
    return { paths: [] };
  },
  migration: 0,
  openFile(path) {
    PluginGlobalVars.defaultApp.commands.execute('docmanager:open', {
      path: path,
      options: {
        mode: 'tab-after',
      },
    });
  },
  generateShareableLink: async (
    params: { id: string } | { raw: string; ext: string }
  ) => {
    let link: string | void;
    if ('id' in params) {
      link = await ShareableLinksService.getInstance().generate({
        id: params.id,
      });
      if (link) copyToClipboard(link);
      return { id: params.id };
    } else {
      const asset =
        await ConnectorSingleton.getInstance().assetsApi.assetsCreateNewAsset({
          seed: {
            type: SeedTypeEnum.SeededAsset,
            asset: {
              application: await getApplication(),
              format: {
                fragment: {
                  string: {
                    raw: params.raw,
                  },
                  metadata: {
                    ext: langExtToClassificationSpecificEnum(params.ext),
                  },
                },
              },
            },
          },
        });
      if (asset) {
        link = await ShareableLinksService.getInstance().generate({
          id: asset.id,
        });
        if (link) copyToClipboard(link);
        return { id: asset.id };
      }
    }
  },
  getApplication,
  requestContextPicker: async (
    type: 'files' | 'folders' | 'snippets',
    conversationId: string
  ) => {
    let paths: string[] | null = null;
    if (type === 'files') {
      paths =
        await ConnectorSingleton.getInstance().osApi.osFilesystemPickFiles({
          filePickerInput: {},
        });
    }
    if (type === 'folders') {
      paths =
        await ConnectorSingleton.getInstance().osApi.osFilesystemPickFolders();
    }

    if (paths) {
      const anchors = await Promise.all(
        paths.map((path) =>
          ConnectorSingleton.getInstance().anchorsApi.anchorsCreateNewAnchor({
            transferables: false,
            seededAnchor: {
              type:
                type === 'folders'
                  ? AnchorTypeEnum.Directory
                  : AnchorTypeEnum.File,
              fullpath: path,
            },
          })
        )
      );
      // QGPTView.lastConversationMessage = new Date();
      for (const anchor of anchors) {
        ConnectorSingleton.getInstance().conversationApi.conversationAssociateAnchor(
          {
            conversation: conversationId,
            anchor: anchor.id,
          }
        );
      }
      return;
    }
    new AddSnippetToContextModal(conversationId).open();
  },
  saveState: (newState: string) => {
    PluginGlobalVars.copilotState = newState;
    PiecesDatabase.writeDB();
  },
  sendNotification: (params: {
    message: string;
    title?: string;
    type: 'info' | 'error' | 'warn';
    actions?: NotificationAction<NotificationActionTypeEnum>[];
  }) => {
    if (params.type === 'info') {
      Notifications.getInstance().information({
        message: params.message,
        actions: params.actions,
      });
    } else {
      Notifications.getInstance().error({
        message: params.message,
        actions: params.actions,
      });
    }
  },
  openLink: (url: string) => BrowserUrl.launch(url),
  track: (event: AppletAnalytics) => {
    SegmentAnalytics.track({ event });
  },
  insertAtCursor(text: string) {
    throw new Error('Not implemented insertAtCursor');
  },
  getCopilotState: function (): { pieces?: CopilotState } {
    throw new Error('Function not implemented.');
  },
  getSavedMaterialsState: function (): Promise<
    SavedMaterialsState | undefined
  > {
    throw new Error('Function not implemented.');
  },
  focusCopilotConversation: function (
    conversation: string
  ): void | Promise<void> {
    const msg: AppletMessageData<AppletWebviewMessageEnum.FocusCopilotConversation> =
      {
        type: AppletWebviewMessageEnum.FocusCopilotConversation,
        data: conversation,
      };

    copilotApplet.postToFrame(msg);
  },
};
