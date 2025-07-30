import ConnectorSingleton from './connectorSingleton';
import { mergeAssetsWithTransferables } from '../transferables';
import { renderFetched } from './streamAssets';
import PiecesCacheSingleton from '../cache/piecesCacheSingleton';

export default class DedupeAssetQueue {
  private idMap: Record<string, boolean> = {};
  private inFetch = false;
  private readonly batchSize: number = 30;

  push(id: string) {
    this.idMap[id] = true;
    if (!this.inFetch) this.doFetch();
  }

  async doFetch() {
    const cache = PiecesCacheSingleton.getInstance();
    const config = ConnectorSingleton.getInstance();
    this.inFetch = true;

    let IDs = Object.keys(this.idMap);
    while (IDs.length) {
      for (let i = 0; i < IDs.length; i += this.batchSize) {
        // memory efficiency gains are negligible with an array if strings
        // the only thing to look out for in this approach is that if debounce is too low,
        // we may end up with some duplicate things as queue is computed based on the map per function call
        const batch = IDs.slice(i, i + this.batchSize).map((id) => {
          delete this.idMap[id];
          return config.assetApi.assetSnapshot({
            asset: id,
            transferables: false,
          });
        });

        const assets = await Promise.all(batch).catch((e) => {
          console.error(
            `Error fetching asset: ${JSON.stringify(e, undefined, 2)}`
          );
          return null;
        });
        if (!assets) continue;

        const formatRequests = assets
          .map((asset) => asset.formats.iterable ?? [])
          .flat()
          .map((format) =>
            config.formatApi.formatSnapshot({
              format: format.id,
              transferable: true,
            })
          );
        const formats = await Promise.all(formatRequests).catch((e) => {
          console.error(
            `Error fetching format: ${JSON.stringify(e, undefined, 2)}`
          );
          return null;
        });
        if (!formats) continue;

        formats?.forEach((format) => {
          cache.fetchedFormats[format.id] = new Date();
          // wonder if we could go with cache.formatTransferables[format.id] = format
          cache.formatTransferables[format.id] = {
            file: format.file,
            fragment: format.fragment,
          };
        });

        setTimeout(() => {
          const mergedAssets = mergeAssetsWithTransferables({
            assets: { iterable: assets },
            references: cache.formatTransferables,
          });

          renderFetched({ assets: mergedAssets });
        }, 0);
      }
      IDs = Object.keys(this.idMap);
    }

    this.inFetch = false;
  }
}
