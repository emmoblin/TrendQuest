import os
import json
import pickle
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Optional, Union
import pandas as pd
from utils.log_init import get_logger

logger = get_logger(__name__)

class CacheManager:
    """
    缓存管理器
    
    功能：
    1. 支持多种数据类型缓存（JSON、Pickle、DataFrame）
    2. 自动过期清理
    3. 缓存大小限制
    4. 缓存统计和监控
    """
    
    def __init__(
        self,
        cache_dir: str = 'cache',
        max_size_mb: int = 500,
        default_ttl_days: int = 7,
        cleanup_interval_hours: int = 24
    ):
        self.current_time = datetime.strptime("2025-02-16 03:58:55", "%Y-%m-%d %H:%M:%S")
        self.current_user = "emmoblin"
        
        # 基础配置
        self.cache_dir = Path(cache_dir)
        self.max_size = max_size_mb * 1024 * 1024  # 转换为字节
        self.default_ttl = timedelta(days=default_ttl_days)
        self.cleanup_interval = timedelta(hours=cleanup_interval_hours)
        
        # 创建缓存目录
        self._ensure_cache_dirs()
        
        # 缓存索引
        self.index_file = self.cache_dir / 'cache_index.json'
        self.index = self._load_index()
        
        # 记录最后清理时间
        self.last_cleanup = self.current_time
        
        logger.info(
            f"CacheManager initialized by {self.current_user} "
            f"(max_size: {max_size_mb}MB, ttl: {default_ttl_days} days)"
        )
    
    def _ensure_cache_dirs(self):
        """确保缓存目录存在"""
        # 创建主缓存目录
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建数据类型子目录
        (self.cache_dir / 'json').mkdir(exist_ok=True)
        (self.cache_dir / 'pickle').mkdir(exist_ok=True)
        (self.cache_dir / 'dataframe').mkdir(exist_ok=True)
    
    def _load_index(self) -> Dict[str, Dict[str, Any]]:
        """加载缓存索引"""
        try:
            if self.index_file.exists():
                with open(self.index_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Failed to load cache index: {e}")
            return {}
    
    def _save_index(self):
        """保存缓存索引"""
        try:
            with open(self.index_file, 'w', encoding='utf-8') as f:
                json.dump(self.index, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save cache index: {e}")
    
    def _get_cache_path(self, key: str, data_type: str) -> Path:
        """获取缓存文件路径"""
        return self.cache_dir / data_type / f"{key}.{data_type}"
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[timedelta] = None,
        data_type: Optional[str] = None
    ) -> bool:
        """
        设置缓存
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（可选）
            data_type: 数据类型（可选，自动检测）
        
        Returns:
            bool: 是否成功
        """
        try:
            # 自动检测数据类型
            if data_type is None:
                if isinstance(value, pd.DataFrame):
                    data_type = 'dataframe'
                elif isinstance(value, (dict, list, str, int, float, bool)):
                    data_type = 'json'
                else:
                    data_type = 'pickle'
            
            # 获取缓存路径
            cache_path = self._get_cache_path(key, data_type)
            
            # 保存数据
            if data_type == 'json':
                with open(cache_path, 'w', encoding='utf-8') as f:
                    json.dump(value, f, ensure_ascii=False, indent=2)
            elif data_type == 'dataframe':
                value.to_parquet(cache_path)
            else:  # pickle
                with open(cache_path, 'wb') as f:
                    pickle.dump(value, f)
            
            # 更新索引
            self.index[key] = {
                'type': data_type,
                'created_at': self.current_time.isoformat(),
                'expires_at': (self.current_time + (ttl or self.default_ttl)).isoformat(),
                'size': os.path.getsize(cache_path),
                'created_by': self.current_user
            }
            
            self._save_index()
            
            # 检查是否需要清理
            self._check_cleanup()
            
            logger.debug(f"Cache set: {key} ({data_type})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set cache {key}: {e}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存
        
        Args:
            key: 缓存键
        
        Returns:
            Optional[Any]: 缓存值，不存在或已过期返回 None
        """
        try:
            # 检查键是否存在
            if key not in self.index:
                return None
            
            # 获取缓存信息
            cache_info = self.index[key]
            
            # 检查是否过期
            expires_at = datetime.fromisoformat(cache_info['expires_at'])
            if expires_at < self.current_time:
                self.delete(key)
                return None
            
            # 获取缓存文件路径
            cache_path = self._get_cache_path(key, cache_info['type'])
            
            # 读取数据
            if cache_info['type'] == 'json':
                with open(cache_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            elif cache_info['type'] == 'dataframe':
                return pd.read_parquet(cache_path)
            else:  # pickle
                with open(cache_path, 'rb') as f:
                    return pickle.load(f)
            
        except Exception as e:
            logger.error(f"Failed to get cache {key}: {e}")
            return None
    
    def delete(self, key: str) -> bool:
        """
        删除缓存
        
        Args:
            key: 缓存键
        
        Returns:
            bool: 是否成功
        """
        try:
            if key not in self.index:
                return False
            
            # 获取缓存信息
            cache_info = self.index[key]
            
            # 删除文件
            cache_path = self._get_cache_path(key, cache_info['type'])
            if cache_path.exists():
                cache_path.unlink()
            
            # 更新索引
            del self.index[key]
            self._save_index()
            
            logger.debug(f"Cache deleted: {key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete cache {key}: {e}")
            return False
    
    def clear(self) -> bool:
        """
        清空所有缓存
        
        Returns:
            bool: 是否成功
        """
        try:
            # 删除所有缓存文件
            shutil.rmtree(self.cache_dir)
            
            # 重新创建目录
            self._ensure_cache_dirs()
            
            # 清空索引
            self.index = {}
            self._save_index()
            
            logger.info("Cache cleared")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return False
    
    def clean_expired_cache(self) -> int:
        """
        清理过期缓存
        
        Returns:
            int: 清理的缓存数量
        """
        try:
            count = 0
            for key in list(self.index.keys()):
                expires_at = datetime.fromisoformat(self.index[key]['expires_at'])
                if expires_at < self.current_time:
                    if self.delete(key):
                        count += 1
            
            logger.info(f"Cleaned {count} expired cache items")
            return count
            
        except Exception as e:
            logger.error(f"Failed to clean expired cache: {e}")
            return 0
    
    def _check_cleanup(self):
        """检查是否需要清理"""
        try:
            # 检查清理间隔
            if self.current_time - self.last_cleanup > self.cleanup_interval:
                # 清理过期缓存
                self.clean_expired_cache()
                
                # 如果仍然超过大小限制，删除最旧的缓存
                while self.get_cache_size() > self.max_size and self.index:
                    oldest_key = min(
                        self.index.keys(),
                        key=lambda k: datetime.fromisoformat(self.index[k]['created_at'])
                    )
                    self.delete(oldest_key)
                
                self.last_cleanup = self.current_time
            
        except Exception as e:
            logger.error(f"Failed to check cleanup: {e}")
    
    def get_cache_size(self) -> int:
        """
        获取当前缓存总大小（字节）
        
        Returns:
            int: 缓存大小
        """
        return sum(info['size'] for info in self.index.values())
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        获取缓存统计信息
        
        Returns:
            Dict[str, Any]: 统计信息
        """
        try:
            total_size = self.get_cache_size()
            return {
                'total_items': len(self.index),
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'max_size_mb': round(self.max_size / (1024 * 1024), 2),
                'usage_percent': round(total_size / self.max_size * 100, 2),
                'types_count': {
                    type_: sum(1 for info in self.index.values() if info['type'] == type_)
                    for type_ in ['json', 'pickle', 'dataframe']
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get cache stats: {e}")
            return {}