import { app, BrowserWindow } from 'electron';
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
            nodeIntegration: true,
            contextIsolation: false
        }
    });

    if (isDev) {
        mainWindow.loadFile(path.join(__dirname, '../dist/index.html'));
        mainWindow.webContents.openDevTools();
    } else {
        mainWindow.loadFile(path.join(__dirname, '../dist/index.html'));
    }

    mainWindow.on('closed', () => {
        mainWindow = null;
    });
}

function startFlaskServer() {
    const flaskScript = path.join(__dirname, '../backend/app.py');
    flaskProcess = spawn('python', [flaskScript]);

    flaskProcess.stdout.on('data', (data: any) => {
        console.log(`Flask: ${data}`);
    });

    flaskProcess.stderr.on('data', (data: any) => {
        console.error(`Flask Error: ${data}`);
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