import { launchRuntime } from '../actions/launchRuntime';
import { AllocationCloud, Asset, Shares } from '@pieces.app/pieces-os-client';
import { AccessEnum, AllocationStatusEnum } from '@pieces.app/pieces-os-client';
import CloudService from './cloudService';
import ConnectorSingleton from './connectorSingleton';
import Notifications from './Notifications';
import Constants from '../const';
import { SegmentAnalytics } from '../analytics/SegmentAnalytics';
import { AnalyticsEnum } from '../analytics/AnalyticsEnum';
import { NotificationActionTypeEnum } from '../ui/views/shared/types/NotificationParameters';
import BrowserUrl from '../utils/browserUrl';

export default class ShareableLinksService {
  private static instance: ShareableLinksService;

  private config: ConnectorSingleton = ConnectorSingleton.getInstance();
  private cloud: CloudService = CloudService.getInstance();
  private notifications: Notifications = Notifications.getInstance();

  private constructor() {}

  public static getInstance(): ShareableLinksService {
    if (!ShareableLinksService.instance) {
      ShareableLinksService.instance = new ShareableLinksService();
    }

    return ShareableLinksService.instance;
  }

  public async generate({
    id,
    retry = false,
  }: {
    id: string;
    retry?: boolean;
  }): Promise<string | void> {
    SegmentAnalytics.track({
      event: AnalyticsEnum.JUPYTER_SHARE,
    });

    try {
      //
      const { config, cloud, notifications } = this;
      const profile = await config.userApi.userSnapshot();

      if (!profile?.user) {
        notifications.error({ message: Constants.LOGIN_TO_POS });
        return;
      } else if (!profile?.user?.allocation) {
        // TODO notify user cloud is connecting
        const allocation: AllocationCloud | undefined = await cloud.connect({
          user: profile?.user,
        });
        if (!allocation) {
          notifications.error({
            message: Constants.CLOUD_CONNECT_FAIL,
          });
          return;
        }
        profile.user.allocation = allocation;
      } else if (
        profile?.user?.allocation?.status.cloud != AllocationStatusEnum.Running
      ) {
        notifications.error({
          message: Constants.CLOUD_CONNECT_INPROG,
        });
        return;
      }

      const asset: Asset = await config.assetApi
        .assetSnapshot({ asset: id })
        .catch((error) => {
          if (error.status === 410) {
            throw new Error('Material no longer exists');
          } else {
            throw new Error('Please check that PiecesOS is installed');
          }
        });

      notifications.information({ message: `Generating a link...` });
      const link: Shares = await config.linkifyApi
        .linkify({
          linkify: {
            asset,
            access: AccessEnum.Public,
          },
        })
        .catch((error) => {
          // TODO: Does it make sense to throw Errors inside a catch statement?
          if (error.status === 413) {
            SegmentAnalytics.track({
              event: AnalyticsEnum.JUPYTER_SHARE_FAILURE,
            });
            throw new Error(
              `Failed to generate shareable link. The asset is too large. Please try a smaller asset.`
            );
          } else if (error.status === 500) {
            SegmentAnalytics.track({
              event: AnalyticsEnum.JUPYTER_SHARE_FAILURE,
            });
            throw new Error(
              `Failed to generate shareable link. Please update your PiecesOS.`
            );
          } else if (error.status === 511) {
            SegmentAnalytics.track({
              event: AnalyticsEnum.JUPYTER_SHARE_FAILURE,
            });
            throw new Error(
              `Failed to generate shareable link. Please make sure you are signed in and connected to cloud.`
            );
          } else {
            SegmentAnalytics.track({
              event: AnalyticsEnum.JUPYTER_SHARE_FAILURE,
            });
            throw new Error(
              `Failed to generate shareable link. Please check that PiecesOS is installed and running.`
            );
          }
        });

      notifications.information({
        message: Constants.LINK_GEN_SUCCESS,
      });

      SegmentAnalytics.track({
        event: AnalyticsEnum.JUPYTER_SHARE_SUCCESS,
      });
      return link.iterable[0].link;
    } catch (error: any) {
      const { config, notifications } = this;
      if (error.status === 401 || error.status === 400) {
        if (retry) {
          notifications.error({
            message: Constants.LINK_GEN_FAIL,
            actions: [
              {
                title: 'Contact Support',
                type: NotificationActionTypeEnum.OPEN_LINK,
                params: { url: BrowserUrl.appendParams('https://docs.pieces.app/products/support') },
              },
            ],
          });
          SegmentAnalytics.track({
            event: AnalyticsEnum.JUPYTER_SHARE_FAILURE,
          });
        } else {
          try {
            config.context = await config.api.connect({
              seededConnectorConnection: config.seeded,
            });
            return await this.generate({ id, retry: true });
          } catch (e) {
            console.log(`Error from generating link ${e}`);
          }
        }
      } else {
        if (!retry) {
          if (error.code === 'ECONNREFUSED') {
            // attempt to launch runtime because we could talk to POS.
            await launchRuntime(true);
          }
          // then retry our request.
          return await this.generate({ id, retry: true });
        }

        notifications.error({
          message: Constants.LINK_GEN_FAIL,
          actions: [
            {
              title: 'Contact Support',
              type: NotificationActionTypeEnum.OPEN_LINK,
              params: { url: BrowserUrl.appendParams('https://docs.pieces.app/products/support') },
            },
          ],
        });
        SegmentAnalytics.track({
          event: AnalyticsEnum.JUPYTER_SHARE_FAILURE,
        });
      }
    }
  }
}
