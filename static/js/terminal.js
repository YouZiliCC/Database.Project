// 终端JavaScript逻辑
const terminalOutput = document.getElementById('terminal-output');
const commandInput = document.getElementById('command-input');

// 命令历史
let commandHistory = [];
let historyIndex = -1;

// 监听回车键
commandInput.addEventListener('keydown', async (e) => {
    if (e.key === 'Enter') {
        const command = commandInput.value.trim();
        if (command) {
            await executeCommand(command);
            commandHistory.push(command);
            historyIndex = commandHistory.length;
            commandInput.value = '';
        }
    } else if (e.key === 'ArrowUp') {
        // 上箭头 - 显示上一条命令
        e.preventDefault();
        if (historyIndex > 0) {
            historyIndex--;
            commandInput.value = commandHistory[historyIndex];
        }
    } else if (e.key === 'ArrowDown') {
        // 下箭头 - 显示下一条命令
        e.preventDefault();
        if (historyIndex < commandHistory.length - 1) {
            historyIndex++;
            commandInput.value = commandHistory[historyIndex];
        } else {
            historyIndex = commandHistory.length;
            commandInput.value = '';
        }
    }
});

// 执行命令
async function executeCommand(command) {
    // 显示输入的命令
    addTerminalLine(`$ ${command}`, 'command');
    
    // 特殊命令处理
    if (command === 'clear' || command === 'cls') {
        clearTerminal();
        return;
    }
    
    if (command === 'help') {
        addTerminalLine('可用命令:');
        addTerminalLine('  ls          - 列出文件');
        addTerminalLine('  pwd         - 显示当前目录');
        addTerminalLine('  echo <text> - 输出文本');
        addTerminalLine('  date        - 显示日期时间');
        addTerminalLine('  whoami      - 显示当前用户');
        addTerminalLine('  docker ps   - 显示运行中的容器');
        addTerminalLine('  docker images - 显示Docker镜像');
        addTerminalLine('  clear/cls   - 清空终端');
        addTerminalLine('  help        - 显示此帮助信息');
        return;
    }
    
    // 发送命令到后端
    try {
        const response = await fetch('/api/execute', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ command })
        });
        
        const data = await response.json();
        
        if (data.success) {
            addTerminalLine(data.output, 'success');
        } else {
            addTerminalLine(data.output, 'error');
        }
    } catch (error) {
        addTerminalLine(`错误: ${error.message}`, 'error');
    }
}

// 添加终端输出行
function addTerminalLine(text, className = '') {
    const line = document.createElement('div');
    line.className = `terminal-line ${className}`;
    line.textContent = text;
    terminalOutput.appendChild(line);
    
    // 自动滚动到底部
    terminalOutput.scrollTop = terminalOutput.scrollHeight;
}

// 清空终端
function clearTerminal() {
    terminalOutput.innerHTML = '';
    addTerminalLine('终端已清空');
}

// 执行示例命令
function executeExample(command) {
    commandInput.value = command;
    commandInput.focus();
    // 模拟回车
    const event = new KeyboardEvent('keydown', { key: 'Enter' });
    commandInput.dispatchEvent(event);
}

// 页面加载时聚焦输入框
window.addEventListener('load', () => {
    commandInput.focus();
});

// 点击终端区域时聚焦输入框
terminalOutput.addEventListener('click', () => {
    commandInput.focus();
});
