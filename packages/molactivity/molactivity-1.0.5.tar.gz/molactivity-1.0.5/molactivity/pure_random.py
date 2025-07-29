# 纯Python随机数生成器 - 完全替代random模块
# 不使用任何外部库，仅使用Python内置功能


class PureRandom:
    """
    纯Python实现的随机数生成器
    使用线性同余生成器(Linear Congruential Generator, LCG)算法
    """
    
    def __init__(self, seed=None):
        """
        初始化随机数生成器
        
        Args:
            seed: 随机种子，如果为None则使用哈希值
        """
        # LCG参数 (使用与glibc相同的参数)
        self.a = 1103515245  # 乘数
        self.c = 12345       # 增量
        self.m = 2**31       # 模数
        
        # 设置种子
        if seed is None:
            # 使用对象ID和哈希值创建种子，避免依赖time模块
            seed = abs(hash(str(id(self))) + id(self)) % self.m
        
        self.seed_value = seed % self.m
        self._state = self.seed_value
    
    def seed(self, seed_value):
        """
        设置随机种子
        
        Args:
            seed_value: 种子值
        """
        if seed_value is None:
            # 使用对象ID和哈希值创建种子
            seed_value = abs(hash(str(id(self))) + id(self)) % self.m
        
        self.seed_value = seed_value % self.m
        self._state = self.seed_value
    
    def _next(self):
        """
        生成下一个随机数
        
        Returns:
            0到m-1之间的整数
        """
        self._state = (self.a * self._state + self.c) % self.m
        return self._state
    
    def random(self):
        """
        生成0到1之间的随机浮点数
        
        Returns:
            [0.0, 1.0)之间的浮点数
        """
        return self._next() / self.m
    
    def randint(self, min_val, max_val):
        """
        生成指定范围内的随机整数
        
        Args:
            min_val: 最小值(包含)
            max_val: 最大值(包含)
            
        Returns:
            [min_val, max_val]之间的整数
        """
        if min_val > max_val:
            raise ValueError("min_val不能大于max_val")
        
        range_size = max_val - min_val + 1
        return min_val + (self._next() % range_size)
    
    def choice(self, sequence):
        """
        从序列中随机选择一个元素
        
        Args:
            sequence: 序列(列表、元组等)
            
        Returns:
            随机选择的元素
        """
        if not sequence:
            raise IndexError("不能从空序列中选择")
        
        index = self.randint(0, len(sequence) - 1)
        return sequence[index]
    
    def shuffle(self, sequence):
        """
        就地打乱序列的顺序
        使用Fisher-Yates洗牌算法
        
        Args:
            sequence: 要打乱的列表(会被直接修改)
        """
        if not sequence:
            return
        
        # Fisher-Yates洗牌算法
        for i in range(len(sequence) - 1, 0, -1):
            j = self.randint(0, i)
            sequence[i], sequence[j] = sequence[j], sequence[i]
    
    def sample(self, population, k):
        """
        从总体中随机抽取k个不重复的元素
        
        Args:
            population: 总体序列
            k: 抽取的数量
            
        Returns:
            包含k个元素的新列表
        """
        if k > len(population):
            raise ValueError("抽取数量不能大于总体大小")
        
        if k < 0:
            raise ValueError("抽取数量不能为负数")
        
        # 创建索引列表
        indices = list(range(len(population)))
        result = []
        
        # 无重复抽取
        for _ in range(k):
            if not indices:
                break
            
            # 随机选择一个索引
            idx = self.randint(0, len(indices) - 1)
            selected_idx = indices.pop(idx)
            result.append(population[selected_idx])
        
        return result
    
    def uniform(self, min_val, max_val):
        """
        生成指定范围内的随机浮点数
        
        Args:
            min_val: 最小值
            max_val: 最大值
            
        Returns:
            [min_val, max_val)之间的浮点数
        """
        return min_val + (max_val - min_val) * self.random()
    
    def normal(self, mean=0.0, std=1.0):
        """
        生成正态分布的随机数
        使用Box-Muller变换算法
        
        Args:
            mean: 均值
            std: 标准差
            
        Returns:
            正态分布的随机数
        """
        # 使用Box-Muller变换，每次生成两个独立的标准正态分布随机数
        # 为了提高效率，我们缓存第二个值
        if not hasattr(self, '_spare_normal'):
            self._spare_normal = None
        
        if self._spare_normal is not None:
            # 使用缓存的值
            z = self._spare_normal
            self._spare_normal = None
        else:
            # 生成两个新的正态分布随机数
            
            # 生成两个(0,1)均匀分布随机数
            u1 = self.random()
            u2 = self.random()
            
            # 确保u1不为0，避免log(0)
            while u1 == 0:
                u1 = self.random()
            
            # Box-Muller变换
            from . import math1
            from . import math_log
            z0 = math1.sqrt(-2.0 * math_log.log(u1)) * math1.cos(2.0 * math1.pi * u2)
            z1 = math1.sqrt(-2.0 * math_log.log(u1)) * math1.sin(2.0 * math1.pi * u2)
            
            # 使用第一个值，缓存第二个值
            z = z0
            self._spare_normal = z1
        
        # 转换为指定均值和标准差的正态分布
        return mean + std * z


