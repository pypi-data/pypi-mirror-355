import ConnectorSingleton from '../../connection/connectorSingleton';
import { UpdatingStatusEnum } from '@pieces.app/pieces-os-client';
import Notifications from '../../connection/Notifications';
import Modal from './Modal';
import BrowserUrl from '../../utils/browserUrl';

export default class PiecesOSUpdating extends Modal {
  private static instance: PiecesOSUpdating;
  btnRow!: HTMLDivElement;
  progressContainer!: HTMLElement;
  notifications: Notifications = Notifications.getInstance();
  expTitleRow!: HTMLDivElement;

  async onOpen() {
    this.titleEl.innerHTML = 'PiecesOS is updating';

    this.expTitleRow = document.createElement('div');
    this.expTitleRow.classList.add('row');
    this.contentEl.appendChild(this.expTitleRow);
    this.expTitleRow.innerText =
      'There is a new version of PiecesOS available. Do you want to update it?';

    this.btnRow = document.createElement('div');
    this.btnRow.classList.add('row');
    this.btnRow.classList.add('justify-around');
    this.contentEl.appendChild(this.btnRow);

    const installBtn = document.createElement('button');
    installBtn.classList.add('jp-btn');
    installBtn.addEventListener('click', () => {
      this.performUpdate();
    });

    installBtn.innerText = 'Update';
    installBtn.title = 'Update PiecesOS';
    this.btnRow.appendChild(installBtn);

    const cancelBtn = document.createElement('button');
    cancelBtn.classList.add('jp-btn');
    cancelBtn.addEventListener('click', () => {
      this.close();
    });
    cancelBtn.innerText = 'Cancel';
    cancelBtn.title = 'Cancel update';
    this.btnRow.appendChild(cancelBtn);
  }
  protected onClose(): void {}
  /**
   * This will render the 'PiecesOS is updating' ui & update PiecesOS
   * @returns a promise which is resolved after timing out, or after PiecesOS has successfully been updated
   */
  public async performUpdate(): Promise<boolean> {
    this.btnRow.classList.add('font-bold');
    setTimeout(async () => {
      this.btnRow.innerHTML = 'Checking for updates...';
    }, 100);

    let resolve: (val: boolean) => void;
    const ret = new Promise<boolean>((res) => {
      resolve = res;
    });

    // let timeoutId: NodeJS.Timeout;
    const intervalId = setInterval(async () => {
      const status = await ConnectorSingleton.getInstance()
        .osApi.osUpdateCheck({ uncheckedOSServerUpdate: {} })
        .catch(() => {
          return null;
        });
      this.btnRow.innerText = this.getStatusText(status?.status);
      if (status?.status === UpdatingStatusEnum.ReadyToRestart) {
        clearInterval(intervalId);
        this.btnRow.innerText = 'Restarting to apply the update';
        ConnectorSingleton.getInstance().osApi.osRestart();
        this.pollForConnection(resolve);
      }
    }, 3e3);
    // timeoutId =
    setTimeout(() => {
      clearInterval(intervalId);
      resolve(false);
    }, 10 * 60 * 1000); // after 10 minutes we will exit this task forcefully
    return ret;
  }

  /**
   * This will poll for a connection to PiecesOS (after the connection is lost due to restarting)
   * & resolve the updater promise when it has found a connection
   * if it doesn't find a connection after 5 minutes it will cancel the task
   * @param resolver the function to resolve the updater promise
   * @param removeMouseMoveListener function to remove the mouse move listener from the svg
   */
  private async pollForConnection(resolver: (val: boolean) => void) {
    let timeoutId: NodeJS.Timeout | undefined = undefined;
    const intervalId = setInterval(async () => {
      const connected = await ConnectorSingleton.getInstance()
        .wellKnownApi.getWellKnownHealth()
        .then(() => true)
        .catch(() => false);
      if (connected) {
        clearInterval(intervalId);
        resolver(true);
        clearTimeout(timeoutId);
      }
    }, 500);

    timeoutId = setTimeout(() => {
      clearInterval(intervalId);
      resolver(false);
    }, 5 * 60 * 1000); // after 5 minutes we will fail this task
  }

  // @ts-ignore
  private isInProgressStatus(status: UpdatingStatusEnum | undefined) {
    return (
      [
        UpdatingStatusEnum.Available,
        UpdatingStatusEnum.ReadyToRestart,
        UpdatingStatusEnum.Downloading,
      ] as Array<UpdatingStatusEnum | undefined>
    ) // gotta love typescript enums!!!
      .includes(status);
  }

  /**
   * This converts UpdatingStatusEnum to a more user friendly format
   * @param status the status from the os update check endpoint
   * @returns readable text to represent the status
   */
  private getStatusText(status: UpdatingStatusEnum | undefined) {
    const url = BrowserUrl.appendParams('https://docs.pieces.app/products/support');
    switch (status) {
      case UpdatingStatusEnum.Available:
        return 'Update detected...';
      case UpdatingStatusEnum.ContactSupport:
        return 'Something went wrong. Please contact support at ' + url ;
      case UpdatingStatusEnum.Downloading:
        return 'Update is downloading...';
      case UpdatingStatusEnum.ReadyToRestart:
        return 'Restarting to apply the update...';
      case UpdatingStatusEnum.ReinstallRequired:
        return 'You need to reinstall PiecesOS for this feature to work!';
      case UpdatingStatusEnum.Unknown:
        return 'Unknown status';
      case UpdatingStatusEnum.UpToDate:
        return 'PiecesOS is up to date.';
      case undefined:
        return 'Failed to get update status, please contact support at ' + url;
    }
  }

  public static getInstance() {
    return (this.instance ??= new PiecesOSUpdating());
  }
}
