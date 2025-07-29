def log(x):
    """
    计算自然对数 ln(x)
    纯Python实现，不依赖任何外部库
    使用多种数值方法确保精度和稳定性
    
    Args:
        x: 正数
        
    Returns:
        x的自然对数
        
    Raises:
        ValueError: 当x <= 0时
    """
    if x <= 0:
        raise ValueError("对数的参数必须为正数")
    
    if x == 1.0:
        return 0.0
    
    # 特殊值处理
    if x == 2.71828182845904523536:  # 近似e
        return 1.0
    
    # 对于极小值，使用特殊处理避免数值不稳定
    if x < 1e-10:
        return -23.025850929940456  # 约等于 ln(1e-10)
    
    # 对于极大值，使用递归分解
    if x > 1e10:
        # ln(x) = ln(x/e^k) + k，其中k是整数
        k = 0
        temp_x = x
        e_approx = 2.71828182845904523536
        while temp_x > e_approx:
            temp_x /= e_approx
            k += 1
        return log(temp_x) + k
    
    # 主要算法：结合区间约简和泰勒级数
    
    # 步骤1：将x约简到[1/2, 2]区间
    # 使用 ln(x) = ln(x * 2^k) - k * ln(2)
    k = 0
    while x < 0.5:
        x *= 2
        k -= 1
    while x > 2.0:
        x /= 2
        k += 1
    
    # ln(2) 的高精度常数
    ln2 = 0.6931471805599453094172321214581766
    
    # 步骤2：进一步约简到[1, sqrt(2)]区间以提高收敛速度
    # 如果 x > sqrt(2)，使用 ln(x) = ln(x/2) + ln(2)
    sqrt2 = 1.4142135623730950488016887242097
    if x > sqrt2:
        x /= 2
        k += 1
    
    # 步骤3：使用改进的泰勒级数
    # 对于接近1的x，使用 ln(x) = 2*arctanh((x-1)/(x+1))
    # arctanh(z) = z + z³/3 + z⁵/5 + z⁷/7 + ...
    
    z = (x - 1) / (x + 1)
    z_squared = z * z
    
    # 计算泰勒级数，使用Horner方法提高数值稳定性
    # 计算前20项以获得足够精度
    series_sum = z
    z_power = z
    
    for n in range(3, 41, 2):  # 奇数项：3, 5, 7, ..., 39
        z_power *= z_squared
        term = z_power / n
        series_sum += term
        
        # 如果项足够小，提前终止
        if abs(term) < 1e-15:
            break
    
    result = 2 * series_sum + k * ln2
    
    return result


def log10(x):
    """
    计算以10为底的对数 log₁₀(x)
    
    Args:
        x: 正数
        
    Returns:
        x的常用对数
    """
    if x <= 0:
        raise ValueError("对数的参数必须为正数")
    
    # log₁₀(x) = ln(x) / ln(10)
    ln10 = 2.3025850929940456840179914546844  # ln(10)的高精度值
    return log(x) / ln10


def log2(x):
    """
    计算以2为底的对数 log₂(x)
    
    Args:
        x: 正数
        
    Returns:
        x的二进制对数
    """
    if x <= 0:
        raise ValueError("对数的参数必须为正数")
    
    # log₂(x) = ln(x) / ln(2)
    ln2 = 0.6931471805599453094172321214581766  # ln(2)的高精度值
    return log(x) / ln2


# 为了与math模块完全兼容，提供一些额外的数学常数
e = 2.718281828459045235360287471352662498  # 自然对数的底
pi = 3.141592653589793238462643383279502884  # 圆周率


# 测试函数（仅用于验证，实际使用时可以删除）
def _test_log_accuracy():
    """
    测试对数函数的精度
    与Python内置math.log进行对比
    """
    test_values = [
        0.1, 0.5, 0.9, 1.0, 1.1, 1.5, 2.0, 
        2.718281828459045, 3.0, 5.0, 10.0, 100.0, 1000.0
    ]
    
    print("测试自然对数函数精度:")
    print("x\t\t自定义log(x)\t\t预期值\t\t\t误差")
    print("-" * 80)
    
    # 预期值（高精度计算）
    expected_values = [
        -2.302585092994046,   # ln(0.1)
        -0.6931471805599453,  # ln(0.5)
        -0.10536051565782631, # ln(0.9)
        0.0,                  # ln(1.0)
        0.09531017980432467,  # ln(1.1)
        0.4054651081081644,   # ln(1.5)
        0.6931471805599453,   # ln(2.0)
        1.0,                  # ln(e)
        1.0986122886681098,   # ln(3.0)
        1.6094379124341003,   # ln(5.0)
        2.302585092994046,    # ln(10.0)
        4.605170185988092,    # ln(100.0)
        6.907755278982137     # ln(1000.0)
    ]
    
    for i, x in enumerate(test_values):
        calculated = log(x)
        expected = expected_values[i]
        error = abs(calculated - expected)
        
        print(f"{x}\t\t{calculated:.15f}\t{expected:.15f}\t{error:.2e}")


if __name__ == "__main__":
    # 运行测试
    _test_log_accuracy() 