# 全局随机数生成器实例
_global_random = PureRandom()


# 提供与random模块兼容的接口
def seed(seed_value=None):
    """设置全局随机种子"""
    _global_random.seed(seed_value)


def random():
    """生成0到1之间的随机浮点数"""
    return _global_random.random()


def randint(min_val, max_val):
    """生成指定范围内的随机整数"""
    return _global_random.randint(min_val, max_val)


def choice(sequence):
    """从序列中随机选择一个元素"""
    return _global_random.choice(sequence)


def weighted_choice(sequence, weights=None, size=1, replace=True):
    """
    带权重的随机选择函数，替代np.random.choice
    
    Args:
        sequence: 要选择的序列或范围
        weights: 权重数组，如果为None则等权重
        size: 要选择的数量
        replace: 是否允许重复选择
        
    Returns:
        选择的结果列表或单个值
    """
    # 处理输入序列
    if isinstance(sequence, int):
        # 如果是整数，创建range
        sequence = list(range(sequence))
    elif not isinstance(sequence, (list, tuple)):
        # 转换为列表
        sequence = list(sequence)
    
    if not sequence:
        raise ValueError("序列不能为空")
    
    # 处理权重
    if weights is None:
        # 等权重
        weights = [1.0] * len(sequence)
    else:
        # 确保权重是列表
        if hasattr(weights, 'data'):
            # 处理arrays.Array对象
            weights = weights.data if isinstance(weights.data, list) else list(weights.data)
        elif hasattr(weights, '__iter__'):
            weights = list(weights)
        else:
            weights = [weights]
    
    if len(weights) != len(sequence):
        raise ValueError(f"权重数量({len(weights)})必须等于序列长度({len(sequence)})")
    
    # 检查权重是否有效
    total_weight = sum(weights)
    if total_weight <= 0:
        raise ValueError("权重总和必须大于0")
    
    # 归一化权重
    normalized_weights = [w / total_weight for w in weights]
    
    # 创建累积分布
    cumulative_weights = []
    cumsum = 0.0
    for w in normalized_weights:
        cumsum += w
        cumulative_weights.append(cumsum)
    
    # 确保最后一个值为1.0（避免浮点精度问题）
    cumulative_weights[-1] = 1.0
    
    def select_one():
        """选择一个元素"""
        rand_val = _global_random.random()
        for i, cum_weight in enumerate(cumulative_weights):
            if rand_val <= cum_weight:
                return sequence[i]
        # 如果由于浮点精度问题没有选中，返回最后一个
        return sequence[-1]
    
    # 执行选择
    if size == 1:
        return select_one()
    
    results = []
    available_indices = list(range(len(sequence)))
    available_weights = normalized_weights[:]
    
    for _ in range(size):
        if not available_indices:
            break
        
        if replace or len(available_indices) == len(sequence):
            # 允许重复或第一次选择
            selected = select_one()
            results.append(selected)
        else:
            # 不允许重复，需要从剩余元素中选择
            if not available_indices:
                break
            
            # 重新计算累积权重
            total_available_weight = sum(available_weights)
            if total_available_weight <= 0:
                break
            
            normalized_available = [w / total_available_weight for w in available_weights]
            cumulative_available = []
            cumsum = 0.0
            for w in normalized_available:
                cumsum += w
                cumulative_available.append(cumsum)
            cumulative_available[-1] = 1.0
            
            # 选择
            rand_val = _global_random.random()
            selected_idx = None
            for i, cum_weight in enumerate(cumulative_available):
                if rand_val <= cum_weight:
                    selected_idx = i
                    break
            
            if selected_idx is None:
                selected_idx = len(cumulative_available) - 1
            
            # 获取实际的序列索引和值
            actual_idx = available_indices[selected_idx]
            selected = sequence[actual_idx]
            results.append(selected)
            
            # 从可用列表中移除
            available_indices.pop(selected_idx)
            available_weights.pop(selected_idx)
    
    return results


