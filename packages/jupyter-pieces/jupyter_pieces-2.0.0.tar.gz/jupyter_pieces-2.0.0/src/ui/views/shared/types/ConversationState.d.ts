import {
	QGPTQuestionOutput,
	RelevantQGPTSeed,
	QGPTConversationMessage,
} from '@pieces.app/pieces-os-client';
import { AskAboutFileInput } from './AppletUnidirectionalMessageData';
import { Directive } from './Directive';
import { CopilotColors } from './Colors';

type ConversationObject = {
  message: QGPTConversationMessage;
  relevant?: RelevantQGPTSeed[];
  files?: AskAboutFileInput;
  image: boolean;
  messageId: string;
};

export type CopilotState = {
  conversation: ConversationObject[];
  conversationId: string;
  hints?: QGPTQuestionOutput;
  selectedModel: string;
  migration: number;
  directives: Directive[];
  colors?: CopilotColors;
  highContrast?: boolean;
};
