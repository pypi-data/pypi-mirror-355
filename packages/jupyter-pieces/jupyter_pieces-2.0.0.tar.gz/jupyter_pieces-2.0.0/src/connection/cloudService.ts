import ConnectorSingleton from './connectorSingleton';
import {
  AllocationCloud,
  AllocationStatusEnum,
  ReturnedUserProfile,
  UserProfile,
} from '@pieces.app/pieces-os-client';
import pRetry from 'p-retry';
import Notifications from './Notifications';
import Constants from '../const';

export default class CloudService {
  private static instance: CloudService;

  private config: ConnectorSingleton = ConnectorSingleton.getInstance();
  private notifications: Notifications = Notifications.getInstance();
  private constructor() {}

  public static getInstance(): CloudService {
    if (!CloudService.instance) {
      CloudService.instance = new CloudService();
    }

    return CloudService.instance;
  }

  public async connect({
    user,
  }: {
    user?: UserProfile;
  }): Promise<AllocationCloud | undefined> {
    if (!user) {
      const profile: ReturnedUserProfile =
        await this.config.userApi.userSnapshot();
      if (!profile.user) {
        this.notifications.error({
          message: Constants.LOGIN_TO_POS_CLOUD,
        });
        return;
      }
      user = profile.user;
    }

    let connected: AllocationCloud | undefined;
    const connectCloud = async () => {
      connected = await this.config.allocationsApi.allocationsConnectNewCloud({
        userProfile: user,
      });
      if (connected.status.cloud !== AllocationStatusEnum.Running) {
        throw new Error('Unable to Connect');
      }
    };

    await pRetry(connectCloud, { retries: 5 });

    if (connected?.status.cloud !== AllocationStatusEnum.Running) {
      this.notifications.error({ message: Constants.CLOUD_CONNECT_FAIL });
      return;
    }
    this.notifications.information({
      message: Constants.CLOUD_CONNECT_SUCCESS,
    });
    return connected;
  }

  public async disconnect({ user }: { user?: UserProfile }): Promise<boolean> {
    try {
      const { config } = this;
      user = user ? user : (await config.userApi.userSnapshot()).user;
      if (!user || !user?.allocation) {
        this.notifications.information({
          message: Constants.CLOUD_DISCONNECT_ALR,
        });
        return true;
      }
      await config.allocationsApi.allocationsDisconnectCloud({
        allocationCloud: user.allocation,
      });
      this.notifications.information({
        message: Constants.CLOUD_DISCONNECT_SUCCESS,
      });

      return true;
    } catch (error) {
      this.notifications.error({
        message: Constants.CLOUD_DISCONNECT_FAIL,
      });
      return false;
    }
  }
}
