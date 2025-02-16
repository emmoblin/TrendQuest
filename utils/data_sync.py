import pandas as pd
import numpy as np
import akshare as ak
import ccxt
import logging
import asyncio
import aiohttp
import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union, Any
from concurrent.futures import ThreadPoolExecutor

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/data_sync.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DataSyncService:
    """
    数据同步服务
    负责管理和同步交易数据，支持股票、指数和加密货币数据
    """
    
    def __init__(
        self,
        data_dir: str = 'data',
        cache_days: int = 7,
        max_retries: int = 3,
        retry_delay: int = 5,
        max_concurrent: int = 5
    ):
        """
        初始化数据同步服务

        Args:
            data_dir: 数据存储目录
            cache_days: 缓存有效期（天）
            max_retries: 最大重试次数
            retry_delay: 重试延迟（秒）
            max_concurrent: 最大并发请求数
        """
        self.current_time = datetime.strptime("2025-02-15 18:31:15", "%Y-%m-%d %H:%M:%S")
        self.current_user = "emmoblin"
        
        self.data_dir = Path(data_dir)
        self.cache_days = cache_days
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.max_concurrent = max_concurrent
        
        # 创建数据目录结构
        self.stock_data_dir = self.data_dir / 'stock_data'
        self.index_data_dir = self.data_dir / 'index_data'
        self.crypto_data_dir = self.data_dir / 'crypto_data'
        
        for directory in [self.stock_data_dir, self.index_data_dir, self.crypto_data_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        # 初始化交易所API
        self.exchange = ccxt.binance()
        
        # 创建数据同步状态文件
        self.sync_status_file = self.data_dir / 'sync_status.json'
        self.sync_status = self._load_sync_status()

    def _load_sync_status(self) -> Dict[str, Any]:
        """加载同步状态"""
        if self.sync_status_file.exists():
            try:
                with open(self.sync_status_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载同步状态失败: {str(e)}")
        return {
            'last_sync': None,
            'sync_count': 0,
            'errors': {},
            'last_modified': self.current_time.strftime("%Y-%m-%d %H:%M:%S"),
            'modified_by': self.current_user
        }

    def _save_sync_status(self):
        """保存同步状态"""
        try:
            self.sync_status['last_modified'] = self.current_time.strftime("%Y-%m-%d %H:%M:%S")
            self.sync_status['modified_by'] = self.current_user
            
            with open(self.sync_status_file, 'w', encoding='utf-8') as f:
                json.dump(self.sync_status, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"保存同步状态失败: {str(e)}")

    async def sync_stock_data(
        self,
        symbols: List[str],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        show_progress: bool = False
    ) -> Dict[str, pd.DataFrame]:
        """
        同步股票数据

        Args:
            symbols: 股票代码列表
            start_date: 开始日期，默认为一年前
            end_date: 结束日期，默认为当前时间
            show_progress: 是否显示进度条

        Returns:
            包含股票数据的字典，key为股票代码，value为DataFrame
        """
        if not start_date:
            start_date = self.current_time - timedelta(days=365)
        if not end_date:
            end_date = self.current_time
        
        results = {}
        errors = []
        
        async with aiohttp.ClientSession() as session:
            semaphore = asyncio.Semaphore(self.max_concurrent)
            tasks = []
            
            for symbol in symbols:
                task = asyncio.create_task(
                    self._fetch_stock_data_with_semaphore(
                        semaphore,
                        session,
                        symbol,
                        start_date,
                        end_date
                    )
                )
                tasks.append(task)
            
            completed = await asyncio.gather(*tasks, return_exceptions=True)
            
            for symbol, result in zip(symbols, completed):
                if isinstance(result, Exception):
                    logger.error(f"获取股票{symbol}数据失败: {str(result)}")
                    errors.append((symbol, str(result)))
                elif result is not None:
                    results[symbol] = result
        
        # 更新同步状态
        self.sync_status['last_sync'] = self.current_time.strftime("%Y-%m-%d %H:%M:%S")
        self.sync_status['sync_count'] += 1
        if errors:
            self.sync_status['errors'].update({
                symbol: error for symbol, error in errors
            })
        self._save_sync_status()
        
        return results

    async def _fetch_stock_data_with_semaphore(
        self,
        semaphore: asyncio.Semaphore,
        session: aiohttp.ClientSession,
        symbol: str,
        start_date: datetime,
        end_date: datetime
    ) -> Optional[pd.DataFrame]:
        """使用信号量控制并发的数据获取"""
        async with semaphore:
            return await self._fetch_stock_data(session, symbol, start_date, end_date)

    async def _fetch_stock_data(
        self,
        session: aiohttp.ClientSession,
        symbol: str,
        start_date: datetime,
        end_date: datetime
    ) -> Optional[pd.DataFrame]:
        """获取单个股票数据"""
        cache_file = self.stock_data_dir / f"{symbol}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.parquet"
        
        # 检查缓存
        if cache_file.exists() and not self._is_cache_expired(cache_file):
            try:
                return pd.read_parquet(cache_file)
            except Exception as e:
                logger.error(f"读取缓存文件失败 {cache_file}: {str(e)}")
        
        # 从API获取数据
        for attempt in range(self.max_retries):
            try:
                df = await self._fetch_from_api(
                    session,
                    symbol,
                    start_date,
                    end_date
                )
                
                if df is not None and not df.empty:
                    # 保存缓存
                    df.to_parquet(cache_file)
                    return df
                
            except Exception as e:
                logger.error(f"获取股票{symbol}数据失败(尝试 {attempt + 1}/{self.max_retries}): {str(e)}")
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(self.retry_delay)
                continue
        
        return None

    async def _fetch_from_api(
        self,
        session: aiohttp.ClientSession,
        symbol: str,
        start_date: datetime,
        end_date: datetime
    ) -> Optional[pd.DataFrame]:
        """从API获取数据"""
        try:
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
            
        except Exception as e:
            logger.error(f"API获取股票{symbol}数据失败: {str(e)}")
            return None

    def _add_technical_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """添加技术指标"""
        # 计算移动平均线
        df['MA5'] = df['close'].rolling(window=5).mean()
        df['MA10'] = df['close'].rolling(window=10).mean()
        df['MA20'] = df['close'].rolling(window=20).mean()
        df['MA60'] = df['close'].rolling(window=60).mean()
        
        # 计算MACD
        exp1 = df['close'].ewm(span=12, adjust=False).mean()
        exp2 = df['close'].ewm(span=26, adjust=False).mean()
        df['MACD'] = exp1 - exp2
        df['Signal'] = df['MACD'].ewm(span=9, adjust=False).mean()
        df['Hist'] = df['MACD'] - df['Signal']
        
        # 计算RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['RSI'] = 100 - (100 / (1 + rs))
        
        return df

    def _is_cache_expired(self, cache_file: Path) -> bool:
        """检查缓存是否过期"""
        if not cache_file.exists():
            return True
            
        mtime = datetime.fromtimestamp(cache_file.stat().st_mtime)
        return (self.current_time - mtime).days >= self.cache_days

    def clean_expired_cache(self):
        """清理过期缓存"""
        cleaned_files = 0
        total_size = 0
        
        for directory in [self.stock_data_dir, self.index_data_dir, self.crypto_data_dir]:
            for file in directory.glob('*.parquet'):
                if self._is_cache_expired(file):
                    size = file.stat().st_size
                    try:
                        file.unlink()
                        cleaned_files += 1
                        total_size += size
                    except Exception as e:
                        logger.error(f"删除缓存文件失败 {file}: {str(e)}")
        
        logger.info(f"清理了 {cleaned_files} 个过期缓存文件，释放了 {total_size / 1024 / 1024:.2f} MB空间")

    def get_sync_status(self) -> Dict[str, Any]:
        """获取同步状态"""
        return self.sync_status

    async def sync_all_data(
        self,
        symbols: List[str],
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """同步所有数据"""
        results = {
            'stocks': {},
            'indices': {},
            'crypto': {},
            'errors': [],
            'sync_time': self.current_time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        try:
            # 同步股票数据
            stock_data = await self.sync_stock_data(symbols, start_date, end_date)
            results['stocks'] = stock_data
            
            # 同步指数数据（示例：沪深300）
            index_data = await self.sync_stock_data(['000300'], start_date, end_date)
            results['indices'] = index_data
            
            # 更新同步状态
            self.sync_status['last_sync'] = self.current_time.strftime("%Y-%m-%d %H:%M:%S")
            self.sync_status['sync_count'] += 1
            self._save_sync_status()
            
        except Exception as e:
            logger.error(f"同步数据失败: {str(e)}")
            results['errors'].append(str(e))
        
        return results

if __name__ == "__main__":
    # 示例使用
    async def main():
        sync_service = DataSyncService()
        
        # 测试股票列表
        test_symbols = ['000001', '600000', '300750']
        
        # 同步数据
        results = await sync_service.sync_all_data(
            symbols=test_symbols,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2025, 2, 15)
        )
        
        # 打印结果
        print(f"同步完成: {len(results['stocks'])} 只股票")
        print(f"错误数: {len(results['errors'])}")
        
        # 清理过期缓存
        sync_service.clean_expired_cache()
    
    # 运行示例
    asyncio.run(main())