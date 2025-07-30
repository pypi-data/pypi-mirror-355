import ConnectorSingleton from '../connection/connectorSingleton';
import {
  AssetsDraftRequest,
  ClassificationSpecificEnum,
} from '@pieces.app/pieces-os-client';
import { SeedTypeEnum } from '@pieces.app/pieces-os-client';

export const draft_asset = ({ text }: { text: string }) => {
  const config = ConnectorSingleton.getInstance();
  const params: AssetsDraftRequest = {
    seed: {
      asset: {
        application: config.context.application,
        format: {
          fragment: {
            string: {
              raw: text,
            },
          },
          classification: {
            specific: ClassificationSpecificEnum.Py,
          },
        },
      },
      type: SeedTypeEnum.SeededAsset,
    },
  };
  return config.assetsApi.assetsDraft(params);
};
