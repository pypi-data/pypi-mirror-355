import { CodeCell } from '@jupyterlab/cells';
import { ICommandPalette } from '@jupyterlab/apputils';
import createAsset from './createAsset';
import {
  AnnotationTypeEnum,
  FullTextSearchRequest,
} from '@pieces.app/pieces-os-client';
import ConnectorSingleton from '../connection/connectorSingleton';
import Constants from '../const';
import { loadPieces } from '../connection/apiWrapper';
import PiecesCacheSingleton from '../cache/piecesCacheSingleton';
import Notifications from '../connection/Notifications';
import ShareableLinksService from '../connection/shareableLink';
import copyToClipboard from '../ui/utils/copyToClipboard';
import { showOnboarding } from '../onboarding/showOnboarding';
import { getStored } from '../localStorageManager';
import { SegmentAnalytics } from '../analytics/SegmentAnalytics';
import { AnalyticsEnum } from '../analytics/AnalyticsEnum';
import { draft_asset } from './draftAsset';
import { returnedMaterial } from '../models/typedefs';
import { calculateLevenshteinDistance } from '../utils/calculateLevenshteinDistance';
import { truncateAfterNewline } from '../utils/truncateAfterNewline';
import { v4 as uuidv4 } from 'uuid';
import AskQGPTModal from '../ui/modals/AskQGPTModal';
import { PluginGlobalVars } from '../PluginGlobalVars';
import { NotificationActionTypeEnum } from '../ui/views/shared/types/NotificationParameters';

export const checkLogin = async () => {
  const context = ConnectorSingleton.getInstance();
  const user = await context.userApi.userSnapshot();
  if (user.user) {
    return true;
  }
  Notifications.getInstance().error({
    message: 'Sign into Pieces to use this feature',
    sendToSentry: false,
    actions: [
      {
        type: NotificationActionTypeEnum.SIGN_IN,
        title: 'Sign in',
        params: {},
      },
      {
        type: NotificationActionTypeEnum.OPEN_LINK,
        title: 'Learn more',
        params: {
          url: 'https://docs.pieces.app/products/meet-pieces/sign-into-pieces',
        },
      },
    ],
  });
  return false;
};

