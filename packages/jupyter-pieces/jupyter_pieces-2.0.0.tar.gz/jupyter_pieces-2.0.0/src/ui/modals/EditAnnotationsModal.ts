import { returnedMaterial } from '../../models/typedefs';
import { Annotation, AnnotationTypeEnum } from '@pieces.app/pieces-os-client';
import ConnectorSingleton from '../../connection/connectorSingleton';
import Notifications from '../../connection/Notifications';
import { v4 as uuidv4 } from 'uuid';
import Constants from '../../const';
import Modal from './Modal';
import { NotificationActionTypeEnum } from '../views/shared/types/NotificationParameters';
import BrowserUrl from '../../utils/browserUrl';

export class AnnotationsModal extends Modal {
  snippetTitle: string;
  snippetId: string;
  snippetContent: string | undefined;
  snippetLanguage: string;
  seperatedRaw: string[];
  snippetAnnotations: Annotation[];
  titleInput: HTMLInputElement | undefined;
  descText: HTMLTextAreaElement | undefined;

  constructor(snippetObject: returnedMaterial) {
    super();
    this.snippetTitle = snippetObject.title;
    this.snippetId = snippetObject.id;
    this.snippetContent = snippetObject.raw;
    this.snippetLanguage = snippetObject.language;
    this.seperatedRaw = (snippetObject.raw || '').split('\n');
    this.snippetAnnotations = snippetObject.annotations || [];
  }

  async onOpen() {
    this.titleEl.innerText = 'Annotations';

    const annotationForm = document.createElement('div');
    this.contentEl.appendChild(annotationForm);
    annotationForm.classList.add('annotation-form');

    const AnnotationRow = document.createElement('div');
    annotationForm.appendChild(AnnotationRow);
    AnnotationRow.classList.add('row', 'v-align-center', 'h-align-center');

    const AnnotationCol = document.createElement('div');
    AnnotationRow.appendChild(AnnotationCol);
    AnnotationCol.classList.add(
      'col',
      'v-align-center',
      'h-align-center',
      'width-full',
      'annotation-col-fix'
    );

    this.addAnnotationWidget(AnnotationCol);

    for (let i = 0; i < this.snippetAnnotations.length; i++) {
      const seperator = this.annotationWidgetSeperator();
      AnnotationCol.appendChild(seperator);
      AnnotationCol.appendChild(
        this.annotationWidget(this.snippetAnnotations[i], false, seperator)
      );
    }
  }

  async updateHandler(annotation: Annotation): Promise<Annotation> {
    const config = ConnectorSingleton.getInstance();
    return config.annotationApi
      .annotationUpdate({ annotation })
      .then((newAnnotation) => {
        Notifications.getInstance().information({
          message: 'Annotation updating was a success!',
        });
        return newAnnotation;
      })
      .catch(() => {
        Notifications.getInstance().error({
          message:
            'Something went wrong updating that annotation! If the issue persists, please contact support. Make sure that PiecesOS is installed, up to date, and running!',
          actions: [
            {
              title: 'Contact Support',
              type: NotificationActionTypeEnum.OPEN_LINK,
              params: { url: BrowserUrl.appendParams('https://docs.pieces.app/products/support') },
            },
          ],
        });
        return annotation;
      });
  }

  addAnnotationWidget = (AnnotationCol: HTMLDivElement) => {
    const AddAnnotationWidget = document.createElement('div');
    AnnotationCol.appendChild(AddAnnotationWidget); // AnnotationCol.createDiv();
    AddAnnotationWidget.classList.add(
      'row',
      'width-full',
      'width-max',
      'annotation-add-body'
    );

    const AnnotationText = document.createElement('span'); //AddAnnotationWidget.createEl('span');
    AddAnnotationWidget.appendChild(AnnotationText);
    AnnotationText.classList.add('width-full', 'width-max');
    AnnotationText.innerText = 'Add Annotation +';

    AddAnnotationWidget.addEventListener('click', async () => {
      const seperator = this.annotationWidgetSeperator();
      AnnotationCol.prepend(
        this.annotationWidget(
          {
            type: AnnotationTypeEnum.Description,
            text: '',
            id: uuidv4(),
            created: {
              value: new Date(),
            },
            updated: {
              value: new Date(),
            },
          },
          true,
          seperator
        )
      );
      AnnotationCol.prepend(seperator);
      AnnotationCol.prepend(AddAnnotationWidget);
    });
  };

