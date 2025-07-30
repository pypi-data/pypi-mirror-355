import {
  Annotation,
  ClassificationGenericEnum,
  ClassificationSpecificEnum,
} from '@pieces.app/pieces-os-client';
import { returnedMaterial } from '../../models/typedefs';
import langExtToReadable from '../utils/langExtToReadable';
import { reclassify, update, updateFormat } from '../../actions/updateAsset';
import { highlightSnippet } from '../utils/loadPrism';
import Notifications from '../../connection/Notifications';
import ConnectorSingleton from '../../connection/connectorSingleton';
import langExtToClassificationSpecificEnum from '../utils/langExtToClassificationSpecificEnum';
import { processAsset } from '../../connection/apiWrapper';
import AnnotationHandler from '../../utils/annotationHandler';
import Modal from './Modal';

export default class EditModal extends Modal {
  editedContent: {
    id: string;
    title: string;
    annotations: Annotation[];
    language: ClassificationSpecificEnum;
    raw: string;
  };
  snippet: returnedMaterial;
  constructor(snippet: returnedMaterial) {
    super();
    this.editedContent = {
      id: snippet.id,
      title: snippet.title,
      annotations: snippet.annotations ?? '',
      language: snippet.language,
      raw: snippet.raw,
    };
    this.snippet = snippet;
  }
  async onOpen() {
    const { snippet, editedContent } = this;
    //TITLE PARENT
    const modalTitleDiv = document.createElement('div');
    modalTitleDiv.classList.add('row');
    this.contentEl.appendChild(modalTitleDiv);

    //CLASSIFICATION PARENT
    const classificationCol = document.createElement('div');
    classificationCol.classList.add('col-fit');

    //CLASSIFICATION LABEL
    const classificationLabelRow = document.createElement('div');
    classificationLabelRow.classList.add('row', 'edit-title-label-row');

    const classificationLabel = document.createElement('span');
    classificationLabel.classList.add('edit-title-label');
    classificationLabel.innerText = 'Language: ';
    classificationLabelRow.appendChild(classificationLabel);
    classificationCol.appendChild(classificationLabelRow);

    //CLASSIFCATION INPUT
    const classificationSelectRow = document.createElement('div');
    classificationSelectRow.classList.add('row', 'edit-title-label-row');

    const snippetClassification = document.createElement('select');
    snippetClassification.classList.add('jp-dropdown', 'edit-dropdown');
    for (const [key, value] of Object.entries(
      ClassificationSpecificEnum
    ).sort()) {
      if (value === 'txt' || value === 'yml') continue;
      const readable = langExtToReadable(value);
      if (!readable) continue;
      const langOption = document.createElement('option');
      langOption.innerText = readable;
      langOption.value = key;
      snippetClassification.appendChild(langOption);
    }

    const curClassification = Object.keys(ClassificationSpecificEnum).find(
      (value) =>
        ClassificationSpecificEnum[
          value as keyof typeof ClassificationSpecificEnum
        ] === snippet.language
    );

    snippetClassification.value =
      curClassification ?? ClassificationSpecificEnum.Dart;

    classificationSelectRow.appendChild(snippetClassification);
    classificationCol.appendChild(classificationSelectRow);
    modalTitleDiv.appendChild(classificationCol);

    //TITLE LABEL
    const titleCol = document.createElement('div');
    titleCol.classList.add('col');

    const titleLabelRow = document.createElement('div');
    titleLabelRow.classList.add('row');
    titleCol.appendChild(titleLabelRow);
    const titleLabel = document.createElement('span');
    titleLabel.classList.add('edit-title-label');
    titleLabel.innerText = 'Title:';
    titleLabelRow.appendChild(titleLabel);

    //TITLE INPUT
    const titleInputRow = document.createElement('div');
    titleInputRow.classList.add('row', 'edit-title-label-row');
    const snippetTitle = document.createElement('input');
    snippetTitle.type = 'text';
    snippetTitle.classList.add('jp-input', 'edit-title-input');
    snippetTitle.value = snippet.title;
    snippetTitle.addEventListener('change', () => {
      editedContent.title = snippetTitle.value;
    });
    titleInputRow.appendChild(snippetTitle);
    titleCol.appendChild(titleInputRow);
    modalTitleDiv.appendChild(titleCol);

    //SNIPPET CODE
    const snippetDivOutter = document.createElement('div');
    snippetDivOutter.classList.add('row', 'snippet');
    snippetDivOutter.id = `snippet-${snippet.id}`;

    const snippetDiv = document.createElement('div');
    snippetDiv.classList.add('snippet-parent', 'row');
    snippetDiv.id = 'edit-snippet-parent';

    snippetDivOutter.appendChild(snippetDiv);
    let highlighted = highlightSnippet({
      snippetContent: snippet.raw,
      snippetLanguage: snippet.language,
    });

    const lineNumDiv = document.createElement('div');
    lineNumDiv.classList.add('snippet-line-div');
    snippetDiv.appendChild(lineNumDiv);

    const rawCodeDiv = document.createElement('div');
    rawCodeDiv.classList.add('snippet-raw');
    snippetDiv.appendChild(rawCodeDiv);
    const preElement = document.createElement('pre');
    preElement.classList.add('edit-snippet-raw-pre');
    rawCodeDiv.appendChild(preElement);

    const seperatedRaw = snippet.raw.split('\n');

    for (let i = 0; i < seperatedRaw.length; i++) {
      const lineNum = document.createElement('code');
      lineNum.classList.add('snippet-line-nums');
      lineNum.innerText = `${i + 1}`;
      lineNumDiv.appendChild(lineNum);
      const br = document.createElement('br');
      lineNumDiv.appendChild(br);
    }

    preElement.innerHTML = highlighted;
    preElement.contentEditable = 'true';

    preElement.addEventListener('focusout', () => {
      editedContent.raw = preElement.innerText;

      const highlighted = highlightSnippet({
        snippetContent: editedContent.raw || '',
        snippetLanguage: langExtToClassificationSpecificEnum(
          editedContent.language
        ),
      });

      preElement.innerHTML = highlighted;
    });

    snippetClassification.addEventListener('change', () => {
      editedContent.language =
        ClassificationSpecificEnum[
          snippetClassification.value as keyof typeof ClassificationSpecificEnum
        ];
      const highlighted = highlightSnippet({
        snippetContent: editedContent.raw || '',
        snippetLanguage: langExtToClassificationSpecificEnum(
          editedContent.language
        ),
      });
      preElement.innerHTML = highlighted;
    });

    this.contentEl.appendChild(snippetDivOutter);

    //SAVE BUTTON
    const btnRow = document.createElement('div');
    btnRow.classList.add('row', 'edit-desc-row');
    const saveBtn = document.createElement('button');
    saveBtn.classList.add('jp-btn');

    saveBtn.addEventListener('click', () => {
      this.containerEl.remove();
      updateHandler(editedContent);
    });

    saveBtn.innerText = 'Save Changes';
    saveBtn.title = 'Save Changes';
    btnRow.appendChild(saveBtn);
    this.contentEl.appendChild(btnRow);
  }
  onClose(): void {}
}

