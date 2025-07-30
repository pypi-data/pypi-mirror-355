import { JupyterFrontEnd } from '@jupyterlab/application';
import { Widget } from '@lumino/widgets';
import createAsset from '../actions/createAsset';
import Constants from '../const';
import { SegmentAnalytics } from '../analytics/SegmentAnalytics';
import { AnalyticsEnum } from '../analytics/AnalyticsEnum';
import { aiSVG, codeSVG, PiecesLogo, settingsSVG } from './LabIcons';
import { driveApplet } from './views/drive/driveApplets';
import { copilotApplet } from './views/copilot/copilotApplet';
import { Applet } from './views/shared/applet';
import { settingsApplet } from './views/settings/settingsApplet';

export class PiecesView {
  private navTab!: Element;
  private driveTabRadio!: HTMLInputElement;
  private driveTabLabel!: HTMLLabelElement;
  private copilotTabRadio!: HTMLInputElement;
  private copilotTabLabel!: HTMLLabelElement;
  private appletsContainer!: HTMLDivElement;
  private driveAppletContainer!: HTMLDivElement;
  private copilotAppletContainer!: HTMLDivElement;
  private settingsTabLabel!: HTMLLabelElement;
  private settingsTabRadio!: HTMLInputElement;
  private settingsAppletContainer!: HTMLDivElement;
  private containerVar!: Element; // Parent Container Element
  private currentTab: 'copilot' | 'drive' | 'settings' = Constants.DEFAULT_TAB;
  private app: any;
  private viewWidget: Widget;
  private eventListenerAdded = false;

  constructor() {
    this.viewWidget = new Widget();
  }

  public async build(app: JupyterFrontEnd): Promise<void> {
    this.app = app;

    await this.createView();
    this.prepareRightClick();
  }

  private saveSelection(): void {
    SegmentAnalytics.track({
      event: AnalyticsEnum.JUPYTER_SAVE_SELECTION,
    });

    const notebookName = this.app.shell.currentPath ?? 'unknown';
    createAsset({
      selection: this.app.Editor.selection,
      filePath: notebookName === 'unknown' ? undefined : notebookName,
    });
  }

  private prepareRightClick(): void {
    const command = 'jupyter_pieces:menuitem';

    this.app.commands.addCommand(command, {
      label: 'Save to Pieces',
      execute: () => this.saveSelection(), // Fixed to bind correct this context
    });

    this.app.contextMenu.addItem({
      command: command,
      selector: '.jp-CodeCell-input .jp-Editor .jp-Notebook *',
      rank: 100,
    });
  }

  private async createView() {
    this.viewWidget.id = 'piecesView';
    this.viewWidget.title.closable = true;
    this.viewWidget.title.icon = PiecesLogo;

    this.containerVar = this.viewWidget.node;
    this.containerVar.remove();
    this.renderNavBar(this.containerVar);

    await driveApplet.init(this.driveAppletContainer);
    await copilotApplet.init(this.copilotAppletContainer);
    await settingsApplet.init(this.settingsAppletContainer);

    this.app.shell.add(this.viewWidget, 'right', { rank: 1 });
  }

  registerEventHandlers() {
    if (!this.eventListenerAdded) {
      this.navTab.addEventListener('click', (event) => {
        this.changeViews(event);
      });
      window.addEventListener('message', this.messageHandler);
      this.eventListenerAdded = true;
    }
  }
  messageHandler(event: MessageEvent) {
    for (const applet of Applet.instances) {
      if (applet.url.port == new URL(event.origin).port) {
        applet.handler(event);
        break;
      }
    }
  }
  public switchTab(tabName: 'drive' | 'copilot' | 'settings') {
    if (
      !this.driveTabRadio ||
      !this.copilotTabRadio ||
      !this.driveTabLabel ||
      !this.copilotTabLabel ||
      !this.settingsTabRadio ||
      !this.settingsTabLabel
    ) {
      this.renderNavBar(this.containerVar);
    }
    this.activateTab(tabName);
  }

  _showSettings() {
    if (this.settingsAppletContainer) {
      this.settingsAppletContainer.style.display = 'block';
    }
  }

  _hideSettings() {
    if (this.settingsAppletContainer) {
      this.settingsAppletContainer.style.display = 'none';
    }
  }

  activateTab(tabName: 'drive' | 'copilot' | 'settings') {
    this._hideDrive();
    this._hideCopilot();
    this._hideSettings();

    switch (tabName) {
      case 'drive':
        this._showDrive();
        Applet.activeApplet = driveApplet;
        this.driveTabRadio.checked = true;
        this.currentTab = 'drive';
        break;
      case 'copilot':
        this._showCopilot();
        Applet.activeApplet = copilotApplet;
        this.copilotTabRadio.checked = true;
        this.currentTab = 'copilot';
        break;
      case 'settings':
        this._showSettings();
        Applet.activeApplet = settingsApplet;
        this.settingsTabRadio.checked = true;
        this.currentTab = 'settings';
        break;
    }

    // Uncheck the other tabs
    this.driveTabRadio.checked = tabName === 'drive';
    this.copilotTabRadio.checked = tabName === 'copilot';
    this.settingsTabRadio.checked = tabName === 'settings';
  }

