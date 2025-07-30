import { ClassificationSpecificEnum } from '@pieces.app/pieces-os-client';
import { FileFormat, FragmentFormat } from '@pieces.app/pieces-os-client';
import { Annotation } from '@pieces.app/pieces-os-client';

type returnedMaterial = {
  title: string;
  id: string;
  type: string;
  // raw could possibly be undefined here, if it hasn't been fetched yet.
  raw: string;
  language: ClassificationSpecificEnum;
  time: string;
  created: Date;
  annotations: Annotation[];
  updated: Date;
  share: string | undefined;
};

type FormatTransferable = {
  /// both are optional but one of the two will exist.
  file?: FileFormat;
  fragment?: FragmentFormat;
};

export interface PiecesPluginSettings {
  cloudCapabilities: 'cloud' | 'local' | 'blended';
  hasLoaded: boolean;
  autoOpen: boolean;
}
