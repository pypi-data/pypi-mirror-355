import { PluginGlobalVars } from '../../../PluginGlobalVars';
import { AppletMessageData } from '../shared/types/AppletMessageData';
import { AppletMessageHandler } from '../shared/types/AppletMessageHandler';
import { AppletWebviewMessageEnum } from '../shared/types/AppletMessageType.enum';
import { copilotParams } from './CopilotParams';

export class CopilotAppletMessageHandler extends AppletMessageHandler {
	handleSetState(
		message: AppletMessageData<AppletWebviewMessageEnum.SetStateReq>
	) {
		// extensionContext.globalState.update(
		// 	'copilot-state-flutter',
		// 	message.data.state
		// );
	}


	handleGetState() {
		return { state: PluginGlobalVars.copilotState };
	}

	async handleRunInTerminal(
		message: AppletMessageData<AppletWebviewMessageEnum.RunInTerminal>
	) {
		const classification = message.data.classification || null;
    	copilotParams.runInTerminal??(message.data.command, classification)
	}

	async handleAddAssetToContext(
		message: AppletMessageData<AppletWebviewMessageEnum.AddAssetToContext>
	) {
		copilotParams.requestContextPicker('snippets', message.data.conversation);
	}

	async handleAddFileToContext(
		message: AppletMessageData<AppletWebviewMessageEnum.AddFileToContext>
	) {
		copilotParams.requestContextPicker('files', message.data.conversation);
	}

	async handleAddFolderToContext(
		message: AppletMessageData<AppletWebviewMessageEnum.AddFolderToContext>
	) {
		copilotParams.requestContextPicker('folders',message.data.conversation);
	}

	async handleFilterFolder(
		message: AppletMessageData<AppletWebviewMessageEnum.FilterFolderReq>
	) {
		// TODO
		// const res: string[] = [];
		// for (const path of message.data) {
		// 	const filteredPaths = await ContextLoader.filterFromPath(path);
		// 	res.push(...filteredPaths);
		// }
		// return res;
	}

	handleAcceptChanges(
		message: AppletMessageData<AppletWebviewMessageEnum.AcceptChanges>
	) {
		// TODO AcceptChanges
	}

	async handleUpdateApplication(){
		// NOT SURE WHAT IS THAT
		const application = this.handleGetApplication();
		if(application){
			copilotParams.updateApplication(application)
		}
		return {};
	}
}
