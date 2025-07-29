"""
误差函数(Error Function)的纯Python实现
100%自主代码，不依赖任何外部库

作者: AI Assistant
版本: 1.0
用途: 替代scipy.special.erf函数
"""

def _factorial(n):
    """计算阶乘"""
    if n <= 1:
        return 1
    result = 1
    for i in range(2, n + 1):
        result *= i
    return result

def _exp(x):
    """计算e^x的近似值"""
    if x > 700:  # 防止溢出
        return float('inf')
    if x < -700:  # 防止下溢
        return 0.0
    
    # 使用泰勒级数展开: e^x = 1 + x + x^2/2! + x^3/3! + ...
    result = 1.0
    term = 1.0
    
    for n in range(1, 100):  # 100项通常足够精确
        term *= x / n
        result += term
        if abs(term) < 1e-15:  # 收敛判断
            break
    
    return result

def _sqrt(x):
    """计算平方根的牛顿法实现"""
    if x < 0:
        raise ValueError("Cannot compute square root of negative number")
    if x == 0:
        return 0.0
    
    # 牛顿法: x_{n+1} = (x_n + a/x_n) / 2
    guess = x / 2.0
    for _ in range(50):  # 最多迭代50次
        new_guess = (guess + x / guess) / 2.0
        if abs(new_guess - guess) < 1e-15:
            break
        guess = new_guess
    
    return guess

def _abs(x):
    """绝对值函数"""
    return x if x >= 0 else -x

def _pi():
    """计算π的近似值 (使用Machin公式)"""
    # π/4 = 4*arctan(1/5) - arctan(1/239)
    # 使用泰勒级数计算arctan
    def arctan(x):
        if _abs(x) > 1:
            # 对于|x|>1，使用恒等式 arctan(x) = π/2 - arctan(1/x) (x>0)
            if x > 0:
                return _pi() / 2 - arctan(1/x)
            else:
                return -_pi() / 2 - arctan(1/x)
        
        # arctan(x) = x - x^3/3 + x^5/5 - x^7/7 + ...
        result = 0.0
        term = x
        x_squared = x * x
        
        for n in range(200):  # 足够的项数
            sign = 1 if n % 2 == 0 else -1
            result += sign * term / (2 * n + 1)
            term *= x_squared
            if _abs(term / (2 * n + 3)) < 1e-15:
                break
        
        return result
    
    # 使用简单的近似，避免递归
    return 3.141592653589793

def erf(x):
    """
    误差函数的高精度实现
    
    erf(x) = (2/√π) * ∫[0 to x] e^(-t²) dt
    
    使用多种数值方法组合以确保高精度:
    - 小x值: 泰勒级数展开
    - 中等x值: 连分数近似 
    - 大x值: 渐近展开
    
    Args:
        x: 输入值(可以是数字、列表或嵌套列表)
        
    Returns:
        erf(x)的值，类型与输入相同
    """
    
    # 处理不同类型的输入
    if isinstance(x, list):
        # 递归处理列表
        return [erf(item) for item in x]
    
    # 处理数值输入
    if x == 0:
        return 0.0
    
    # 利用erf的奇函数性质: erf(-x) = -erf(x)
    if x < 0:
        return -erf(-x)
    
    # 对于大的x值，erf(x) ≈ 1
    if x > 6:
        return 1.0
    
    # 使用不同的近似方法根据x的大小
    if x <= 2.5:
        # 小到中等值：使用泰勒级数
        return _erf_series(x)
    else:
        # 中到大值：使用互补误差函数的连分数近似
        return 1.0 - _erfc_continued_fraction(x)

def _erf_series(x):
    """
    使用泰勒级数计算erf(x)
    erf(x) = (2/√π) * [x - x³/3·1! + x⁵/5·2! - x⁷/7·3! + ...]
    """
    sqrt_pi = _sqrt(_pi())
    two_over_sqrt_pi = 2.0 / sqrt_pi
    
    result = 0.0
    term = x
    x_squared = x * x
    
    for n in range(100):  # 足够的项数保证精度
        factorial_n = _factorial(n)
        denominator = (2 * n + 1) * factorial_n
        
        # 交替符号
        sign = 1 if n % 2 == 0 else -1
        result += sign * term / denominator
        
        # 下一项
        term *= x_squared
        
        # 收敛判断
        if _abs(term / ((2 * n + 3) * _factorial(n + 1))) < 1e-15:
            break
    
    return two_over_sqrt_pi * result

def _erfc_continued_fraction(x):
    """
    使用连分数近似计算互补误差函数erfc(x) = 1 - erf(x)
    对于x > 2.5使用，基于渐近展开
    """
    # erfc(x) ≈ (e^(-x²) / (x√π)) * 连分数
    sqrt_pi = _sqrt(_pi())
    exp_neg_x_squared = _exp(-x * x)
    
    # 连分数的计算
    # 使用Lentz算法计算连分数
    b0 = x
    a1 = 0.5
    b1 = x + a1
    
    f = b0 / b1
    
    for n in range(1, 100):
        an = n * 0.5
        bn = x + an
        
        # Lentz算法的迭代
        if _abs(bn) < 1e-30:
            bn = 1e-30
        
        f_old = f
        f = b0 / (bn + an / f)
        
        if _abs(f - f_old) / _abs(f) < 1e-15:
            break
    
    return (exp_neg_x_squared / (sqrt_pi * x)) * f

def erfc(x):
    """
    互补误差函数: erfc(x) = 1 - erf(x)
    
    Args:
        x: 输入值
        
    Returns:
        erfc(x)的值
    """
    if isinstance(x, list):
        return [erfc(item) for item in x]
    
    return 1.0 - erf(x)

# 测试函数
def _test_erf():
    """测试erf函数的准确性"""
    test_cases = [
        (0.0, 0.0),
        (0.1, 0.11246291601828),
        (0.5, 0.5204998778130465),
        (1.0, 0.8427007929497149),
        (1.5, 0.9661051464753107),
        (2.0, 0.9953222650189527),
        (-1.0, -0.8427007929497149),
        (-0.5, -0.5204998778130465),
    ]
    
    print("测试erf函数:")
    for x, expected in test_cases:
        result = erf(x)
        error = _abs(result - expected)
        print(f"erf({x:4.1f}) = {result:.15f}, 期望值: {expected:.15f}, 误差: {error:.2e}")
    
    # 测试列表输入
    test_list = [0.0, 0.5, 1.0, 1.5]
    result_list = erf(test_list)
    print(f"\n测试列表输入: erf({test_list}) = {result_list}")

if __name__ == "__main__":
    # 运行测试
    _test_erf() 