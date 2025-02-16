import akshare as ak
import tushare as ts
import pandas as pd
import numpy as np
import baostock as bs
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from utils.log_init import get_logger

logger = get_logger(__name__)

class DataLoader:
    """数据加载器"""
    
    def __init__(self):
        """初始化数据加载器"""
        self.cache = {}
        
        # 初始化 tushare
        self.ts_token = "your_tushare_token"  # 需要替换为实际的token
        ts.set_token(self.ts_token)
        self.ts_pro = ts.pro_api()
        
        # 初始化 baostock
        bs.login()
        
        # 交易所映射
        self.exchange_map = {
            '600': 'sh', '601': 'sh', '603': 'sh', '605': 'sh',  # 上交所
            '000': 'sz', '001': 'sz', '002': 'sz', '003': 'sz',  # 深交所
            '300': 'sz', '301': 'sz'  # 创业板
        }
    
    def __del__(self):
        """清理资源"""
        bs.logout()
    
    def _format_stock_code(self, symbol: str) -> tuple:
        """格式化股票代码
        
        Args:
            symbol: 原始股票代码
            
        Returns:
            (baostock格式, tushare格式, akshare格式)的元组
        """
        # 移除可能存在的交易所前缀
        clean_symbol = symbol.replace('sh', '').replace('sz', '')
        
        # 获取交易所前缀
        prefix = clean_symbol[:3]
        exchange = self.exchange_map.get(prefix)
        
        if not exchange:
            raise ValueError(f"Unknown stock code format: {symbol}")
        
        # 返回不同格式的代码
        return (
            f"{exchange}.{clean_symbol}",  # baostock格式
            f"{clean_symbol}.{exchange.upper()}",  # tushare格式
            clean_symbol  # akshare格式
        )
    
    def load_stock_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime
    ) -> Optional[pd.DataFrame]:
        """加载股票数据，尝试多个数据源
        
        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            DataFrame包含OHLCV数据
        """
        try:
            # 检查缓存
            cache_key = f"{symbol}_{start_date.date()}_{end_date.date()}"
            if cache_key in self.cache:
                return self.cache[cache_key]
            
            # 格式化股票代码
            bs_code, ts_code, ak_code = self._format_stock_code(symbol)
            
            # 1. 尝试 baostock
            df = self._load_from_baostock(bs_code, start_date, end_date)
            
            # 2. 如果失败，尝试 tushare
            if df is None:
                logger.info(f"Trying tushare for {symbol}")
                df = self._load_from_tushare(ts_code, start_date, end_date)
            
            # 3. 如果还是失败，尝试 akshare
            if df is None:
                logger.info(f"Trying akshare for {symbol}")
                df = self._load_from_akshare(ak_code, start_date, end_date)
            
            if df is not None:
                # 确保数据连续
                idx = pd.date_range(start_date, end_date)
                df = df.reindex(idx, method='ffill')
                
                # 缓存数据
                self.cache[cache_key] = df
                logger.info(f"Successfully loaded data for {symbol}")
                return df
            
            logger.error(f"All data sources failed for {symbol}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to load data for {symbol}", exc_info=True)
            return None
    
    def _load_from_baostock(
        self,
        code: str,
        start_date: datetime,
        end_date: datetime
    ) -> Optional[pd.DataFrame]:
        """从baostock加载数据"""
        try:
            rs = bs.query_history_k_data_plus(
                code,
                "date,open,high,low,close,volume,amount",
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d'),
                frequency="d",
                adjustflag="3"  # 3：后复权
            )
            
            if rs.error_code != '0':
                logger.warning(f"Baostock error: {rs.error_msg}")
                return None
            
            df = rs.get_data()
            if df.empty:
                return None
                
            # 转换数据类型
            for col in ['open', 'high', 'low', 'close', 'volume', 'amount']:
                df[col] = pd.to_numeric(df[col])
            
            # 设置索引
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            
            # 重命名列
            df.columns = ['Open', 'High', 'Low', 'Close', 'Volume', 'Amount']
            return df
            
        except Exception as e:
            logger.error("Baostock load failed", exc_info=True)
            return None
    
    def _load_from_tushare(
        self,
        code: str,
        start_date: datetime,
        end_date: datetime
    ) -> Optional[pd.DataFrame]:
        """从tushare加载数据"""
        try:
            df = self.ts_pro.daily(
                ts_code=code,
                start_date=start_date.strftime('%Y%m%d'),
                end_date=end_date.strftime('%Y%m%d'),
                adj='hfq'  # 后复权
            )
            
            if df.empty:
                return None
            
            # 设置索引
            df['trade_date'] = pd.to_datetime(df['trade_date'])
            df.set_index('trade_date', inplace=True)
            
            # 重命名列
            df = df.rename(columns={
                'open': 'Open',
                'high': 'High',
                'low': 'Low',
                'close': 'Close',
                'vol': 'Volume',
                'amount': 'Amount'
            })
            
            # 调整顺序
            df.sort_index(inplace=True)
            return df[['Open', 'High', 'Low', 'Close', 'Volume', 'Amount']]
            
        except Exception as e:
            logger.error("Tushare load failed", exc_info=True)
            return None
    
    def _load_from_akshare(
        self,
        code: str,
        start_date: datetime,
        end_date: datetime
    ) -> Optional[pd.DataFrame]:
        """从akshare加载数据"""
        try:
            df = ak.stock_zh_a_hist(
                symbol=code,
                period="daily",
                start_date=start_date.strftime('%Y%m%d'),
                end_date=end_date.strftime('%Y%m%d'),
                adjust="hfq"
            )
            
            if df.empty:
                return None
            
            # 重命名列
            df = df.rename(columns={
                '日期': 'Date',
                '开盘': 'Open',
                '最高': 'High',
                '最低': 'Low',
                '收盘': 'Close',
                '成交量': 'Volume',
                '成交额': 'Amount'
            })
            
            # 设置索引
            df['Date'] = pd.to_datetime(df['Date'])
            df.set_index('Date', inplace=True)
            
            return df[['Open', 'High', 'Low', 'Close', 'Volume', 'Amount']]
            
        except Exception as e:
            logger.error("Akshare load failed", exc_info=True)
            return None
    
    def load_index_data(
        self,
        symbol: str = "sh000300",
        start_date: datetime = None,
        end_date: datetime = None
    ) -> Optional[pd.DataFrame]:
        """加载指数数据"""
        try:
            # 尝试baostock
            df = self._load_from_baostock(
                f"sh.{symbol.replace('sh', '')}",
                start_date,
                end_date
            )
            
            if df is None:
                # 尝试tushare
                df = self._load_from_tushare(
                    f"{symbol.replace('sh', '')}.SH",
                    start_date,
                    end_date
                )
            
            if df is None:
                # 尝试akshare
                df = self._load_from_akshare(
                    symbol,
                    start_date,
                    end_date
                )
            
            if df is not None:
                # 计算收益率
                df['Return'] = df['Close'].pct_change()
                return df
            
            logger.error(f"All data sources failed for index {symbol}")
            return None
            
        except Exception as e:
            logger.error(f"Failed to load index data for {symbol}", exc_info=True)
            return None