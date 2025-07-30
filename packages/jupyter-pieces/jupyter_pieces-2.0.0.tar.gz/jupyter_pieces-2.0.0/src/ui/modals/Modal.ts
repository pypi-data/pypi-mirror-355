export default abstract class Modal {
  protected containerEl: HTMLElement;

  protected contentEl: HTMLElement;

  protected titleEl: HTMLElement;

  private modalParent: HTMLElement;

  constructor() {
    //ROOT DIV
    const main = document.body;

    // MODAL CONTAINER
    const modalContainer = document.createElement('div');
    this.containerEl = modalContainer;
    modalContainer.classList.add(
      '!hidden',
      'absolute',
      'left-0',
      'top-0',
      'flex',
      'h-full',
      'w-full',
      'items-center',
      'justify-center'
    );

    // MODAL BACKGROUND
    const modalBackground = document.createElement('div');
    modalBackground.classList.add(
      'absolute',
      'left-0',
      'top-0',
      'h-full',
      'w-full',
      'opacity-80',
      'bg-[rgba(10,10,10,0.4)]'
    );

    //MODAL PARENT(S)
    const modalParent = document.createElement('div');
    this.modalParent = modalParent;
    modalParent.classList.add(
      'relative',
      'flex',
      'max-h-[85vh]',
      'min-h-[100px]',
      'w-[560px]',
      'max-w-[80vw]',
      'flex-col',
      'overflow-auto',
      'rounded-lg',
      'border-[var(--pieces-background-modifier-border)]',
      'border-solid',
      'bg-[var(--pieces-background-primary)]',
      'px-4',
      'py-2',
      'z-[50]'
    );

    // MODAL HEADER
    const modalHeader = document.createElement('div');
    modalHeader.classList.add(
      'flex',
      'flex-row',
      'modal-header',
      'justify-between',
      'text-xl'
    );
    modalParent.appendChild(modalHeader);

    // titleEl
    const titleCol = modalHeader.createDiv();
    titleCol.classList.add('flex-col');
    this.titleEl = titleCol;

    //CLOSE BUTTON
    const modalCloseButtonDiv = document.createElement('div');
    modalCloseButtonDiv.classList.add('flex-col');
    modalHeader.appendChild(modalCloseButtonDiv);

    const closeBtn = document.createElement('span');
    closeBtn.innerHTML = '&times;';
    closeBtn.classList.add('cursor-pointer');
    modalCloseButtonDiv.appendChild(closeBtn);

    // MODAL CONTENT
    const modalContent = document.createElement('div');
    this.contentEl = modalContent;
    modalContent.classList.add(
      'modal-content',
      'scrollbar-hide',
      'flex',
      'flex-col',
      'text-sm',
      'overflow-auto'
    );
    modalParent.appendChild(modalContent);

    //APPEND MODAL TO ROOT
    modalContainer.appendChild(modalBackground);
    modalContainer.appendChild(modalParent);
    main!.appendChild(modalContainer);

    closeBtn.addEventListener('click', () => {
      this.close();
    });
  }

  protected abstract onOpen(): Promise<void>;

  protected abstract onClose(): void;

  hide(): void {
    this.containerEl.classList.add('!hidden');
  }

  show(): void {
    setTimeout(() => {
      window.addEventListener('click', this.handleWindowHide);
    }, 200);
    this.containerEl.classList.remove('!hidden', 'hidden');
  }

  async open(show = true) {
    setTimeout(() => {
      window.addEventListener('click', this.handleWindowHide);
    }, 200);
    if (show) {
      this.containerEl.classList.remove('!hidden');
    }
    await this.onOpen();
  }

  close(): void {
    this.onClose();
    setTimeout(() => {
      window.removeEventListener('click', this.handleWindowHide);
    }, 200);
    this.containerEl.classList.add('!hidden');
  }

  private handleWindowHide = (event: any) => {
    if (this.containerEl.classList.contains('!hidden')) return;
    if (
      event.target !== this.modalParent &&
      !this.modalParent.contains(event.target)
    ) {
      this.close();
    }
  };
}
