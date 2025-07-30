/* eslint-disable @typescript-eslint/no-explicit-any */
/* eslint-disable no-mixed-spaces-and-tabs */
import * as semver from 'semver';
import { v4 as uuidv4 } from 'uuid';
import getTheme from './theme';
import { showErrorView } from './errorView';
import PiecesOSUpdating from '../../modals/PiecesOSUpdating';
import ConnectorSingleton from '../../../connection/connectorSingleton';
import { launchRuntime } from '../../../actions/launchRuntime';
import {
  currentMaxVersion,
  currentMinVersion,
} from '../../../connection/versionCheck';

export abstract class Applet {
  protected iframe!: HTMLIFrameElement;
  protected tab!: HTMLDivElement;
  protected iframeId: string;
  public url!: URL;
  protected static minimumVersion = currentMinVersion;
  protected static maximumVersion = currentMaxVersion;
  protected static migration: number;
  protected static schemaNumber = 0;
  static resolveLoading: () => void;
  static loadingPromise: Promise<void> = new Promise(
    (resolve) => (Applet.resolveLoading = resolve)
  );
  abstract getUrl(): Promise<URL>;
  static activeApplet: Applet;
  public handler!: (event: MessageEvent) => void;
  static instances: Applet[] = [];
  static _updateModalShowed = false;

  constructor(iframeId: string, handler: (event: MessageEvent) => void) {
    this.iframeId = iframeId;
    this.handler = handler;
    Applet.instances.push(this);
  }
  public static waitForDBPromise: Promise<void> = new Promise(
    (resolve) => (Applet.resolveDBLock = resolve)
  );
  public static resolveDBLock: () => void;

  async init(tab: HTMLDivElement) {
    this.tab = tab;
    this.setupFrame();
    this.tab.appendChild(this.iframe);
    this.connectionPoller();
    this.setupThemeObserver();
  }

  protected setupThemeObserver() {
    const setTheme = () => {
      this.iframe.contentWindow?.postMessage(
        {
          type: 'setTheme',
          destination: 'webview',
          data: getTheme(),
        },
        '*'
      );
    };

    const observer = new MutationObserver(() => {
      setTheme();
    });
    observer.observe(document.body, { attributes: true });
  }

  static launchPos() {
    launchRuntime();
  }

  protected getNextMessageId() {
    return uuidv4();
  }

  protected async setupFrame() {
    this.iframe = document.createElement('iframe');
    this.iframe.id = this.iframeId;
    this.iframe.name = this.iframeId;
    this.iframe.classList.add('!hidden');
    this.iframe.setAttribute(
      'style',
      'width: 100%; height: 100%; margin: 0px; overflow: hidden; border: none;'
    );
    this.iframe.setAttribute('allow', 'clipboard-read; clipboard-write;');
  }

  async postToFrame(message: { [key: string]: any }) {
    message.destination = 'webview';
    await Applet.loadingPromise;
    this.iframe.contentWindow?.postMessage(message, '*');
  }

  protected async checkForConnection() {
    return ConnectorSingleton.getInstance()
      .wellKnownApi.getWellKnownHealth()
      .then(() => true)
      .catch(() => false);
  }

  protected async connectionPoller(): Promise<void> {
    const connected = await this.checkForConnection();

    let version = await ConnectorSingleton.getInstance()
      .wellKnownApi.getWellKnownVersion()
      .catch(() => null);

    const isStaging = version?.includes('staging');
    version = version?.replace('-staging', '') ?? null;
    const isDebug = version?.includes('debug');
    if (!isStaging && !isDebug && version) {
      // PiecesOS needs to update
      if (version && semver.lt(version, Applet.minimumVersion)) {
        this.tab.classList.remove('!hidden');
        this.iframe?.classList.add('!hidden');
        // PiecesOS does not have auto update capabilities previously 9.0.2
        if (semver.gt(version, '9.0.2') && !Applet._updateModalShowed) {
          Applet._updateModalShowed = true;
          new PiecesOSUpdating().open();
        }
        showErrorView('Please Update PiecesOS!', this.tab);
        return this.connectDelay();
      }
      // extension needs to update
      if (version && semver.gte(version, Applet.maximumVersion)) {
        this.tab.classList.remove('!hidden');
        this.iframe.classList.add('!hidden');
        showErrorView(
          `The Pieces for Jupyter extension needs to be updated in order to work with PiecesOS version >= ${Applet.maximumVersion}`,
          this.tab
        );

        return this.connectDelay();
      }
    }
    if (!connected) {
      this.iframe.classList.add('!hidden');
      if (!document.getElementById(`${this.tab.id}-error-view`))
        showErrorView('PiecesOS is not running!', this.tab);
    } else if (this.iframe.classList.contains('!hidden')) {
      document.getElementById(`${this.tab.id}-error-view`)?.remove();
      this.iframe.classList.remove('!hidden');
      this.setIframeUrl();
    }
    return this.connectDelay();
  }

  protected async connectDelay() {
    await new Promise((res) => setTimeout(res, 5000));
    return this.connectionPoller();
  }

  protected async setIframeUrl() {
    if (this.iframe === null) {
      this.iframe = document.getElementById(this.iframeId) as HTMLIFrameElement;
    }
    if (!this.iframe) this.setupFrame();

    await Applet.waitForDBPromise;
    this.url = await this.getUrl();
    this.iframe.src = this.url.href;
    this.iframe.src = this.url.href;
  }
}
