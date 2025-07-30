import Notifications from './Notifications';
import ConnectorSingleton from './connectorSingleton';
import { launchRuntime } from '../actions/launchRuntime';
import { gte, lt } from 'semver';

const notifications: Notifications = Notifications.getInstance();
const config: ConnectorSingleton = ConnectorSingleton.getInstance();
export const currentMinVersion = '12.0.0';
export const currentMaxVersion = '13.0.0';
export let versionValid = false;

/*
    Returns promise<true> if the user has a supported version of POS for this plugin
    otherwise... promise<false>
*/
export default async function versionCheck({
  retry,
  minVersion,
  notify = false,
}: {
  retry?: boolean;
  minVersion?: string;
  notify?: boolean;
}): Promise<boolean> {
  try {
    if (versionValid) {
      return versionValid;
    }
    const osVersion: string = await config.wellKnownApi.getWellKnownVersion();
    console.log('Pieces for Developers:  PiecesOS Version: ', osVersion);
    if (osVersion.includes('staging') || osVersion.includes('debug')) {
      versionValid = true;
      return true;
    }

    versionValid =
      gte(osVersion, minVersion ?? currentMinVersion) &&
      lt(osVersion, currentMaxVersion);

    if (!versionValid && notify) {
      notifications.error({
        message: `In order to use the Pieces for Jupyter lab extension, you must have PiecesOS version ${currentMinVersion} or greater! Please update your PiecesOS`,
      });
    }

    return versionValid;
  } catch (error: any) {
    if (retry) {
      console.log('retrying');
      return false;
    }
    if (error.code === 'ECONNREFUSED') {
      await launchRuntime(true);
    }
    return await versionCheck({ retry: true });
  }
}

/*
  The above function has a very bad side effect so I'm going to implement 
  this with a TODO to refactor the versionValid variable in this file...
   - caleb
*/
export async function versionChecker({
  retry,
  minVersion,
}: {
  retry?: boolean;
  minVersion?: string;
  notify?: boolean;
}): Promise<boolean> {
  try {
    const osVersion: string = await config.wellKnownApi.getWellKnownVersion();

    if (osVersion.includes('staging') || osVersion.includes('debug')) {
      return true;
    }

    return (
      gte(osVersion, minVersion ?? currentMinVersion) &&
      lt(osVersion, currentMaxVersion)
    );
  } catch (error: any) {
    if (retry) {
      console.log('retrying');
      return false;
    }
    if (error.code === 'ECONNREFUSED') {
      await launchRuntime(true);
    }
    return await versionCheck({ retry: true });
  }
}