export const createCommands = ({ palette }: { palette: ICommandPalette }) => {
  const { commands } = PluginGlobalVars.defaultApp;

  // Enrich Selection
  const enrich_selection_command = 'jupyter_pieces:enrich-selection';
  commands.addCommand(enrich_selection_command, {
    label: 'Enrich Selection via Pieces',
    caption: 'Add a description to your selection',
    execute: enrichSelection,
  });
  PluginGlobalVars.defaultApp.contextMenu.addItem({
    command: enrich_selection_command,
    selector: '.jp-Cell',
    rank: 101,
  });

  // Onboarding command
  const onboarding_command = 'jupyter_pieces:open-onboarding';
  commands.addCommand(onboarding_command, {
    label: 'Pieces for Developers Onboarding',
    execute: showOnboarding,
  });
  palette.addItem({
    command: onboarding_command,
    category: 'Pieces for Developers',
  });

  // save active cell to pieces command
  const save_active_cell_command = 'jupyter_pieces:save-cell-to-pieces';
  commands.addCommand(save_active_cell_command, {
    label: 'Save Active Cell to Pieces',
    caption: 'Save the Active Cell to Pieces',
    execute: saveActiveCellToPieces,
  });
  PluginGlobalVars.defaultApp.contextMenu.addItem({
    command: save_active_cell_command,
    selector: '.jp-Cell',
    rank: 100,
  });

  const share_active_cell_command = 'jupyter_pieces:share-cell-via-pieces';
  commands.addCommand(share_active_cell_command, {
    label: 'Share Active Cell via Pieces',
    caption: 'Share the Active Cell via Pieces',
    execute: shareActiveCellViaPieces,
  });
  PluginGlobalVars.defaultApp.contextMenu.addItem({
    command: share_active_cell_command,
    selector: '.jp-Cell',
    rank: 100,
  });

  // save selection to pieces command
  const save_selection_to_pieces_command =
    'jupyter_pieces:save-selection-to-pieces';
  commands.addCommand(save_selection_to_pieces_command, {
    label: 'Save Selection to Pieces',
    caption: 'Save your Selection to Pieces',
    execute: saveSelectionToPieces,
  });
  PluginGlobalVars.defaultApp.contextMenu.addItem({
    command: save_selection_to_pieces_command,
    selector: '*',
    rank: 100,
  });

  const share_selection_via_pieces_command =
    'jupyter_pieces:share-selection-via-pieces';
  commands.addCommand(share_selection_via_pieces_command, {
    label: 'Share Selection via Pieces',
    caption: 'Share your Selection via Pieces',
    execute: shareSelectionViaPieces,
  });
  PluginGlobalVars.defaultApp.contextMenu.addItem({
    command: share_selection_via_pieces_command,
    selector: '*',
    rank: 100,
  });

  // Ask QGPT about selectin
  const askCopilotCommand = 'jupyter_pieces:ask-copilot-about-selection';
  commands.addCommand(askCopilotCommand, {
    label: 'Ask Pieces about your selection',
    caption: 'Ask Pieces Copilot a question about your selected text',
    execute: async () => {
      if (!(await checkLogin())) return;
      const selection = document.getSelection();
      if (!selection) {
        Notifications.getInstance().error({
          message: 'Please select some text to ask our Copilot about!',
        });
        return;
      }
      new AskQGPTModal(selection.toString()).open();
    },
  });
  PluginGlobalVars.defaultApp.contextMenu.addItem({
    command: askCopilotCommand,
    selector: '*',
    rank: 101,
  });

  // Right-click menu
  commands.addCommand('text-shortcuts:save-selection-to-pieces', {
    label: 'Save Selection to Pieces',
    execute: saveSelectionToPieces,
  });
  commands.addCommand('text-shortcuts:share-selection-via-pieces', {
    label: 'Share Selection via Pieces',
    execute: shareSelectionViaPieces,
  });
  commands.addCommand('text-shortcuts:save-cell-to-pieces', {
    label: 'Save Active Cell to Pieces',
    execute: saveActiveCellToPieces,
  });
  commands.addCommand('text-shortcuts:share-cell-via-pieces', {
    label: 'Share Active Cell via Pieces',
    execute: shareActiveCellViaPieces,
  });
};

const enrichSelection = async () => {
  if (!(await checkLogin())) return;
  const notifications: Notifications = Notifications.getInstance();
  const selection = document.getSelection();
  if (!selection || selection.toString().length < 5) {
    notifications.error({ message: Constants.NO_SAVE_SELECTION });
    return;
  }

  const draft_seed = await draft_asset({ text: selection.toString() });

  const editor =
    //@ts-ignore this does not exist in the api given by jupyterlab, however editor does exist if they have a notebook open.
    PluginGlobalVars.defaultApp.shell.currentWidget?.content.activeCell.editor;
  if (!editor || editor === undefined) {
    notifications.error({
      message: 'Unable to detect editor, cannot enrich.',
    });
    return;
  }

  // Define the text you want to insert
  const textToInsert = `'''\n${
    draft_seed.asset?.metadata?.annotations
      ?.map((annotation) => annotation.text)
      .join('\n') ?? ''
  }\n'''\n`;

  editor.replaceSelection(textToInsert + selection);

  await loadPieces();
};

