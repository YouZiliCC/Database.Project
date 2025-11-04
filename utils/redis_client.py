"""Redis 客户端封装，用于跨 worker 共享数据"""

import redis
import json
import logging
import os
from typing import Any, Optional

logger = logging.getLogger(__name__)


class RedisClient:
    """Redis 客户端单例"""

    _instance = None
    _redis_client = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._redis_client is None:
            try:
                self._redis_client = redis.Redis(
                    host=os.getenv("REDIS_HOST", "localhost"),
                    port=int(os.getenv("REDIS_PORT", 6379)),
                    db=int(os.getenv("REDIS_DB", 0)),
                    decode_responses=True,  # 自动解码为字符串
                    socket_connect_timeout=5,
                    socket_timeout=5,
                )
                # 测试连接
                self._redis_client.ping()
                logger.info("Redis 连接成功")
            except Exception as e:
                logger.warning(f"Redis 连接失败，将使用内存字典: {e}")
                self._redis_client = None

    @property
    def client(self):
        return self._redis_client

    def is_available(self) -> bool:
        """检查 Redis 是否可用"""
        return self._redis_client is not None


class SharedDict:
    """基于 Redis 的共享字典，支持 fallback 到内存字典"""

    def __init__(self, namespace: str):
        self.namespace = namespace
        self.redis_client = RedisClient()
        self._memory_dict = {}  # fallback 内存字典

    def _make_key(self, key: str) -> str:
        """生成带命名空间的 Redis key"""
        return f"{self.namespace}:{key}"

    def set(self, key: str, value: Any, ex: Optional[int] = None) -> bool:
        """设置值，支持过期时间（秒）"""
        try:
            if self.redis_client.is_available():
                redis_key = self._make_key(key)
                # 如果值是复杂对象，序列化为 JSON
                if isinstance(value, (dict, list)):
                    value = json.dumps(value)
                self.redis_client.client.set(redis_key, value, ex=ex)
                return True
            else:
                # fallback 到内存
                self._memory_dict[key] = value
                return True
        except Exception as e:
            logger.error(f"Redis set 失败: {e}")
            self._memory_dict[key] = value
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """获取值"""
        try:
            if self.redis_client.is_available():
                redis_key = self._make_key(key)
                value = self.redis_client.client.get(redis_key)
                if value is None:
                    return default
                # 尝试解析 JSON
                try:
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    return value
            else:
                # fallback 到内存
                return self._memory_dict.get(key, default)
        except Exception as e:
            logger.error(f"Redis get 失败: {e}")
            return self._memory_dict.get(key, default)

    def delete(self, key: str) -> bool:
        """删除键"""
        try:
            if self.redis_client.is_available():
                redis_key = self._make_key(key)
                self.redis_client.client.delete(redis_key)
                return True
            else:
                self._memory_dict.pop(key, None)
                return True
        except Exception as e:
            logger.error(f"Redis delete 失败: {e}")
            self._memory_dict.pop(key, None)
            return False

    def keys(self) -> list:
        """获取所有键（只返回当前命名空间的）"""
        try:
            if self.redis_client.is_available():
                pattern = f"{self.namespace}:*"
                keys = self.redis_client.client.keys(pattern)
                # 去掉命名空间前缀
                return [k.replace(f"{self.namespace}:", "", 1) for k in keys]
            else:
                return list(self._memory_dict.keys())
        except Exception as e:
            logger.error(f"Redis keys 失败: {e}")
            return list(self._memory_dict.keys())

    def items(self):
        """返回所有键值对"""
        for key in self.keys():
            yield key, self.get(key)

    def pop(self, key: str, default: Any = None) -> Any:
        """弹出并删除键"""
        value = self.get(key, default)
        self.delete(key)
        return value

    def __getitem__(self, key: str) -> Any:
        value = self.get(key)
        if value is None:
            raise KeyError(key)
        return value

    def __setitem__(self, key: str, value: Any):
        self.set(key, value)

    def __delitem__(self, key: str):
        self.delete(key)

    def __contains__(self, key: str) -> bool:
        return self.get(key) is not None


# 创建共享字典实例
docker_status = SharedDict("docker_status")
terminal_sessions = SharedDict("terminal_sessions")
