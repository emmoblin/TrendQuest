def format_number(value: float, is_percentage: bool = False) -> str:
    """格式化数字显示
    
    Args:
        value: 要格式化的数值
        is_percentage: 是否以百分比格式显示
    
    Returns:
        格式化后的字符串
    """
    if is_percentage:
        return f"{value * 100:.2f}%"
    return f"{value:.2f}"