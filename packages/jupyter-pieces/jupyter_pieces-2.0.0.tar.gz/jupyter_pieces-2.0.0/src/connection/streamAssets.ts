import PiecesCacheSingleton from '../cache/piecesCacheSingleton';
import { loadConnect, processAsset } from './apiWrapper';
import {
  Asset,
  StreamedIdentifiers,
  Assets,
  Annotation,
} from '@pieces.app/pieces-os-client';
import DedupeAssetQueue from './dedupeQueue';
import PiecesDatabase from '../database/PiecesDatabase';
import { SentryTracking } from '../analytics/SentryTracking';
import CheckVersionAndConnection from './checkVersionAndConnection';
import { sleep } from '../utils/sleep';
import ConnectorSingleton from './connectorSingleton';
import AnnotationHandler from '../utils/annotationHandler';

let identifierWs: WebSocket;
const fetchQueue = new DedupeAssetQueue();
export let streamOpen = false;
let streamClosed = false;
export const waitTimer = 10_000;
export const setStreamOpen = (val: boolean) => {
  streamOpen = val;
};
export const stream = async () => {
  streamIdentifiers();
};

/*
	This establishes a websocket connection with POS
	on each event, we first check if it is a delete
	if it's a delete, remove the asset from UI and cache, then return
	if not, then we fetch the snapshot and formats related to that asset
	we then run checks to see if it is a new asset, or an updated asset,
	and then update ui + cache accordingly.
*/
const streamIdentifiers = async (): Promise<void> => {
  if (streamClosed) return;
  if (streamOpen) {
    return;
  }
  streamOpen = true;
  if (identifierWs?.readyState === identifierWs?.OPEN) {
    identifierWs?.close();
  }



  identifierWs = new WebSocket(
    (
      ConnectorSingleton.getHost()
    )
      .replace('https://', 'wss://')
      .replace('http://', 'ws://') + "/assets/stream/identifiers"
  );

  identifierWs.onclose = async () => {
    await sleep(15_000);
    streamOpen = false;
    CheckVersionAndConnection.run().then(() => {
      streamIdentifiers();
    });
  };

  // update the ui when socket is established
  identifierWs.onopen = () => {
    loadConnect()
      .then(async () => {
        await SentryTracking.update();
      })
      .catch(() => {
        // do nothing
      });
    PiecesDatabase.clearStaleIds();
  };

  identifierWs.onmessage = async (event) => {
    const cache = PiecesCacheSingleton.getInstance();
    const assets = JSON.parse(event.data) as StreamedIdentifiers;

    for (let i = 0; i < assets.iterable.length; i++) {
      if (assets.iterable[i].deleted) {
        const snippetEl = document.getElementById(
          `snippet-el-${assets.iterable[i].asset!.id}`
        );
        snippetEl?.remove();

        // remove from cache
        delete cache.mappedAssets[assets.iterable[i].asset!.id];
        const indx = cache.assets.findIndex(
          (e) => e.id === assets.iterable[i].asset!.id
        );
        if (indx >= 0) {
          // <-- this check is somewhat redundant but why not be safe
          cache.assets = [
            ...cache.assets.slice(0, indx),
            ...cache.assets.slice(indx + 1),
          ];
          PiecesDatabase.writeDB();
        }
        continue;
      }

      fetchQueue.push(assets.iterable[i].asset!.id);
    }
  };
};

export const closeStreams = async () => {
  streamClosed = true;
  identifierWs?.close();
};

/*
	Forewarning: somewhat complex
	This receives assets from the fetch queue and updates the dom accordingly
	first make sure to remove the loading / 0 snippet divs
	then update snippet list element(s)
*/
export const renderFetched = async ({ assets }: { assets: Assets }) => {
  const cache = PiecesCacheSingleton.getInstance();
  const loadingDivs = document.querySelectorAll('.loading-div');

  const emptyDivs = document.querySelectorAll('.pieces-empty-state');
  emptyDivs?.forEach((div) => {
    div.remove();
  });

  const newDivs = document.querySelectorAll('.new-div');
  newDivs?.forEach((newDiv) => {
    newDiv.remove();
  });

  if (newDivs.length || loadingDivs.length) {
    const onlyDiv = document.querySelectorAll('.only-snippet');
    onlyDiv?.forEach((el) => {
      el.remove();
    });
    // commenting this out because i think it's causing more issues than it solves.
    //await triggerUIRedraw(false, undefined, undefined, false);
  }
  const config = ConnectorSingleton.getInstance();
  assets.iterable.forEach(async (element: Asset) => {
    const cachedAsset = cache.mappedAssets[element.id];
    let processed = processAsset({ asset: element });

    const annotationsReqs = Object.keys(element.annotations?.indices ?? {})
      .filter((key) => (element.annotations?.indices ?? {})[key] !== -1)
      .map((annotation) =>
        config.annotationApi.annotationSpecificAnnotationSnapshot({
          annotation,
        })
      );
    const annotations = await Promise.all(annotationsReqs).catch((e) => {
      console.error(e);
      return [] as Annotation[];
    });
    //new asset
    if (!cachedAsset) {
      cache.storeAnnotations(annotations, element.id);
      cache.prependAsset({ asset: element });
      const processed = processAsset({ asset: element });

      // Need to update the Map
      const newMap = cache.MaterialMap.get(processed.language);
      // If the language map does not exist, create it
      if (!newMap) {
        cache.MaterialMap.set(processed.language, [processed.id]);
      } else {
        newMap.unshift(processed.id);
        cache.MaterialMap.set(processed.language, newMap);
      }
    }

    //updated asset
    else if (
      !AnnotationHandler.getInstance().annotationsAreEqual(
        cachedAsset.annotations,
        annotations
      ) ||
      processed.raw === cachedAsset.raw ||
      processed.title === cachedAsset.title ||
      processed.language === cachedAsset.language ||
      processed.share === cachedAsset.share
    ) {
      cache.storeAnnotations(annotations, element.id);
      processed = processAsset({ asset: element });
      if (processed.language !== cachedAsset.language) {
        // Need to remove the old asset from the map
        const oldMapKeyValues = cache.MaterialMap.get(cachedAsset.language);

        oldMapKeyValues?.forEach((value, i) => {
          if (value === processed.id) {
            oldMapKeyValues.splice(i, 1);
            if (oldMapKeyValues.length === 0) {
              cache.MaterialMap.delete(cachedAsset.language);
            } else {
              cache.MaterialMap.set(cachedAsset.language, oldMapKeyValues);
            }
          }
        });

        const newMapkeyValues = cache.MaterialMap.get(processed.language) || [];
        newMapkeyValues.unshift(processed.id);
        cache.MaterialMap.set(processed.language, newMapkeyValues);
      }
      cache.updateAsset({ asset: element });
  }});
  PiecesDatabase.writeDB();
};
