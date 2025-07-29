/**
 * MCP Feedback Enhanced - WebSocket 管理模組
 * =========================================
 * 
 * 處理 WebSocket 連接、訊息傳遞和重連邏輯
 */

(function() {
    'use strict';

    // 確保命名空間和依賴存在
    window.MCPFeedback = window.MCPFeedback || {};
    const Utils = window.MCPFeedback.Utils;

    /**
     * WebSocket 管理器建構函數
     */
    function WebSocketManager(options) {
        options = options || {};

        this.websocket = null;
        this.isConnected = false;
        this.connectionReady = false;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = options.maxReconnectAttempts || Utils.CONSTANTS.MAX_RECONNECT_ATTEMPTS;
        this.reconnectDelay = options.reconnectDelay || Utils.CONSTANTS.DEFAULT_RECONNECT_DELAY;
        this.heartbeatInterval = null;
        this.heartbeatFrequency = options.heartbeatFrequency || Utils.CONSTANTS.DEFAULT_HEARTBEAT_FREQUENCY;

        // 事件回調
        this.onOpen = options.onOpen || null;
        this.onMessage = options.onMessage || null;
        this.onClose = options.onClose || null;
        this.onError = options.onError || null;
        this.onConnectionStatusChange = options.onConnectionStatusChange || null;

        // 標籤頁管理器引用
        this.tabManager = options.tabManager || null;

        // 連線監控器引用
        this.connectionMonitor = options.connectionMonitor || null;

        // 待處理的提交
        this.pendingSubmission = null;
        this.sessionUpdatePending = false;
    }

    /**
     * 建立 WebSocket 連接
     */
    WebSocketManager.prototype.connect = function() {
        if (!Utils.isWebSocketSupported()) {
            console.error('❌ 瀏覽器不支援 WebSocket');
            return;
        }

        // 確保 WebSocket URL 格式正確
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host;
        const wsUrl = protocol + '//' + host + '/ws';

        console.log('嘗試連接 WebSocket:', wsUrl);
        const connectingMessage = window.i18nManager ? window.i18nManager.t('connectionMonitor.connecting') : '連接中...';
        this.updateConnectionStatus('connecting', connectingMessage);

        try {
            // 如果已有連接，先關閉
            if (this.websocket) {
                this.websocket.close();
                this.websocket = null;
            }

            this.websocket = new WebSocket(wsUrl);
            this.setupWebSocketEvents();

        } catch (error) {
            console.error('WebSocket 連接失敗:', error);
            const connectionFailedMessage = window.i18nManager ? window.i18nManager.t('connectionMonitor.connectionFailed') : '連接失敗';
            this.updateConnectionStatus('error', connectionFailedMessage);
        }
    };

    /**
     * 設置 WebSocket 事件監聽器
     */
    WebSocketManager.prototype.setupWebSocketEvents = function() {
        const self = this;

        this.websocket.onopen = function() {
            self.handleOpen();
        };

        this.websocket.onmessage = function(event) {
            self.handleMessage(event);
        };

        this.websocket.onclose = function(event) {
            self.handleClose(event);
        };

        this.websocket.onerror = function(error) {
            self.handleError(error);
        };
    };

    /**
     * 處理連接開啟
     */
    WebSocketManager.prototype.handleOpen = function() {
        this.isConnected = true;
        this.connectionReady = false; // 等待連接確認
        const connectedMessage = window.i18nManager ? window.i18nManager.t('connectionMonitor.connected') : '已連接';
        this.updateConnectionStatus('connected', connectedMessage);
        console.log('WebSocket 連接已建立');

        // 重置重連計數器和延遲
        this.reconnectAttempts = 0;
        this.reconnectDelay = Utils.CONSTANTS.DEFAULT_RECONNECT_DELAY;

        // 通知連線監控器
        if (this.connectionMonitor) {
            this.connectionMonitor.startMonitoring();
        }

        // 開始心跳
        this.startHeartbeat();

        // 請求會話狀態
        this.requestSessionStatus();

        // 調用外部回調
        if (this.onOpen) {
            this.onOpen();
        }
    };

    /**
     * 處理訊息接收
     */
    WebSocketManager.prototype.handleMessage = function(event) {
        try {
            const data = Utils.safeJsonParse(event.data, null);
            if (data) {
                // 記錄訊息到監控器
                if (this.connectionMonitor) {
                    this.connectionMonitor.recordMessage();
                }

                this.processMessage(data);

                // 調用外部回調
                if (this.onMessage) {
                    this.onMessage(data);
                }
            }
        } catch (error) {
            console.error('解析 WebSocket 訊息失敗:', error);
        }
    };

    /**
     * 處理連接關閉
     */
    WebSocketManager.prototype.handleClose = function(event) {
        this.isConnected = false;
        this.connectionReady = false;
        console.log('WebSocket 連接已關閉, code:', event.code, 'reason:', event.reason);

        // 停止心跳
        this.stopHeartbeat();

        // 通知連線監控器
        if (this.connectionMonitor) {
            this.connectionMonitor.stopMonitoring();
        }

        // 處理不同的關閉原因
        if (event.code === 4004) {
            const noActiveSessionMessage = window.i18nManager ? window.i18nManager.t('connectionMonitor.noActiveSession') : '沒有活躍會話';
            this.updateConnectionStatus('disconnected', noActiveSessionMessage);
        } else {
            const disconnectedMessage = window.i18nManager ? window.i18nManager.t('connectionMonitor.disconnected') : '已斷開';
            this.updateConnectionStatus('disconnected', disconnectedMessage);
            this.handleReconnection(event);
        }

        // 調用外部回調
        if (this.onClose) {
            this.onClose(event);
        }
    };

    /**
     * 處理連接錯誤
     */
    WebSocketManager.prototype.handleError = function(error) {
        console.error('WebSocket 錯誤:', error);
        const connectionErrorMessage = window.i18nManager ? window.i18nManager.t('connectionMonitor.connectionError') : '連接錯誤';
        this.updateConnectionStatus('error', connectionErrorMessage);

        // 調用外部回調
        if (this.onError) {
            this.onError(error);
        }
    };

    /**
     * 處理重連邏輯
     */
    WebSocketManager.prototype.handleReconnection = function(event) {
        // 會話更新導致的正常關閉，立即重連
        if (event.code === 1000 && event.reason === '會話更新') {
            console.log('🔄 會話更新導致的連接關閉，立即重連...');
            this.sessionUpdatePending = true;
            const self = this;
            setTimeout(function() {
                self.connect();
            }, 200);
        }
        // 只有在非正常關閉時才重連
        else if (event.code !== 1000 && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            this.reconnectDelay = Math.min(this.reconnectDelay * 1.5, 15000);
            console.log(this.reconnectDelay / 1000 + '秒後嘗試重連... (第' + this.reconnectAttempts + '次)');

            // 更新狀態為重連中
            const reconnectingTemplate = window.i18nManager ? window.i18nManager.t('connectionMonitor.reconnecting') : '重連中... (第{attempt}次)';
            const reconnectingMessage = reconnectingTemplate.replace('{attempt}', this.reconnectAttempts);
            this.updateConnectionStatus('reconnecting', reconnectingMessage);

            const self = this;
            setTimeout(function() {
                console.log('🔄 開始重連 WebSocket... (第' + self.reconnectAttempts + '次)');
                self.connect();
            }, this.reconnectDelay);
        } else if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.log('❌ 達到最大重連次數，停止重連');
            const maxReconnectMessage = window.i18nManager ? window.i18nManager.t('connectionMonitor.maxReconnectReached') : 'WebSocket 連接失敗，請刷新頁面重試';
            Utils.showMessage(maxReconnectMessage, Utils.CONSTANTS.MESSAGE_ERROR);
        }
    };

    /**
     * 處理訊息
     */
    WebSocketManager.prototype.processMessage = function(data) {
        console.log('收到 WebSocket 訊息:', data);

        switch (data.type) {
            case 'connection_established':
                console.log('WebSocket 連接確認');
                this.connectionReady = true;
                this.handleConnectionReady();
                break;
            case 'heartbeat_response':
                this.handleHeartbeatResponse();
                // 記錄 pong 時間到監控器
                if (this.connectionMonitor) {
                    this.connectionMonitor.recordPong();
                }
                break;
            default:
                // 其他訊息類型由外部處理
                break;
        }
    };

    /**
     * 處理連接就緒
     */
    WebSocketManager.prototype.handleConnectionReady = function() {
        // 如果有待提交的內容，現在可以提交了
        if (this.pendingSubmission) {
            console.log('🔄 連接就緒，提交待處理的內容');
            const self = this;
            setTimeout(function() {
                if (self.pendingSubmission) {
                    self.send(self.pendingSubmission);
                    self.pendingSubmission = null;
                }
            }, 100);
        }
    };

    /**
     * 處理心跳回應
     */
    WebSocketManager.prototype.handleHeartbeatResponse = function() {
        if (this.tabManager) {
            this.tabManager.updateLastActivity();
        }
    };

    /**
     * 發送訊息
     */
    WebSocketManager.prototype.send = function(data) {
        if (this.websocket && this.websocket.readyState === WebSocket.OPEN) {
            try {
                this.websocket.send(JSON.stringify(data));
                return true;
            } catch (error) {
                console.error('發送 WebSocket 訊息失敗:', error);
                return false;
            }
        } else {
            console.warn('WebSocket 未連接，無法發送訊息');
            return false;
        }
    };

    /**
     * 請求會話狀態
     */
    WebSocketManager.prototype.requestSessionStatus = function() {
        this.send({
            type: 'get_status'
        });
    };

    /**
     * 開始心跳
     */
    WebSocketManager.prototype.startHeartbeat = function() {
        this.stopHeartbeat();

        const self = this;
        this.heartbeatInterval = setInterval(function() {
            if (self.websocket && self.websocket.readyState === WebSocket.OPEN) {
                // 記錄 ping 時間到監控器
                if (self.connectionMonitor) {
                    self.connectionMonitor.recordPing();
                }

                self.send({
                    type: 'heartbeat',
                    tabId: self.tabManager ? self.tabManager.getTabId() : null,
                    timestamp: Date.now()
                });
            }
        }, this.heartbeatFrequency);

        console.log('💓 WebSocket 心跳已啟動，頻率: ' + this.heartbeatFrequency + 'ms');
    };

    /**
     * 停止心跳
     */
    WebSocketManager.prototype.stopHeartbeat = function() {
        if (this.heartbeatInterval) {
            clearInterval(this.heartbeatInterval);
            this.heartbeatInterval = null;
            console.log('💔 WebSocket 心跳已停止');
        }
    };

    /**
     * 更新連接狀態
     */
    WebSocketManager.prototype.updateConnectionStatus = function(status, text) {
        if (this.onConnectionStatusChange) {
            this.onConnectionStatusChange(status, text);
        }
    };

    /**
     * 設置待處理的提交
     */
    WebSocketManager.prototype.setPendingSubmission = function(data) {
        this.pendingSubmission = data;
    };

    /**
     * 檢查是否已連接且就緒
     */
    WebSocketManager.prototype.isReady = function() {
        return this.isConnected && this.connectionReady;
    };

    /**
     * 關閉連接
     */
    WebSocketManager.prototype.close = function() {
        this.stopHeartbeat();
        if (this.websocket) {
            this.websocket.close();
            this.websocket = null;
        }
        this.isConnected = false;
        this.connectionReady = false;
    };

    // 將 WebSocketManager 加入命名空間
    window.MCPFeedback.WebSocketManager = WebSocketManager;

    console.log('✅ WebSocketManager 模組載入完成');

})();
