import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import jinja2
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

class ReportGenerator:
    """回测报告生成器"""
    
    def __init__(self, template_dir: str = 'templates'):
        self.template_dir = Path(template_dir)
        self.env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_dir)
        )
    
    def create_performance_chart(
        self,
        prices: pd.Series,
        trades: List[Dict[str, Any]],
        title: str
    ) -> go.Figure:
        """创建交易表现图表"""
        fig = make_subplots(
            rows=2,
            cols=1,
            shared_xaxes=True,
            vertical_spacing=0.03,
            subplot_titles=(title, '交易量'),
            row_width=[0.7, 0.3]
        )
        
        # 添加价格线
        fig.add_trace(
            go.Scatter(
                x=prices.index,
                y=prices.values,
                mode='lines',
                name='价格',
                line=dict(color='blue', width=1)
            ),
            row=1,
            col=1
        )
        
        # 添加交易点
        buy_trades = [t for t in trades if t['type'] == 'buy']
        sell_trades = [t for t in trades if t['type'] == 'sell']
        
        if buy_trades:
            fig.add_trace(
                go.Scatter(
                    x=[t['date'] for t in buy_trades],
                    y=[t['price'] for t in buy_trades],
                    mode='markers',
                    name='买入',
                    marker=dict(
                        symbol='triangle-up',
                        size=10,
                        color='red'
                    )
                ),
                row=1,
                col=1
            )
        
        if sell_trades:
            fig.add_trace(
                go.Scatter(
                    x=[t['date'] for t in sell_trades],
                    y=[t['price'] for t in sell_trades],
                    mode='markers',
                    name='卖出',
                    marker=dict(
                        symbol='triangle-down',
                        size=10,
                        color='green'
                    )
                ),
                row=1,
                col=1
            )
        
        # 添加成交量
        fig.add_trace(
            go.Bar(
                x=prices.index,
                y=prices.values,
                name='成交量',
                marker_color='rgb(158,202,225)',
                opacity=0.6
            ),
            row=2,
            col=1
        )
        
        # 更新布局
        fig.update_layout(
            height=800,
            showlegend=True,
            hovermode='x unified'
        )
        
        return fig
    
    def create_summary_chart(
        self,
        results: Dict[str, Dict[str, Any]]
    ) -> go.Figure:
        """创建汇总分析图表"""
        symbols = list(results.keys())
        returns = [r['return_rate'] for r in results.values()]
        win_rates = [r['win_rate'] for r in results.values()]
        
        fig = go.Figure()
        
        # 添加收益率柱状图
        fig.add_trace(
            go.Bar(
                x=symbols,
                y=returns,
                name='收益率',
                text=[f"{r:.2%}" for r in returns],
                textposition='auto'
            )
        )
        
        # 添加胜率线
        fig.add_trace(
            go.Scatter(
                x=symbols,
                y=win_rates,
                name='胜率',
                text=[f"{r:.2%}" for r in win_rates],
                mode='lines+markers',
                yaxis='y2'
            )
        )
        
        # 更新布局
        fig.update_layout(
            title='策略表现汇总',
            xaxis_title='股票代码',
            yaxis_title='收益率',
            yaxis2=dict(
                title='胜率',
                overlaying='y',
                side='right'
            ),
            showlegend=True
        )
        
        return fig
    
    def generate_html_report(
        self,
        results: Dict[str, Dict[str, Any]],
        config: Dict[str, Any],
        output_file: str
    ) -> bool:
        """生成HTML报告"""
        try:
            template = self.env.get_template('backtest_report.html')
            
            # 准备报告数据
            report_data = {
                'title': '回测报告',
                'generation_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'config': config,
                'results': results,
                'summary_chart': self.create_summary_chart(results).to_html(),
                'performance_charts': {
                    symbol: self.create_performance_chart(
                        data['prices'],
                        data['trades'],
                        f"{symbol} 交易表现"
                    ).to_html()
                    for symbol, data in results.items()
                }
            }
            
            # 生成报告
            html = template.render(**report_data)
            
            # 保存报告
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html)
            
            return True
            
        except Exception as e:
            print(f"生成报告失败: {str(e)}")
            return False