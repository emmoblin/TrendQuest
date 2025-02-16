import unittest
from strategies import strategy_factory
from strategies.base_strategy import BaseStrategy

class TestStrategyFactory(unittest.TestCase):
    def test_strategy_factory_initialization(self):
        """测试策略工厂初始化"""
        self.assertIsNotNone(strategy_factory)
        self.assertTrue(len(strategy_factory.list_strategies()) > 0)
    
    def test_get_strategy(self):
        """测试获取策略"""
        # 测试获取内置策略
        strategy_class = strategy_factory.get_strategy('DualMA')
        self.assertTrue(issubclass(strategy_class, BaseStrategy))
        
        # 测试获取不存在的策略
        with self.assertRaises(ValueError):
            strategy_factory.get_strategy('NonexistentStrategy')

if __name__ == '__main__':
    unittest.main()