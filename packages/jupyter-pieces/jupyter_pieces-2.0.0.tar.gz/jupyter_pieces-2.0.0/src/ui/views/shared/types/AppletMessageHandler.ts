import { Application } from '@pieces.app/pieces-os-client';
import { AppletMessageData } from './AppletMessageData';
import {
  AppletExtensionMessageEnum,
  AppletWebviewMessageEnum,
  WebviewMsgExcludeUniEnum,
} from './AppletMessageType.enum';
import {
  NotificationActionTypeEnum,
  NotificationParameters,
} from './NotificationParameters';
import { AppletDataTypes } from './AppletMessageDataTypes';
import { copilotParams } from '../../copilot/CopilotParams';
import ConnectorSingleton from '../../../../connection/connectorSingleton';
import Notifications from '../../../../connection/Notifications';
import { PluginGlobalVars } from '../../../../PluginGlobalVars';
import BrowserUrl from '../../../../utils/browserUrl';

const getErrorMessage = <T extends AppletWebviewMessageEnum>(type: T) =>
  `Pieces for Developers: Error ${
    webviewMessageEnumToErrorString[type] ?? 'unknown'
  }, please make sure that PiecesOS is installed, up to date, and running. If issues persist please contact support`;

const webviewMessageEnumToErrorString = {
  [AppletWebviewMessageEnum.Notify]: 'sending notification',
  [AppletWebviewMessageEnum.CopyToClipboard]: 'copying to clipboard',
  [AppletWebviewMessageEnum.OpenFile]: 'opening file',
  [AppletWebviewMessageEnum.ShareReq]: 'generating shareable link',
  [AppletWebviewMessageEnum.LoadContext]: 'loading context',
  [AppletWebviewMessageEnum.ApplicationReq]: 'fetching application',
  [AppletWebviewMessageEnum.OpenLink]: 'opening link',
  [AppletWebviewMessageEnum.Track]: 'tracking',
  [AppletWebviewMessageEnum.AddAssetToContext]: 'adding asset to conversation',
  [AppletWebviewMessageEnum.AddFileToContext]: 'adding file to conversation',
  [AppletWebviewMessageEnum.AddFolderToContext]:
    'adding folder to conversation',
  [AppletWebviewMessageEnum.FilterFolderReq]: 'filtering folder for context',
  [AppletWebviewMessageEnum.InsertAtCursor]: 'inserting at cursor',
  [AppletWebviewMessageEnum.RunInTerminal]: 'running command in terminal',
  [AppletWebviewMessageEnum.GetRecentFilesReq]: 'getting recent files',
  [AppletWebviewMessageEnum.GetWorkspacePathReq]: 'getting workspace path',
  [AppletWebviewMessageEnum.AcceptChanges]: 'accepting changes',
  [AppletWebviewMessageEnum.CorsProxyReq]: 'using cors proxy',
  [AppletWebviewMessageEnum.UpdateApplicationReq]: 'updating application',
  [AppletWebviewMessageEnum.GetStateReq]: 'getting copilot state',
  [AppletWebviewMessageEnum.SetStateReq]: 'setting copilot state',
  [AppletWebviewMessageEnum.FocusCopilotConversation]: 'focusing conversation',
  [AppletWebviewMessageEnum.GetUserPreferencesReq]: 'getting user preferences',
  else: 'unknown',
};

const excludeNotify = [
  AppletWebviewMessageEnum.Notify,
  AppletWebviewMessageEnum.ApplicationReq,
  AppletWebviewMessageEnum.Track,
  AppletWebviewMessageEnum.AddAssetToContext,
  AppletWebviewMessageEnum.AddFileToContext,
  AppletWebviewMessageEnum.AddFolderToContext,
  AppletWebviewMessageEnum.FilterFolderReq,
  AppletWebviewMessageEnum.CorsProxyReq,
  AppletWebviewMessageEnum.GetStateReq,
  AppletWebviewMessageEnum.SetStateReq,
];

const AppletTypeReqToResponse = {
  [AppletWebviewMessageEnum.ShareReq]: AppletExtensionMessageEnum.ShareRes,
  [AppletWebviewMessageEnum.ApplicationReq]:
    AppletExtensionMessageEnum.ApplicationRes,
  [AppletWebviewMessageEnum.FilterFolderReq]:
    AppletExtensionMessageEnum.FilterFolderRes,
  [AppletWebviewMessageEnum.GetRecentFilesReq]:
    AppletExtensionMessageEnum.GetRecentFilesRes,
  [AppletWebviewMessageEnum.GetWorkspacePathReq]:
    AppletExtensionMessageEnum.GetWorkSpacePathRes,
  [AppletWebviewMessageEnum.GetStateReq]:
    AppletExtensionMessageEnum.GetStateRes,
};

