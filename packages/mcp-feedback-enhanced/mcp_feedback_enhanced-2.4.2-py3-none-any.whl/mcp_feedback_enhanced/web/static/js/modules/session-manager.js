/**
 * MCP Feedback Enhanced - 會話管理模組（重構版）
 * =============================================
 *
 * 整合會話數據管理、UI 渲染和面板控制功能
 * 使用模組化架構提升可維護性
 */

(function() {
    'use strict';

    // 確保命名空間和依賴存在
    window.MCPFeedback = window.MCPFeedback || {};

    // 獲取 DOMUtils 的安全方法
    function getDOMUtils() {
        return window.MCPFeedback && window.MCPFeedback.Utils && window.MCPFeedback.Utils.DOM;
    }

    /**
     * 會話管理器建構函數（重構版）
     */
    function SessionManager(options) {
        options = options || {};

        // 子模組實例
        this.dataManager = null;
        this.uiRenderer = null;
        this.detailsModal = null;

        // UI 狀態
        this.isPanelVisible = true;
        this.isLoading = false;

        // UI 元素
        this.panel = null;
        this.edgeToggleBtn = null;
        this.collapsedToggleBtn = null;
        this.mainContent = null;

        // 設定管理器引用
        this.settingsManager = options.settingsManager || null;

        // 回調函數
        this.onSessionChange = options.onSessionChange || null;
        this.onSessionSelect = options.onSessionSelect || null;

        this.initializeModules(options);
        this.initializeUI();
        this.loadPanelState();

        console.log('📋 SessionManager (重構版) 初始化完成');
    }

    /**
     * 初始化子模組
     */
    SessionManager.prototype.initializeModules = function(options) {
        const self = this;

        // 先初始化 UI 渲染器（避免數據管理器回調時 UI 組件尚未準備好）
        this.uiRenderer = new window.MCPFeedback.Session.UIRenderer({
            showFullSessionId: options.showFullSessionId || false,
            enableAnimations: options.enableAnimations !== false
        });

        // 初始化詳情彈窗
        this.detailsModal = new window.MCPFeedback.Session.DetailsModal({
            enableEscapeClose: options.enableEscapeClose !== false,
            enableBackdropClose: options.enableBackdropClose !== false,
            showFullSessionId: options.showFullSessionId || false
        });

        // 最後初始化數據管理器（確保 UI 組件已準備好接收回調）
        this.dataManager = new window.MCPFeedback.Session.DataManager({
            onSessionChange: function(sessionData) {
                self.handleSessionChange(sessionData);
            },
            onHistoryChange: function(history) {
                self.handleHistoryChange(history);
            },
            onStatsChange: function(stats) {
                self.handleStatsChange(stats);
            }
        });
    };

    /**
     * 初始化 UI 元素
     */
    SessionManager.prototype.initializeUI = function() {
        const DOMUtils = getDOMUtils();

        if (!DOMUtils) {
            console.warn('📋 DOMUtils 尚未載入，使用原生 DOM 方法');
            // 使用原生 DOM 方法作為後備
            this.panel = document.querySelector('.session-management-panel');
            this.edgeToggleBtn = document.querySelector('#edgeToggleBtn');
            this.collapsedToggleBtn = document.querySelector('#collapsedToggleBtn');
            this.mainContent = document.querySelector('.main-content');
        } else {
            // 使用 DOMUtils
            this.panel = DOMUtils.safeQuerySelector('.session-management-panel');
            this.edgeToggleBtn = DOMUtils.safeQuerySelector('#edgeToggleBtn');
            this.collapsedToggleBtn = DOMUtils.safeQuerySelector('#collapsedToggleBtn');
            this.mainContent = DOMUtils.safeQuerySelector('.main-content');
        }

        // 設置事件監聽器
        this.setupEventListeners();

        // 初始化顯示
        this.updateDisplay();
    };

    /**
     * 處理會話變更
     */
    SessionManager.prototype.handleSessionChange = function(sessionData) {
        console.log('📋 處理會話變更:', sessionData);

        // 更新 UI 渲染
        this.uiRenderer.renderCurrentSession(sessionData);

        // 調用外部回調
        if (this.onSessionChange) {
            this.onSessionChange(sessionData);
        }
    };

    /**
     * 處理歷史記錄變更
     */
    SessionManager.prototype.handleHistoryChange = function(history) {
        console.log('📋 處理歷史記錄變更:', history.length, '個會話');

        // 更新 UI 渲染
        this.uiRenderer.renderSessionHistory(history);
    };

    /**
     * 處理統計資訊變更
     */
    SessionManager.prototype.handleStatsChange = function(stats) {
        console.log('📋 處理統計資訊變更:', stats);

        // 更新 UI 渲染
        this.uiRenderer.renderStats(stats);
    };

    /**
     * 設置事件監聽器
     */
    SessionManager.prototype.setupEventListeners = function() {
        const self = this;
        const DOMUtils = getDOMUtils();

        // 邊緣收合按鈕
        if (this.edgeToggleBtn) {
            this.edgeToggleBtn.addEventListener('click', function() {
                self.togglePanel();
            });
        }

        // 收合狀態下的展開按鈕
        if (this.collapsedToggleBtn) {
            this.collapsedToggleBtn.addEventListener('click', function() {
                self.togglePanel();
            });
        }

        // 刷新按鈕
        const refreshButton = DOMUtils ?
            DOMUtils.safeQuerySelector('#refreshSessions') :
            document.querySelector('#refreshSessions');
        if (refreshButton) {
            refreshButton.addEventListener('click', function() {
                self.refreshSessionData();
            });
        }

        // 詳細資訊按鈕
        const detailsButton = DOMUtils ?
            DOMUtils.safeQuerySelector('#viewSessionDetails') :
            document.querySelector('#viewSessionDetails');
        if (detailsButton) {
            detailsButton.addEventListener('click', function() {
                self.showSessionDetails();
            });
        }
    };

    /**
     * 更新當前會話（委託給數據管理器）
     */
    SessionManager.prototype.updateCurrentSession = function(sessionData) {
        return this.dataManager.updateCurrentSession(sessionData);
    };

    /**
     * 更新狀態資訊（委託給數據管理器）
     */
    SessionManager.prototype.updateStatusInfo = function(statusInfo) {
        return this.dataManager.updateStatusInfo(statusInfo);
    };










    /**
     * 切換面板顯示
     */
    SessionManager.prototype.togglePanel = function() {
        if (!this.panel) return;

        const DOMUtils = getDOMUtils();
        this.isPanelVisible = !this.isPanelVisible;

        if (this.isPanelVisible) {
            // 展開面板
            this.panel.classList.remove('collapsed');
            if (this.mainContent) {
                this.mainContent.classList.remove('panel-collapsed');
            }

            // 隱藏收合狀態下的展開按鈕
            const collapsedToggle = DOMUtils ?
                DOMUtils.safeQuerySelector('#collapsedPanelToggle') :
                document.querySelector('#collapsedPanelToggle');
            if (collapsedToggle) {
                collapsedToggle.style.display = 'none';
            }

            // 更新邊緣按鈕圖示和提示
            this.updateToggleButton('◀', '收合面板');
        } else {
            // 收合面板
            this.panel.classList.add('collapsed');
            if (this.mainContent) {
                this.mainContent.classList.add('panel-collapsed');
            }

            // 顯示收合狀態下的展開按鈕
            const collapsedToggle = DOMUtils ?
                DOMUtils.safeQuerySelector('#collapsedPanelToggle') :
                document.querySelector('#collapsedPanelToggle');
            if (collapsedToggle) {
                collapsedToggle.style.display = 'block';
            }

            // 更新邊緣按鈕圖示和提示
            this.updateToggleButton('▶', '展開面板');
        }

        // 保存面板狀態到設定
        this.savePanelState();

        console.log('📋 會話面板', this.isPanelVisible ? '顯示' : '隱藏');
    };

    /**
     * 更新切換按鈕
     */
    SessionManager.prototype.updateToggleButton = function(iconText, title) {
        if (this.edgeToggleBtn) {
            const icon = this.edgeToggleBtn.querySelector('.toggle-icon');
            if (icon) {
                icon.textContent = iconText;
            }
            this.edgeToggleBtn.setAttribute('title', title);
        }
    };

    /**
     * 刷新會話數據
     */
    SessionManager.prototype.refreshSessionData = function() {
        if (this.isLoading) return;

        console.log('📋 刷新會話數據');
        this.isLoading = true;

        const self = this;
        // 這裡可以發送 WebSocket 請求獲取最新數據
        setTimeout(function() {
            self.isLoading = false;
            console.log('📋 會話數據刷新完成');
        }, 1000);
    };

    /**
     * 顯示當前會話詳情
     */
    SessionManager.prototype.showSessionDetails = function() {
        const currentSession = this.dataManager.getCurrentSession();

        if (!currentSession) {
            this.showMessage('目前沒有活躍的會話數據', 'warning');
            return;
        }

        this.detailsModal.showSessionDetails(currentSession);
    };



    /**
     * 查看會話詳情（通過會話ID）
     */
    SessionManager.prototype.viewSessionDetails = function(sessionId) {
        console.log('📋 查看會話詳情:', sessionId);

        const sessionData = this.dataManager.findSessionById(sessionId);

        if (sessionData) {
            this.detailsModal.showSessionDetails(sessionData);
        } else {
            this.showMessage('找不到會話資料', 'error');
        }
    };



    /**
     * 獲取當前會話（便利方法）
     */
    SessionManager.prototype.getCurrentSession = function() {
        return this.dataManager.getCurrentSession();
    };

    /**
     * 獲取會話歷史（便利方法）
     */
    SessionManager.prototype.getSessionHistory = function() {
        return this.dataManager.getSessionHistory();
    };

    /**
     * 獲取統計資訊（便利方法）
     */
    SessionManager.prototype.getStats = function() {
        return this.dataManager.getStats();
    };

    /**
     * 獲取當前會話數據（相容性方法）
     */
    SessionManager.prototype.getCurrentSessionData = function() {
        console.log('📋 嘗試獲取當前會話數據...');

        const currentSession = this.dataManager.getCurrentSession();

        if (currentSession && currentSession.session_id) {
            console.log('📋 從 dataManager 獲取數據:', currentSession.session_id);
            return currentSession;
        }

        // 嘗試從 app 的 WebSocketManager 獲取
        if (window.feedbackApp && window.feedbackApp.webSocketManager) {
            const wsManager = window.feedbackApp.webSocketManager;
            if (wsManager.sessionId) {
                console.log('📋 從 WebSocketManager 獲取數據:', wsManager.sessionId);
                return {
                    session_id: wsManager.sessionId,
                    status: this.getCurrentSessionStatus(),
                    created_at: this.getSessionCreatedTime(),
                    project_directory: this.getProjectDirectory(),
                    summary: this.getAISummary()
                };
            }
        }

        // 嘗試從 app 的 currentSessionId 獲取
        if (window.feedbackApp && window.feedbackApp.currentSessionId) {
            console.log('📋 從 app.currentSessionId 獲取數據:', window.feedbackApp.currentSessionId);
            return {
                session_id: window.feedbackApp.currentSessionId,
                status: this.getCurrentSessionStatus(),
                created_at: this.getSessionCreatedTime(),
                project_directory: this.getProjectDirectory(),
                summary: this.getAISummary()
            };
        }

        console.log('📋 無法獲取會話數據');
        return null;
    };

    /**
     * 獲取會話建立時間
     */
    SessionManager.prototype.getSessionCreatedTime = function() {
        // 嘗試從 WebSocketManager 的連線開始時間獲取
        if (window.feedbackApp && window.feedbackApp.webSocketManager) {
            const wsManager = window.feedbackApp.webSocketManager;
            if (wsManager.connectionStartTime) {
                return wsManager.connectionStartTime / 1000;
            }
        }

        // 嘗試從最後收到的狀態更新中獲取
        if (this.dataManager && this.dataManager.lastStatusUpdate && this.dataManager.lastStatusUpdate.created_at) {
            return this.dataManager.lastStatusUpdate.created_at;
        }

        // 如果都沒有，返回 null
        return null;
    };

    /**
     * 獲取當前會話狀態
     */
    SessionManager.prototype.getCurrentSessionStatus = function() {
        // 嘗試從 UIManager 獲取當前狀態
        if (window.feedbackApp && window.feedbackApp.uiManager) {
            const currentState = window.feedbackApp.uiManager.getFeedbackState();
            if (currentState) {
                // 將內部狀態轉換為會話狀態
                const stateMap = {
                    'waiting_for_feedback': 'waiting',
                    'processing': 'active',
                    'feedback_submitted': 'feedback_submitted'
                };
                return stateMap[currentState] || currentState;
            }
        }

        // 嘗試從最後收到的狀態更新中獲取
        if (this.dataManager && this.dataManager.lastStatusUpdate && this.dataManager.lastStatusUpdate.status) {
            return this.dataManager.lastStatusUpdate.status;
        }

        // 預設狀態
        return 'waiting';
    };

    /**
     * 獲取專案目錄
     */
    SessionManager.prototype.getProjectDirectory = function() {
        const projectElement = document.querySelector('.session-project');
        if (projectElement) {
            return projectElement.textContent.replace('專案: ', '');
        }

        // 從頂部狀態列獲取
        const topProjectInfo = document.querySelector('.project-info');
        if (topProjectInfo) {
            return topProjectInfo.textContent.replace('專案目錄: ', '');
        }

        return '未知';
    };

    /**
     * 獲取 AI 摘要
     */
    SessionManager.prototype.getAISummary = function() {
        const summaryElement = document.querySelector('.session-summary');
        if (summaryElement && summaryElement.textContent !== 'AI 摘要: 載入中...') {
            return summaryElement.textContent.replace('AI 摘要: ', '');
        }

        // 嘗試從主要內容區域獲取
        const mainSummary = document.querySelector('#combinedSummaryContent');
        if (mainSummary && mainSummary.textContent.trim()) {
            return mainSummary.textContent.trim();
        }

        return '暫無摘要';
    };



    /**
     * 載入面板狀態
     */
    SessionManager.prototype.loadPanelState = function() {
        if (!this.settingsManager) {
            console.log('📋 沒有設定管理器，使用預設面板狀態');
            return;
        }

        const isCollapsed = this.settingsManager.get('sessionPanelCollapsed', false);
        this.isPanelVisible = !isCollapsed;

        console.log('📋 載入面板狀態:', this.isPanelVisible ? '顯示' : '隱藏');

        // 應用面板狀態
        this.applyPanelState();
    };

    /**
     * 保存面板狀態
     */
    SessionManager.prototype.savePanelState = function() {
        if (!this.settingsManager) {
            console.log('📋 沒有設定管理器，無法保存面板狀態');
            return;
        }

        const isCollapsed = !this.isPanelVisible;
        this.settingsManager.set('sessionPanelCollapsed', isCollapsed);

        console.log('📋 保存面板狀態:', isCollapsed ? '收合' : '展開');
    };

    /**
     * 應用面板狀態
     */
    SessionManager.prototype.applyPanelState = function() {
        if (!this.panel) return;

        const DOMUtils = getDOMUtils();

        if (this.isPanelVisible) {
            // 展開面板
            this.panel.classList.remove('collapsed');
            if (this.mainContent) {
                this.mainContent.classList.remove('panel-collapsed');
            }

            // 隱藏收合狀態下的展開按鈕
            const collapsedToggle = DOMUtils ?
                DOMUtils.safeQuerySelector('#collapsedPanelToggle') :
                document.querySelector('#collapsedPanelToggle');
            if (collapsedToggle) {
                collapsedToggle.style.display = 'none';
            }

            // 更新邊緣按鈕圖示和提示
            this.updateToggleButton('◀', '收合面板');
        } else {
            // 收合面板
            this.panel.classList.add('collapsed');
            if (this.mainContent) {
                this.mainContent.classList.add('panel-collapsed');
            }

            // 顯示收合狀態下的展開按鈕
            const collapsedToggle = DOMUtils ?
                DOMUtils.safeQuerySelector('#collapsedPanelToggle') :
                document.querySelector('#collapsedPanelToggle');
            if (collapsedToggle) {
                collapsedToggle.style.display = 'block';
            }

            // 更新邊緣按鈕圖示和提示
            this.updateToggleButton('▶', '展開面板');
        }
    };

    /**
     * 更新顯示
     */
    SessionManager.prototype.updateDisplay = function() {
        const currentSession = this.dataManager.getCurrentSession();
        const history = this.dataManager.getSessionHistory();
        const stats = this.dataManager.getStats();

        this.uiRenderer.renderCurrentSession(currentSession);
        this.uiRenderer.renderSessionHistory(history);
        this.uiRenderer.renderStats(stats);
    };

    /**
     * 清理資源
     */
    SessionManager.prototype.cleanup = function() {
        // 清理子模組
        if (this.dataManager) {
            this.dataManager.cleanup();
            this.dataManager = null;
        }

        if (this.uiRenderer) {
            this.uiRenderer.cleanup();
            this.uiRenderer = null;
        }

        if (this.detailsModal) {
            this.detailsModal.cleanup();
            this.detailsModal = null;
        }

        // 清理 UI 引用
        this.panel = null;
        this.edgeToggleBtn = null;
        this.collapsedToggleBtn = null;
        this.mainContent = null;

        console.log('📋 SessionManager (重構版) 清理完成');
    };

    // 將 SessionManager 加入命名空間
    window.MCPFeedback.SessionManager = SessionManager;

    // 全域方法供 HTML 調用
    window.MCPFeedback.SessionManager.viewSessionDetails = function(sessionId) {
        console.log('📋 全域查看會話詳情:', sessionId);

        // 找到當前的 SessionManager 實例
        if (window.MCPFeedback && window.MCPFeedback.app && window.MCPFeedback.app.sessionManager) {
            const sessionManager = window.MCPFeedback.app.sessionManager;
            sessionManager.viewSessionDetails(sessionId);
        } else {
            // 如果找不到實例，顯示錯誤訊息
            console.warn('找不到 SessionManager 實例');
            if (window.MCPFeedback && window.MCPFeedback.Utils && window.MCPFeedback.Utils.showMessage) {
                window.MCPFeedback.Utils.showMessage('會話管理器未初始化', 'error');
            }
        }
    };

    console.log('✅ SessionManager (重構版) 模組載入完成');

})();
