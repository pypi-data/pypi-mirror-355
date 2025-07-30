import { versionValid } from '../../connection/versionCheck';
import { marked } from 'marked';
import { sendSVG as sendIcon } from '../LabIcons';
import Notifications from '../../connection/Notifications';
import Modal from './Modal';
import { getStored } from '../../localStorageManager';
import { CodeCell } from '@jupyterlab/cells';
import { ClassificationSpecificEnum } from '@pieces.app/pieces-os-client';
import { copilotApplet } from '../views/copilot/copilotApplet';
import { CopilotAssetSeed } from '../views/shared/types/EditorSeed';
import { highlightSnippet } from '../utils/loadPrism';
import ConnectorSingleton from '../../connection/connectorSingleton';
import { PluginGlobalVars } from '../../PluginGlobalVars';

export default class AskQGPTModal extends Modal {
  inputText: HTMLElement | undefined;
  text: string;
  constructor(selection: string) {
    super();

    this.text = selection;
  }

  async onOpen() {
    this.titleEl.innerText = 'Ask Copilot about your selection';

    const selectionRow = document.createElement('div');
    this.contentEl.appendChild(selectionRow); //this.contentEl.createEl('div');
    selectionRow.classList.add('ask-row');
    const selectionCol = document.createElement('div');
    selectionRow.appendChild(selectionCol); //selectionRow.createDiv();
    selectionCol.classList.add('ask-col');
    //@ts-ignore this api is there we just don't got typing ;(
    const activeCell = PluginGlobalVars.defaultApp.shell.currentWidget?.content.activeCell;
    if (activeCell instanceof CodeCell) {
      selectionCol.innerHTML = highlightSnippet({
        snippetContent: this.text.trim(),
        snippetLanguage: ClassificationSpecificEnum.Py,
      });
    } else {
      selectionCol.innerHTML = marked.parse(this.text.trim());
    }

    selectionCol.classList.add('ask-selection');

    const inputRow = document.createElement('div');
    this.contentEl.appendChild(inputRow); //this.contentEl.createEl('div');
    inputRow.classList.add('ask-row', 'ask-input-row');
    const connected = ConnectorSingleton.checkConnection({notification:false});
    const inputCol = document.createElement('div');
    inputRow.appendChild(inputCol); //inputRow.createDiv();
    inputCol.classList.add('ask-col');
    const inputText = document.createElement('span'); //inputCol.createEl('span');
    inputCol.appendChild(inputText);
    inputText.classList.add('ask-input', 'no-edit-border', 'overflow-hidden');
    this.inputText = inputText;
    inputText.classList.add('gpt-input-textarea');
    inputText.title = !versionValid
      ? 'PiecesOS is not up-to-date, please update to use Copilot.'
      : !connected
      ? 'PiecesOS not detected, please launch PiecesOS to use Copilot.'
      : 'Ask a question about your selection';
    inputText.contentEditable =
      !versionValid || !connected ? 'false' : 'true';
    inputText.spellcheck = true;

    inputText.focus();

    const sendCol = document.createElement('div');
    inputRow.appendChild(sendCol); //inputRow.createDiv();
    sendCol.classList.add('ask-col');
    inputCol.classList.add('ask-col', 'ask-col-input');
    const sendDiv = document.createElement('div');
    sendCol.appendChild(sendDiv); //sendCol.createEl('div');
    sendIcon.element({ container: sendDiv });
    sendDiv.classList.add('gpt-img', 'ask-send-div');
    const sendSVG = sendDiv.firstChild as HTMLElement;
    sendSVG.classList.add('gpt-send-unactive');

    sendDiv.onmouseup = async () => {
      // Tested to make sure this is only added once.
      if (inputText.innerText.trim() === '') {
        return;
      }
      this.handleQuery();
    };

    // input handler
    inputText.onkeyup = async (evt) => {
      // Tested to make sure this is only added once.
      if (inputText.innerText !== '') {
        sendSVG.classList.remove('gpt-send-unactive');
        sendSVG.classList.add('gpt-send-active');
      } else {
        sendSVG.classList.remove('gpt-send-active');
        sendSVG.classList.add('gpt-send-unactive');
      }
      if (evt.key !== 'Enter' || evt.shiftKey) {
        return;
      }
      if (inputText.innerText.trim() === '') {
        return;
      }
      sendSVG.classList.remove('gpt-send-active');
      sendSVG.classList.add('gpt-send-unactive');
      this.handleQuery();
    };
    selectionCol.scrollTop = 0;
    selectionCol.children[0].scrollTop = 0;
    if (selectionCol.children[0].children[0])
      selectionCol.children[0].children[0].scrollTop = 0;
    inputText.focus();
  }

  handleQuery() {
    const query = this.inputText?.innerText;
    if (!query) {
      Notifications.getInstance().error({
        message: 'Please enter a question for the Copilot!',
      });
      return;
    }

    const gptTab = document.getElementById('copilot-applet-container') as HTMLDivElement;

    if (gptTab.style.display === 'none') {
      const navTab = document.getElementById('piecesTabs');
      const clickEvt = new Event('click', { bubbles: true });
      navTab?.children[0].dispatchEvent(clickEvt);
    }
    const queryObj: { query: string; relevant: CopilotAssetSeed } = {
      query: query.trim(),
      relevant: { text: this.text.trim(), extension: undefined },
    };
    //@ts-ignore this api is there we just don't got typing ;(
    const activeCell = PluginGlobalVars.defaultApp.shell.currentWidget?.content.activeCell;
    if (activeCell instanceof CodeCell) {
      queryObj.relevant.extension = ClassificationSpecificEnum.Py;
    }
    setTimeout(
      () =>
        copilotApplet.postToFrame({
          type: 'askCopilot',
          destination: 'webview',
          data: queryObj,
        }),
      1400
    );

    if (getStored('AutoOpen')) {
      PluginGlobalVars.defaultApp.shell.activateById('piecesView');
    }

    this.close();
  }

  onClose() {}
}
