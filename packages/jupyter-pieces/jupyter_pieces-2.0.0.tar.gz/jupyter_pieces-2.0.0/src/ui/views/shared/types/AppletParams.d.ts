/* eslint-disable @typescript-eslint/indent */
import {
  Application,
  ClassificationSpecificEnum,
} from '@pieces.app/pieces-os-client';
import { AppletAnalytics } from './AppletAnalytics.enum';
import { CopilotState } from './ConversationState';
import { NotificationParameters } from './NotificationParameters';
import { AppletRange } from './range';
import { SavedMaterialsState } from './SavedMaterialsState';

export type AppletParams = {
  /**
   * Use this to track what the persisted copilot data migration should be, this is not applicable in any integration besides vscode at the moment.
   */
  migration: number;
  /**
   * This function will open a file in the user's editor
   * @param path the path to the file that should be opened
   * @returns
   */
  openFile: (path: string) => void;
  /**
   * This function will generate a shareable link, copy it to the clipboard, and return the asset id the link was generated for.
   * If a raw string and extension is passed in, a new asset will get created, and then a shareable link will be generated.
   * @param params either an asset id, or a raw string and extension that will make up an asset
   * @returns
   */
  generateShareableLink: (
    params: { id: string } | { raw: string; ext: string }
  ) => Promise<{ id: string } | undefined>;
  /**
   * Get the current application the copilot is living within
   * @returns
   */
  getApplication: () => Promise<Application | undefined>;
  /**
   * This opens a file / folder picker, or an asset picker depending on the type that is inputted.
   * The user then selects a file, folder, or asset and the resource is then added as context to the inputted conversation.
   * @param type what type of context to be added
   * @param conversationId which conversation to add the context to
   * @returns
   */
  requestContextPicker: (
    type: 'files' | 'folders' | 'snippets',
    conversationId: string
  ) => Promise<void>;
  /**
   * This function will save the inputted state into a persistent database.
   * @param state the state to be saved
   * @returns
   */
  saveState: (state: string) => void;
  /**
   * use this to fetch things like the current conversation, the selected model id, etc
   * @returns The current state of the copilot webview
   */
  getCopilotState: () => { pieces?: CopilotState };
  /**
   * use this to fetch the saved Materials state
   * @returns The current state of the copilot webview
   */
  getSavedMaterialsState: () => Promise<SavedMaterialsState | undefined>;
  /**
   * This will display a notification to the user within the editor
   * @param params the notification to be sent
   * @returns
   */
  sendNotification: (params: NotificationParameters) => void;
  /**
   * This will send an event to mixpanel
  * NOTE: THIS SHOULD ALWAYS BE EMPTY IN OBSIDIAN, TRACKING IS NOT ALLOWED IN OBSIDIAN
   * @param event the event to track
   * @returns
   */
  track: (event: AppletAnalytics) => void;
  /**
   * This will open a url in the user's browser, a typical implemantion here is simply window.open
   * @param url the url to open
   * @returns
   */
  openLink: (url: string) => void;
  /**
   * This will copy some text to the clipboard
   * This is optional because we can have a fallback of navigator.clipboard.write
   * @param text the text to copy
   */
  copyToClipboard?: (text: string) => Promise<void>;
  /**
   * This will insert code at your cursor within the editor
   * @param text The text to insert
   * @returns
   */
  insertAtCursor: (text: string) => void | Promise<void>;
  /**
   * This will focus the copilot conversation and insert the text into the conversation
   * @param conversation the conversation to focus
   * @returns
   */
  focusCopilotConversation: (conversation: string) => void | Promise<void>;
  /**
   * This will run the inputted command in the terminal
   * @param command {string} the command to run
   */
  runInTerminal?: (command: string, type?: ClassificationSpecificEnum) => void;
  /**
   * @returns absolute paths of recent opened files
   */
  getRecentFiles: () => Promise<{ paths: string[] }>;
  /**
   * @returns the absolute path of the workspace folder(s)
   */
  getWorkspacePaths: () => Promise<{ paths: string[] }>;
  /**
   * This will allow a user to 'accept changes' while using copilot features such as: code lens and quick action.
   *
   * in order for you to properly use this feature, while calling {@link QGPTView.createGPTView}
   * your `query` parameter must also contain a `replaceable` property {@link AppletUnidirectionalMessageData['performQuery']}
   *
   * @param rangeToReplace the range of the document to replace with the new content
   * @param replacement the new content to put into the document
   * @param filePath the filepath of the document
   * @returns
   */
  acceptChanges?: (
    rangeToReplace: AppletRange,
    replacement: string,
    filePath: string
  ) => void;
  /**
   * Use this if you are getting blocked by cors while trying to fetch things
   *
   * i.e this is required for the websites as context feature in vscode as the vscode-webview origin is getting blocked by CORS
   *
   * @param url the url to fetch
   * @param options our fetch options
   * @returns the response as if you called `fetch(url, options).then((data) => data.text());`
   */
  corsProxyFetch?: (
    url: string,
    options?: RequestInit
  ) => Promise<{ content: string }>;
  /**
   * This is called when the application needs to update
   *
   * i.e: updating the local / cloud capapbilities of an application:
   *   - perform an application update in POS
   *   - update any user settings present in the integration related to the application object
   *   - invalidate any client side application caches
   *
   * @param application the newly updated application
   * @returns a promise which is resolved once the application is finished updating.
   */
  updateApplication: (application: Application) => Promise<void>;
};
