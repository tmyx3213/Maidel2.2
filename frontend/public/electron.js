/**
 * Maidel 2.2 Electron Main Process
 *
 * ADK Python プロセスとの連携機能付き
 */

const { app, BrowserWindow, ipcMain } = require('electron');
const { spawn } = require('child_process');
const path = require('path');
const isDev = require('electron-is-dev');

class MaidelElectronApp {
    constructor() {
        this.mainWindow = null;
        this.adkProcess = null;
        this.isQuitting = false;
        // Buffer for stdout JSONL parsing
        this.stdoutBuffer = '';
        // ADK process start guard
        this._starting = false;
    }

    createWindow() {
        // メインウィンドウを作成
        this.mainWindow = new BrowserWindow({
            width: 1200,
            height: 800,
            webPreferences: {
                nodeIntegration: false,
                contextIsolation: true,
                enableRemoteModule: false,
                preload: path.join(__dirname, 'preload.js')
            },
            icon: path.join(__dirname, 'icon.png'), // アイコンがあれば
            title: 'Maidel 2.2 - AI Desktop Assistant',
            minWidth: 800,
            minHeight: 600,
            show: false // 準備完了まで非表示
        });

        // 開発時はlocalhost、本番時はローカルファイル
        const startUrl = isDev
            ? 'http://localhost:3000'
            : `file://${path.join(__dirname, '../build/index.html')}`;

        this.mainWindow.loadURL(startUrl);

        // 開発時はDevToolsを開く
        if (isDev) {
            this.mainWindow.webContents.openDevTools();
        }

        // ウィンドウの準備ができたら表示
        this.mainWindow.once('ready-to-show', () => {
            this.mainWindow.show();

            // ADKプロセス開始
            this.startADKProcess();
        });

        // ウィンドウが閉じられたときの処理
        this.mainWindow.on('closed', () => {
            this.mainWindow = null;
        });

        // ウィンドウが閉じようとしているときの処理
        this.mainWindow.on('close', (event) => {
            if (!this.isQuitting) {
                event.preventDefault();
                this.gracefulShutdown();
            }
        });
    }

    startADKProcess() {
        try {
            if (this._starting || (this.adkProcess && !this.adkProcess.killed)) {
                return;
            }
            this._starting = true;
            console.log('Starting ADK Python process...');

            // ADKプロセス起動
            this.adkProcess = spawn('py', ['-m', 'backend.main', '--stdio'], {
                cwd: path.join(__dirname, '../../'),
                stdio: ['pipe', 'pipe', 'pipe'],
                env: { ...process.env, PYTHONIOENCODING: 'utf-8' }
            });

            console.log('ADK process started with PID:', this.adkProcess.pid);
            this._starting = false;

            // ADKプロセスからの出力を処理
            this.adkProcess.stdout.on('data', (data) => {
                const chunk = data.toString('utf-8');
                this.stdoutBuffer += chunk;
                let nlIndex;
                while ((nlIndex = this.stdoutBuffer.indexOf('\n')) >= 0) {
                    const line = this.stdoutBuffer.slice(0, nlIndex).trim();
                    this.stdoutBuffer = this.stdoutBuffer.slice(nlIndex + 1);
                    if (!line) continue;
                    try {
                        const response = JSON.parse(line);
                        console.log('ADK Response:', response);
                        if (this.mainWindow) {
                            this.mainWindow.webContents.send('adk-response', response);
                        }
                    } catch (e) {
                        console.warn('Non-JSON stdout from ADK:', line);
                    }
                }
            });

            // ADKプロセスのエラー出力
            this.adkProcess.stderr.on('data', (data) => {
                console.log('ADK Error:', data.toString());
            });

            // ADKプロセス終了時
            this.adkProcess.on('close', (code) => {
                console.log(`ADK process exited with code ${code}`);
                this.adkProcess = null;
            });

            // ADKプロセスエラー時
            this.adkProcess.on('error', (error) => {
                console.error('ADK process error:', error);
                this.adkProcess = null;
                this._starting = false;
            });

        } catch (error) {
            console.error('Failed to start ADK process:', error);
            this._starting = false;

            // エラーをレンダラーに通知
            if (this.mainWindow) {
                this.mainWindow.webContents.send('adk-error', {
                    error: 'Failed to start ADK process',
                    details: error.message
                });
            }
        }
    }

    sendToADK(message) {
        if (this.adkProcess && this.adkProcess.stdin) {
            try {
                const jsonMessage = JSON.stringify({ message }) + '\n';
                this.adkProcess.stdin.write(jsonMessage);
                console.log('Sent to ADK:', message);
                return true;
            } catch (error) {
                console.error('Failed to send to ADK:', error);
                return false;
            }
        } else {
            console.warn('ADK process not available; attempting restart');
            try {
                this.startADKProcess();
                setTimeout(() => {
                    try {
                        if (this.adkProcess && this.adkProcess.stdin) {
                            const jsonMessage = JSON.stringify({ message }) + '\n';
                            this.adkProcess.stdin.write(jsonMessage);
                            console.log('Sent to ADK after restart:', message);
                        } else {
                            console.error('ADK still not available after restart');
                        }
                    } catch (e) {
                        console.error('Retry send failed:', e);
                    }
                }, 800);
            } catch (e) {
                console.error('Restart attempt failed:', e);
            }
            return false;
        }
    }

    gracefulShutdown() {
        console.log('Starting graceful shutdown...');
        this.isQuitting = true;

        // ADKプロセス終了
        if (this.adkProcess) {
            console.log('Terminating ADK process...');
            this.adkProcess.kill('SIGTERM');

            // 強制終了のタイマー
            setTimeout(() => {
                if (this.adkProcess) {
                    console.log('Force killing ADK process...');
                    this.adkProcess.kill('SIGKILL');
                }
                app.quit();
            }, 3000);
        } else {
            app.quit();
        }
    }

    setupIPC() {
        // レンダラープロセスからのメッセージ処理
        ipcMain.handle('send-to-adk', async (event, message) => {
            console.log('IPC received message:', message);

            if (this.sendToADK(message)) {
                return { success: true };
            }
            // Wait briefly and retry once after auto-restart
            await new Promise((r) => setTimeout(r, 900));
            if (this.sendToADK(message)) {
                return { success: true };
            }
            return {
                success: false,
                error: 'Failed to send message to ADK'
            };
        });

        // ADKプロセス状態取得
        ipcMain.handle('get-adk-status', async (event) => {
            return {
                isRunning: this.adkProcess !== null,
                pid: this.adkProcess ? this.adkProcess.pid : null
            };
        });

        // ADKプロセス再起動
        ipcMain.handle('restart-adk', async (event) => {
            if (this.adkProcess) {
                this.adkProcess.kill();
                this.adkProcess = null;
            }

            setTimeout(() => {
                this.startADKProcess();
            }, 1000);

            return { success: true };
        });
    }
}

// アプリケーションインスタンス
const maidelApp = new MaidelElectronApp();

// アプリ準備完了時
app.whenReady().then(() => {
    maidelApp.setupIPC();
    maidelApp.createWindow();

    app.on('activate', () => {
        if (BrowserWindow.getAllWindows().length === 0) {
            maidelApp.createWindow();
        }
    });
});

// 全ウィンドウが閉じられたとき
app.on('window-all-closed', () => {
    if (process.platform !== 'darwin') {
        maidelApp.gracefulShutdown();
    }
});

// アプリ終了前
app.on('before-quit', () => {
    maidelApp.isQuitting = true;
});

// 証明書エラーを無視（開発時のみ）
if (isDev) {
    app.commandLine.appendSwitch('ignore-certificate-errors');
}
