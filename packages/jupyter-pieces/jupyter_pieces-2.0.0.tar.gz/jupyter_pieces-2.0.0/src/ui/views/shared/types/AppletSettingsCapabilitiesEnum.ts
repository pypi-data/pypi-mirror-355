export enum AppletSettingsCapabilities {
  savedMaterialAutoOpenDrive = 0b0000_0001, // 1
  savedMaterialEnrichmentLevel = 0b0000_0010, // 2
  savedMaterialUsePageTitle = 0b0000_0100, // 4
  savedMaterialEditingCloseOnSave = 0b0000_1000, // 8
  savedMaterialSharingAutoCopyLink = 0b0001_0000, // 16

  piecesOSLaunchOnStart = 0b0010_0000, // 32
  piecesOSLaunchOnInteraction = 0b0100_0000, // 64
  autocompleteEnabled = 0b1000_0000, // 128

  codelensEnabled = 0b0000_0001 << 8, // 256
  codelensReuseConversation = 0b0000_0010 << 8, // 512

  gitCommitLinks = 0b0000_0100 << 8, // 1024
  gitCommitAuthors = 0b0000_1000 << 8, // 2048
  gitCommitMessages = 0b0001_0000 << 8, // 4096
  gitCommitTags = 0b0010_0000 << 8, // 8192

  notificationPluginUpdate = 0b0100_0000 << 8, // 16_384

  analyticsErrorEnabled = 0b1000_0000 << 8, // 32768
  analyticsUsageEnabled = 0b0000_0001 << 16, // 65536
  codeBlockActionsUseIntegratedTerminal = 0b0000_0010 << 16, // 131072
  settingsCopilotPersistedState = 0b0000_0100 << 16, // 262144
}
