import pandas as pd
import akshare as ak
import ccxt
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from .log_init import get_logger

logger = get_logger(__name__)

class DataLoader:
    """数据加载器"""
    
    def __init__(self, cache_dir: str = 'data/stock_data', cache_days: int = 7):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.cache_days = cache_days
        self.exchange = ccxt.binance()
    
    def get_stock_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        force_reload: bool = False
    ) -> Optional[pd.DataFrame]:
        """获取股票数据"""
        try:
            cache_file = self._get_cache_path(symbol, start_date, end_date)
            
            # 检查缓存
            if not force_reload and cache_file.exists():
                # 检查缓存是否过期
                if self._is_cache_valid(cache_file):
                    return pd.read_parquet(cache_file)
            
            # 从API获取数据
            df = ak.stock_zh_a_hist(
                symbol=symbol,
                period="daily",
                start_date=start_date.strftime("%Y%m%d"),
                end_date=end_date.strftime("%Y%m%d"),
                adjust="qfq"
            )
            
            if df is None or df.empty:
                logger.warning(f"获取股票{symbol}数据失败")
                return None
            
            # 处理数据
            df = self._process_stock_data(df)
            
            # 保存缓存
            df.to_parquet(cache_file)
            
            return df
            
        except Exception as e:
            logger.error(f"获取股票{symbol}数据时出错: {str(e)}")
            return None
    
    def get_index_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        force_reload: bool = False
    ) -> Optional[pd.DataFrame]:
        """获取指数数据"""
        try:
            cache_file = self._get_cache_path(f"idx_{symbol}", start_date, end_date)
            
            if not force_reload and cache_file.exists():
                if self._is_cache_valid(cache_file):
                    return pd.read_parquet(cache_file)
            
            df = ak.stock_zh_index_daily(symbol=symbol)
            
            if df is None or df.empty:
                logger.warning(f"获取指数{symbol}数据失败")
                return None
            
            df = self._process_index_data(df)
            df.to_parquet(cache_file)
            
            return df
            
        except Exception as e:
            logger.error(f"获取指数{symbol}数据时出错: {str(e)}")
            return None
    
    def get_crypto_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        force_reload: bool = False
    ) -> Optional[pd.DataFrame]:
        """获取加密货币数据"""
        try:
            cache_file = self._get_cache_path(f"crypto_{symbol}", start_date, end_date)
            
            if not force_reload and cache_file.exists():
                if self._is_cache_valid(cache_file):
                    return pd.read_parquet(cache_file)
            
            # 获取OHLCV数据
            ohlcv = self.exchange.fetch_ohlcv(
                symbol,
                timeframe='1d',
                since=int(start_date.timestamp() * 1000),
                limit=None
            )
            
            df = pd.DataFrame(
                ohlcv,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            
            df = self._process_crypto_data(df)
            df.to_parquet(cache_file)
            
            return df
            
        except Exception as e:
            logger.error(f"获取加密货币{symbol}数据时出错: {str(e)}")
            return None
    
    def _get_cache_path(self, symbol: str, start_date: datetime, end_date: datetime) -> Path:
        """获取缓存文件路径"""
        return self.cache_dir / f"{symbol}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.parquet"
    
    def _is_cache_valid(self, cache_file: Path) -> bool:
        """检查缓存是否有效"""
        if not cache_file.exists():
            return False
            
        # 检查文件修改时间
        mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
        return (datetime.now() - mtime).days < self.cache_days
    
    def _process_stock_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """处理股票数据"""
        df = df.rename(columns={
            '日期': 'date',
            '开盘': 'open',
            '收盘': 'close',
            '最高': 'high',
            '最低': 'low',
            '成交量': 'volume',
            '成交额': 'amount'
        })
        
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        
        return df
    
    def _process_index_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """处理指数数据"""
        df = df.rename(columns={
            '日期': 'date',
            '开盘': 'open',
            '收盘': 'close',
            '最高': 'high',
            '最低': 'low',
            '成交量': 'volume'
        })
        
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        
        return df
    
    def _process_crypto_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """处理加密货币数据"""
        df['date'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('date', inplace=True)
        df.drop('timestamp', axis=1, inplace=True)
        
        return df