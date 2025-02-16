import backtrader as bt
import asyncio
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Dict, Any
from engine.base_engine import BaseEngine
from engine.data_handler import DataHandler
from engine.performance import PerformanceAnalyzer
from engine.visualizer import Visualizer
from utils import utils_manager, Event
from utils.log_init import get_logger
import sys

from strategies.strategy_factory import get_strategy  # 直接导入函数

logger = get_logger(__name__)

class BacktestEngine(BaseEngine):
    """回测引擎"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_time = datetime.strptime("2025-02-16 01:43:56", "%Y-%m-%d %H:%M:%S")
        self.current_user = "emmoblin"
        
        # 获取配置
        engine_config = utils_manager.config.get_config().get('backtest', {})
        
        # 初始化组件
        self.data_handler = DataHandler(self.cache_dir)
        self.analyzer = PerformanceAnalyzer()
        self.visualizer = Visualizer()
        
        # 获取策略类
        self.strategy_class = get_strategy(self.strategy_name)
        
        # 订阅事件
        utils_manager.event.subscribe('data_updated', self._handle_data_update)
    
    def initialize(self) -> bool:
        """初始化引擎"""
        try:
            # 创建Cerebro实例
            self.cerebro = bt.Cerebro()
            
            # 设置初始资金
            self.cerebro.broker.setcash(self.initial_cash)
            
            # 设置手续费
            self.cerebro.broker.setcommission(commission=0.0003)
            
            # 添加分析器
            self.cerebro.addanalyzer(bt.analyzers.Returns, _name='returns')
            self.cerebro.addanalyzer(bt.analyzers.DrawDown, _name='drawdown')
            self.cerebro.addanalyzer(bt.analyzers.SharpeRatio, _name='sharpe', riskfreerate=0.03)
            self.cerebro.addanalyzer(bt.analyzers.TradeAnalyzer, _name='trades')
            
            # 添加策略
            self.cerebro.addstrategy(
                self.strategy_class,
                **self.strategy_params
            )
            
            return True
            
        except Exception as e:
            logger.error(f"初始化引擎失败: {str(e)}")
            return False
    
    async def run(self) -> Dict[str, Any]:
        """运行回测"""
        try:
            # 准备数据
            data = {}
            for symbol in self.symbols:
                df = await self.data_handler.fetch_stock_data(
                    symbol,
                    self.start_date,
                    self.end_date
                )
                if df is not None:
                    data[symbol] = df
                    # 发布数据更新事件
                    utils_manager.event.publish(Event(
                        'data_updated',
                        {'symbol': symbol, 'data': df}
                    ))
            
            if not data:
                raise ValueError("没有有效数据")
            
            # 添加数据源
            for symbol, df in data.items():
                data_feed = bt.feeds.PandasData(
                    dataname=df,
                    name=symbol
                )
                self.cerebro.adddata(data_feed)
            
            # 运行回测
            results = self.cerebro.run()
            if not results:
                raise ValueError("回测执行失败")
            
            # 分析结果
            strat = results[0]
            self.analyze_results(strat)
            
            return self.results
            
        except Exception as e:
            logger.error(f"运行回测失败: {str(e)}")
            return {}
        
    def _handle_data_update(self, event: Event):
        """处理数据更新事件"""
        try:
            symbol = event.data['symbol']
            logger.info(f"数据更新: {symbol}")
            
            # 更新缓存
            utils_manager.cache.set(
                f"data_{symbol}",
                event.data['data']
            )
            
        except Exception as e:
            logger.error(f"处理数据更新事件失败: {str(e)}")
    
    def cleanup(self):
        """清理资源"""
        try:
            # 取消事件订阅
            utils_manager.event.unsubscribe('data_updated', self._handle_data_update)
            
            # 清理缓存
            utils_manager.cache.clean_expired_cache()
            
            logger.info("回测引擎资源清理完成")
            
        except Exception as e:
            logger.error(f"清理资源失败: {str(e)}")

    def analyze_results(self, strat):
        """分析回测结果"""
        try:
            # 获取交易记录
            self.trades_list = strat.trades
            
            # 创建权益曲线
            self.equity_curve = pd.DataFrame({
                'datetime': strat.datas[0].datetime.array,
                'close': strat.datas[0].close.array,
                'value': [strat.broker.getvalue() for _ in range(len(strat.datas[0]))]
            })
            self.equity_curve['datetime'] = pd.to_datetime(self.equity_curve['datetime'])
            self.equity_curve.set_index('datetime', inplace=True)
            
            # 分析性能
            performance = self.analyzer.analyze_trades(
                self.trades_list,
                self.equity_curve
            )
            
            # 创建图表
            charts = {
                'equity': self.visualizer.create_equity_curve_chart(
                    self.equity_curve,
                    self.trades_list
                ),
                'distribution': self.visualizer.create_pnl_distribution_chart(
                    self.trades_list
                )
            }
            
            # 保存结果
            self.results = {
                'summary': performance,
                'trades': self.trades_list,
                'equity_curve': self.equity_curve,
                'charts': charts
            }
            
        except Exception as e:
            logger.error(f"分析结果失败: {str(e)}")
    
    def save_results(self, output_dir: str = 'results'):
        """保存回测结果"""
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            # 保存汇总结果
            pd.DataFrame([self.results['summary']]).to_csv(
                output_path / 'summary.csv',
                index=False
            )
            
            # 保存交易记录
            pd.DataFrame(self.trades_list).to_csv(
                output_path / 'trades.csv',
                index=False
            )
            
            # 保存权益曲线
            self.equity_curve.to_csv(
                output_path / 'equity_curve.csv'
            )
            
            logger.info(f"回测结果已保存到 {output_path}")
            
        except Exception as e:
            logger.error(f"保存回测结果失败: {str(e)}")