  annotationWidget = (
    annotation: Annotation,
    isNew = false,
    seperator: HTMLElement
  ) => {
    annotation.created.value = new Date(annotation.created.value);
    annotation.updated.value = new Date(annotation.updated.value);
    const AnnotationWidget = document.createElement('div');
    AnnotationWidget.classList.add(
      'row',
      'width-full',
      'width-max',
      'annotation-body'
    );

    const AnnotationWidgetBody = document.createElement('div');
    AnnotationWidget.appendChild(AnnotationWidgetBody); //AnnotationWidget.createDiv();
    AnnotationWidgetBody.classList.add(
      'col',
      'width-full',
      'width-max',
      'annotation-col-fix'
    );

    const AnnotationText = document.createElement('span'); // AnnotationWidgetBody.createEl('span');
    AnnotationWidgetBody.appendChild(AnnotationText);
    AnnotationText.contentEditable = 'true';
    AnnotationText.classList.add(
      'width-full',
      'width-max',
      'annotation-text-height-max',
      'annotation-text-height-min',
      'annotation-text-body'
    );
    AnnotationText.innerText = annotation.text;

    const AnnotationMetaRow = document.createElement('div');
    AnnotationWidgetBody.appendChild(AnnotationMetaRow); //AnnotationWidgetBody.createDiv();
    AnnotationMetaRow.classList.add('row', 'width-max', 'annotation-metadata');

    const AnnotationMetaRowLeft = document.createElement('div');
    AnnotationMetaRow.appendChild(AnnotationMetaRowLeft); //AnnotationMetaRow.createDiv();
    AnnotationMetaRowLeft.classList.add('annotation-metadata-left');

    AnnotationMetaRowLeft.innerHTML = Constants.ENRICH_ICON;

    const annotationDate = document.createElement('span');
    AnnotationMetaRowLeft.appendChild(annotationDate); //AnnotationMetaRowLeft.createEl('span');
    annotationDate.textContent = `Added ${
      annotation.created.readable ?? 'just now'
    }`;

    const AnnotationActionDiv = document.createElement('div');
    AnnotationActionDiv.classList.add('annotation-action-row');

    AnnotationMetaRowLeft.appendChild(AnnotationActionDiv); //AnnotationMetaRowLeft.createDiv();

    const favoriteBtn = document.createElement('div'); // AnnotationMetaRowLeft.createDiv();
    AnnotationActionDiv.appendChild(favoriteBtn);
    favoriteBtn.classList.add('annotation-metadata-left-btn');
    favoriteBtn.onclick = () => {
      annotation.favorited = annotation.favorited ? false : true;
      favoriteBtn.style.color = annotation.favorited
        ? 'yellow'
        : 'currentColor';
      this.handleCrupdate(annotation, AnnotationText, isNew, true).then(
        (newAnnotation) => {
          annotation = newAnnotation;
        }
      );
      isNew = false;
    };
    favoriteBtn.innerHTML = Constants.STAR_ICON;
    favoriteBtn.style.color = annotation.favorited ? 'yellow' : 'currentColor';

    const saveBtn = document.createElement('div');
    AnnotationActionDiv.appendChild(saveBtn); //AnnotationMetaRowLeft.createDiv();
    saveBtn.classList.add('annotation-metadata-left-btn', 'annotation-save');
    saveBtn.innerHTML = Constants.SAVE_ALL_ICON;
    saveBtn.title = 'Save annotation';
    saveBtn.onclick = async () => {
      this.handleCrupdate(annotation, AnnotationText, isNew).then(
        (newAnnotation) => {
          if (annotation.id !== newAnnotation.id) isNew = false;
          annotation = newAnnotation;
        }
      );
    };

    const deleteBtn = document.createElement('div');
    AnnotationActionDiv.appendChild(deleteBtn); //AnnotationMetaRowLeft.createDiv();
    deleteBtn.classList.add(
      'annotation-metadata-left-btn',
      'annotation-delete'
    );
    deleteBtn.onclick = async () => {
      seperator.remove();
      this.handleDelete(annotation, AnnotationWidget, isNew);
    };
    deleteBtn.innerHTML = Constants.DELETE_SVG;
    deleteBtn.title = 'Delete annotation';
    deleteBtn.style.color = '#FF4343';

    const AnnotationMetaRowRight = document.createElement('div');
    AnnotationMetaRow.appendChild(AnnotationMetaRowRight); //AnnotationMetaRow.createDiv();

    const annotationTypeDropdown = document.createElement('select');
    annotationTypeDropdown.classList.add('jp-dropdown');
    Object.values(AnnotationTypeEnum).forEach((el) => {
      const option = document.createElement('option');
      option.innerText = el.toUpperCase().replace('_', ' ');
      option.value = el;
      option.selected = (el as AnnotationTypeEnum) === annotation.type;
      annotationTypeDropdown.appendChild(option);
    });
    annotationTypeDropdown.onchange = () => {
      annotation.type = annotationTypeDropdown.value as AnnotationTypeEnum;
      this.handleCrupdate(
        annotation,
        AnnotationText,
        isNew,
        undefined,
        true
      ).then((newAnnotation) => {
        annotation = newAnnotation;
        if (annotation.id !== newAnnotation.id) isNew = false;
      });
    };
    AnnotationMetaRowRight.appendChild(annotationTypeDropdown); //AnnotationMetaRowRight.createEl('span');

    const option_arrow = document.createElement('span');
    option_arrow.innerText = '▼';
    option_arrow.classList.add('jp-dropdown-arrow');
    AnnotationMetaRowRight.appendChild(option_arrow);

    AnnotationActionDiv.classList.add('actions-hidden');

    AnnotationWidget.onmouseenter = () => {
      AnnotationActionDiv.classList.remove('hidden-out');
      AnnotationActionDiv.classList.add('hidden-in');
    };

    AnnotationWidget.onmouseleave = () => {
      if (
        AnnotationText.innerText === annotation.text &&
        annotation.type === (annotationTypeDropdown.value as AnnotationTypeEnum)
      ) {
        AnnotationActionDiv.classList.remove('hidden-in');
        AnnotationActionDiv.classList.add('hidden-out');
      }
    };

    return AnnotationWidget;
  };

