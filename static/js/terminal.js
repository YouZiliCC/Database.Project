// Terminal WebShell JavaScript
// 使用 Socket.IO 和 Xterm.js 实现交互式终端

let term;
let fitAddon;
let socket;
let pid;
let reconnectAttempts = 0;
const MAX_RECONNECT_ATTEMPTS = 5;

function initTerminal(projectId) {
    pid = projectId;
    
    // 初始化 Xterm.js
    term = new Terminal({
        cursorBlink: true,
        fontSize: 14,
        fontFamily: 'Consolas, "Courier New", "Liberation Mono", Menlo, Monaco, monospace',
        theme: {
            background: '#1e1e1e',
            foreground: '#d4d4d4',
            cursor: '#d4d4d4',
            black: '#000000',
            red: '#cd3131',
            green: '#0dbc79',
            yellow: '#e5e510',
            blue: '#2472c8',
            magenta: '#bc3fbc',
            cyan: '#11a8cd',
            white: '#e5e5e5',
            brightBlack: '#666666',
            brightRed: '#f14c4c',
            brightGreen: '#23d18b',
            brightYellow: '#f5f543',
            brightBlue: '#3b8eea',
            brightMagenta: '#d670d6',
            brightCyan: '#29b8db',
            brightWhite: '#e5e5e5'
        },
        allowProposedApi: true,
        scrollback: 1000,
        allowTransparency: false,
    });
    
    // 自动适应大小插件
    fitAddon = new FitAddon.FitAddon();
    term.loadAddon(fitAddon);
    
    // 打开终端
    const terminalContainer = document.getElementById('terminal-container');
    if (!terminalContainer) {
        console.error('找不到终端容器元素');
        return;
    }
    
    term.open(terminalContainer);
    
    // 等待DOM完全加载后再fit
    setTimeout(() => {
        try {
            fitAddon.fit();
            console.log(`终端大小: ${term.rows}行 x ${term.cols}列`);
        } catch (e) {
            console.error('终端适配失败:', e);
        }
    }, 100);
    
    // 窗口大小改变时自动调整
    let resizeTimeout;
    window.addEventListener('resize', () => {
        clearTimeout(resizeTimeout);
        resizeTimeout = setTimeout(() => {
            try {
                fitAddon.fit();
                if (socket && socket.connected) {
                    socket.emit('resize', {
                        rows: term.rows,
                        cols: term.cols
                    });
                }
                console.log(`终端大小已调整: ${term.rows}行 x ${term.cols}列`);
            } catch (e) {
                console.error('终端大小调整失败:', e);
            }
        }, 250);
    });
    
    // 监听用户输入
    term.onData((data) => {
        console.log('发送输入:', JSON.stringify(data).substring(0, 50));
        if (socket && socket.connected) {
            socket.emit('input', { data: data });
        } else {
            console.warn('Socket 未连接，无法发送输入');
            term.write('\r\n\x1b[1;31m错误: 未连接到服务器\x1b[0m\r\n');
        }
    });
    
    // 连接 WebSocket
    connectWebSocket();
    
    // 按钮事件
    const btnClear = document.getElementById('btn-clear');
    const btnReconnect = document.getElementById('btn-reconnect');
    
    if (btnClear) {
        btnClear.addEventListener('click', () => {
            term.clear();
            term.write('\x1b[2J\x1b[H'); // 清除整个屏幕并移动光标到顶部
            console.log('终端已清空');
        });
    }
    
    if (btnReconnect) {
        btnReconnect.addEventListener('click', () => {
            reconnectAttempts = 0;
            term.write('\r\n\x1b[1;36m正在重新连接...\x1b[0m\r\n');
            connectWebSocket();
        });
    }
}

