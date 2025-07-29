"""
自主数学函数库 math1.py
包含所有常用数学函数和常量，不依赖任何外部库
"""

# 数学常量
pi = 3.141592653589793
e = 2.718281828459045
tau = 2 * pi  # 2π
inf = float('inf')
nan = float('nan')

# 基础数学函数
def abs(x):
    """绝对值函数"""
    if x >= 0:
        return x
    else:
        return -x

def fabs(x):
    """浮点数绝对值函数"""
    return float(abs(x))

def sign(x):
    """符号函数"""
    if x > 0:
        return 1
    elif x < 0:
        return -1
    else:
        return 0

def sqrt(x):
    """平方根函数 - 使用牛顿迭代法"""
    if x < 0:
        raise ValueError("Cannot take square root of negative number")
    if x == 0:
        return 0.0
    
    # 初始猜测
    guess = x / 2.0
    
    # 牛顿迭代法
    for _ in range(50):  # 足够的迭代次数
        new_guess = 0.5 * (guess + x / guess)
        if abs(new_guess - guess) < 1e-15:
            break
        guess = new_guess
    
    return guess

def pow(x, y):
    """幂函数 x^y"""
    if y == 0:
        return 1.0
    if y == 1:
        return x
    if y == -1:
        return 1.0 / x
    
    if isinstance(y, int) and y > 0:
        # 快速幂算法
        result = 1.0
        base = x
        exp = y
        while exp > 0:
            if exp % 2 == 1:
                result *= base
            base *= base
            exp //= 2
        return result
    
    # 对于非整数幂，使用 exp(y * ln(x))
    if x <= 0:
        if x == 0:
            if y > 0:
                return 0.0
            else:
                raise ValueError("0 raised to negative power")
        else:
            raise ValueError("Negative number raised to non-integer power")
    
    return exp(y * log(x))

def exp(x):
    """指数函数 e^x - 使用泰勒级数"""
    if x == 0:
        return 1.0
    
    # 处理大数值
    if x > 700:
        return inf
    if x < -700:
        return 0.0
    
    # 将x缩放到[-1, 1]范围内以提高精度
    n = int(x)
    x = x - n
    
    # 使用泰勒级数计算 e^x
    result = 1.0
    term = 1.0
    
    for i in range(1, 50):
        term *= x / i
        result += term
        if abs(term) < 1e-15:
            break
    
    # 恢复缩放: e^(n+x) = e^n * e^x
    for _ in range(abs(n)):
        if n > 0:
            result *= e
        else:
            result /= e
    
    return result

def log(x):
    """自然对数函数 ln(x) - 使用牛顿迭代法"""
    if x <= 0:
        raise ValueError("log of non-positive number")
    if x == 1:
        return 0.0
    
    # 将x缩放到[1, 2]范围内
    n = 0
    while x >= 2:
        x /= 2
        n += 1
    while x < 1:
        x *= 2
        n -= 1
    
    # 使用级数展开 ln(1+u) = u - u²/2 + u³/3 - ...
    u = x - 1
    result = 0.0
    term = u
    
    for i in range(1, 50):
        result += term / i if i % 2 == 1 else -term / i
        term *= u
        if abs(term) < 1e-15:
            break
    
    # 恢复缩放: ln(2^n * x) = n * ln(2) + ln(x)
    return result + n * 0.6931471805599453  # ln(2)

def log10(x):
    """常用对数 log₁₀(x)"""
    return log(x) / 2.302585092994046  # log(10)

def log2(x):
    """二进制对数 log₂(x)"""
    return log(x) / 0.6931471805599453  # log(2)

# 三角函数
def sin(x):
    """正弦函数 - 使用泰勒级数"""
    # 将x规范化到[-π, π]
    x = x % (2 * pi)
    if x > pi:
        x -= 2 * pi
    
    # 泰勒级数: sin(x) = x - x³/3! + x⁵/5! - x⁷/7! + ...
    result = 0.0
    term = x
    
    for n in range(1, 50, 2):
        result += term
        term *= -x * x / ((n + 1) * (n + 2))
        if abs(term) < 1e-15:
            break
    
    return result

def cos(x):
    """余弦函数 - 使用泰勒级数"""
    # 将x规范化到[-π, π]
    x = x % (2 * pi)
    if x > pi:
        x -= 2 * pi
    
    # 泰勒级数: cos(x) = 1 - x²/2! + x⁴/4! - x⁶/6! + ...
    result = 1.0
    term = 1.0
    
    for n in range(2, 50, 2):
        term *= -x * x / (n * (n - 1))
        result += term
        if abs(term) < 1e-15:
            break
    
    return result

def tan(x):
    """正切函数"""
    cos_x = cos(x)
    if abs(cos_x) < 1e-15:
        raise ValueError("tan is undefined at this point")
    return sin(x) / cos_x

def asin(x):
    """反正弦函数"""
    if abs(x) > 1:
        raise ValueError("asin input must be in [-1, 1]")
    if x == 1:
        return pi / 2
    if x == -1:
        return -pi / 2
    if x == 0:
        return 0.0
    
    # 使用级数展开
    result = x
    term = x
    
    for n in range(1, 30):
        term *= x * x * (2 * n - 1) * (2 * n - 1) / ((2 * n) * (2 * n + 1))
        result += term
        if abs(term) < 1e-15:
            break
    
    return result

def acos(x):
    """反余弦函数"""
    if abs(x) > 1:
        raise ValueError("acos input must be in [-1, 1]")
    return pi / 2 - asin(x)