  handleDelete = (
    annotation: Annotation,
    AnnotationWidget: HTMLElement,
    isNew: boolean
  ) => {
    setTimeout(() => {
      // close modal listener fires if this is removed straight away.
      AnnotationWidget.remove();
    }, 50);
    const config = ConnectorSingleton.getInstance();
    if (!isNew) {
      config.annotationsApi
        .annotationsDeleteSpecificAnnotation({
          annotation: annotation.id,
        })
        .then(() => {
          Notifications.getInstance().information({
            message: 'Annotation deletion success!',
          });
        })
        .catch((e) => {
          Notifications.getInstance().error({
            message:
              'Error deleting that annotation! If the issue persists, please contact support. Make sure that PiecesOS is installed, up to date, and running.',
            actions: [
              {
                title: 'Contact Support',
                type: NotificationActionTypeEnum.OPEN_LINK,
                params: { url: BrowserUrl.appendParams('https://docs.pieces.app/products/support') },
              },
            ],
          });
        });
    }
  };

  handleCrupdate = async (
    annotation: Annotation,
    AnnotationText: HTMLElement,
    isNew: boolean,
    favorite?: boolean,
    typeChange?: boolean
  ): Promise<Annotation> => {
    if (
      AnnotationText.innerText === annotation.text &&
      !favorite &&
      !typeChange
    ) {
      Notifications.getInstance().error({
        message: 'Please modify your annotation to save changes!',
      });
      return annotation;
    } else if (!AnnotationText.innerText) {
      Notifications.getInstance().error({
        message: 'Please add some text to your annotation to save changes!',
      });
      return annotation;
    }
    // this should not ever be empty because we check for falsy AnnotationText.textContent
    annotation.text = AnnotationText.innerText ?? '';
    if (isNew) {
      isNew = false;
      const config = ConnectorSingleton.getInstance();
      return config.annotationsApi
        .annotationsCreateNewAnnotation({
          seededAnnotation: {
            asset: this.snippetId,
            type: annotation.type,
            text: annotation.text,
          },
        })
        .then((newAnnotation) => {
          Notifications.getInstance().information({
            message: 'Annotation creation was a success!',
          });
          return newAnnotation;
        })
        .catch(() => {
          Notifications.getInstance().error({
            message:
              'Something went wrong creating that annotation! If the issue persists, please contact support. Make sure that PiecesOS is installed, up to date, and running!',
            actions: [
              {
                title: 'Contact Support',
                type: NotificationActionTypeEnum.OPEN_LINK,
                params: { url: BrowserUrl.appendParams('https://docs.pieces.app/products/support') },
              },
            ],
          });
          return annotation;
        });
    } else {
      return this.updateHandler(annotation);
    }
  };

  annotationWidgetSeperator = () => {
    const AnnotationWidgetSeperator = document.createElement('div');
    AnnotationWidgetSeperator.classList.add(
      'row',
      'width-full',
      'width-max',
      'annotation-seperator'
    );

    const AnnotationWidgetSeperatorBody = document.createElement('div');
    AnnotationWidgetSeperator.appendChild(AnnotationWidgetSeperatorBody); //AnnotationWidgetSeperator.createDiv();
    AnnotationWidgetSeperatorBody.classList.add(
      'col',
      'width-full',
      'width-max'
    );
    return AnnotationWidgetSeperator;
  };

  onClose() {}
}
