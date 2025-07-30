import PiecesCacheSingleton from '../../cache/piecesCacheSingleton';
import ConnectorSingleton from '../../connection/connectorSingleton';
import Modal from './Modal';

export default class AddSnippetToContextModal extends Modal {
  protected async onOpen(): Promise<void> {
    //
  }
  snippetsToAdd: { [key: string]: boolean } = {};
  conversation: string;
  constructor(conversation: string) {
    super();
    this.conversation = conversation;
    this.titleEl.innerText = 'Add snippet to context';
    this.contentEl.onclick = (e) => {
      e.stopPropagation();
    };

    for (const snippet of PiecesCacheSingleton.getInstance().assets) {
      const snippetRow = this.contentEl.createDiv();
      snippetRow.classList.add('flex', 'flex-row', 'items-center');

      const checkBox = snippetRow.createEl('input');
      checkBox.type = 'checkbox';
      checkBox.onchange = () => {
        this.snippetsToAdd[snippet.id] = checkBox.checked;
      };
    }

    if (!PiecesCacheSingleton.getInstance().assets.length) {
      const emptyText = this.contentEl.createDiv();
      emptyText.classList.add('p-4', 'text-center');
      emptyText.innerText =
        "Doesn't seem like you have any snippets saved yet! Try saving a snippet and then adding it to context";
    }

    const actionRow = this.contentEl.createDiv();
    actionRow.classList.add('flex', 'flex-row', 'justify-center', 'p-3');

    const saveBtn = actionRow.createDiv();
    saveBtn.classList.add(
      'p-2',
      'bg-[var(--pieces-background-secondary)]',
      'cursor-pointer',
      'rounded',
      'shadow-sm',
      'shadow-[var(--pieces-background-modifier-box-shadow)]'
    );
    saveBtn.innerText = 'save';
    saveBtn.onclick = () => {
      this.close();
    };
  }

  handleAddToContext() {
    this.containerEl.remove();
    const snippetIds = Object.keys(this.snippetsToAdd).filter(
      (id) => this.snippetsToAdd[id]
    );
    // QGPTView.lastConversationMessage = new Date();
    for (const id of snippetIds) {
      ConnectorSingleton.getInstance().conversationApi.conversationAssociateAsset(
        {
          conversation: this.conversation,
          asset: id,
        }
      );
    }
  }

  onClose(): void {
    this.handleAddToContext();
  }
}
