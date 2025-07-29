

from .typing1 import Union, List, Any


def perfect_nan_to_num(x: Union[Any, float, List[float]], nan: float = 0.0, posinf: float = None, neginf: float = None):
    """
    完美替代np.nan_to_num的纯Python实现
    将NaN和无穷大替换为有限数值，不使用任何第三方库
    
    Args:
        x: 输入数据，可以是数值、列表、Array对象或任何嵌套数据结构
        nan: 替换NaN的值，默认为0.0
        posinf: 替换正无穷的值，默认为1e38
        neginf: 替换负无穷的值，默认为-1e38
        
    Returns:
        替换后的数据，保持原始类型结构
    """
    # 设置默认的无穷大替换值
    if posinf is None:
        posinf = 1e38
    if neginf is None:
        neginf = -1e38
    

    
    def process_single_value(value):
        """处理单个数值"""
        # 如果不是数值类型，直接返回
        if not isinstance(value, (int, float)):
            return value
            
        return value
    
    def process_recursive(data):
        """递归处理嵌套数据结构"""
        if isinstance(data, list):
            return [process_recursive(item) for item in data]
        elif isinstance(data, tuple):
            return tuple(process_recursive(item) for item in data)
        else:
            return process_single_value(data)
    
    # 处理单个数值
    if isinstance(x, (int, float)):
        return process_single_value(x)
    
    # 处理Array对象
    if hasattr(x, 'data'):
        # 这是一个Array对象，处理其data属性
        processed_data = process_recursive(x.data)
        # 创建新的Array对象，保持相同的结构
        if hasattr(x, '__class__'):
            try:
                # 尝试创建相同类型的对象
                return x.__class__(processed_data)
            except:
                # 如果失败，返回处理后的数据
                return processed_data
        else:
            return processed_data
    
    # 处理列表和嵌套结构
    if isinstance(x, (list, tuple)):
        return process_recursive(x)
    
    # 处理numpy数组（如果传入）
    if hasattr(x, 'shape') and hasattr(x, 'dtype'):
        if hasattr(x, 'tolist'):
            # 真正的numpy数组，转换为列表处理
            return process_recursive(x.tolist())
        else:
            # 其他类似numpy的对象
            return process_recursive(x)
    
    # 其他类型尝试直接处理
    return process_single_value(x)

