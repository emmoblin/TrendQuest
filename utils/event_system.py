from typing import Dict, List, Callable, Any
from datetime import datetime
import logging
import asyncio
from collections import defaultdict
from .log_init import get_logger

logger = get_logger(__name__)

class Event:
    """事件类"""
    
    def __init__(self, event_type: str, data: Any = None):
        self.current_time = datetime.strptime("2025-02-15 18:54:58", "%Y-%m-%d %H:%M:%S")
        self.current_user = "emmoblin"
        
        self.type = event_type
        self.data = data
        self.timestamp = self.current_time

class EventSystem:
    """事件系统"""
    
    def __init__(self):
        self.current_time = datetime.strptime("2025-02-15 18:54:58", "%Y-%m-%d %H:%M:%S")
        self.current_user = "emmoblin"
        
        self.handlers: Dict[str, List[Callable]] = defaultdict(list)
        self.logger = logging.getLogger(__name__)
    
    def subscribe(self, event_type: str, handler: Callable):
        """订阅事件"""
        self.handlers[event_type].append(handler)
        self.logger.debug(f"订阅事件: {event_type}")
    
    def unsubscribe(self, event_type: str, handler: Callable):
        """取消订阅事件"""
        if event_type in self.handlers:
            self.handlers[event_type].remove(handler)
            self.logger.debug(f"取消订阅事件: {event_type}")
    
    async def publish(self, event: Event):
        """发布事件"""
        if event.type in self.handlers:
            tasks = []
            for handler in self.handlers[event.type]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        tasks.append(asyncio.create_task(handler(event)))
                    else:
                        handler(event)
                except Exception as e:
                    self.logger.error(f"处理事件 {event.type} 失败: {str(e)}")
            
            if tasks:
                await asyncio.gather(*tasks)
    
    def clear(self):
        """清除所有订阅"""
        self.handlers.clear()
        self.logger.debug("清除所有事件订阅")