def shuffle(sequence):
    """就地打乱序列的顺序"""
    _global_random.shuffle(sequence)


def sample(population, k):
    """从总体中随机抽取k个不重复的元素"""
    return _global_random.sample(population, k)


def uniform(min_val, max_val):
    """生成指定范围内的随机浮点数"""
    return _global_random.uniform(min_val, max_val)


def normal(mean=0.0, std=1.0):
    """
    生成正态分布的随机数
    使用Box-Muller变换算法
    
    Args:
        mean: 均值
        std: 标准差
        
    Returns:
        正态分布的随机数
    """
    return _global_random.normal(mean, std)


def normal_batch(size, mean=0.0, std=1.0):
    """
    批量生成正态分布随机数，优化的Box-Muller算法
    
    Args:
        size: 要生成的随机数数量
        mean: 均值
        std: 标准差
        
    Returns:
        正态分布随机数列表
    """
    # 预分配列表提高性能
    result = [0.0] * size
    from . import math1
    from . import math_log
    
    # 预计算常量
    two_pi = 2.0 * math1.pi
    
    # 优化的Box-Muller变换，减少函数调用
    i = 0
    random_func = _global_random.random  # 缓存函数引用
    sqrt_func = math1.sqrt
    cos_func = math1.cos
    sin_func = math1.sin
    log_func = math_log.log
    
    while i < size:
        # 生成两个(0,1)均匀分布随机数
        u1 = random_func()
        u2 = random_func()
        
        # 确保u1不为0，避免log(0)
        if u1 <= 1e-10:  # 使用更小的阈值
            continue
        
        # Box-Muller变换
        sqrt_term = sqrt_func(-2.0 * log_func(u1))
        angle = two_pi * u2
        
        z0 = sqrt_term * cos_func(angle)
        result[i] = mean + std * z0
        i += 1
        
        # 如果还需要更多数字，使用第二个值
        if i < size:
            z1 = sqrt_term * sin_func(angle)
            result[i] = mean + std * z1
            i += 1
    
    return result


def uniform_batch(size, low=0.0, high=1.0):
    """
    批量生成均匀分布随机数，提高大数组生成效率
    
    Args:
        size: 要生成的随机数数量
        low: 最小值
        high: 最大值
        
    Returns:
        均匀分布随机数列表
    """
    # 预分配列表并预计算范围
    from . import arrays
    total_size = size if isinstance(size, int) else int(arrays.prod(arrays.Array(size)))
    result = [0.0] * total_size
    range_val = high - low
    
    for i in range(total_size):
        result[i] = low + range_val * _global_random.random()
    
    return result


