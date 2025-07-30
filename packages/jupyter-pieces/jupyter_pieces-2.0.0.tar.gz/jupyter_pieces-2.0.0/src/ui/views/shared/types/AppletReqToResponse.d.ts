import { AppletDataTypes } from './AppletMessageDataTypes';
import { AppletWebviewMessageEnum } from './AppletMessageType.enum';

export type AppletReqToResponse = {
  [AppletWebviewMessageEnum.ShareReq]: AppletDataTypes['shareRes'];
  [AppletWebviewMessageEnum.ApplicationReq]: AppletDataTypes['applicationRes'];
  [AppletWebviewMessageEnum.FilterFolderReq]: AppletDataTypes['filterFolderRes'];
  [AppletWebviewMessageEnum.GetRecentFilesReq]: AppletDataTypes['getRecentFilesRes'];
  [AppletWebviewMessageEnum.GetWorkspacePathReq]: AppletDataTypes['getWorkspacePathRes'];
  [AppletWebviewMessageEnum.CorsProxyReq]: AppletDataTypes['corsProxyRes'];
  [AppletWebviewMessageEnum.UpdateApplicationReq]: AppletDataTypes['updateApplicationRes'];
  [AppletWebviewMessageEnum.GetStateReq]: AppletDataTypes['getStateRes'];
  [AppletWebviewMessageEnum.GetUserPreferencesReq]: AppletDataTypes['getUserPreferencesRes'];
};
