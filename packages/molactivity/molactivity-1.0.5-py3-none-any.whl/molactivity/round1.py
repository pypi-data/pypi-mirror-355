"""
四舍五入函数(Round Function)的纯Python实现
100%自主代码，不依赖任何外部库

作者: AI Assistant
版本: 1.0
用途: 替代builtins.round函数
"""

def _abs(x):
    """绝对值函数"""
    return x if x >= 0 else -x

def _floor(x):
    """向下取整函数"""
    if x >= 0:
        return int(x)
    else:
        # 对于负数，如果有小数部分，需要减1
        if x == int(x):
            return int(x)
        else:
            return int(x) - 1

def _ceil(x):
    """向上取整函数"""
    if x >= 0:
        # 对于正数，如果有小数部分，需要加1
        if x == int(x):
            return int(x)
        else:
            return int(x) + 1
    else:
        return int(x)

def _pow10(n):
    """计算10的n次方"""
    if n == 0:
        return 1
    elif n > 0:
        result = 1
        for _ in range(n):
            result *= 10
        return result
    else:  # n < 0
        result = 1.0
        for _ in range(-n):
            result /= 10
        return result

def round(number, ndigits=None):
    """
    四舍五入函数的高精度实现
    
    实现Python内置round函数的行为:
    - 使用"银行家四舍五入"(Round half to even)
    - 当数字恰好在两个数中间时，四舍五入到最接近的偶数
    
    Args:
        number: 要四舍五入的数字
        ndigits: 保留的小数位数，None表示四舍五入到整数
        
    Returns:
        四舍五入后的结果
    """
    
    # 处理特殊情况
    if number != number:  # NaN检查 (NaN != NaN 为True)
        return number
    
    if number == float('inf') or number == float('-inf'):
        return number
    
    # 如果ndigits为None，四舍五入到整数
    if ndigits is None:
        return _round_to_int(number)
    
    # 确保ndigits是整数
    if not isinstance(ndigits, int):
        raise TypeError("ndigits must be an integer")
    
    # 如果ndigits为0，等同于四舍五入到整数
    if ndigits == 0:
        return _round_to_int(number)
    
    # 计算缩放因子
    scale = _pow10(ndigits)
    
    # 将数字缩放，四舍五入，然后缩放回来
    scaled = number * scale
    rounded_scaled = _round_to_int(scaled)
    result = rounded_scaled / scale
    
    return result

def _round_to_int(x):
    """
    四舍五入到最接近的整数
    使用银行家四舍五入规则
    """
    if x == 0.0:
        return 0
    
    # 获取符号
    sign = 1 if x >= 0 else -1
    abs_x = _abs(x)
    
    # 获取整数部分和小数部分
    int_part = int(abs_x)
    frac_part = abs_x - int_part
    
    # 银行家四舍五入规则
    if frac_part < 0.5:
        # 小于0.5，向下取整
        result = int_part
    elif frac_part > 0.5:
        # 大于0.5，向上取整
        result = int_part + 1
    else:
        # 恰好等于0.5，四舍五入到最接近的偶数
        if int_part % 2 == 0:
            # 整数部分是偶数，向下取整
            result = int_part
        else:
            # 整数部分是奇数，向上取整
            result = int_part + 1
    
    return result * sign

def _is_close_to_half(frac_part):
    """
    检查小数部分是否接近0.5
    处理浮点数精度问题
    """
    epsilon = 1e-15
    return _abs(frac_part - 0.5) < epsilon

# 测试函数
def _test_round():
    """测试round函数的准确性"""
    test_cases = [
        # (输入, ndigits, 期望输出)
        (2.5, None, 2),    # 银行家四舍五入：向偶数取整
        (3.5, None, 4),    # 银行家四舍五入：向偶数取整
        (2.4, None, 2),    # 普通四舍五入
        (2.6, None, 3),    # 普通四舍五入
        (-2.5, None, -2),  # 负数银行家四舍五入
        (-3.5, None, -4),  # 负数银行家四舍五入
        (0.0, None, 0),    # 零
        (1.23456, 2, 1.23), # 保留2位小数
        (1.23556, 3, 1.236), # 保留3位小数
        (1234.5, -1, 1230), # 负数位：十位四舍五入
        (1235.0, -1, 1240), # 负数位：十位四舍五入（银行家规则）
        (123.456, 0, 123),  # ndigits=0等同于None
    ]
    
    print("测试round函数:")
    for number, ndigits, expected in test_cases:
        result = round(number, ndigits)
        print(f"round({number}, {ndigits}) = {result}, 期望值: {expected}, {'✓' if result == expected else '✗'}")
    
    # 测试边界情况
    print("\n边界情况测试:")
    edge_cases = [
        (float('inf'), None),
        (float('-inf'), None),
        (0.5, None),
        (1.5, None),
        (2.5, None),
        (-0.5, None),
        (-1.5, None),
        (-2.5, None),
    ]
    
    for number, ndigits in edge_cases:
        try:
            result = round(number, ndigits)
            print(f"round({number}, {ndigits}) = {result}")
        except Exception as e:
            print(f"round({number}, {ndigits}) 引发异常: {e}")

if __name__ == "__main__":
    # 运行测试
    _test_round() 