export abstract class AppletMessageHandler {
  async handlerWrapper<T extends AppletWebviewMessageEnum>(
    message: AppletMessageData<T>,
    handler: (
      message: AppletMessageData<T>
    ) =>
      | Promise<AppletDataTypes[WebviewMsgExcludeUniEnum]>
      | void
      | Promise<void>,
    executeCommand: (msg: AppletMessageData<AppletWebviewMessageEnum>) => void
  ) {
    try {
      if (
        // messages that do not require a response
        message.type === AppletWebviewMessageEnum.Notify ||
        message.type === AppletWebviewMessageEnum.OpenFile ||
        message.type === AppletWebviewMessageEnum.LoadContext ||
        message.type === AppletWebviewMessageEnum.OpenLink ||
        message.type === AppletWebviewMessageEnum.Track ||
        message.type === AppletWebviewMessageEnum.AddAssetToContext ||
        message.type === AppletWebviewMessageEnum.AddFileToContext ||
        message.type === AppletWebviewMessageEnum.AddFolderToContext ||
        message.type === AppletWebviewMessageEnum.InsertAtCursor ||
        message.type === AppletWebviewMessageEnum.FocusCopilotConversation ||
        message.type === AppletWebviewMessageEnum.RunInTerminal ||
        message.type === AppletWebviewMessageEnum.AcceptChanges ||
        message.type === AppletWebviewMessageEnum.SetStateReq ||
        message.type === AppletWebviewMessageEnum.CopyToClipboard
      ) {
        return await handler(message);
      }
      const data = await handler(message);

      // there is no return data, so the message was unidirectional.
      // this could possibly be removed with conditional typings but unsure.
      if (!data) {
        return;
      }

      const msg: AppletMessageData<AppletWebviewMessageEnum> = {
        // @ts-expect-error
        type: AppletTypeReqToResponse[message.type],
        id: message.id,
        data: data,
      };

      executeCommand(msg);
    } catch (e) {
      const error = e instanceof Error ? e : new Error(String(e));
      this.sendError(
        'id' in message ? message.id : '',
        error.toString(),
        message.type,
        executeCommand
      );
    }
  }

  sendError<T extends AppletWebviewMessageEnum>(
    id: string,
    error: string,
    type: T,
    executeCommand: (msg: AppletMessageData<AppletWebviewMessageEnum>) => void
  ) {
    // @ts-ignore
    executeCommand({
      type: type,
      id: id,
      data: error,
    });
    if (!excludeNotify.includes(type)) {
      Notifications.getInstance().error({
        message: getErrorMessage(type),
        actions: [
          {
            title: 'Get Support',
            type: NotificationActionTypeEnum.OPEN_LINK,
            params: {
              url: BrowserUrl.appendParams(
                'https://docs.pieces.app/products/support'
              ),
            },
          },
        ],
      });
    }
  }

  async handleLoadContext(
    message: AppletMessageData<AppletWebviewMessageEnum.LoadContext>
  ) {
    throw 'Not implemented yet the HandleLoadContext';
  }

  handleCopilotFocus(
    message: AppletMessageData<AppletWebviewMessageEnum.FocusCopilotConversation>
  ) {
    PluginGlobalVars.defaultView.switchTab('copilot');
    copilotParams.focusCopilotConversation(message.data);
  }

  handleDefault(message: string) {
    console.log('NOT FOUND!!');
    console.log(message);
    console.log('=====');
  }

  async handleOpenFile(
    message: AppletMessageData<AppletWebviewMessageEnum.OpenFile>
  ): Promise<void> {
    throw 'Not implemented yet handleOpenFile';
  }

  async handleShareReq(
    message: AppletMessageData<AppletWebviewMessageEnum.ShareReq>
  ) {
    throw 'Not Implemented yet handleShareReq';
  }

  handleNotify(message: AppletMessageData<AppletWebviewMessageEnum.Notify>) {
    const params: NotificationParameters = {
      actions: message.data.actions,
      message: message.data.message,
      title: message.data.title,
      type:
        message.data.type === 'warning'
          ? 'warn'
          : message.data.type === 'success' ||
            message.data.type === 'information'
          ? 'info'
          : 'error',
    };
    copilotParams.sendNotification(params);
  }

  handleGetApplication() {
    return ConnectorSingleton.getInstance().context.application as
      | Application
      | undefined;
  }

  async handleOpenLink(
    message: AppletMessageData<AppletWebviewMessageEnum.OpenLink>
  ) {
    window.open(message.data.link);
  }

  // Not sure if we need this here
  async handleTrack(
    message: AppletMessageData<AppletWebviewMessageEnum.Track>
  ) {
    throw 'Not implemented yet handlerTrack';
  }

  handleGetUserPreferences() {
    throw 'Not implemented yet';
  }

  handleInsertAtCursor(
    message: AppletMessageData<AppletWebviewMessageEnum.InsertAtCursor>
  ) {
    if (typeof message.data !== 'string') {
      throw new Error('invalid insert at cursor data');
    }
    copilotParams.insertAtCursor(message.data);
  }

  async handleCorsProxy(
    message: AppletMessageData<AppletWebviewMessageEnum.CorsProxyReq>
  ) {
    const content = await fetch(message.data.url, message.data.options).then(
      (data) => data.text()
    );
    return { content };
  }

  handleCopyToClipboard(
    message: AppletMessageData<AppletWebviewMessageEnum.CopyToClipboard>
  ) {
    window.navigator.clipboard.writeText(message.data);
  }

  handleGetRecentFiles() {
    throw 'Not implemented handleGetRecentFiles';
  }

  handleGetWorkspacePaths() {
    throw 'Not implemented handGetWorkspacePaths';
  }

  abstract handleSetState(
    message: AppletMessageData<AppletWebviewMessageEnum.SetStateReq>
  ): void;

  abstract handleGetState(
    message: AppletMessageData<AppletWebviewMessageEnum.GetStateReq>
  ): { state: string };

  handleRunInTerminal(
    message: AppletMessageData<AppletWebviewMessageEnum.RunInTerminal>
  ) {
    throw 'Not implemented handleRunInTerminal';
  }
}
