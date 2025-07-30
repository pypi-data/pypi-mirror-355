import { ClassificationSpecificEnum } from '@pieces.app/pieces-os-client';

export type AppletAssetSeed = {
  text: string;
  extension?: ClassificationSpecificEnum;
  filePath?: string;
};