function connectWebSocket() {
    const statusEl = document.getElementById('connection-status');
    const reconnectBtn = document.getElementById('btn-reconnect');
    
    if (!statusEl) {
        console.error('找不到状态元素');
        return;
    }
    
    // 如果已有连接，先断开
    if (socket && socket.connected) {
        console.log('断开现有连接');
        socket.disconnect();
    }
    
    statusEl.textContent = '连接中...';
    statusEl.className = 'connection-status status-connecting';
    if (reconnectBtn) {
        reconnectBtn.style.display = 'none';
    }
    
    // 连接到 /terminal 命名空间
    socket = io('/terminal', {
        reconnection: true,
        reconnectionDelay: 1000,
        reconnectionAttempts: MAX_RECONNECT_ATTEMPTS,
        reconnectionDelayMax: 5000,
        timeout: 10000,
        transports: ['websocket', 'polling']
    });
    
    socket.on('connect', () => {
        console.log('WebSocket 已连接');
        statusEl.textContent = '连接中...';
        statusEl.className = 'connection-status status-connecting';
        
        // 启动 Shell 会话
        socket.emit('start_shell', { pid: pid });
    });
    
    socket.on('ready', (data) => {
        console.log('Shell 已就绪:', data.message);
        reconnectAttempts = 0; // 重置重连次数
        statusEl.textContent = '已连接';
        statusEl.className = 'connection-status status-connected';
        if (reconnectBtn) {
            reconnectBtn.style.display = 'none';
        }
        
        // 显示欢迎信息
        term.write('\r\n\x1b[1;32m╔════════════════════════════════════════╗\x1b[0m\r\n');
        term.write('\x1b[1;32m║     WebShell 已成功连接到容器         ║\x1b[0m\r\n');
        term.write('\x1b[1;32m╚════════════════════════════════════════╝\x1b[0m\r\n');
        term.write('\x1b[33m\r\n💡 提示:\x1b[0m\r\n');
        term.write('\x1b[90m  • 您现在在 Docker 容器内的 Bash Shell 环境\x1b[0m\r\n');
        term.write('\x1b[90m  • 支持所有标准 Linux 命令和工具\x1b[0m\r\n');
        term.write('\x1b[90m  • 键入 exit 退出会话\x1b[0m\r\n');
        term.write('\x1b[90m  • 可使用 Ctrl+C 中断运行中的命令\x1b[0m\r\n\r\n');
    });
    
    socket.on('output', (data) => {
        // 接收并显示容器输出
        console.log('收到输出:', data.data.length, '字符');
        term.write(data.data);
    });
    
    socket.on('error', (data) => {
        console.error('服务器错误:', data.message);
        term.write(`\r\n\x1b[1;31m╔════════════════════════════════════════╗\x1b[0m\r\n`);
        term.write(`\x1b[1;31m║  ❌ 错误: ${data.message.padEnd(30)}\x1b[0m║\r\n`);
        term.write(`\x1b[1;31m╚════════════════════════════════════════╝\x1b[0m\r\n`);
        statusEl.textContent = '连接失败';
        statusEl.className = 'connection-status status-disconnected';
        if (reconnectBtn) {
            reconnectBtn.style.display = 'inline-block';
        }
    });
    
    socket.on('disconnected', (data) => {
        console.log('Shell 会话已关闭:', data.message);
        term.write('\r\n\x1b[1;33m╔════════════════════════════════════════╗\x1b[0m\r\n');
        term.write('\x1b[1;33m║     Shell 会话已正常关闭              ║\x1b[0m\r\n');
        term.write('\x1b[1;33m╚════════════════════════════════════════╝\x1b[0m\r\n');
        term.write('\x1b[90m\r\n点击"重新连接"按钮或刷新页面以继续\x1b[0m\r\n');
        statusEl.textContent = '已断开';
        statusEl.className = 'connection-status status-disconnected';
        if (reconnectBtn) {
            reconnectBtn.style.display = 'inline-block';
        }
    });
    
    socket.on('disconnect', (reason) => {
        console.log('WebSocket 已断开:', reason);
        statusEl.textContent = '已断开';
        statusEl.className = 'connection-status status-disconnected';
        
        const reasonMap = {
            'io server disconnect': '服务器主动断开连接',
            'io client disconnect': '客户端主动断开连接',
            'ping timeout': '连接超时',
            'transport close': '传输连接关闭',
            'transport error': '传输错误'
        };
        
        const displayReason = reasonMap[reason] || reason;
        term.write('\r\n\x1b[1;31m╔════════════════════════════════════════╗\x1b[0m\r\n');
        term.write('\x1b[1;31m║     WebShell 连接已断开               ║\x1b[0m\r\n');
        term.write('\x1b[1;31m╚════════════════════════════════════════╝\x1b[0m\r\n');
        term.write(`\x1b[90m原因: ${displayReason}\x1b[0m\r\n`);
        
        if (reconnectBtn) {
            reconnectBtn.style.display = 'inline-block';
        }
    });
    
    socket.on('connect_error', (error) => {
        reconnectAttempts++;
        console.error(`连接错误 (尝试 ${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS}):`, error);
        statusEl.textContent = '连接失败';
        statusEl.className = 'connection-status status-disconnected';
        
        if (reconnectAttempts === 1) {
            term.write('\r\n\x1b[1;31m╔════════════════════════════════════════╗\x1b[0m\r\n');
            term.write('\x1b[1;31m║     无法连接到 WebShell 服务器        ║\x1b[0m\r\n');
            term.write('\x1b[1;31m╚════════════════════════════════════════╝\x1b[0m\r\n');
            term.write(`\x1b[90m错误信息: ${error.message || '未知错误'}\x1b[0m\r\n`);
        }
        
        if (reconnectAttempts >= MAX_RECONNECT_ATTEMPTS) {
            term.write('\r\n\x1b[1;31m已达到最大重连次数，请检查:\x1b[0m\r\n');
            term.write('\x1b[90m  1. 容器是否正常运行\x1b[0m\r\n');
            term.write('\x1b[90m  2. 网络连接是否正常\x1b[0m\r\n');
            term.write('\x1b[90m  3. 服务器是否正常响应\x1b[0m\r\n\r\n');
            if (reconnectBtn) {
                reconnectBtn.style.display = 'inline-block';
            }
        }
    });
    
    socket.on('reconnect_attempt', (attemptNumber) => {
        console.log(`正在尝试重新连接... (${attemptNumber}/${MAX_RECONNECT_ATTEMPTS})`);
        term.write(`\r\n\x1b[33m🔄 重连中... (${attemptNumber}/${MAX_RECONNECT_ATTEMPTS})\x1b[0m\r\n`);
    });
    
    socket.on('reconnect', (attemptNumber) => {
        console.log(`重连成功，用了 ${attemptNumber} 次尝试`);
        term.write('\r\n\x1b[1;32m✓ 重新连接成功！\x1b[0m\r\n');
    });
    
    socket.on('reconnect_failed', () => {
        console.error('重连失败');
        term.write('\r\n\x1b[1;31m✗ 重连失败，请手动刷新页面\x1b[0m\r\n');
        statusEl.textContent = '连接失败';
        statusEl.className = 'connection-status status-disconnected';
        if (reconnectBtn) {
            reconnectBtn.style.display = 'inline-block';
        }
    });
}

// 页面卸载时断开连接
window.addEventListener('beforeunload', () => {
    if (socket && socket.connected) {
        socket.disconnect();
    }
});
