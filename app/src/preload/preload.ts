// src/preload/preload.ts
import { contextBridge, ipcRenderer } from 'electron';

console.log('Preload script is loading...');

contextBridge.exposeInMainWorld('electron', {
    openDirectoryDialog: async () => {
        console.log('Attempting to open directory dialog...');
        try {
            const result = await ipcRenderer.invoke('open-directory-dialog');
            console.log('Dialog result:', result);
            return result;
        } catch (error) {
            console.error('Failed to open directory dialog:', error);
            return null;
        }
    }
});