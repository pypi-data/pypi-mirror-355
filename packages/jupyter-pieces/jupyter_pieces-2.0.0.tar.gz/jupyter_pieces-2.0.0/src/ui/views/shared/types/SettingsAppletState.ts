export enum EnrichmentLevelEnum {
  High = 'Hight',
  Medium = 'Medium',
  Low = 'Low',
  None = 'None',
}

interface SavedMaterials {
  autoOpen: boolean;
  enrichmentLevel: EnrichmentLevelEnum;
  appendWebsites: boolean;
  usePageTitle: boolean;
  closeOnSave: boolean;
  autoCopyShareableLink: boolean;
  appendWebsitesCount: number;
}
interface SavedContext {
  recentWebsites: boolean;
}

interface PiecesOSConfig {
  onStart: boolean;
  onInteraction: boolean;
}

interface AutoComplete {
  enabled: boolean;
}

interface CodeLens {
  enabled: boolean;
  reuseConversation: boolean;
}

interface GitIntegration {
  commitLinks: boolean;
  commitAuthors: boolean;
  commitMessages: boolean;
  commitTags: boolean;
}

interface Notifications {
  pluginUpdate: boolean;
}

interface Onboarding {
  onboarded: boolean;
}

interface Telemetry {
  analyticsErrorEnabled: boolean;
  analyticsUsageEnabled: boolean;
}

export interface SettingsAppletState {
  savedMaterials: SavedMaterials;
  savedContext: SavedContext;
  piecesOSConfig: PiecesOSConfig;
  autoComplete: AutoComplete;
  codeLens: CodeLens;
  gitIntegration: GitIntegration;
  notifications: Notifications;
  onboarding: Onboarding;
  telemetry: Telemetry;
}
