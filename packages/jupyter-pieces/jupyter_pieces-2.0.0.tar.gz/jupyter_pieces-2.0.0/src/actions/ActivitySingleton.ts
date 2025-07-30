import ConnectorSingleton from '../connection/connectorSingleton';
import {
  MechanismEnum,
  SeededActivity,
  TrackedAssetEventIdentifierDescriptionPairsAssetFormatCopiedEnum,
  TrackedAssetEventIdentifierDescriptionPairsAssetReferencedEnum,
  TrackedAssetEventIdentifierDescriptionPairsSearchedAssetReferencedEnum,
} from '@pieces.app/pieces-os-client';
import { AnalyticsTrackedAdoptionEventIdentifierDescriptionPairsAdoptionInstallEnum } from '@pieces.app/pieces-os-client';

export default class ActivitySingleton {
  private static instance: ActivitySingleton;

  private constructor() {
    /* */
  }

  public static getInstance() {
    return (this.instance ??= new ActivitySingleton());
  }

  public async referenced(id: string, query?: string, copied = false) {
    const config = ConnectorSingleton.getInstance();
    const seededActivity: SeededActivity = {
      application: config.context.application,
      mechanism: MechanismEnum.Automatic,
      asset: {
        id,
      },
      event: {
        asset: {
          asset: {
            id,
          },
          identifierDescriptionPair: {
            assetReferenced:
              TrackedAssetEventIdentifierDescriptionPairsAssetReferencedEnum.AnAssetWasReferencedByTheUser,
          },
        },
      },
    };
    if (copied) {
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      seededActivity.event.asset!.identifierDescriptionPair = {
        assetFormatCopied:
          TrackedAssetEventIdentifierDescriptionPairsAssetFormatCopiedEnum.AnAssetPreviewFormatWasCopied,
      };
    }
    if (query) {
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      seededActivity.event.asset!.metadata = {
        search: {
          query,
        },
      };
      // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
      seededActivity.event.asset!.identifierDescriptionPair! = {
        searchedAssetReferenced:
          TrackedAssetEventIdentifierDescriptionPairsSearchedAssetReferencedEnum.ASearchedAssetWasReferencedByTheUser,
      };
    }
    return config.activitiesApi
      .activitiesCreateNewActivity({
        transferables: false,
        seededActivity,
      })
      .catch();
  }

  public async installed() {
    const config = ConnectorSingleton.getInstance();
    const seededActivity: SeededActivity = {
      application: config.context.application,
      mechanism: MechanismEnum.Automatic,
      event: {
        adoption: {
          identifierDescriptionPair: {
            adoptionInstall:
              AnalyticsTrackedAdoptionEventIdentifierDescriptionPairsAdoptionInstallEnum.TheUserHasInstalledAPiecesApplication,
          },
        },
      },
    };
    return config.activitiesApi
      .activitiesCreateNewActivity({
        transferables: false,
        seededActivity,
      })
      .catch();
  }
}
