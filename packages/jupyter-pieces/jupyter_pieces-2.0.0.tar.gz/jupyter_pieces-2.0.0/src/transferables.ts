import { Asset, Assets, Format } from '@pieces.app/pieces-os-client';
import { FormatTransferable } from './models/typedefs';

/**
 * TODO add a 2 more functions that will remove the transferables from Assets and Asset,
 * This will enable us to look throgh the class and remove any values.
 *
 * We would have these functions so that when calling asset.update or some other update we send the least amount of dta so that it is extremely fast.
 *
 * would call the function(s) removeAsset(s)Transferables.
 */

/**
 * This will take assets(likely polinated with transferables already.) and return all the format uuids and their Transferables.
 * @param {Assets} assets
 * @returns {[key: string]: FormatTransferable} This will return an object of references with the key being a format uui and the value being a formatTransferable
 */
export const extractAssetsTransferables: (assets: Assets) => {
  [key: string]: FormatTransferable;
} = (assets: Assets) => {
  let references: { [key: string]: FormatTransferable } = {};
  for (const asset of assets.iterable) {
    references = { ...references, ...extractAssetTransferables(asset) };
  }
  return references;
};

/**
 * This will take an individual asset(likely polinated with transferables already.) and return all the format uuids and their Transferables.
 * The key here is still a format uuid tho.
 * @param {Asset} asset
 * @returns {[key: string]: FormatTransferable} This will return an object of references with the key being a format uui and the value being a formatTransferable
 */
export const extractAssetTransferables: (asset: Asset) => {
  [key: string]: FormatTransferable;
} = (asset: Asset) => {
  const references: { [key: string]: FormatTransferable } = {};

  /// when packaging up our format values all we need to do is just get our format values,
  /// b/c original, and previews are all just values that are in the formats iterable
  for (const format of asset.formats.iterable || []) {
    references[format.id] = {
      file: format.file,
      fragment: format.fragment,
    };
  }
  return references;
};

/**
 * This will take assets(flat or polinated) and references and merge our references back into our assets.
 * @param { asset:Assets, references: { [key: string]: FormatTransferable }}
 * @returns {Assets} this will return Assets that are fully polinated with transferables or at least all the transferables that were already included in the references.
 */
export const mergeAssetsWithTransferables: ({
  assets,
  references,
}: {
  assets: Assets;
  references: {
    [key: string]: FormatTransferable;
  };
}) => Assets = ({
  assets,
  references,
}: {
  assets: Assets;
  references: { [key: string]: FormatTransferable };
}) => {
  const iterable: Asset[] = assets.iterable;
  for (let i = 0; i < iterable.length; i++) {
    const asset: Asset = assets.iterable[i];
    assets.iterable[i] = mergeAssetWithTransferables({
      asset: asset,
      references: references,
    });
  }
  return assets;
};

/**
 * This will take an asset(flat or polinated) and references and merge our references back into our asset.
 * @param { asset:Assets, references: { [key: string]: FormatTransferable }}
 * @returns {Asset} This will return an Asset that is fully polinated with reference data.
 */
export const mergeAssetWithTransferables: ({
  asset,
  references,
}: {
  asset: Asset;
  references: {
    [key: string]: FormatTransferable;
  };
}) => Asset = ({
  asset,
  references,
}: {
  asset: Asset;
  references: { [key: string]: FormatTransferable };
}) => {
  const iterable: Format[] = asset.formats.iterable || [];
  // (1) merge all our formats
  for (let i = 0; i < iterable.length; i++) {
    const format = iterable[i];
    iterable[i].fragment = references[format.id]?.fragment;
    iterable[i].file = references[format.id]?.file;
  }

  // (2) merge our original
  if (asset.original.reference) {
    asset.original.reference.fragment = references[asset.original.id]?.fragment;
    asset.original.reference.file = references[asset.original.id]?.file;
  }

  // (3a) merge for our preview base
  if (asset.preview.base.reference) {
    asset.preview.base.reference.fragment =
      references[asset.preview.base.id]?.fragment;
    asset.preview.base.reference.file = references[asset.preview.base.id]?.file;
  }

  // (3b) merge for our preview overlay
  if (asset.preview.overlay?.reference) {
    asset.preview.overlay.reference.fragment =
      references[asset.preview.overlay?.id]?.fragment;
    asset.preview.overlay.reference.file =
      references[asset.preview.overlay?.id]?.file;
  }
  return asset;
};
