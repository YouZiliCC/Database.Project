# Windows NpipeSocket 兼容性修复

## 问题
在 Windows 上运行时，Docker 使用 `NpipeSocket`（命名管道）而不是标准的 Unix socket。
`NpipeSocket` 对象没有 `_sock` 属性，导致以下错误：
```
AttributeError: 'NpipeSocket' object has no attribute '_sock'
```

## 修复方案

### 1. 读取输出时的 Socket 类型检测
**修复位置**: `blueprints/terminal.py` - `read_output()` 函数

```python
# 之前（错误）
sock._sock.setblocking(True)  # NpipeSocket 没有 _sock 属性

# 修复后
try:
    if hasattr(sock, '_sock'):
        # Unix socket (Linux/Mac)
        sock._sock.setblocking(True)
        logger.debug("使用 Unix socket 模式")
    else:
        # Windows named pipe - 默认就是阻塞的
        logger.debug("使用 Windows NpipeSocket 模式")
except Exception as e:
    logger.warning(f"设置阻塞模式失败（可忽略）: {e}")
```

**关键点**:
- ✅ 使用 `hasattr()` 检查 `_sock` 属性是否存在
- ✅ Windows NpipeSocket 默认是阻塞的，无需设置
- ✅ 添加异常处理，即使失败也不影响主流程

### 2. 发送输入时的兼容性处理
**修复位置**: `blueprints/terminal.py` - `handle_input()` 函数

```python
# 之前
if hasattr(sock, '_sock'):
    sock._sock.sendall(input_bytes)
else:
    sock.sendall(input_bytes)

# 修复后（添加备用方案）
try:
    if hasattr(sock, '_sock'):
        sock._sock.sendall(input_bytes)
    else:
        sock.sendall(input_bytes)
except AttributeError:
    # 备用方案：直接使用 socket 的 send 方法
    sock.send(input_bytes)
```

### 3. 关闭 Socket 时的兼容性
**修复位置**: `blueprints/terminal.py` - `handle_disconnect()` 函数

```python
# 修复后
if sock:
    try:
        # 尝试多种关闭方法以确保兼容性
        if hasattr(sock, '_sock'):
            sock._sock.close()
        if hasattr(sock, 'close'):
            sock.close()
        logger.info(f"Socket 已关闭: sid={request.sid}")
    except Exception as close_error:
        logger.warning(f"关闭 socket 时出错（可忽略）: {close_error}")
```

## Socket 类型对比

| 特性 | Unix Socket | Windows NpipeSocket |
|-----|-------------|---------------------|
| 底层实现 | `socket.socket` | Named Pipe |
| `_sock` 属性 | ✅ 有 | ❌ 没有 |
| `recv()` 方法 | ✅ 有 | ✅ 有 |
| `send()`/`sendall()` | ✅ 有 | ✅ 有 |
| `close()` 方法 | ✅ 有 | ✅ 有 |
| 阻塞模式设置 | 需要设置 | 默认阻塞 |

## 使用模式

### 读取数据（跨平台）
```python
if hasattr(sock, '_sock'):
    # Linux/Mac: 使用底层 socket
    data = sock._sock.recv(4096)
else:
    # Windows: 直接使用 NpipeSocket
    data = sock.recv(4096)
```

### 发送数据（跨平台）
```python
try:
    if hasattr(sock, '_sock'):
        sock._sock.sendall(data)
    else:
        sock.sendall(data)
except AttributeError:
    sock.send(data)  # 备用方案
```

## 测试验证

在 Windows 上运行后，日志应显示：
```
DEBUG - 开始读取容器输出: sid=xxx
DEBUG - Socket 类型: NpipeSocket
DEBUG - 使用 Windows NpipeSocket 模式
DEBUG - 发送输出: 45 字符, sid=xxx
```

在 Linux/Mac 上运行后，日志应显示：
```
DEBUG - 开始读取容器输出: sid=xxx
DEBUG - Socket 类型: SocketIO
DEBUG - 使用 Unix socket 模式
DEBUG - 发送输出: 45 字符, sid=xxx
```

## 验证清单

- [x] 修复 socket 阻塞模式设置
- [x] 添加 socket 类型检测
- [x] 修复读取操作的兼容性
- [x] 修复发送操作的兼容性
- [x] 修复关闭操作的兼容性
- [x] 添加详细日志输出
- [x] 添加异常处理

---

**修复时间**: 2025-11-03  
**平台**: Windows (NpipeSocket)  
**状态**: ✅ 已修复，可测试
