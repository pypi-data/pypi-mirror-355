import ConnectorSingleton from '../connection/connectorSingleton';
import { launchRuntime } from './launchRuntime';
import Notifications from '../connection/Notifications';
import PiecesCacheSingleton from '../cache/piecesCacheSingleton';
import Constants from '../const';
import { SegmentAnalytics } from '../analytics/SegmentAnalytics';
import { AnalyticsEnum } from '../analytics/AnalyticsEnum';
import { NotificationActionTypeEnum } from '../ui/views/shared/types/NotificationParameters';
import BrowserUrl from '../utils/browserUrl';

export default class DeletePiece {
  public static async delete({
    id,
    retry = false,
  }: {
    id: string;
    retry?: boolean;
  }): Promise<void> {
    SegmentAnalytics.track({
      event: AnalyticsEnum.JUPYTER_DELETE,
    });

    const config: ConnectorSingleton = ConnectorSingleton.getInstance();
    const notifications: Notifications = Notifications.getInstance();
    const storage: PiecesCacheSingleton = PiecesCacheSingleton.getInstance();

    try {
      const piece = storage.mappedAssets[id];
      if (!piece) {
        notifications.information({
          message: Constants.MATERIAL_IS_DELETED,
        });
        return;
      }
      await config.assetsApi.assetsDeleteAsset({ asset: id });

      notifications.information({
        message: Constants.MATERIAL_DELETE_SUCCESS,
      });
      SegmentAnalytics.track({
        event: AnalyticsEnum.JUPYTER_DELETE_SUCCESS,
      });
    } catch (error: any) {
      if (error.status === 401 || error.status === 400) {
        if (retry) {
          notifications.error({
            message: Constants.MATERIAL_DELETE_FAILURE,
            actions: [
              {
                title: 'Contact Support',
                type: NotificationActionTypeEnum.OPEN_LINK,
                params: { url: BrowserUrl.appendParams('https://docs.pieces.app/products/support') },
              },
            ],
          });
          SegmentAnalytics.track({
            event: AnalyticsEnum.JUPYTER_DELETE_FAILURE,
          });
        } else {
          try {
            config.context = await config.api.connect({
              seededConnectorConnection: config.seeded,
            });
            return await this.delete({ id, retry: true });
          } catch (e) {
            console.log(`Error from deleting material ${e}`);
            SegmentAnalytics.track({
              event: AnalyticsEnum.JUPYTER_DELETE_FAILURE,
            });
          }
        }
      } else {
        if (!retry) {
          if (error.code === 'ECONNREFUSED') {
            // attempt to launch runtime because we could talk to POS.
            await launchRuntime(true);
            config.context = await config.api.connect({
              seededConnectorConnection: config.seeded,
            });
          }
          // then retry our request.
          return await this.delete({ id, retry: true });
        }
        notifications.error({
          message: Constants.MATERIAL_DELETE_FAILURE,
          actions: [
            {
              title: 'Contact Support',
              type: NotificationActionTypeEnum.OPEN_LINK,
              params: { url: BrowserUrl.appendParams('https://docs.pieces.app/products/support') },
            },
          ],
        });
        SegmentAnalytics.track({
          event: AnalyticsEnum.JUPYTER_DELETE_FAILURE,
        });
      }
    }
  }
}
