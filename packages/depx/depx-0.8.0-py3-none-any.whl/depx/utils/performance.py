"""
性能优化工具模块

提供缓存、内存优化和性能监控功能
"""

import functools
import hashlib
import logging
import time
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Union

logger = logging.getLogger(__name__)


class SmartCache:
    """智能缓存系统"""

    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        """
        初始化缓存

        Args:
            max_size: 最大缓存条目数
            ttl: 生存时间（秒）
        """
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.access_times: Dict[str, float] = {}
        self.max_size = max_size
        self.ttl = ttl

    def _generate_key(self, *args, **kwargs) -> str:
        """生成缓存键"""
        key_data = str(args) + str(sorted(kwargs.items()))
        return hashlib.md5(key_data.encode()).hexdigest()

    def _is_expired(self, key: str) -> bool:
        """检查缓存是否过期"""
        if key not in self.cache:
            return True

        entry = self.cache[key]
        return time.time() - entry["timestamp"] > self.ttl

    def _evict_if_needed(self):
        """如果需要，清理缓存"""
        if len(self.cache) < self.max_size:
            return

        # 清理过期条目
        expired_keys = [key for key in self.cache.keys() if self._is_expired(key)]

        for key in expired_keys:
            self._remove_entry(key)

        # 如果还是太多，清理最少使用的条目
        if len(self.cache) >= self.max_size:
            # 按访问时间排序，清理最旧的条目
            sorted_keys = sorted(
                self.access_times.keys(), key=lambda k: self.access_times[k]
            )

            num_to_remove = len(self.cache) - self.max_size + 1
            for key in sorted_keys[:num_to_remove]:
                self._remove_entry(key)

    def _remove_entry(self, key: str):
        """移除缓存条目"""
        self.cache.pop(key, None)
        self.access_times.pop(key, None)

    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        if key not in self.cache or self._is_expired(key):
            return None

        self.access_times[key] = time.time()
        return self.cache[key]["value"]

    def set(self, key: str, value: Any):
        """设置缓存值"""
        self._evict_if_needed()

        self.cache[key] = {"value": value, "timestamp": time.time()}
        self.access_times[key] = time.time()

    def get_or_compute(self, key: str, compute_func: Callable) -> Any:
        """获取缓存值或计算新值"""
        cached_value = self.get(key)
        if cached_value is not None:
            return cached_value

        value = compute_func()
        self.set(key, value)
        return value

    def clear(self):
        """清空缓存"""
        self.cache.clear()
        self.access_times.clear()

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        return {
            "size": len(self.cache),
            "max_size": self.max_size,
            "hit_rate": getattr(self, "_hit_count", 0)
            / max(getattr(self, "_total_requests", 1), 1),
            "ttl": self.ttl,
        }


# 全局缓存实例
_global_cache = SmartCache()


def cached(ttl: int = 3600, key_func: Optional[Callable] = None):
    """
    缓存装饰器

    Args:
        ttl: 生存时间（秒）
        key_func: 自定义键生成函数
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # 生成缓存键
            if key_func:
                cache_key = key_func(*args, **kwargs)
            else:
                cache_key = (
                    f"{func.__name__}_{_global_cache._generate_key(*args, **kwargs)}"
                )

            # 尝试从缓存获取
            def compute():
                return func(*args, **kwargs)

            return _global_cache.get_or_compute(cache_key, compute)

        return wrapper

    return decorator


class PerformanceMonitor:
    """性能监控器"""

    def __init__(self):
        self.metrics = {}

    def start_timer(self, name: str):
        """开始计时"""
        self.metrics[name] = {"start_time": time.time()}

    def end_timer(self, name: str) -> float:
        """结束计时并返回耗时"""
        if name not in self.metrics:
            logger.warning(f"计时器 {name} 未启动")
            return 0.0

        elapsed = time.time() - self.metrics[name]["start_time"]
        self.metrics[name]["elapsed"] = elapsed
        return elapsed

    def record_metric(self, name: str, value: Any):
        """记录指标"""
        self.metrics[name] = value

    def get_metrics(self) -> Dict[str, Any]:
        """获取所有指标"""
        return self.metrics.copy()

    def log_metrics(self):
        """记录指标到日志"""
        for name, value in self.metrics.items():
            if isinstance(value, dict) and "elapsed" in value:
                logger.info(f"性能指标 {name}: {value['elapsed']:.3f}秒")
            else:
                logger.info(f"指标 {name}: {value}")


def timed(func: Callable) -> Callable:
    """计时装饰器"""

    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            elapsed = time.time() - start_time
            logger.debug(f"函数 {func.__name__} 执行时间: {elapsed:.3f}秒")

    return wrapper


class MemoryOptimizer:
    """内存优化器"""

    @staticmethod
    def get_memory_usage() -> Dict[str, float]:
        """获取内存使用情况"""
        try:
            import psutil

            process = psutil.Process()
            memory_info = process.memory_info()

            return {
                "rss_mb": memory_info.rss / 1024 / 1024,  # 物理内存
                "vms_mb": memory_info.vms / 1024 / 1024,  # 虚拟内存
                "percent": process.memory_percent(),
            }
        except ImportError:
            logger.warning("psutil 不可用，无法获取内存使用情况")
            return {}

    @staticmethod
    def optimize_large_list(items: list, chunk_size: int = 1000):
        """优化大列表处理"""
        for i in range(0, len(items), chunk_size):
            yield items[i : i + chunk_size]

    @staticmethod
    def lazy_file_reader(file_path: Path, chunk_size: int = 8192):
        """惰性文件读取器"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    yield chunk
        except Exception as e:
            logger.error(f"读取文件失败: {file_path}, 错误: {e}")


def file_hash_cache_key(file_path: Union[str, Path]) -> str:
    """
    基于文件修改时间生成缓存键

    Args:
        file_path: 文件路径

    Returns:
        缓存键
    """
    try:
        path_obj = Path(file_path)
        if not path_obj.exists():
            return f"nonexistent_{file_path}"

        stat = path_obj.stat()
        return f"{file_path}_{stat.st_mtime}_{stat.st_size}"
    except Exception:
        return f"error_{file_path}"


def batch_process(
    items: list, batch_size: int = 100, progress_callback: Optional[Callable] = None
):
    """
    批量处理数据

    Args:
        items: 要处理的项目列表
        batch_size: 批次大小
        progress_callback: 进度回调函数
    """
    total_batches = (len(items) + batch_size - 1) // batch_size

    for i, batch_start in enumerate(range(0, len(items), batch_size)):
        batch_end = min(batch_start + batch_size, len(items))
        batch = items[batch_start:batch_end]

        if progress_callback:
            progress_callback(i + 1, total_batches, len(batch))

        yield batch


# 全局性能监控器
performance_monitor = PerformanceMonitor()
