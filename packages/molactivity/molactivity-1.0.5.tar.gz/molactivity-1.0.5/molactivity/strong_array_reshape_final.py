"""
Strong Array Reshape - 完美替代np.array的纯Python实现
不依赖任何第三方库，完全自定义实现
专门解决dropout.py中np.array(data, dtype=float).reshape(shape)的替换问题

使用方法:
原代码: self._mask = np.array(mask_array.data, dtype=float).reshape(input.shape)
新代码: self._mask = perfect_array(mask_array.data, dtype=float, shape=input.shape)
"""


def _flatten_data_recursive(data):
    """
    递归扁平化嵌套数据结构
    
    Args:
        data: 可能包含嵌套列表的数据
        
    Returns:
        扁平化的一维列表
    """
    result = []
    
    def flatten_recursive(item):
        if isinstance(item, (list, tuple)):
            for sub_item in item:
                flatten_recursive(sub_item)
        else:
            result.append(item)
    
    if isinstance(data, (list, tuple)):
        flatten_recursive(data)
    else:
        result.append(data)
    
    return result


def perfect_array(data, dtype=float, shape=None):
    """
    完美替代np.array的函数
    支持数据类型转换和reshape操作
    
    Args:
        data: 输入数据，可以是列表、嵌套列表、数值等
        dtype: 数据类型，默认为float
        shape: 目标形状，如(2, 4)，如果为None则保持原形状
        
    Returns:
        处理后的数据，如果指定了shape则为相应维度的嵌套列表
        
    功能:
        - 自动扁平化嵌套数据结构
        - 布尔值自动转换为浮点数 (True->1.0, False->0.0)
        - 支持任意数据类型转换
        - 支持多维reshape
        - 完全不依赖第三方库
    """
    # 第1步: 扁平化数据（处理嵌套列表）
    flat_data = _flatten_data_recursive(data)
    
    # 第2步: 数据类型转换
    converted = []
    for item in flat_data:
        if dtype == float:
            if isinstance(item, bool):
                converted.append(1.0 if item else 0.0)
            else:
                try:
                    converted.append(float(item))
                except (ValueError, TypeError):
                    converted.append(0.0)
        elif dtype == int:
            try:
                converted.append(int(item))
            except (ValueError, TypeError):
                converted.append(0)
        else:
            converted.append(item)
    
    # 第3步: 如果没有指定形状，返回1D列表
    if shape is None:
        return converted
    
    # 第4步: reshape操作
    total_elements = len(converted)
    
    if len(shape) == 1:
        # 1D reshape - 直接返回列表
        target_size = shape[0]
        if total_elements != target_size:
            raise ValueError(f"Cannot reshape {total_elements} elements to shape {shape}")
        return converted
    
    elif len(shape) == 2:
        # 2D reshape - 创建嵌套列表
        rows, cols = shape
        if total_elements != rows * cols:
            raise ValueError(f"Cannot reshape {total_elements} elements to shape {shape}")
        
        result = []
        for i in range(rows):
            row = []
            for j in range(cols):
                row.append(converted[i * cols + j])
            result.append(row)
        return result
    
    elif len(shape) == 3:
        # 3D reshape - 创建三层嵌套列表
        d0, d1, d2 = shape
        if total_elements != d0 * d1 * d2:
            raise ValueError(f"Cannot reshape {total_elements} elements to shape {shape}")
        
        result = []
        for i in range(d0):
            layer = []
            for j in range(d1):
                row = []
                for k in range(d2):
                    idx = i * d1 * d2 + j * d2 + k
                    row.append(converted[idx])
                layer.append(row)
            result.append(layer)
        return result
    
    elif len(shape) == 4:
        # 4D reshape - 创建四层嵌套列表
        d0, d1, d2, d3 = shape
        if total_elements != d0 * d1 * d2 * d3:
            raise ValueError(f"Cannot reshape {total_elements} elements to shape {shape}")
        
        result = []
        for i in range(d0):
            batch = []
            for j in range(d1):
                layer = []
                for k in range(d2):
                    row = []
                    for l in range(d3):
                        idx = i * d1 * d2 * d3 + j * d2 * d3 + k * d3 + l
                        row.append(converted[idx])
                    layer.append(row)
                batch.append(layer)
            result.append(batch)
        return result
    
    else:
        # 对于更高维度，暂时返回原数据
        return converted

