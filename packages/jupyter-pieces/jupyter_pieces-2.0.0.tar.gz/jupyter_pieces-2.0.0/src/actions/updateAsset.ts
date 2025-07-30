import ConnectorSingleton from '../connection/connectorSingleton';
import {
  AssetReclassification,
  AssetReclassifyRequest,
  ClassificationGenericEnum,
  Format,
} from '@pieces.app/pieces-os-client';
import { ClassificationSpecificEnum } from '@pieces.app/pieces-os-client';
import { Asset } from '@pieces.app/pieces-os-client';
import Notifications from '../connection/Notifications';
import Constants from '../const';
import { SegmentAnalytics } from '../analytics/SegmentAnalytics';
import { AnalyticsEnum } from '../analytics/AnalyticsEnum';
import { NotificationActionTypeEnum } from '../ui/views/shared/types/NotificationParameters';
import BrowserUrl from '../utils/browserUrl';

const config = ConnectorSingleton.getInstance();
const notifications = Notifications.getInstance();

export const reclassify = async ({
  asset,
  ext,
}: {
  asset: Asset;
  ext: ClassificationSpecificEnum;
}): Promise<Asset | void> => {
  try {
    const isImage =
      asset.original.reference?.classification.generic ===
      ClassificationGenericEnum.Image;
    let ret = asset;
    if (isImage) {
      const ocrId = asset.original.reference?.analysis?.image?.ocr?.raw.id;

      if (!ocrId) {
        // we don't have an ocrId somehow
        console.log('No OCRId Available');
        return asset;
      }

      const format = asset.formats.iterable?.find(
        (format) => format.id === ocrId
      );

      if (!format) {
        // we don't have a format somehow
        console.log('Failed to find the format on an asset');
        return asset;
      }

      format.file = undefined;
      format.fragment = undefined;

      await config.formatApi.formatReclassify({
        formatReclassification: {
          ext: ext,
          format: format,
        },
      });
      ret = await config.assetApi.assetSnapshot({
        asset: asset.id,
        transferables: true,
      });
    } else {
      const reclassification: AssetReclassification = {
        asset: asset,
        ext: ext,
      };
      const params: AssetReclassifyRequest = {
        assetReclassification: reclassification,
        transferables: false,
      };
      ret = await config.assetApi.assetReclassify(params);
    }

    notifications.information({ message: Constants.RECLASSIFY_SUCCESS });
    return ret;
  } catch (error) {
    console.error(error);
    notifications.error({
      message: Constants.RECLASSIFY_FAILURE,
      actions: [
        {
          title: 'Contact Support',
          type: NotificationActionTypeEnum.OPEN_LINK,
          params: { url: BrowserUrl.appendParams('https://docs.pieces.app/products/support') },
        },
      ],
    });
    return;
  }
};

export const update = async ({
  asset,
}: {
  asset: Asset;
}): Promise<Asset | void> => {
  SegmentAnalytics.track({
    event: AnalyticsEnum.JUPYTER_EDIT_MATERIAL,
  });

  try {
    const ret: Asset = await config.assetApi.assetUpdate({ asset: asset });
    notifications.information({ message: Constants.UPDATE_SUCCESS });

    SegmentAnalytics.track({
      event: AnalyticsEnum.JUPYTER_EDIT_MATERIAL_SUCCESS,
    });

    return ret;
  } catch (error) {
    // console.error(error);

    SegmentAnalytics.track({
      event: AnalyticsEnum.JUPYTER_EDIT_MATERIAL_FAILURE,
    });

    notifications.error({
      message: Constants.UPDATE_FAILURE,
      actions: [
        {
          title: 'Contact Support',
          type: NotificationActionTypeEnum.OPEN_LINK,
          params: { url: BrowserUrl.appendParams('https://docs.pieces.app/products/support') },
        },
      ],
    });
    return;
  }
};

export const updateFormat = async ({ format }: { format: Format }) => {
  try {
    const ret = await config.formatApi.formatUpdateValue({ format: format });
    notifications.information({ message: Constants.UPDATE_CODE_SUCCESS });
    return ret;
  } catch (error) {
    console.error(error);
    notifications.error({
      message: Constants.UPDATE_CODE_FAILURE,
      actions: [
        {
          title: 'Contact Support',
          type: NotificationActionTypeEnum.OPEN_LINK,
          params: { url: BrowserUrl.appendParams('https://docs.pieces.app/products/support') },
        },
      ],
    });
    return;
  }
};
