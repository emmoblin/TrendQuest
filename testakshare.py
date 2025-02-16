import akshare as ak
import pandas as pd

# 测试数据获取
try:
    df = ak.stock_zh_a_daily(symbol="sz000001",
                    start_date="20200101",
                    end_date="20241201",
                    adjust="qfq")
    
    print("数据获取成功:")
    print(df.head())
except Exception as e:
    print(f"错误: {str(e)}")