export const saveActiveCellToPieces = async () => {
  if (!(await checkLogin())) return;
  const notifications: Notifications = Notifications.getInstance();
  SegmentAnalytics.track({
    event: AnalyticsEnum.JUPYTER_SAVE_ACTIVE_CELL,
  });

  // TODO very sad can't use typescript lsp magic D:
  const activeCell =
    //@ts-ignore
    PluginGlobalVars.defaultApp.shell.currentWidget?.content.activeCell;
  const cells =
    //@ts-ignore
    PluginGlobalVars.defaultApp.shell.currentWidget?.content?.cellsArray;
  const notebookName =
    //@ts-ignore
    PluginGlobalVars.defaultApp.shell.currentPath ?? 'unknown';
  let cellNum;

  if (!activeCell) {
    notifications.error({ message: Constants.NO_ACTIVE_CELL });
    return;
  } else if (!(activeCell instanceof CodeCell)) {
    notifications.error({ message: Constants.NO_CODE_CELL });
    return;
  }

  for (let i = 0; i < cells.length; i++) {
    if (cells[i] === activeCell) {
      cellNum = i;
      break;
    }
  }

  const code = activeCell.model.toJSON().source;
  if (code.length < 5) {
    notifications.error({
      message: 'There is no code saved in this cell!',
    });
    return;
  }
  try {
    const { similarity } = await findSimilarity(code);
    if (similarity < 2) {
      notifications.information({ message: Constants.SAVE_EXISTS });
    } else {
      await createAsset({
        selection: code as string,
        filePath: notebookName === 'unknown' ? undefined : notebookName,
        annotations: [
          {
            text: `This material came from cell ${
              (cellNum ?? -1) + 1
            } of ${notebookName}`,
            type: AnnotationTypeEnum.Description,
            id: uuidv4(),
            created: {
              value: new Date(),
            },
            updated: {
              value: new Date(),
            },
          },
        ],
      });
    }
  } catch (e) {
    notifications.error({
      message:
        'Failed to save material to Pieces, are you sure that PiecesOS is running?',
    });
  }
  if (getStored('AutoOpen')) {
    PluginGlobalVars.defaultApp.shell.activateById('piecesView');
  }
};

export const saveSelectionToPieces = async () => {
  if (!(await checkLogin())) return;
  const notifications: Notifications = Notifications.getInstance();
  SegmentAnalytics.track({
    event: AnalyticsEnum.JUPYTER_SAVE_SELECTION,
  });

  const selection = document.getSelection();
  //@ts-ignore
  const filename = PluginGlobalVars.defaultApp.shell.currentPath ?? 'unknown';
  if (!selection || selection.toString().length < 5) {
    notifications.error({ message: Constants.NO_SAVE_SELECTION });
    return;
  }
  try {
    await createAsset({
      selection: selection.toString(),
      filePath: filename === 'unknown' ? undefined : filename,
      annotations: [
        {
          text: `This material was saved via selection from ${filename}`,
          type: AnnotationTypeEnum.Description,
          id: uuidv4(),
          created: {
            value: new Date(),
          },
          updated: {
            value: new Date(),
          },
        },
      ],
    });
  } catch (e) {
    notifications.error({
      message:
        'Failed to save selection to Pieces. Are you sure PiecesOS is running?',
    });
  }
  if (getStored('AutoOpen')) {
    PluginGlobalVars.defaultApp.shell.activateById('piecesView');
  }
};

export const shareSelectionViaPieces = async () => {
  if (!(await checkLogin())) return;
  const notifications: Notifications = Notifications.getInstance();
  const linkService: ShareableLinksService =
    ShareableLinksService.getInstance();
  const cache: PiecesCacheSingleton = PiecesCacheSingleton.getInstance();
  SegmentAnalytics.track({
    event: AnalyticsEnum.JUPYTER_SHARE_SELECTION,
  });

  const selection = document.getSelection();
  if (!selection || selection.toString().length < 5) {
    notifications.error({ message: Constants.NO_SAVE_SELECTION });
    return;
  }

  try {
    const { similarity, comparisonID } = await findSimilarity(
      selection.toString()
    );
    if (similarity < 2) {
      if (typeof comparisonID === 'string') {
        const existingLink = cache.mappedAssets[comparisonID].share;
        const link =
          existingLink ??
          (await linkService.generate({
            id: comparisonID,
          }));
        link && copyToClipboard(link);

        notifications.information({
          message: Constants.LINK_GEN_COPY,
        });
      }
    } else {
      await saveAndShare(selection.toString());
    }
  } catch (e) {
    notifications.error({
      message:
        'Failed to share selection via pieces, are you sure PiecesOS is running?',
    });
  }
};

