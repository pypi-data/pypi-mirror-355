/* eslint-disable no-mixed-spaces-and-tabs */
import {
  AppletExtensionMessageEnum as AppletExtensionMessageEnum,
  AppletWebviewMessageEnum as AppletWebviewMessageEnum,
} from './AppletMessageType.enum';
import { AppletDataTypes as AppletDataTypes } from './AppletMessageDataTypes';
import { AppletUnidirectionalMessage } from './AppletUnidirectionalMessageData';

export type BaseAppletMessage<
  T extends AppletExtensionMessageEnum | AppletWebviewMessageEnum,
> = { type: T; id: string; error?: string };

/**
 *  For one directional message we don't need an id or an error
 */
export type BaseUnidirectionalCopilotMessage<
  T extends AppletExtensionMessageEnum | AppletWebviewMessageEnum,
> = {
  type: T;
  error?: string;
};

/**
 * Declares all valid types of messages to be sent
 * @param T: the type of message to be sent/received
 */
export type AppletMessageData<
  T extends AppletWebviewMessageEnum | AppletExtensionMessageEnum,
> = T extends keyof AppletUnidirectionalMessage
  ? BaseUnidirectionalCopilotMessage<T> & {
    data: AppletUnidirectionalMessage[T];
  }
  : T extends keyof AppletDataTypes
  ? BaseAppletMessage<T> & { data: AppletDataTypes[T] }
  : BaseAppletMessage<T>;
