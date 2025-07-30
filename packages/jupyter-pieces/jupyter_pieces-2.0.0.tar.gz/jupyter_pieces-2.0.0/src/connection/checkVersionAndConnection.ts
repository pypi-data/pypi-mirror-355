import { loadConnect } from './apiWrapper';
import versionCheck, { versionValid } from './versionCheck';
import { waitTimer, setStreamOpen } from './streamAssets';
import { sleep } from '../utils/sleep';

export default class CheckVersionAndConnection {
  private static promise: Promise<void> | undefined = undefined;

  private constructor() {}

  public static run() {
    if (this.promise === undefined) {
      this.promise = this._run();
    }
    return this.promise;
  }

  /*
        This will recursively call itself until BOTH POS is open AND POS has a proper version
         - also makes sure to update ui when fetchFailed changes
    */
  private static async _run(): Promise<void> {
    const posOpen = await loadConnect(); // whether or not pos is open
    await versionCheck({}); // whether or not pos has the correct version for this plugin

    if (posOpen && versionValid) {
      // if both are good, we can break out of this function
      this.promise = undefined;
      return;
    }

    /*
                If POS is open, and the fetch failed, need to update fetch failed to false
                if pos is closed, and the initial fetch did not fail, need to update fetch failed to true
            */

    await sleep(waitTimer);
    setStreamOpen(false);
    return this._run();
  }
}