export const shareActiveCellViaPieces = async () => {
  if (!(await checkLogin())) return;
  const notifications: Notifications = Notifications.getInstance();
  const linkService: ShareableLinksService =
    ShareableLinksService.getInstance();
  // TODO very sad can't use typescript lsp magic D:
  const activeCell =
    //@ts-ignore
    PluginGlobalVars.defaultApp.shell.currentWidget?.content.activeCell;
  const cells =
    //@ts-ignore
    PluginGlobalVars.defaultApp.shell.currentWidget?.content?.cellsArray;
  const notebookName =
    //@ts-ignore
    PluginGlobalVars.defaultApp.shell.currentPath ?? 'unknown';

  if (!activeCell) {
    notifications.error({ message: Constants.NO_ACTIVE_CELL });
    return;
  } else if (!(activeCell instanceof CodeCell)) {
    notifications.error({ message: Constants.NO_CODE_CELL });
    return;
  }

  let cellNum;
  for (let i = 0; i < cells.length; i++) {
    if (cells[i] === activeCell) {
      cellNum = i;
      break;
    }
  }

  const code = activeCell.model.toJSON().source;
  const { similarity, comparisonID } = await findSimilarity(code);

  if (similarity < 2) {
    if (typeof comparisonID === 'string') {
      const link = await linkService.generate({
        id: comparisonID,
      });
      copyToClipboard(link || '');
    }
  } else {
    const id = await createAsset({
      selection: code as string,
      filePath: notebookName === 'unknown' ? undefined : notebookName,
      annotations: [
        {
          text: `This material came from cell ${
            (cellNum ?? -1) + 1
          } of ${notebookName}`,
          type: AnnotationTypeEnum.Description,
          id: uuidv4(),
          created: {
            value: new Date(),
          },
          updated: {
            value: new Date(),
          },
        },
      ],
    });
    const link = await linkService.generate({
      id: id!,
    });
    copyToClipboard(link || '');
  }
};

/*
Handler for editor menu -> share material
    - creates a material
    - generates a link
    - copies to clipboard
*/
async function saveAndShare(selection: string) {
  const linkService: ShareableLinksService =
    ShareableLinksService.getInstance();
  const notebookName =
    //@ts-ignore
    PluginGlobalVars.defaultApp.shell.currentPath ?? 'unknown';
  const id = await createAsset({
    selection: selection,
    filePath: notebookName === 'unknown' ? undefined : notebookName,
  });
  if (typeof id === 'string') {
    const link = await linkService.generate({ id: id });
    copyToClipboard(link || '');
  }
}

export async function findSimilarity(
  codeBlock: string | string[]
): Promise<{ similarity: number; comparisonID: string }> {
  const config: ConnectorSingleton = ConnectorSingleton.getInstance();
  const cache: PiecesCacheSingleton = PiecesCacheSingleton.getInstance();
  let comparisonScore = Infinity;
  let comparisonID = '';
  const rawCode: FullTextSearchRequest = {
    query: truncateAfterNewline(codeBlock),
  };

  const result = config.searchApi.fullTextSearch(rawCode);

  const assetArray: returnedMaterial[] = [];

  await result.then(
    async (
      res: { iterable: { identifier: string | number }[] } | undefined
    ) => {
      res?.iterable.forEach((element: { identifier: string | number }) => {
        assetArray.push(cache.mappedAssets[element.identifier]);
      });
      const returnedMaterials = assetArray;

      returnedMaterials.forEach((element) => {
        try {
          // TODO: Make sure that `element.raw` is always going to be a string
          const currentCompScore = calculateLevenshteinDistance(
            codeBlock,
            element.raw as string
          );

          if (currentCompScore < comparisonScore) {
            comparisonScore = currentCompScore; // Update the current low number if the condition is true
            comparisonID = element.id;
          }
        } catch {
          console.log('Error in calculating similarity score');
        }
      });
    }
  );
  return { similarity: comparisonScore, comparisonID: comparisonID };
}
