import ConnectorSingleton from './connectorSingleton';
import { returnedMaterial } from '../models/typedefs';
import PiecesCacheSingleton from '../cache/piecesCacheSingleton';
import { AccessEnum, Asset, Assets } from '@pieces.app/pieces-os-client';
import { Format } from '@pieces.app/pieces-os-client';
import { mergeAssetsWithTransferables } from '../transferables';
import { ClassificationSpecificEnum } from '@pieces.app/pieces-os-client';
import Notifications from './Notifications';
import { sleep } from '../utils/sleep';
import { NotificationActionTypeEnum } from '../ui/views/shared/types/NotificationParameters';
import BrowserUrl from '../utils/browserUrl';

export const loadConnect = async (): Promise<boolean> => {
  const config: ConnectorSingleton = ConnectorSingleton.getInstance();
  try {
    config.context = await config.api.connect({
      seededConnectorConnection: config.seeded,
    });
    ConnectorSingleton.getInstance().addHeader(config.context.application.id);
    return true;
  } catch (err) {
    return false;
  }
};

export const loadPieces = async (): Promise<returnedMaterial[]> => {
  //
  const config: ConnectorSingleton = ConnectorSingleton.getInstance();
  const notifications: Notifications = Notifications.getInstance();

  if (!config.context) {
    try {
      config.context = await config.api.connect({
        seededConnectorConnection: config.seeded,
      });
    } catch (err) {
      // ignore we will just warn
    }

    if (!config.context) {
      notifications.error({
        message:
          'Failed to connect to PiecesOS. Please check that PiecesOS is installed.',
      });
      return Promise.reject(new Error('Context Undefined'));
    }
  }

  const snapshot = await fetchSnapshot({ config: config });

  if (snapshot instanceof Error) {
    return Promise.reject(snapshot);
  }

  await fetchAllFormats({ assets: snapshot.iterable });

  const piecesStorage = PiecesCacheSingleton.getInstance();
  const assets = mergeAssetsWithTransferables({
    assets: snapshot,
    references: piecesStorage.formatTransferables,
  });

  /// (2) save our assets
  piecesStorage.store({
    assets: processAssets({ assets: assets.iterable }).snippets,
  });

  const snippets = piecesStorage.assets;
  //writeData(piecesStorage.assets);
  return snippets;
};

const fetchSnapshot = async ({
  config,
  retry = false,
}: {
  suggested?: boolean;
  config: ConnectorSingleton;
  retry?: boolean;
}): Promise<Assets | Error> => {
  const notifications: Notifications = Notifications.getInstance();

  let snapshot: Assets;

  try {
    snapshot = await config.assetsApi.assetsSnapshot({
      suggested: false,
      transferables: false,
      pseudo: false,
    });
    return snapshot;
  } catch (error) {
    if (!retry) {
      return await fetchSnapshot({
        suggested: false,
        config: config,
        retry: true,
      });
    } else {
      notifications.error({
        message:
          'Failed to load Materials. Please restart PiecesOS, ensure that it is up-to-date, and try again. If the problem persists please reach out to support.',
        actions: [
          {
            title: 'Contact Support',
            type: NotificationActionTypeEnum.OPEN_LINK,
            params: { url: BrowserUrl.appendParams('https://docs.pieces.app/products/support') },
          },
        ],
      });
      return Promise.reject('Failed to fetch snapshot');
    }
  }
};

// fetches all formats for the assets and stores them in cache
const fetchAllFormats = async ({ assets }: { assets: Asset[] }) => {
  const piecesStorage = PiecesCacheSingleton.getInstance();
  const formatFetching: Promise<void>[] = [];
  for (const asset of assets) {
    // TODO may need to tweak this value (every 10 format fetchs) as well as we may need to space our timeoutPromise a bit more, but shouldnt need too.
    // await timeoutPromise(0);

    /// if we want to fetch.
    for (const format of asset.formats.iterable || []) {
      /// (3) fetch any formats that we havnt fetched yet.
      if (
        !(format.id in piecesStorage.fetchedFormats) ||
        piecesStorage.fetchedFormats[format.id] < format.updated.value
      ) {
        /// if either (1) our format hasnt been fetched yet
        /// or if (2) our format was updated before the last time it has been fetched.
        /// then we will want to fetch our format.
        /// dont await this as it can just happen syncronously
        formatFetching.push(fetchFormatTransferable({ format, asset }));
      }
    }
  }
  await Promise.all(formatFetching);
};

