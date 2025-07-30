import { Annotation } from '@pieces.app/pieces-os-client';
import PiecesCacheSingleton from '../cache/piecesCacheSingleton';
import ConnectorSingleton from '../connection/connectorSingleton';

export default class AnnotationHandler {
  private constructor() {}

  private static instance: AnnotationHandler;

  public static getInstance(): AnnotationHandler {
    return (AnnotationHandler.instance ??= new AnnotationHandler());
  }

  public sortAnnotationsByCreated({
    annotations,
    ascending = true,
  }: {
    annotations: Annotation[];
    ascending?: boolean;
  }): Annotation[] {
    return annotations.sort((a, b) => {
      const timeA = a.created.value.getTime();
      const timeB = b.created.value.getTime();

      return ascending ? timeA - timeB : timeB - timeA;
    });
  }

  public sortAnnotationsByUpdated({
    annotations,
    ascending = true,
  }: {
    annotations: Annotation[];
    ascending?: boolean;
  }): Annotation[] {
    return annotations.sort((a, b) => {
      const timeA = new Date(a.updated.value).getTime();
      const timeB = new Date(b.updated.value).getTime();

      return ascending ? timeA - timeB : timeB - timeA;
    });
  }

  public getFavorited(annotations: Annotation[]): Annotation[] {
    return annotations.filter((a) => a.favorited);
  }

  annotationsAreEqual(arr1: Annotation[], arr2: Annotation[]): boolean {
    if (arr1.length !== arr2.length) {
      return false;
    }
    const arr1Map = new Map(
      arr1.map((item) => [
        item.id,
        { text: item.text, favorited: item.favorited },
      ])
    );
    const arr2Map = new Map(
      arr2.map((item) => [
        item.id,
        { text: item.text, favorited: item.favorited },
      ])
    );
    for (const [id, annotation] of arr1Map) {
      const cur = arr2Map.get(id);
      if (!cur) return false;
      if (cur.text !== annotation.text) return false;
      if (cur.favorited !== annotation.favorited) return false;
    }
    return true;
  }

  loadAnnotations = async () => {
    const config = ConnectorSingleton.getInstance();
    const cache = PiecesCacheSingleton.getInstance();
    const annotations = await config.annotationsApi.annotationsSnapshot({});
    cache.storeAnnotations(annotations.iterable);
  };
}
