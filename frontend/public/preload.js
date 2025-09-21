/**
 * Maidel 2.2 Electron Preload Script
 *
 * セキュアなIPC通信のためのブリッジ
 */

const { contextBridge, ipcRenderer } = require('electron');

// メインプロセスとの安全な通信インターフェース
contextBridge.exposeInMainWorld('electronAPI', {
    // ADKプロセスにメッセージ送信
    sendToADK: async (message) => {
        return await ipcRenderer.invoke('send-to-adk', message);
    },

    // ADKプロセス状態取得
    getADKStatus: async () => {
        return await ipcRenderer.invoke('get-adk-status');
    },

    // ADKプロセス再起動
    restartADK: async () => {
        return await ipcRenderer.invoke('restart-adk');
    },

    // ADKからのレスポンス受信
    onADKResponse: (callback) => {
        ipcRenderer.on('adk-response', (event, response) => {
            callback(response);
        });
    },

    // ADKエラー受信
    onADKError: (callback) => {
        ipcRenderer.on('adk-error', (event, error) => {
            callback(error);
        });
    },

    // リスナーを削除
    removeAllListeners: (channel) => {
        ipcRenderer.removeAllListeners(channel);
    }
});

console.log('Preload script loaded for Maidel 2.2');