def atan(x):
    """反正切函数"""
    if abs(x) > 1:
        # 使用恒等式 atan(x) = π/2 - atan(1/x) for |x| > 1
        if x > 0:
            return pi / 2 - atan(1 / x)
        else:
            return -pi / 2 - atan(1 / x)
    
    # 泰勒级数: atan(x) = x - x³/3 + x⁵/5 - x⁷/7 + ...
    result = 0.0
    term = x
    
    for n in range(1, 50, 2):
        result += term / n
        term *= -x * x
        if abs(term) < 1e-15:
            break
    
    return result

def atan2(y, x):
    """二参数反正切函数"""
    if x > 0:
        return atan(y / x)
    elif x < 0:
        if y >= 0:
            return atan(y / x) + pi
        else:
            return atan(y / x) - pi
    else:  # x == 0
        if y > 0:
            return pi / 2
        elif y < 0:
            return -pi / 2
        else:
            return 0.0  # 或者抛出异常

# 双曲函数
def sinh(x):
    """双曲正弦函数"""
    return (exp(x) - exp(-x)) / 2

def cosh(x):
    """双曲余弦函数"""
    return (exp(x) + exp(-x)) / 2

def tanh(x):
    """双曲正切函数"""
    if x > 700:
        return 1.0
    if x < -700:
        return -1.0
    
    exp_2x = exp(2 * x)
    return (exp_2x - 1) / (exp_2x + 1)

# 特殊函数
def factorial(n):
    """阶乘函数"""
    if not isinstance(n, int) or n < 0:
        raise ValueError("factorial is only defined for non-negative integers")
    
    result = 1
    for i in range(1, n + 1):
        result *= i
    return result

def gamma(x):
    """伽马函数 - 使用Stirling近似"""
    if x <= 0:
        raise ValueError("gamma function is not defined for non-positive real numbers")
    
    if x < 1:
        # 使用递推关系 Γ(x) = Γ(x+1) / x
        return gamma(x + 1) / x
    
    # Stirling近似
    x -= 1  # 因为Γ(n) = (n-1)!
    if x == 0:
        return 1.0
    
    return sqrt(2 * pi / x) * pow(x / e, x)

def erf(x):
    """误差函数 - 使用级数展开"""
    if x == 0:
        return 0.0
    
    # 使用级数展开: erf(x) = (2/√π) * Σ((-1)^n * x^(2n+1) / (n! * (2n+1)))
    sqrt_pi = sqrt(pi)
    result = 0.0
    term = x
    
    for n in range(50):
        coeff = 1.0
        for i in range(1, n + 1):
            coeff /= i
        
        result += ((-1) ** n) * term * coeff / (2 * n + 1)
        term *= x * x
        
        if abs(term * coeff) < 1e-15:
            break
    
    return 2 / sqrt_pi * result

def floor(x):
    """向下取整函数"""
    return int(x) if x >= 0 else int(x) - 1

def ceil(x):
    """向上取整函数"""
    return int(x) + 1 if x > int(x) else int(x)

def trunc(x):
    """截断函数"""
    return int(x)

def fmod(x, y):
    """浮点数模运算"""
    if y == 0:
        raise ValueError("fmod: division by zero")
    return x - int(x / y) * y

def modf(x):
    """返回x的小数部分和整数部分"""
    integer_part = trunc(x)
    fractional_part = x - integer_part
    return (fractional_part, integer_part)

def ldexp(x, i):
    """返回 x * 2^i"""
    return x * pow(2, i)

def frexp(x):
    """将x分解为尾数和指数"""
    if x == 0:
        return (0.0, 0)
    
    sign = 1 if x >= 0 else -1
    x = abs(x)
    
    exp = 0
    while x >= 1:
        x /= 2
        exp += 1
    while x < 0.5:
        x *= 2
        exp -= 1
    
    return (sign * x, exp)

def hypot(x, y):
    """计算 sqrt(x² + y²)"""
    return sqrt(x * x + y * y)

def degrees(x):
    """弧度转角度"""
    return x * 180 / pi

def radians(x):
    """角度转弧度"""
    return x * pi / 180

# 比较函数
def isnan(x):
    """检查是否为NaN"""
    return x != x

def isinf(x):
    """检查是否为无穷大"""
    return x == inf or x == -inf

def isfinite(x):
    """检查是否为有限数"""
    return not (isnan(x) or isinf(x))

def copysign(x, y):
    """返回具有y符号的x的绝对值"""
    if y >= 0:
        return abs(x)
    else:
        return -abs(x)

# 最大最小函数
def fmax(x, y):
    """返回两个数中的最大值"""
    if isnan(x):
        return y
    if isnan(y):
        return x
    return max(x, y)

def fmin(x, y):
    """返回两个数中的最小值"""
    if isnan(x):
        return y
    if isnan(y):
        return x
    return min(x, y)

# 导出所有函数和常量
__all__ = [
    'pi', 'e', 'tau', 'inf', 'nan',
    'abs', 'fabs', 'sign', 'sqrt', 'pow', 'exp', 'log', 'log10', 'log2',
    'sin', 'cos', 'tan', 'asin', 'acos', 'atan', 'atan2',
    'sinh', 'cosh', 'tanh',
    'factorial', 'gamma', 'erf',
    'floor', 'ceil', 'trunc', 'fmod', 'modf', 'ldexp', 'frexp',
    'hypot', 'degrees', 'radians',
    'isnan', 'isinf', 'isfinite', 'copysign', 'fmax', 'fmin'
] 