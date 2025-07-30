export enum SavedMaterialsSearchResultAction {
  OpenPreview = 'openPreview',
  CopyToClipboard = 'copyToClipboard',
  InsertAtCursor = 'insertAtCursor',
  CopyToClipboardAndOpenPreview = 'copyToClipboardAndOpenPreview',
}

export function getSavedMaterialsSearchResultActionFromVscodePrefs(action: string): SavedMaterialsSearchResultAction {
  switch (action) {
    case 'Open in Overview':
      return SavedMaterialsSearchResultAction.OpenPreview;
    case 'Insert snippet at cursor position':
      return SavedMaterialsSearchResultAction.InsertAtCursor;
    case 'Copy to clipboard only':
      return SavedMaterialsSearchResultAction.CopyToClipboard;
    case 'Open in Overview & Copy to Clipboard':
      return SavedMaterialsSearchResultAction.CopyToClipboardAndOpenPreview;
    default:
      return SavedMaterialsSearchResultAction.OpenPreview;
  }
}

export type SavedMaterialsState = {
  searchResultAction: SavedMaterialsSearchResultAction;
};
