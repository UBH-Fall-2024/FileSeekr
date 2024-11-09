import { app, BrowserWindow, ipcMain, dialog } from 'electron';
import * as path from 'path';
import * as isDev from 'electron-is-dev';
import { spawn } from 'child_process';

let mainWindow: BrowserWindow | null;
let flaskProcess: any;

function createWindow() {
    mainWindow = new BrowserWindow({
        width: 800,
        height: 600,
        webPreferences: {

            nodeIntegration: false,
            contextIsolation: true,
            preload: path.join(__dirname, './preload.js')

        }
    });

    console.log('Preload path:', path.join(__dirname, './preload.js'));
    console.log('Current directory:', __dirname);

    if (isDev) {
        mainWindow.loadFile(path.join(__dirname, '../dist/index.html'));

        // this opens dev tools on popup. Disable
        //mainWindow.webContents.openDevTools();
    } else {
        mainWindow.loadFile(path.join(__dirname, '../dist/index.html'));
    }


    mainWindow.on('closed', () => {
        mainWindow = null;
    });
}

// this starts the flask server
function startFlaskServer() {
    const flaskScript = path.join(__dirname, '../src/backend/app.py');
    
    // Kill any existing Flask processes
    if (flaskProcess) {
        flaskProcess.kill();
    }
    
    flaskProcess = spawn('python', [flaskScript]);

    flaskProcess.stdout.on('data', (data: any) => {
        console.log(`Flask: ${data}`);
    });

    flaskProcess.stderr.on('data', (data: any) => {
        console.error(`Flask Error: ${data}`);
    });

    flaskProcess.on('close', (code: number) => {
        console.log(`Flask process exited with code ${code}`);
    });
}

app.whenReady().then(() => {
    startFlaskServer();
    createWindow();
});

app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        app.quit();
    }
    if (flaskProcess) {
        flaskProcess.kill();
    }
});

app.on('activate', () => {
    if (mainWindow === null) {
        createWindow();
    }
});


ipcMain.handle('open-directory-dialog', async () => {
    const result = await dialog.showOpenDialog({
        properties: ['openDirectory'],
        title: 'Select Directory'
    });

    if (!result.canceled) {
        return result.filePaths[0];
    }
    return null;
  
});

app.on('will-quit', () => {
    if (flaskProcess) {
        flaskProcess.kill();
    }

});