import { Applet } from './shared/applet';
import { CopilotAppletMessageHandler } from './copilot/copilotAppletMessageHandler';
import { copilotApplet } from './copilot/copilotApplet';
import { AppletMessageData } from './shared/types/AppletMessageData';
import { AppletWebviewMessageEnum } from './shared/types/AppletMessageType.enum';
import { copilotParams } from './copilot/CopilotParams';
import { PluginGlobalVars } from '../../PluginGlobalVars';

const copilotAppletMessageHandler = new CopilotAppletMessageHandler();

const messageTypeToFunction = {
  openFile: copilotAppletMessageHandler.handleOpenFile,
  shareReq: copilotAppletMessageHandler.handleShareReq,
  displayNotification: copilotAppletMessageHandler.handleNotify,
  loadContext: copilotAppletMessageHandler.handleLoadContext,
  applicationReq: copilotAppletMessageHandler.handleGetApplication,
  openLink: copilotAppletMessageHandler.handleOpenLink,
  track: copilotAppletMessageHandler.handleTrack,
  default: copilotAppletMessageHandler.handleDefault,
  addAssetToContext: copilotAppletMessageHandler.handleAddAssetToContext,
  addFileToContext: copilotAppletMessageHandler.handleAddFileToContext,
  addFolderToContext: copilotAppletMessageHandler.handleAddFolderToContext,
  insertAtCursor: copilotAppletMessageHandler.handleInsertAtCursor,
  filterFolderReq: copilotAppletMessageHandler.handleFilterFolder,
  runInTerminal: copilotAppletMessageHandler.handleRunInTerminal,
  getRecentFilesReq: copilotAppletMessageHandler.handleGetRecentFiles,
  acceptChanges: copilotAppletMessageHandler.handleAcceptChanges,
  getWorkspacePathReq: copilotAppletMessageHandler.handleGetWorkspacePaths,
  corsProxyReq: copilotAppletMessageHandler.handleCorsProxy,
  updateApplicationReq: copilotAppletMessageHandler.handleUpdateApplication,
  getStateReq: copilotAppletMessageHandler.handleGetState,
  setStateReq: copilotAppletMessageHandler.handleSetState,
  copyToClipboard: copilotAppletMessageHandler.handleCopyToClipboard,
  focusCopilotConversation: copilotAppletMessageHandler.handleCopilotFocus,
};

/**
  Handles all incoming messages from the front end
    - acts as the backend for the Copilot webview.
  @param message: the message sent from the front end of type {@link AppletMessageData}.
*/
export async function handleOnMessage(event: MessageEvent) {
  if (event.data.destination != 'extension') return;

  const message = event.data as
    | AppletMessageData<AppletWebviewMessageEnum>
    | { type: 'loaded' | 'launchPos' | 'openSettings' | 'installPos' }
    | { type: 'previewAsset' | 'persistState'; data: string };

  if (message.type === 'loaded') {
    Applet.resolveLoading();
    return;
  }

  if (message.type === 'launchPos') {
    Applet.launchPos();
    return;
  }
  if (message.type === 'openSettings') {
    PluginGlobalVars.defaultApp.commands.execute('settingeditor:open');
    return;
  }
  if (message.type === 'persistState') {
    copilotParams.saveState(JSON.stringify(message.data));
    return;
  }
  //   if (message.type === 'previewAsset') {
  //     DisplayController.createExpandedView({
  //       snippetId: message.data,
  //       snippetTitle:
  //         PiecesCacheSingleton.getInstance().mappedAssets[message.data ?? '']
  //           .title || '',
  //     });
  //     return;
  //   }
  const messageType = message.type; // Asserting the type here
  const handlerFunction =
    //@ts-ignore
    messageTypeToFunction[messageType] || messageTypeToFunction.default;
  // eslint-disable-next-line @typescript-eslint/ban-ts-comment
  //@ts-ignore i spent one hour trying to get rid of this type error this is due to be refactored to not be such a confusing time sink anyways
  copilotAppletMessageHandler.handlerWrapper(message, handlerFunction, (msg) =>
    copilotApplet.postToFrame(msg)
  );
}
