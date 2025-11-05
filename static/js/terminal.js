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
    window.addEventListener('beforeunload', function (e) {
        socket.disconnect();
    });

    // ========== 文件上传功能 ==========
    
    const MAX_UPLOAD_SIZE = 200 * 1024 * 1024; // 200MB
    
    const fileInput = document.getElementById('file-upload');
    const folderInput = document.getElementById('folder-upload');
    const uploadProgress = document.getElementById('upload-progress');
    const uploadFilename = document.getElementById('upload-filename');
    const uploadStatus = document.getElementById('upload-status');
    const progressFill = document.getElementById('progress-fill');
    const dropZone = document.getElementById('drop-zone');
    const terminalContainer = document.getElementById('terminal');

    // 文件选择事件
    fileInput.addEventListener('change', function(e) {
        const files = Array.from(e.target.files);
        if (files.length > 0) {
            handleFileSelection(files);
        }
        // 清空input，允许重复上传同一文件
        e.target.value = '';
    });
    
    // 文件夹选择事件
    folderInput.addEventListener('change', function(e) {
        const files = Array.from(e.target.files);
        if (files.length > 0) {
            handleFileSelection(files);
        }
        // 清空input
        e.target.value = '';
    });

    // 拖放事件
    terminalContainer.addEventListener('dragover', function(e) {
        e.preventDefault();
        e.stopPropagation();
        dropZone.style.display = 'flex';
    });

    dropZone.addEventListener('dragleave', function(e) {
        if (e.target === dropZone) {
            dropZone.style.display = 'none';
        }
    });

    dropZone.addEventListener('drop', function(e) {
        e.preventDefault();
        e.stopPropagation();
        dropZone.style.display = 'none';
        
        const items = e.dataTransfer.items;
        const files = [];
        
        if (items) {
            // 使用 DataTransferItemList 接口处理文件夹
            const promises = [];
            for (let i = 0; i < items.length; i++) {
                const item = items[i].webkitGetAsEntry();
                if (item) {
                    promises.push(traverseFileTree(item, ''));
                }
            }
            
            Promise.all(promises).then(results => {
                results.forEach(fileList => files.push(...fileList));
                if (files.length > 0) {
                    handleFileSelection(files);
                }
            });
        } else {
            // 降级方案：仅支持文件
            const fileList = Array.from(e.dataTransfer.files);
            if (fileList.length > 0) {
                handleFileSelection(fileList);
            }
        }
    });
    
    // 递归遍历文件树（支持文件夹）
    async function traverseFileTree(item, path) {
        return new Promise((resolve) => {
            if (item.isFile) {
                item.file(file => {
                    // 保存相对路径信息
                    file.relativePath = path + file.name;
                    resolve([file]);
                });
            } else if (item.isDirectory) {
                const dirReader = item.createReader();
                const files = [];
                
                function readEntries() {
                    dirReader.readEntries(async (entries) => {
                        if (entries.length === 0) {
                            resolve(files);
                        } else {
                            for (const entry of entries) {
                                const subFiles = await traverseFileTree(entry, path + item.name + '/');
                                files.push(...subFiles);
                            }
                            readEntries(); // 继续读取（可能有多批）
                        }
                    });
                }
                readEntries();
            } else {
                resolve([]);
            }
        });
    }
    
    // 处理文件选择（检查大小限制）
    function handleFileSelection(files) {
        // 计算总大小
        let totalSize = 0;
        for (const file of files) {
            totalSize += file.size;
        }
        
        if (totalSize > MAX_UPLOAD_SIZE) {
            const sizeMB = (totalSize / (1024 * 1024)).toFixed(2);
            const maxMB = (MAX_UPLOAD_SIZE / (1024 * 1024)).toFixed(0);
            term.write(`\r\n\x1b[1;31m✗ 上传失败: 文件总大小 ${sizeMB}MB 超过限制 ${maxMB}MB\x1b[0m\r\n`);
            alert(`上传失败：文件总大小 ${sizeMB}MB 超过限制 ${maxMB}MB`);
            return;
        }
        
        uploadFiles(files);
    }

    // 上传文件函数
    async function uploadFiles(files) {
        for (let i = 0; i < files.length; i++) {
            await uploadSingleFile(files[i], i + 1, files.length);
        }
    }

    // 上传单个文件
    async function uploadSingleFile(file, index, total) {
        try {
            // 获取文件相对路径
            const relativePath = file.relativePath || file.webkitRelativePath || file.name;
            const displayName = relativePath;
            
            // 显示上传进度
            uploadProgress.style.display = 'block';
            uploadFilename.textContent = `正在上传 (${index}/${total}): ${displayName}`;
            uploadStatus.textContent = '准备中...';
            progressFill.style.width = '0%';

            // 读取文件
            const fileData = await readFileAsArrayBuffer(file);
            
            // 使用pako进行gzip压缩
            uploadStatus.textContent = '压缩中...';
            
            const compressed = pako.gzip(new Uint8Array(fileData));
            
            const originalSize = fileData.byteLength;
            const compressedSize = compressed.byteLength;
            const ratio = ((1 - compressedSize / originalSize) * 100).toFixed(1);
            

            // 创建FormData
            const formData = new FormData();
            formData.append('file', new Blob([compressed]), file.name);
            formData.append('is_compressed', 'true');
            formData.append('target_path', '/root');
            // 添加相对路径信息用于保持文件夹结构
            formData.append('relative_path', relativePath);
            
            // 添加 CSRF token
            const csrfToken = document.querySelector('meta[name="csrf-token"]')?.content;
            if (csrfToken) {
                formData.append('csrf_token', csrfToken);
            }

            // 上传
            uploadStatus.textContent = '上传中...';
            
            const xhr = new XMLHttpRequest();
            
            // 上传进度
            xhr.upload.addEventListener('progress', function(e) {
                if (e.lengthComputable) {
                    const percent = Math.round((e.loaded / e.total) * 100);
                    uploadStatus.textContent = `${percent}% (${formatBytes(e.loaded)}/${formatBytes(e.total)})`;
                    progressFill.style.width = percent + '%';
                }
            });

            // 上传完成
            const uploadPromise = new Promise((resolve, reject) => {
                xhr.addEventListener('load', function() {
                    if (xhr.status === 200) {
                        const response = JSON.parse(xhr.responseText);
                        resolve(response);
                    } else {
                        try {
                            const error = JSON.parse(xhr.responseText);
                            console.error('服务器返回错误:', error);
                            reject(new Error(error.message || '上传失败'));
                        } catch (e) {
                            console.error('解析错误响应失败:', xhr.responseText);
                            reject(new Error('上传失败 (状态码: ' + xhr.status + ')'));
                        }
                    }
                });

                xhr.addEventListener('error', function() {
                    reject(new Error('网络错误'));
                });

                xhr.open('POST', `/terminal/upload/${PROJECT_ID}`);
                xhr.send(formData);
            });

            const result = await uploadPromise;
            
            // 上传成功
            uploadStatus.textContent = '✓ 上传成功';
            progressFill.style.width = '100%';
            progressFill.style.backgroundColor = '#0dbc79';
            
            // 在终端显示提示
            term.write(`\r\n\x1b[1;32m✓ 文件已上传: ${displayName} -> ${result.path}\x1b[0m\r\n`);
            term.write(`\x1b[90m  压缩率: ${ratio}%, 已保存 ${formatBytes(originalSize - compressedSize)}\x1b[0m\r\n`);
            
            // 延迟后隐藏进度条
            await sleep(1000);
            
        } catch (error) {
            console.error('上传失败:', error);
            uploadStatus.textContent = '✗ 上传失败: ' + error.message;
            progressFill.style.backgroundColor = '#cd3131';
            
            term.write(`\r\n\x1b[1;31m✗ 上传失败: ${displayName}\x1b[0m\r\n`);
            term.write(`\x1b[31m  ${error.message}\x1b[0m\r\n`);
            
            await sleep(2000);
        } finally {
            // 如果是最后一个文件，隐藏进度条
            if (index === total) {
                uploadProgress.style.display = 'none';
                progressFill.style.backgroundColor = '#2472c8';
            }
        }
    }

    // 辅助函数：读取文件为ArrayBuffer
    function readFileAsArrayBuffer(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => resolve(e.target.result);
            reader.onerror = (e) => reject(new Error('文件读取失败'));
            reader.readAsArrayBuffer(file);
        });
    }

    // 辅助函数：格式化字节大小
    function formatBytes(bytes) {
        if (bytes === 0) return '0 B';
        const k = 1024;
        const sizes = ['B', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }

    // 辅助函数：延迟
    function sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
})();