  renderNavBar = (containerVar: Element): void => {
    const backgroundDiv = document.createElement('div');
    backgroundDiv.classList.add('background');
    containerVar.appendChild(backgroundDiv);

    const wrapperDiv = document.createElement('div');
    wrapperDiv.classList.add('wrapper');
    containerVar.appendChild(wrapperDiv);

    // Nav tab container
    this.navTab = document.createElement('div');
    wrapperDiv.appendChild(this.navTab);
    this.navTab.classList.add('tabs', 'text-[var(--jp-inverse-layout-color)]');
    this.navTab.id = 'piecesTabs';

    // Pieces Copilot nav tab
    const copilotTabRadio = document.createElement('input');
    this.navTab.appendChild(copilotTabRadio);
    copilotTabRadio.type = 'radio';
    copilotTabRadio.id = 'copilot-tab-radio';
    copilotTabRadio.name = 'copilot-tabs';

    const copilotTabRadioLabel = document.createElement('label');
    this.navTab.appendChild(copilotTabRadioLabel);
    copilotTabRadioLabel.htmlFor = 'copilot-tab-radio';
    copilotTabRadioLabel.classList.add('tab');
    copilotTabRadioLabel.id = 'copilot';
    copilotTabRadioLabel.setAttribute('title', 'Pieces Copilot');

    aiSVG.element({ container: copilotTabRadioLabel });

    // Pieces Drive nav tab
    const driveTabRadio = document.createElement('input');
    this.navTab.appendChild(driveTabRadio);
    driveTabRadio.type = 'radio';
    driveTabRadio.id = 'drive-tab-radio';
    driveTabRadio.name = 'drive-tabs';

    const driveTabRadioLabel = document.createElement('label');
    this.navTab.appendChild(driveTabRadioLabel);
    driveTabRadioLabel.htmlFor = 'drive-tab-radio';
    driveTabRadioLabel.classList.add('tab');
    driveTabRadioLabel.id = 'drive';
    driveTabRadioLabel.setAttribute('title', 'Pieces Drive');

    codeSVG.element({ container: driveTabRadioLabel });

    // Pieces Settings nav tab
    const settingsTabRadio = document.createElement('input');
    this.navTab.appendChild(settingsTabRadio);
    settingsTabRadio.type = 'radio';
    settingsTabRadio.id = 'settings-tab-radio';
    settingsTabRadio.name = 'settings-tabs';

    const settingsTabRadioLabel = document.createElement('label');
    this.navTab.appendChild(settingsTabRadioLabel);
    settingsTabRadioLabel.htmlFor = 'settings-tab-radio';
    settingsTabRadioLabel.classList.add('tab');
    settingsTabRadioLabel.id = 'settings';
    settingsTabRadioLabel.setAttribute('title', 'Pieces Settings');

    settingsSVG.element({ container: settingsTabRadioLabel });

    const slider = document.createElement('span');
    this.navTab.appendChild(slider);
    slider.classList.add('glider');

    // set elements as class properties
    this.driveTabLabel = driveTabRadioLabel;
    this.driveTabRadio = driveTabRadio;
    this.copilotTabLabel = copilotTabRadioLabel;
    this.copilotTabRadio = copilotTabRadio;
    this.settingsTabLabel = settingsTabRadioLabel;
    this.settingsTabRadio = settingsTabRadio;

    this.appletsContainer = document.createElement('div');
    this.appletsContainer.classList.add('parent-div-container', 'w-full');
    this.appletsContainer.id = 'pieces-applets-container';
    containerVar.appendChild(this.appletsContainer);

    this.driveAppletContainer = document.createElement('div');
    this.driveAppletContainer.classList.add('px-2', 'w-full', 'pt-8');
    this.driveAppletContainer.id = 'drive-applet-container';
    this.appletsContainer.appendChild(this.driveAppletContainer);

    this.copilotAppletContainer = document.createElement('div');
    this.copilotAppletContainer.classList.add('px-2', 'w-full', 'pt-8');
    this.copilotAppletContainer.id = 'copilot-applet-container';
    this.appletsContainer.appendChild(this.copilotAppletContainer);

    this.settingsAppletContainer = document.createElement('div');
    this.settingsAppletContainer.classList.add('px-2', 'w-full', 'pt-8');
    this.settingsAppletContainer.id = 'settings-applet';
    this.appletsContainer.appendChild(this.settingsAppletContainer);

    this.copilotTabRadio.checked = true;
    this.driveTabRadio.checked = false;
    this.settingsTabRadio.checked = false;
    if (this.currentTab === 'drive') {
      this._hideCopilot();
      this._hideSettings();
    } else if (this.currentTab === 'copilot') {
      this._hideDrive();
      this._hideSettings();
    } else if (this.currentTab === 'settings') {
      this._hideCopilot();
      this._hideDrive();
    }
    this.switchTab(this.currentTab);
    // run last to ensure all elements are rendered
    this.registerEventHandlers();
  };

  private changeViews(event: Event) {
    event.stopPropagation();
    event.preventDefault();

    const target = event.target as HTMLElement;
    if (target.id !== this.currentTab) {
      this.switchTab(target.id as 'drive' | 'copilot' | 'settings');
    }
  }

  _hideCopilot() {
    if (this.copilotAppletContainer) {
      this.copilotAppletContainer.style.display = 'none';
    }
  }

  _hideDrive() {
    if (this.driveAppletContainer) {
      this.driveAppletContainer.style.display = 'none';
    }
  }

  _showCopilot() {
    if (this.copilotAppletContainer) {
      this.copilotAppletContainer.style.display = 'flex';
    }
  }

  _showDrive() {
    if (this.driveAppletContainer) {
      this.driveAppletContainer.style.display = 'block';
    }
  }
}