/**
 * This is a helper function that will enable us to process our Assets and turn them into the ReturnedAssets type.
 * This will also return a list of promises, that will represent everything that is currently being fetched.
 * @param {Boolean} fetch if we want to also attempt to fetch the assets.
 * @param {Assets} assets
 * @returns
 */
export const processAssets = ({ assets }: { assets: Asset[] }) => {
  const snippets: returnedMaterial[] = [];

  for (const asset of assets) {
    snippets.push(processAsset({ asset: asset }));
  }
  return {
    snippets,
  };
};

export const processAsset = ({ asset }: { asset: Asset }): returnedMaterial => {
  const cache = PiecesCacheSingleton.getInstance();
  let rawText = undefined;
  let rawFormat = undefined;

  const type = asset.original.reference?.classification.generic;
  if (type === 'IMAGE') {
    const decoder = new TextDecoder('utf-8');
    const ocrid = asset.original.reference?.analysis?.image?.ocr?.raw.id;
    if (!ocrid) {
      // LOG IN SENTRY
    }
    const format = asset.formats.iterable?.find((e) => e.id === ocrid);
    const bytes = new Uint8Array(format?.file?.bytes?.raw ?? []);
    rawText = decoder.decode(bytes);
    rawFormat = format?.classification.specific;
  }

  let link: string | undefined = undefined;
  for (let i = 0; i < (asset.shares?.iterable.length ?? 0); i++) {
    if (asset.shares?.iterable[i].access === AccessEnum.Public) {
      link = asset.shares?.iterable[i].link;
      break;
    }
  }

  return {
    title: asset.name || 'Unnamed Asset',
    id: asset.id,
    type: asset.original.reference?.classification.generic || 'Unknown Type',
    raw:
      rawText ??
      asset.original.reference?.fragment?.string?.raw ??
      asset.preview.base.reference?.fragment?.string?.raw ??
      asset.original.reference?.file?.string?.raw ??
      asset.preview.base.reference?.file?.string?.raw ??
      'Unable to unpack material :(',
    //@ts-ignore
    language:
      rawFormat ??
      (asset.original.reference?.classification.specific ||
        ClassificationSpecificEnum.Ts),
    time: asset.created.readable || 'Unknown Time',
    created: asset.created.value,
    annotations: cache.getAllAnnotations(asset.id),
    updated: asset.updated.value,
    share: link ?? undefined,
  };
};

export const fetchFormatTransferable = async ({
  format,
  asset,
  retryCount = 0,
}: {
  format: Format;
  asset: Asset;
  retryCount?: number;
}): Promise<void> => {
  const connector: ConnectorSingleton = ConnectorSingleton.getInstance();
  const storage = PiecesCacheSingleton.getInstance();

  // This is going to syncronously pull down and update as a fetch finishes.
  return connector.formatApi
    .formatSnapshot({
      format: format.id,
      transferable: true,
    })
    .then((fetched: Format) => {
      storage.formatTransferables[format.id] = {
        file: fetched.file,
        fragment: fetched.fragment,
      };

      /// (3) format has been fetched (we will use this to determine on the next refresh, to see if we need to refrech the format or not.)
      storage.fetchedFormats[format.id] = new Date();
    })
    .catch((error) => {
      /// TODO: if it fails, we want to load it in when the user actually clicks on it and add it in the storage.
      /// We want to try atleast 5 times if we get the connect ECONNRESET error. We are looking for this error specifically because of the rapid fire of the requests to our server.
      if (
        (error.message ?? '').includes('connect ECONNRESET') &&
        retryCount++ <= 5
      ) {
        console.log(`Making request ${format.id} Retry: ${retryCount}`);
        sleep(200).then((_) => {
          fetchFormatTransferable({
            format,
            asset,
            retryCount: retryCount,
          });
        });
      } else if (
        (error.message ?? '').includes('connect ECONNRESET') &&
        retryCount++ > 5
      ) {
        console.log(
          `Max threshold hit for this format ${format.id} Error: ${error}`
        );
      }
    });
};