async function updateHandler(editedContent: {
  id: string;
  annotations: Annotation[];
  language: ClassificationSpecificEnum;
  title: string;
  raw: string;
}): Promise<void> {
  try {
    const config = ConnectorSingleton.getInstance();
    let asset = await config.assetApi.assetSnapshot({
      asset: editedContent.id,
      transferables: false,
    });
    const isImage =
      asset.original.reference?.classification.generic ===
      ClassificationGenericEnum.Image;
    let originalClassification;

    // if it was an image, the classification comes from the ocr format
    if (isImage) {
      const ocrId = asset.original.reference?.analysis?.image?.ocr?.raw.id;
      const format = asset.formats.iterable?.find((frmt) => frmt.id === ocrId);
      originalClassification = format?.classification.specific;
    } else {
      originalClassification =
        asset.original?.reference?.classification.specific ??
        ClassificationSpecificEnum.Dart;
    }

    // Update transaction
    if (editedContent.language !== originalClassification) {
      const newClassification = editedContent.language;

      asset =
        (await reclassify({
          asset: asset,
          ext: newClassification,
        })) || asset;
    }
    if (
      asset.name !== editedContent.title ||
      AnnotationHandler.getInstance().annotationsAreEqual(
        asset.annotations?.iterable ?? [],
        editedContent.annotations
      )
    ) {
      asset.name = editedContent.title;
      asset.annotations = { iterable: editedContent.annotations };

      asset = (await update({ asset: asset })) || asset;
    }
    const processed = processAsset({ asset: asset });
    if (processed.raw !== editedContent.raw) {
      // if the user changed the code in the snippet.
      const id = isImage
        ? asset.original.reference?.analysis?.image?.ocr?.raw.id
        : asset.preview.base.id;
      const encoder = new TextEncoder();
      const format = asset.formats.iterable?.find(
        (element) => element.id === id
      );

      if (isImage) {
        format!.file = {
          bytes: {
            raw: Array.from(encoder.encode(editedContent.raw)),
          },
        };
      } else {
        format!.fragment = {
          string: {
            raw: editedContent.raw,
          },
        };
      }

      updateFormat({ format: format! });
    }

    // End update transaction
  } catch (error) {
    const notifications = Notifications.getInstance();
    notifications.error({
      message: 'Failed to edit snippet, are you sure POS is running?',
    });
    console.log(error);
  }
}
