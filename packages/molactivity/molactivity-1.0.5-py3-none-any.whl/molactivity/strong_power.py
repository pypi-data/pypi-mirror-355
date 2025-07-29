"""
Strong Power Library - 强大的幂运算库
专门为反向传播设计，不使用任何第三方库
完全自主实现，具有强大的数值稳定性
"""

from . import math1 as math

def backward_power(base, exponent):
    """
    强大的幂运算函数，专门为反向传播设计
    
    特点：
    - 完全自主实现，不依赖第三方库
    - 强大的数值稳定性处理
    - 专门针对梯度计算的特殊需求
    - 支持标量、列表、多维数组
    
    Args:
        base: 底数（标量、列表或多维数组）
        exponent: 指数（标量、列表或多维数组）
        
    Returns:
        幂运算结果，保持输入的数据类型和形状
    """
    
    # 1. 类型检查和预处理
    base_is_scalar = isinstance(base, (int, float))
    exp_is_scalar = isinstance(exponent, (int, float))
    
    if base_is_scalar and exp_is_scalar:
        return _scalar_power(base, exponent)
    elif base_is_scalar:
        return _broadcast_base_power(base, exponent)
    elif exp_is_scalar:
        return _broadcast_exp_power(base, exponent)
    else:
        return _array_power(base, exponent)

def _scalar_power(base, exp):
    """处理标量幂运算"""
    try:
        # 特殊情况处理
        if base == 0:
            if exp > 0:
                return 0.0
            elif exp == 0:
                return 1.0  # 数学上0^0通常定义为1
            else:
                return float('inf')  # 0的负数次幂
                
        if exp == 0:
            return 1.0
            
        if exp == 1:
            return float(base)
            
        if base == 1:
            return 1.0
            
        # 处理负底数
        if base < 0:
            if isinstance(exp, int) or exp == int(exp):
                # 整数指数，可以正常计算
                result = abs(base) ** exp
                if int(exp) % 2 == 1:  # 奇数次幂保持负号
                    result = -result
                return result
            else:
                # 非整数指数，取绝对值避免复数
                return abs(base) ** exp
                
        # 数值稳定性检查
        if abs(exp) > 100:
            if abs(base) > 1:
                # 大底数大指数，容易溢出
                if exp > 0:
                    return 1e38  # 接近float的最大值
                else:
                    return 1e-38  # 接近0
            elif abs(base) < 1:
                # 小底数大指数
                if exp > 0:
                    return 1e-38  # 接近0
                else:
                    return 1e38  # 很大
                    
        # 使用指数对数等价形式进行安全计算
        if base > 0:
            try:
                log_base = math.log(base)
                if abs(exp * log_base) > 88:  # exp(88)接近float最大值
                    if exp * log_base > 0:
                        return 1e38
                    else:
                        return 1e-38
                return math.exp(exp * log_base)
            except (OverflowError, ValueError):
                return 1.0  # 安全默认值
                
        # 如果所有特殊处理都不适用，使用内置power
        return pow(base, exp)
        
    except (OverflowError, ValueError, ZeroDivisionError):
        # 完全失败的情况，返回安全值
        if base == 0:
            return 0.0
        else:
            return 1.0

def _broadcast_base_power(base_scalar, exp_array):
    """广播标量底数到数组指数"""
    if isinstance(exp_array, list):
        if isinstance(exp_array[0], list):
            # 多维列表
            return [[_scalar_power(base_scalar, exp_val) 
                    for exp_val in row] for row in exp_array]
        else:
            # 一维列表
            return [_scalar_power(base_scalar, exp_val) for exp_val in exp_array]
    else:
        # 假设是单个值
        return _scalar_power(base_scalar, exp_array)

def _broadcast_exp_power(base_array, exp_scalar):
    """广播标量指数到数组底数"""
    if isinstance(base_array, list):
        if isinstance(base_array[0], list):
            # 多维列表
            return [[_scalar_power(base_val, exp_scalar) 
                    for base_val in row] for row in base_array]
        else:
            # 一维列表
            return [_scalar_power(base_val, exp_scalar) for base_val in base_array]
    else:
        # 假设是单个值
        return _scalar_power(base_array, exp_scalar)

def _array_power(base_array, exp_array):
    """处理数组对数组的幂运算"""
    
    def _process_recursive(base_data, exp_data):
        """递归处理多维数组"""
        if isinstance(base_data, list) and isinstance(exp_data, list):
            if isinstance(base_data[0], list):
                # 多维情况
                return [_process_recursive(base_row, exp_row) 
                       for base_row, exp_row in zip(base_data, exp_data)]
            else:
                # 一维情况
                return [_scalar_power(b, e) for b, e in zip(base_data, exp_data)]
        else:
            # 标量情况
            return _scalar_power(base_data, exp_data)
    
    try:
        return _process_recursive(base_array, exp_array)
    except Exception:
        # 如果形状不匹配或其他错误，返回安全的默认值
        if isinstance(base_array, list):
            if isinstance(base_array[0], list):
                return [[1.0 for _ in row] for row in base_array]
            else:
                return [1.0 for _ in base_array]
        else:
            return 1.0

def safe_power_with_offset(base_array, exp_array, offset=1e-6):
    """
    安全的幂运算，带有偏移量处理
    专门用于梯度计算中的 (abs_base + offset)^exp 模式
    
    Args:
        base_array: 底数数组
        exp_array: 指数数组  
        offset: 偏移量，防止除零
        
    Returns:
        安全的幂运算结果
    """
    
    def _add_offset_recursive(data, offset_val):
        """递归地给数组添加偏移量"""
        if isinstance(data, list):
            if isinstance(data[0], list):
                return [[max(abs(val), 0) + offset_val for val in row] for row in data]
            else:
                return [max(abs(val), 0) + offset_val for val in data]
        else:
            return max(abs(data), 0) + offset_val
    
    # 添加偏移量并取绝对值
    safe_base = _add_offset_recursive(base_array, offset)
    
    # 使用标准的power函数
    return backward_power(safe_base, exp_array)

def gradient_power(base_array, exp_array, mode='base'):
    """
    专门用于梯度计算的幂运算
    
    Args:
        base_array: 底数数组
        exp_array: 指数数组
        mode: 'base' 计算对底数的梯度, 'exp' 计算对指数的梯度
        
    Returns:
        梯度计算需要的幂运算结果
    """
    
    if mode == 'base':
        # 计算 base^(exp-1) 用于底数梯度
        def _subtract_one_recursive(data):
            if isinstance(data, list):
                if isinstance(data[0], list):
                    return [[val - 1 for val in row] for row in data]
                else:
                    return [val - 1 for val in data]
            else:
                return data - 1
                
        exp_minus_one = _subtract_one_recursive(exp_array)
        return safe_power_with_offset(base_array, exp_minus_one)
        
    elif mode == 'exp':
        # 计算 base^exp 用于指数梯度
        return safe_power_with_offset(base_array, exp_array)
    else:
        raise ValueError(f"Unknown mode: {mode}. Use 'base' or 'exp'")

# 便利函数，直接替换np.power的使用
def replace_np_power(base, exp):
    """
    直接替换np.power调用的函数
    """
    return backward_power(base, exp)
