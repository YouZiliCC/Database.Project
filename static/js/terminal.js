// WebShell 终端实现
(function () {
    'use strict';

    // 初始化 xterm.js
    const term = new Terminal({
        cursorBlink: true,
        fontSize: 14,
        fontFamily: 'Consolas, "Courier New", monospace',
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
            brightWhite: '#ffffff'
        },
        allowTransparency: false,
        rows: 24,
        cols: 80
    });

    // 初始化 FitAddon 用于自适应大小
    const fitAddon = new FitAddon.FitAddon();
    term.loadAddon(fitAddon);

    // 打开终端
    term.open(document.getElementById('terminal'));
    fitAddon.fit();

    // 连接 Socket.IO
    const socket = io('/terminal', {
        transports: ['websocket', 'polling']
    });

    // Socket.IO 事件处理
    socket.on('connect', function () {
        console.log('WebSocket 已连接');
        term.write('\r\n正在连接终端...\r\n');
        
        // 启动 shell
        socket.emit('start_shell', {
            pid: PROJECT_ID
        });
    });

    socket.on('ready', function (data) {
        console.log('Shell 已就绪:', data.message);
        
        // Shell 就绪后立即发送实际的终端尺寸
        socket.emit('resize', {
            rows: term.rows,
            cols: term.cols
        });
    });

    socket.on('output', function (data) {
        // 接收容器输出并显示
        term.write(data.data);
    });

    socket.on('error', function (data) {
        console.error('终端错误:', data.message);
        term.write('\r\n\x1b[1;31m错误: ' + data.message + '\x1b[0m\r\n');
    });

    socket.on('disconnected', function (data) {
        console.log('Shell 已断开:', data.message);
        term.write('\r\n\x1b[1;33m' + data.message + '\x1b[0m\r\n');
    });

    socket.on('disconnect', function () {
        console.log('WebSocket 已断开');
        term.write('\r\n\x1b[1;31m连接已断开\x1b[0m\r\n');
    });

    // 监听终端输入
    term.onData(function (data) {
        socket.emit('input', { data: data });
    });

    // 窗口大小调整
    window.addEventListener('resize', function () {
        fitAddon.fit();
        socket.emit('resize', {
            rows: term.rows,
            cols: term.cols
        });
    });

    // 页面卸载时断开连接
    window.addEventListener('beforeunload', function () {
        socket.emit('exit\n');
        socket.disconnect();
    });
})();
