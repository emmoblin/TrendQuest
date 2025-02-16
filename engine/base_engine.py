from typing import Dict, Any, Optional
from datetime import datetime
from utils.log_init import get_logger

logger = get_logger(__name__)

class BaseEngine:
    """回测引擎基类"""
    
    def __init__(
        self,
        strategy_class: type,
        strategy_params: Dict[str, Any],
        symbols: Dict[str, Dict[str, str]],
        start_date: datetime,
        end_date: datetime,
        initial_cash: float = 100000.0,
        commission: float = 0.0003,
        slippage: float = 0.0001,
        size: int = 100,
        margin: float = 1.0,
        trade_on_close: bool = False,
        **kwargs
    ):
        """初始化引擎
        
        Args:
            strategy_class: 策略类
            strategy_params: 策略参数字典
            symbols: 交易标的字典 {symbol: {"name": name, "industry": industry}}
            start_date: 回测开始日期
            end_date: 回测结束日期
            initial_cash: 初始资金
            commission: 佣金率
            slippage: 滑点率
            size: 每手数量
            margin: 保证金率
            trade_on_close: 是否以收盘价交易
            **kwargs: 其他参数
        """
        self.strategy_class = strategy_class
        self.strategy_params = strategy_params
        self.symbols = symbols
        self.start_date = start_date
        self.end_date = end_date
        self.initial_cash = initial_cash
        self.commission = commission
        self.slippage = slippage
        self.size = size
        self.margin = margin
        self.trade_on_close = trade_on_close
        self.kwargs = kwargs
        
        # 运行状态
        self.is_running = False
        self.progress = 0.0
        self.status = "初始化"
        self.error = None
    
    def run(self) -> Dict[str, Any]:
        """运行回测
        
        Returns:
            回测结果字典
        """
        raise NotImplementedError("子类必须实现run方法")
    
    def stop(self):
        """停止回测"""
        self.is_running = False
        self.status = "已停止"
    
    def get_status(self) -> Dict[str, Any]:
        """获取运行状态
        
        Returns:
            状态信息字典
        """
        return {
            "is_running": self.is_running,
            "progress": self.progress,
            "status": self.status,
            "error": str(self.error) if self.error else None
        }