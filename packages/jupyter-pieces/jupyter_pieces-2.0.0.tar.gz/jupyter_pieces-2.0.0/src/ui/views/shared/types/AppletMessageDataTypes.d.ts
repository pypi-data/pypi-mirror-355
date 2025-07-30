/* eslint-disable no-mixed-spaces-and-tabs */
import { Application } from '@pieces.app/pieces-os-client';

/**
 * Declares all valid data types for message communication between applet webviews and the backend extension
 */
export type AppletDataTypes = {
	shareReq:
		| {
				asset: {
					raw: string;
					ext: string;
				};
		  }
		| {
				id: string;
		  };
	shareRes: { link: string | undefined; id: string };
	applicationReq: undefined;
	applicationRes: Application | undefined;
	filterFolderReq: string[];
	filterFolderRes: string[];
	getRecentFilesReq: undefined;
	getRecentFilesRes: { paths: string[] };
	getWorkspacePathReq: undefined;
	getWorkspacePathRes: { paths: string[] };
	corsProxyReq: { url: string; options?: RequestInit };
	corsProxyRes: { content: string };
	updateApplicationReq: { application: Application };
	updateApplicationRes: undefined;
	getStateReq: {
		type: 'copilot' | 'savedMaterials';
	};
	getStateRes: { state: string };
	getUserPreferencesReq: undefined;
	getUserPreferencesRes: undefined;
};
