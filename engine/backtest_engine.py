import backtrader as bt
from datetime import datetime
from typing import Dict, Any, List, Optional
import pandas as pd
import numpy as np
from .base_engine import BaseEngine
from .data_loader import DataLoader
from strategies.strategy_factory import get_strategy
from utils.log_init import get_logger

logger = get_logger(__name__)

class BacktestEngine(BaseEngine):
    """回测引擎实现"""
    
    def __init__(self, **kwargs):
        """初始化引擎"""
        super().__init__(**kwargs)
        self.cerebro = None
        self.results = None
        self.benchmark_data = None
        self.data_loader = DataLoader()
        
        # 获取策略类
        self.strategy_class = get_strategy(self.strategy_name)
    
    def load_benchmark(self):
        """加载基准数据"""
        try:
            logger.info("Loading benchmark data...")
            df = self.data_loader.load_index_data(
                symbol="sh000300",
                start_date=self.start_date,
                end_date=self.end_date
            )
            
            if df is not None:
                # 计算基准收益率
                df['Return'] = df['Close'].pct_change()
                self.benchmark_data = df
                logger.info("Successfully loaded benchmark data")
            else:
                logger.warning("Failed to load benchmark data")
                
        except Exception as e:
            logger.error("Failed to load benchmark data", exc_info=True)
            self.benchmark_data = None
    
    def load_data(self, symbol: str) -> Optional[bt.feeds.PandasData]:
        """加载股票数据
        
        Args:
            symbol: 股票代码
            
        Returns:
            backtrader数据源
        """
        try:
            # 加载数据
            df = self.data_loader.load_stock_data(
                symbol=symbol,
                start_date=self.start_date,
                end_date=self.end_date
            )
            
            if df is None:
                logger.warning(f"No data loaded for {symbol}")
                return None
            
            # 转换为backtrader数据源
            data = bt.feeds.PandasData(
                dataname=df,
                fromdate=self.start_date,
                todate=self.end_date,
                name=symbol
            )
            
            return data
            
        except Exception as e:
            logger.error(f"Failed to load data for {symbol}", exc_info=True)
            return None
    
    def add_analyzers(self):
        """添加分析器"""
        if self.cerebro is None:
            return
            
        self.cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe')
        self.cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
        self.cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
        self.cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
        self.cerebro.addanalyzer(bt.analyzers.TimeReturn, _name='time_returns')
        self.cerebro.addanalyzer(bt.analyzers.PyFolio, _name='pyfolio')
        
        logger.info("Added analyzers to cerebro")
    
    def run(self) -> Dict[str, Any]:
        """运行回测"""
        try:
            self.is_running = True
            
            # 加载基准数据
            self.update_progress(0.1, "正在加载基准数据")
            self.load_benchmark()
            
            # 创建回测引擎
            self.update_progress(0.2, "正在初始化回测引擎")
            self.cerebro = bt.Cerebro()
            
            # 设置初始资金
            self.cerebro.broker.setcash(self.initial_cash)
            
            # 设置交易成本
            self.cerebro.broker.setcommission(commission=self.commission)
            
            # 添加数据
            self.update_progress(0.3, "正在加载交易数据")
            data_loaded = False
            for symbol in self.symbols:
                data = self.load_data(symbol)
                if data is not None:
                    self.cerebro.adddata(data)
                    data_loaded = True
            
            if not data_loaded:
                raise ValueError("No data loaded for any symbol")
            
            # 添加策略
            self.update_progress(0.5, "正在配置策略")
            self.cerebro.addstrategy(self.strategy_class, **self._strategy_params)
            
            # 添加分析器
            self.update_progress(0.6, "正在配置分析器")
            self.add_analyzers()
            
            # 运行回测
            self.update_progress(0.7, "正在执行回测")
            self.results = self.cerebro.run()
            
            # 生成结果
            self.update_progress(0.9, "正在生成报告")
            result = self._generate_results()
            
            self.update_progress(1.0, "回测完成")
            self.is_running = False
            
            return result
            
        except Exception as e:
            self.error = str(e)
            self.status = "错误"
            self.is_running = False
            logger.error("回测执行失败", exc_info=True)
            raise
    
    def _generate_results(self) -> Dict[str, Any]:
        """生成回测结果"""
        try:
            if not self.results:
                return {"error": "No results available"}
                
            strategy = self.results[0]
            
            # 获取分析结果
            returns = strategy.analyzers.returns.get_analysis()
            sharpe = strategy.analyzers.sharpe.get_analysis()
            drawdown = strategy.analyzers.drawdown.get_analysis()
            trades = strategy.analyzers.trades.get_analysis()
            
            # 计算策略收益曲线
            portfolio_stats = strategy.analyzers.pyfolio.get_analysis()
            returns_df = pd.DataFrame(
                portfolio_stats['returns'],
                columns=['strategy_returns']
            )
            
            # 添加基准收益率
            if self.benchmark_data is not None:
                benchmark_returns = self.benchmark_data['Return']
                returns_df = returns_df.join(
                    benchmark_returns.rename('benchmark_returns'),
                    how='left'
                )
            
            # 计算累计收益
            returns_df['strategy_cum_returns'] = (1 + returns_df['strategy_returns']).cumprod()
            if 'benchmark_returns' in returns_df.columns:
                returns_df['benchmark_cum_returns'] = (1 + returns_df['benchmark_returns']).cumprod()
            
            return {
                "summary": {
                    "total_return": returns.get('rtot', 0),
                    "sharpe_ratio": sharpe.get('sharperatio', 0),
                    "max_drawdown": drawdown.get('max', {}).get('drawdown', 0),
                    "max_drawdown_period": drawdown.get('max', {}).get('len', 0),
                    "trade_count": trades.get('total', {}).get('total', 0),
                    "win_rate": trades.get('won', {}).get('total', 0) / 
                               max(trades.get('total', {}).get('total', 1), 1),
                    "profit_factor": (
                        trades.get('won', {}).get('pnl', 0) /
                        abs(trades.get('lost', {}).get('pnl', 1))
                    ),
                    "avg_trade_return": trades.get('won', {}).get('pnl', 0) /
                                      max(trades.get('total', {}).get('total', 1), 1)
                },
                "returns": returns_df.to_dict(orient='index'),
                "trades": self._format_trades(trades),
                "positions": self.get_positions() if hasattr(self, 'get_positions') else []
            }
            
        except Exception as e:
            logger.error("Failed to generate results", exc_info=True)
            return {
                "error": str(e)
            }
    
    def _format_trades(self, trades: Dict[str, Any]) -> List[Dict[str, Any]]:
        """格式化交易记录"""
        formatted_trades = []
        if not trades:
            return formatted_trades
            
        try:
            closed_trades = trades.get('closed', [])
            for trade in closed_trades:
                formatted_trades.append({
                    'datetime': trade.dtclose.strftime('%Y-%m-%d %H:%M:%S'),
                    'symbol': trade.data._name,
                    'type': 'LONG' if trade.long else 'SHORT',
                    'size': trade.size,
                    'price': trade.price,
                    'commission': trade.commission,
                    'pnl': trade.pnl,
                    'return': trade.pnlcomm / (trade.price * trade.size)
                })
        except Exception as e:
            logger.error("Failed to format trades", exc_info=True)
            
        return formatted_trades
    
    def get_positions(self) -> List[Dict[str, Any]]:
        """获取当前持仓"""
        positions = []
        if not self.results:
            return positions
            
        try:
            strategy = self.results[0]
            for data in strategy.datas:
                pos = strategy.getposition(data)
                if pos.size != 0:
                    positions.append({
                        'symbol': data._name,
                        'size': pos.size,
                        'price': pos.price,
                        'value': pos.size * pos.price
                    })
        except Exception as e:
            logger.error("Failed to get positions", exc_info=True)
            
        return positions