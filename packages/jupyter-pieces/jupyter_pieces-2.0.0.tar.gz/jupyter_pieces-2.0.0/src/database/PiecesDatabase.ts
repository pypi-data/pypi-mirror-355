import PiecesCacheSingleton from '../cache/piecesCacheSingleton';
import ConnectorSingleton from '../connection/connectorSingleton';
import PiecesDB from '../models/databaseModel';
import { ReadonlyJSONObject } from '@lumino/coreutils';
import DevLogger from '../dev/DevLogger';
import { PluginGlobalVars } from '../PluginGlobalVars';

export default class PiecesDatabase {
  public static writeDB = () => {
    const cache = PiecesCacheSingleton.getInstance();
    DevLogger.info('Pieces for Developers, writing data.');
    PluginGlobalVars.defaultApp.restored.then(() => {
      PluginGlobalVars.defaultState.save(PluginGlobalVars.PLUGIN_ID, {
        assets: cache.assets,
        remoteCopilotState: PluginGlobalVars.copilotState,
        remoteSettingsState: PluginGlobalVars.settingsState,
      } as PiecesDB as unknown as ReadonlyJSONObject);
    });
  };

  public static clearStaleIds = async () => {
    const config = ConnectorSingleton.getInstance();
    const cache = PiecesCacheSingleton.getInstance();
    const idSnapshot = await config.assetsApi
      .assetsIdentifiersSnapshot({ pseudo: false })
      .catch();
    if (!idSnapshot) return;
    const idMap = new Map();
    idSnapshot.iterable?.forEach((identifier) => {
      idMap.set(identifier.id, true);
    });
    // if cache id is not in idsnapshot delete
    const staleIds = Object.keys(cache.mappedAssets).filter((id) => {
      return !idMap.has(id);
    });

    staleIds.forEach((id) => {
      const snippetEl = document.getElementById(`snippet-el-${id}`);
      snippetEl?.remove();
      delete cache.mappedAssets[id];
    });
    cache.assets = Object.values(cache.mappedAssets);
    PiecesDatabase.writeDB();
  };
}
