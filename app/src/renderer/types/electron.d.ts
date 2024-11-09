export interface ElectronAPI {
    openDirectoryDialog: () => Promise<string | null>;
}

declare global {
    interface Window {
        electron: ElectronAPI;
    }
}