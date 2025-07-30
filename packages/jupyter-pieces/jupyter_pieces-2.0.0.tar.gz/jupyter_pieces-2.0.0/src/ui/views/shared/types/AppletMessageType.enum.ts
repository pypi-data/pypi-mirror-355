export enum AppletWebviewMessageEnum {
	OpenFile = 'openFile',
	ShareReq = 'shareReq',
	Notify = 'displayNotification',
	LoadContext = 'loadContext',
	ApplicationReq = 'applicationReq',
	OpenLink = 'openLink',
	Track = 'track',
	AddAssetToContext = 'addAssetToContext',
	AddFileToContext = 'addFileToContext',
	AddFolderToContext = 'addFolderToContext',
	FilterFolderReq = 'filterFolderReq',
	InsertAtCursor = 'insertAtCursor',
	FocusCopilotConversation = 'focusCopilotConversation',
	RunInTerminal = 'runInTerminal',
	GetRecentFilesReq = 'getRecentFilesReq',
	GetWorkspacePathReq = 'getWorkspacePathReq',
	AcceptChanges = 'acceptChanges',
	CorsProxyReq = 'corsProxyReq',
	UpdateApplicationReq = 'updateApplicationReq',
	GetStateReq = 'getStateReq',
	SetStateReq = 'setStateReq',
	GetUserPreferencesReq = 'getUserPreferencesReq',
	CopyToClipboard = 'copyToClipboard',
}

export enum AppletExtensionMessageEnum {
  ShareRes = 'shareRes',
  PerformQuery = 'performQuery',
  ApplicationRes = 'applicationRes',
  FilterFolderRes = 'filterFolderRes',
  GetRecentFilesRes = 'getRecentFilesRes',
  GetWorkSpacePathRes = 'getWorkspacePathRes',
  CorsProxyRes = 'corsProxyRes',
  UpdateApplicationRes = 'updateApplicationRes',
  GetStateRes = 'getStateRes',
}

export type ExtensionMsgExcludeUniEnum = Exclude<
  AppletExtensionMessageEnum,
  'performQuery'
>;
export type WebviewMsgExcludeUniEnum = Exclude<
	AppletWebviewMessageEnum,
	| 'copyToClipboard'
	| 'displayNotification'
	| 'openFile'
	| 'loadContext'
	| 'downloadModel'
	| 'openLink'
	| 'cancelDownload'
	| 'track'
	| 'addAssetToContext'
	| 'addFolderToContext'
	| 'addFileToContext'
	| 'runInTerminal'
	| 'insertAtCursor'
	| 'focusCopilotConversation'
	| 'acceptChanges'
	| 'setStateReq'
>;
