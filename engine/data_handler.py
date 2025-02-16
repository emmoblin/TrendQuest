import pandas as pd
import numpy as np
import akshare as ak
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from utils import utils_manager, Event
from utils.log_init import get_logger

logger = get_logger(__name__)

class DataHandler:
    """数据处理类"""
    
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.current_time = datetime.strptime("2025-02-15 18:49:36", "%Y-%m-%d %H:%M:%S")
    
    async def fetch_stock_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime
    ) -> Optional[pd.DataFrame]:
        """获取股票数据"""
        try:
            # 检查缓存
            cache_key = f"data_{symbol}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}"
            cached_data = utils_manager.cache.get(cache_key)
            
            if cached_data is not None:
                logger.info(f"使用缓存数据: {symbol}")
                return cached_data
            
            # 从API获取数据
            df = ak.stock_zh_a_hist(
                symbol=symbol,
                period="daily",
                start_date=start_date.strftime("%Y%m%d"),
                end_date=end_date.strftime("%Y%m%d"),
                adjust="qfq"
            )
            
            if df is None or df.empty:
                return None
            
            # 处理数据
            df = self._process_data(df)
            
            # 保存缓存
            utils_manager.cache.set(cache_key, df)
            
            # 发布数据更新事件
            utils_manager.event.publish(Event(
                'data_updated',
                {'symbol': symbol, 'data': df}
            ))
            
            return df
            
        except Exception as e:
            logger.error(f"获取股票{symbol}数据失败: {str(e)}")
            return None
    
    def _process_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """处理原始数据"""
        # 重命名列
        df = df.rename(columns={
            '日期': 'date',
            '开盘': 'open',
            '收盘': 'close',
            '最高': 'high',
            '最低': 'low',
            '成交量': 'volume',
            '成交额': 'amount'
        })
        
        # 添加技术指标
        df = self._add_technical_indicators(df)
        
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        
        return df
    
    def _add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """添加技术指标"""
        # 移动平均线
        df['MA5'] = df['close'].rolling(window=5).mean()
        df['MA10'] = df['close'].rolling(window=10).mean()
        df['MA20'] = df['close'].rolling(window=20).mean()
        df['MA60'] = df['close'].rolling(window=60).mean()
        
        # MACD
        exp1 = df['close'].ewm(span=12, adjust=False).mean()
        exp2 = df['close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['Hist'] = df['MACD'] - df['Signal']
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        return df