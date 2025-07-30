import { ClassificationSpecificEnum } from '@pieces.app/pieces-os-client';

export type CopilotAssetSeed = {
  text: string;
  extension?: ClassificationSpecificEnum;
  filePath?: string;
};
