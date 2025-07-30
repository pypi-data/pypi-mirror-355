import { Asset } from '@pieces.app/pieces-os-client';
import { SeededAsset } from '@pieces.app/pieces-os-client';
import {
  Annotation,
  ClassificationSpecificEnum,
} from '@pieces.app/pieces-os-client';
import { processAsset } from '../connection/apiWrapper';
import { FormatTransferable, returnedMaterial } from '../models/typedefs';

export default class PiecesCacheSingleton {
  private static _instance: PiecesCacheSingleton;
  public assets: returnedMaterial[] = [];
  public suggestedAssets: Asset[] = [];
  public explainedMappedAssets = new Map<string, SeededAsset>();
  public mappedAssets: { [key: string]: returnedMaterial } = {};
  public fetchedFormats: { [key: string]: Date } = {};
  public discoveredMaterials: returnedMaterial[] = [];
  public assetAnnotations: Map<string, Map<string, Annotation>> = new Map<
    string,
    Map<string, Annotation>
  >();

  public MaterialMap = new Map<ClassificationSpecificEnum, string[]>();
  // this is a map of key: format uuid and value here is a transferable
  public formatTransferables: { [key: string]: FormatTransferable } = {};

  private constructor() {
    /* */
  }

  /**
   * Stores the loaded pieces in one singleton variable so they are accessible everywhere.
   */
  public store({
    assets: incomingAssets,
    transferables,
  }: {
    assets?: returnedMaterial[];
    transferables?: { [key: string]: FormatTransferable };
  }): void {
    if (incomingAssets) {
      this.assets = incomingAssets;
      this.convertToMap(incomingAssets);
    }
    if (transferables) {
      this.formatTransferables = transferables;
    }
  }
  /*
    This will add an asset to the beginning of the assets list
    @DEV make sure to provide transferables with the asset!!
  */
  public prependAsset({ asset }: { asset: Asset }): void {
    const processed = processAsset({ asset: asset });
    this.assets.unshift(processed);
    this.mappedAssets[asset.id] = processed;
    if (asset.original.reference?.file || asset.original.reference?.fragment) {
      this.formatTransferables[asset.original.reference?.id] = {
        file: asset.original.reference?.file,
        fragment: asset.original.reference?.fragment,
      };
    }
  }

  public updateAsset({ asset }: { asset: Asset }): void {
    const processed = processAsset({ asset: asset });
    for (let i = 0; i < this.assets.length; i++) {
      if (this.assets[i].id === asset.id) {
        this.assets[i] = processed;
      }
    }
    this.mappedAssets[asset.id] = processed;
  }

  /**
   * Maps the iterable of Pieces so they are accessible by the id.
   */
  public convertToMap(iterable: returnedMaterial[]): void {
    for (const iter of iterable) {
      this.mappedAssets[iter.id] = iter;
    }
  }

  /**
   *
   * Loads the scheme and providers for each piece required for the material display to work.
   */
  public static getInstance(): PiecesCacheSingleton {
    if (!PiecesCacheSingleton._instance) {
      PiecesCacheSingleton._instance = new PiecesCacheSingleton();
    }
    return PiecesCacheSingleton._instance;
  }

  /*
		Overwrites the asset annotations cache to the inputted annotations
	*/
  public storeAnnotations(annotations: Annotation[], asset?: string) {
    if (asset && !annotations.length)
      this.assetAnnotations.set(asset, new Map());
    for (let i = 0; i < annotations.length; i++) {
      this.assetAnnotations.delete(annotations[i].asset?.id ?? '');
    }

    for (let i = 0; i < annotations.length; i++) {
      const curMap =
        this.assetAnnotations.get(annotations[i].asset?.id ?? '') ??
        new Map<string, Annotation>();
      curMap.set(annotations[i].id, annotations[i]);
      this.assetAnnotations.set(annotations[i].asset?.id ?? '', curMap);
    }
  }

  public getAllAnnotations(asset: string) {
    return Array.from(this.assetAnnotations.get(asset)?.values() ?? []);
  }
}
