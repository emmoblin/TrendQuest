from ui.backtest_page import BacktestPage

def show_strategy_backtest():
    """显示策略回测界面"""
    page = BacktestPage()
    page.render()

if __name__ == "__main__":
    show_strategy_backtest()