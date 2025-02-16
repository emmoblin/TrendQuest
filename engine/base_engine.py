from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from utils.log_init import get_logger

logger = get_logger(__name__)

class BaseEngine:
    """回测引擎基类"""
    
    def __init__(
        self,
        strategy_name: str,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime,
        initial_cash: float = 100000.0,
        commission: float = 0.0003
    ):
        """初始化引擎
        
        Args:
            strategy_name: 策略名称
            symbols: 交易标的列表
            start_date: 回测开始日期
            end_date: 回测结束日期
            initial_cash: 初始资金
            commission: 佣金率
        """
        self.strategy_name = strategy_name
        self.symbols = symbols
        self.start_date = start_date
        self.end_date = end_date
        self.initial_cash = initial_cash
        self.commission = commission
        
        # 策略参数
        self._strategy_params = {}
        
        # 运行状态
        self.is_running = False
        self.progress = 0.0
        self.status = "初始化"
        self.error = None
        
        # 进度回调
        self.progress_callback: Optional[Callable[[float, str], None]] = None
    
    def set_strategy_params(self, params: Dict[str, Any]):
        """设置策略参数
        
        Args:
            params: 策略参数字典
        """
        self._strategy_params = params
    
    def update_progress(self, progress: float, status: str):
        """更新进度
        
        Args:
            progress: 进度值(0-1)
            status: 状态描述
        """
        self.progress = progress
        self.status = status
        if self.progress_callback:
            self.progress_callback(progress, status)
    
    def run(self) -> Dict[str, Any]:
        """运行回测
        
        Returns:
            回测结果字典
        """
        raise NotImplementedError("子类必须实现run方法")