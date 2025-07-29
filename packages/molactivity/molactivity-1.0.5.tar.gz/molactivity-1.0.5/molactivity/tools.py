"""
工具模块 - 100%自主实现
替代threading, functools, enum等标准库功能

作者: AI Assistant
版本: 1.0
用途: 提供threading.Lock, functools.wraps, Enum等功能的纯Python实现
"""

# ============================================================================
# Threading模块的Lock实现
# ============================================================================

class Lock:
    """
    线程锁的简单实现
    在单线程环境下提供基本的锁接口
    """
    
    def __init__(self):
        self._locked = False
        self._owner = None
    
    def acquire(self, blocking=True, timeout=-1):
        """
        获取锁
        
        Args:
            blocking: 是否阻塞等待
            timeout: 超时时间
            
        Returns:
            bool: 是否成功获取锁
        """
        if not self._locked:
            self._locked = True
            self._owner = id(object())  # 简单的所有者标识
            return True
        else:
            if not blocking:
                return False
            # 在真实的多线程环境中，这里需要等待
            # 简化实现中直接返回False
            return False
    
    def release(self):
        """释放锁"""
        if not self._locked:
            raise RuntimeError("release unlocked lock")
        self._locked = False
        self._owner = None
    
    def locked(self):
        """检查锁是否被获取"""
        return self._locked
    
    def __enter__(self):
        """上下文管理器进入"""
        self.acquire()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.release()

# Threading模块的模拟
class threading:
    """模拟threading模块"""
    
    @staticmethod
    def Lock():
        """创建一个新的锁对象"""
        return Lock()

# ============================================================================
# functools模块的wraps实现
# ============================================================================

def wraps(wrapped, assigned=None, updated=None):
    """
    装饰器工厂，用于创建包装器函数
    复制被包装函数的元数据到包装器函数
    
    Args:
        wrapped: 被包装的函数
        assigned: 要复制的属性列表
        updated: 要更新的属性列表
        
    Returns:
        装饰器函数
    """
    if assigned is None:
        assigned = ('__module__', '__name__', '__qualname__', '__doc__', '__annotations__')
    if updated is None:
        updated = ('__dict__',)
    
    def decorator(wrapper):
        """实际的装饰器"""
        # 复制指定的属性
        for attr in assigned:
            try:
                original_value = getattr(wrapped, attr)
                setattr(wrapper, attr, original_value)
            except AttributeError:
                pass
        
        # 更新指定的属性
        for attr in updated:
            try:
                wrapper_attr = getattr(wrapper, attr)
                wrapped_attr = getattr(wrapped, attr)
                if hasattr(wrapper_attr, 'update'):
                    wrapper_attr.update(wrapped_attr)
            except AttributeError:
                pass
        
        # 设置特殊属性
        wrapper.__wrapped__ = wrapped
        
        return wrapper
    
    return decorator

# functools模块的模拟
class functools:
    """模拟functools模块"""
    
    @staticmethod
    def wraps(wrapped, assigned=None, updated=None):
        """wraps装饰器"""
        return wraps(wrapped, assigned, updated)

# ============================================================================
# enum模块的实现
# ============================================================================

class _AutoValue:
    """自动值生成器"""
    
    def __init__(self):
        self._value = 0
    
    def __call__(self):
        self._value += 1
        return self._value

# 全局自动值生成器实例
_auto_instance = _AutoValue()

def auto():
    """
    自动生成枚举值
    
    Returns:
        int: 自动递增的整数值
    """
    return _auto_instance()

class EnumMeta(type):
    """枚举类的元类"""
    
    def __new__(cls, name, bases, namespace):
        # 处理auto()值
        auto_value = 0
        enum_members = {}
        
        # 第一遍：收集所有枚举成员并处理auto()
        for key, value in list(namespace.items()):
            if not key.startswith('_') and not callable(value):
                if hasattr(value, '__call__') and value.__name__ == 'auto':
                    # 这是auto()调用的结果
                    auto_value += 1
                    enum_members[key] = auto_value
                    namespace[key] = auto_value
                elif isinstance(value, int):
                    enum_members[key] = value
                    auto_value = max(auto_value, value)
        
        # 创建类
        enum_class = super().__new__(cls, name, bases, namespace)
        
        # 存储枚举成员
        enum_class._member_map_ = enum_members
        enum_class._member_names_ = list(enum_members.keys())
        enum_class._member_values_ = list(enum_members.values())
        
        return enum_class
    
    def __iter__(cls):
        """支持迭代枚举成员"""
        for name in cls._member_names_:
            yield getattr(cls, name)
    
    def __len__(cls):
        """返回枚举成员数量"""
        return len(cls._member_names_)

class Enum(metaclass=EnumMeta):
    """
    枚举基类
    """
    
    def __init__(self, value):
        self._value_ = value
        self._name_ = None
    
    @property
    def name(self):
        """枚举成员名称"""
        if self._name_ is None:
            # 查找对应的名称
            for name, val in self.__class__._member_map_.items():
                if val == self._value_:
                    self._name_ = name
                    break
        return self._name_
    
    @property
    def value(self):
        """枚举成员值"""
        return self._value_
    
    def __str__(self):
        return f"{self.__class__.__name__}.{self.name}"
    
    def __repr__(self):
        return f"<{self.__class__.__name__}.{self.name}: {self.value}>"
    
    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self._value_ == other._value_
        return False
    
    def __hash__(self):
        return hash(self._value_)

# enum模块的模拟
class enum:
    """模拟enum模块"""
    
    Enum = Enum
    auto = auto

# ============================================================================
# sys模块的argv实现
# ============================================================================

class _ArgvHandler:
    """
    命令行参数处理器
    模拟sys.argv的功能
    """
    
    def __init__(self):
        # 默认argv，第一个元素通常是脚本名
        self._argv = ['script.py']
        self._initialized = False
    
    def set_argv(self, argv_list):
        """
        设置命令行参数
        
        Args:
            argv_list: 命令行参数列表，第一个元素应该是脚本名
        """
        if isinstance(argv_list, list):
            self._argv = argv_list[:]
        else:
            self._argv = [str(argv_list)]
        self._initialized = True
    
    def get_argv(self):
        """
        获取命令行参数列表
        
        Returns:
            list: 命令行参数列表
        """
        return self._argv[:]
    
    def get_args(self):
        """
        获取脚本参数（不包括脚本名）
        等价于sys.argv[1:]
        
        Returns:
            list: 脚本参数列表
        """
        return self._argv[1:] if len(self._argv) > 1 else []
    
    def parse_command_line(self, command_string):
        """
        从命令行字符串解析参数
        
        Args:
            command_string: 完整的命令行字符串
            
        Example:
            parse_command_line("python script.py arg1 arg2 --flag")
            结果: ['script.py', 'arg1', 'arg2', '--flag']
        """
        if not command_string:
            return
        
        # 简单的命令行解析
        parts = command_string.split()
        if not parts:
            return
        
        # 查找Python脚本
        script_index = -1
        for i, part in enumerate(parts):
            if part.endswith('.py'):
                script_index = i
                break
        
        if script_index != -1:
            # 从脚本开始构建argv
            self._argv = parts[script_index:]
        else:
            # 如果没找到.py文件，使用所有参数
            self._argv = parts[:]
        
        self._initialized = True
    
    def add_arg(self, arg):
        """
        添加单个参数
        
        Args:
            arg: 要添加的参数
        """
        self._argv.append(str(arg))
    
    def clear(self):
        """清除所有参数，重置为默认状态"""
        self._argv = ['script.py']
        self._initialized = False
    
    def __len__(self):
        """返回参数数量"""
        return len(self._argv)
    
    def __getitem__(self, index):
        """支持索引访问"""
        return self._argv[index]
    
    def __setitem__(self, index, value):
        """支持索引设置"""
        self._argv[index] = str(value)
    
    def __iter__(self):
        """支持迭代"""
        return iter(self._argv)
    
    def __str__(self):
        """字符串表示"""
        return str(self._argv)
    
    def __repr__(self):
        """详细字符串表示"""
        return f"ArgvHandler({self._argv})"

# 创建全局argv处理器实例 - 直接作为argv使用，支持索引访问
argv = _ArgvHandler()

def get_argv():
    """
    获取命令行参数列表
    等价于sys.argv
    
    Returns:
        list: 完整的命令行参数列表，包括脚本名
    """
    return argv.get_argv()

def args():
    """
    获取脚本参数（不包括脚本名）
    等价于sys.argv[1:]
    
    Returns:
        list: 脚本参数列表
    """
    return argv.get_args()

def set_argv(argv_list):
    """
    设置命令行参数
    
    Args:
        argv_list: 命令行参数列表
    """
    argv.set_argv(argv_list)

def parse_command_line(command_string):
    """
    从命令行字符串解析参数
    
    Args:
        command_string: 完整的命令行字符串
    """
    argv.parse_command_line(command_string)

def add_arg(arg):
    """
    添加单个命令行参数
    
    Args:
        arg: 要添加的参数
    """
    argv.add_arg(arg)

def clear_argv():
    """清除所有命令行参数"""
    argv.clear()

# sys模块的模拟
class sys:
    """模拟sys模块"""
    
    @staticmethod
    def argv():
        """获取命令行参数"""
        return argv()

# ============================================================================
# copy模块的实现
# ============================================================================

class _CopyRegistry:
    """
    拷贝注册表，管理自定义类型的拷贝方法
    """
    
    def __init__(self):
        self._registry = {}
    
    def register(self, type_cls, copy_func):
        """注册自定义类型的拷贝函数"""
        self._registry[type_cls] = copy_func
    
    def get(self, type_cls):
        """获取类型对应的拷贝函数"""
        return self._registry.get(type_cls)

# 全局拷贝注册表
_copy_registry = _CopyRegistry()

def copy(obj):
    """
    浅拷贝对象
    创建对象的浅层副本，只拷贝对象本身，不拷贝对象内部的可变对象
    
    Args:
        obj: 要拷贝的对象
        
    Returns:
        拷贝后的对象
    """
    # 不可变类型直接返回
    if obj is None or isinstance(obj, (int, float, str, bool, complex, bytes, frozenset)):
        return obj
    
    # 检查是否有自定义拷贝方法
    obj_type = type(obj)
    custom_copy = _copy_registry.get(obj_type)
    if custom_copy:
        return custom_copy(obj)
    
    # 检查对象是否有__copy__方法
    if hasattr(obj, '__copy__'):
        return obj.__copy__()
    
    # 处理常见类型
    if isinstance(obj, list):
        return obj[:]  # 浅拷贝列表
    
    elif isinstance(obj, tuple):
        return tuple(obj)  # 元组本身不可变，但可能包含可变对象
    
    elif isinstance(obj, dict):
        return obj.copy()  # 字典的浅拷贝
    
    elif isinstance(obj, set):
        return obj.copy()  # 集合的浅拷贝
    
    # 处理自定义类的实例
    elif hasattr(obj, '__dict__'):
        # 创建同类型的新实例
        try:
            # 尝试不调用__init__创建实例
            new_obj = obj.__class__.__new__(obj.__class__)
            
            # 拷贝属性字典
            if hasattr(obj, '__dict__'):
                new_obj.__dict__.update(obj.__dict__)
            
            # 处理slots
            if hasattr(obj, '__slots__'):
                for slot in obj.__slots__:
                    if hasattr(obj, slot):
                        setattr(new_obj, slot, getattr(obj, slot))
            
            return new_obj
        except:
            # 如果上述方法失败，尝试其他方法
            pass
    
    # 最后的尝试：直接返回对象（对于一些特殊类型）
    return obj

def deepcopy(obj, memo=None):
    """
    深拷贝对象
    递归地拷贝对象及其内部的所有可变对象
    
    Args:
        obj: 要拷贝的对象
        memo: 备忘录字典，用于处理循环引用
        
    Returns:
        深拷贝后的对象
    """
    if memo is None:
        memo = {}
    
    # 获取对象ID
    obj_id = id(obj)
    
    # 检查是否已经拷贝过（处理循环引用）
    if obj_id in memo:
        return memo[obj_id]
    
    # 不可变类型直接返回
    if obj is None or isinstance(obj, (int, float, str, bool, complex, bytes, frozenset)):
        return obj
    
    # 检查是否有自定义深拷贝方法
    obj_type = type(obj)
    custom_copy = _copy_registry.get(obj_type)
    if custom_copy:
        result = custom_copy(obj, memo)
        memo[obj_id] = result
        return result
    
    # 检查对象是否有__deepcopy__方法
    if hasattr(obj, '__deepcopy__'):
        result = obj.__deepcopy__(memo)
        memo[obj_id] = result
        return result
    
    # 处理列表
    if isinstance(obj, list):
        result = []
        memo[obj_id] = result  # 先记录，防止循环引用
        for item in obj:
            result.append(deepcopy(item, memo))
        return result
    
    # 处理元组
    elif isinstance(obj, tuple):
        # 先检查是否需要深拷贝（是否包含可变对象）
        needs_copy = False
        for item in obj:
            if not isinstance(item, (int, float, str, bool, complex, bytes, frozenset, type(None))):
                needs_copy = True
                break
        
        if not needs_copy:
            return obj  # 元组中都是不可变对象，直接返回
        
        # 需要深拷贝
        temp_list = []
        memo[obj_id] = temp_list  # 临时记录，防止循环引用
        for item in obj:
            temp_list.append(deepcopy(item, memo))
        result = tuple(temp_list)
        memo[obj_id] = result  # 更新记录
        return result
    
    # 处理字典
    elif isinstance(obj, dict):
        result = {}
        memo[obj_id] = result  # 先记录，防止循环引用
        for key, value in obj.items():
            new_key = deepcopy(key, memo)
            new_value = deepcopy(value, memo)
            result[new_key] = new_value
        return result
    
    # 处理集合
    elif isinstance(obj, set):
        result = set()
        memo[obj_id] = result  # 先记录，防止循环引用
        for item in obj:
            result.add(deepcopy(item, memo))
        return result
    
    # 处理自定义类的实例
    elif hasattr(obj, '__dict__') or hasattr(obj, '__slots__'):
        try:
            # 创建同类型的新实例
            new_obj = obj.__class__.__new__(obj.__class__)
            memo[obj_id] = new_obj  # 先记录，防止循环引用
            
            # 深拷贝属性字典
            if hasattr(obj, '__dict__'):
                for key, value in obj.__dict__.items():
                    setattr(new_obj, key, deepcopy(value, memo))
            
            # 处理slots
            if hasattr(obj, '__slots__'):
                for slot in obj.__slots__:
                    if hasattr(obj, slot):
                        value = getattr(obj, slot)
                        setattr(new_obj, slot, deepcopy(value, memo))
            
            return new_obj
        except Exception as e:
            # 如果创建失败，尝试其他方法
            pass
    
    # 处理函数和方法（通常不需要拷贝）
    if callable(obj):
        return obj
    
    # 最后的尝试：对于无法处理的类型，返回浅拷贝
    try:
        return copy(obj)
    except:
        # 实在无法拷贝，返回原对象
        return obj

def _deepcopy_atomic(obj, memo):
    """深拷贝原子类型对象（内部使用）"""
    return obj

def _deepcopy_list(obj, memo):
    """深拷贝列表（内部使用）"""
    obj_id = id(obj)
    if obj_id in memo:
        return memo[obj_id]
    
    result = []
    memo[obj_id] = result
    for item in obj:
        result.append(deepcopy(item, memo))
    return result

def _deepcopy_tuple(obj, memo):
    """深拷贝元组（内部使用）"""
    obj_id = id(obj)
    if obj_id in memo:
        return memo[obj_id]
    
    temp_list = []
    for item in obj:
        temp_list.append(deepcopy(item, memo))
    result = tuple(temp_list)
    memo[obj_id] = result
    return result

def _deepcopy_dict(obj, memo):
    """深拷贝字典（内部使用）"""
    obj_id = id(obj)
    if obj_id in memo:
        return memo[obj_id]
    
    result = {}
    memo[obj_id] = result
    for key, value in obj.items():
        new_key = deepcopy(key, memo)
        new_value = deepcopy(value, memo)
        result[new_key] = new_value
    return result

def _deepcopy_method(obj, memo):
    """深拷贝方法（通常返回原方法）"""
    return obj

def _keep_alive(obj, memo):
    """保持对象存活（防止垃圾回收）"""
    pass

# 注册常见类型的拷贝函数
_copy_registry.register(type(None), _deepcopy_atomic)
_copy_registry.register(int, _deepcopy_atomic)
_copy_registry.register(float, _deepcopy_atomic) 
_copy_registry.register(str, _deepcopy_atomic)
_copy_registry.register(bool, _deepcopy_atomic)
_copy_registry.register(complex, _deepcopy_atomic)
_copy_registry.register(bytes, _deepcopy_atomic)
_copy_registry.register(list, _deepcopy_list)
_copy_registry.register(tuple, _deepcopy_tuple)
_copy_registry.register(dict, _deepcopy_dict)

class Error(Exception):
    """copy模块的基础异常类"""
    pass

# copy模块的模拟
class copy:
    """模拟copy模块"""
    
    @staticmethod
    def copy(obj):
        """浅拷贝"""
        # 直接实现浅拷贝逻辑，避免递归调用
        # 不可变类型直接返回
        if obj is None or isinstance(obj, (int, float, str, bool, complex, bytes, frozenset)):
            return obj
        
        # 检查对象是否有__copy__方法
        if hasattr(obj, '__copy__'):
            return obj.__copy__()
        
        # 处理常见类型
        if isinstance(obj, list):
            return obj[:]  # 浅拷贝列表
        elif isinstance(obj, tuple):
            return tuple(obj)  # 元组本身不可变
        elif isinstance(obj, dict):
            return obj.copy()  # 字典的浅拷贝
        elif isinstance(obj, set):
            return obj.copy()  # 集合的浅拷贝
        
        # 处理自定义类的实例
        elif hasattr(obj, '__dict__'):
            try:
                new_obj = obj.__class__.__new__(obj.__class__)
                if hasattr(obj, '__dict__'):
                    new_obj.__dict__.update(obj.__dict__)
                if hasattr(obj, '__slots__'):
                    for slot in obj.__slots__:
                        if hasattr(obj, slot):
                            setattr(new_obj, slot, getattr(obj, slot))
                return new_obj
            except:
                pass
        
        return obj
    
    @staticmethod  
    def deepcopy(obj, memo=None):
        """深拷贝"""
        # 调用全局的deepcopy函数
        return _perform_deepcopy(obj, memo)
    
    Error = Error

def _perform_deepcopy(obj, memo=None):
    """执行深拷贝的内部函数"""
    if memo is None:
        memo = {}
    
    obj_id = id(obj)
    if obj_id in memo:
        return memo[obj_id]
    
    # 不可变类型直接返回
    if obj is None or isinstance(obj, (int, float, str, bool, complex, bytes, frozenset)):
        return obj
    
    # 检查对象是否有__deepcopy__方法
    if hasattr(obj, '__deepcopy__'):
        result = obj.__deepcopy__(memo)
        memo[obj_id] = result
        return result
    
    # 处理列表
    if isinstance(obj, list):
        result = []
        memo[obj_id] = result
        for item in obj:
            result.append(_perform_deepcopy(item, memo))
        return result
    
    # 处理元组
    elif isinstance(obj, tuple):
        needs_copy = any(not isinstance(item, (int, float, str, bool, complex, bytes, frozenset, type(None))) for item in obj)
        if not needs_copy:
            return obj
        
        temp_list = []
        memo[obj_id] = temp_list
        for item in obj:
            temp_list.append(_perform_deepcopy(item, memo))
        result = tuple(temp_list)
        memo[obj_id] = result
        return result
    
    # 处理字典
    elif isinstance(obj, dict):
        result = {}
        memo[obj_id] = result
        for key, value in obj.items():
            new_key = _perform_deepcopy(key, memo)
            new_value = _perform_deepcopy(value, memo)
            result[new_key] = new_value
        return result
    
    # 处理集合
    elif isinstance(obj, set):
        result = set()
        memo[obj_id] = result
        for item in obj:
            result.add(_perform_deepcopy(item, memo))
        return result
    
    # 处理自定义类的实例
    elif hasattr(obj, '__dict__') or hasattr(obj, '__slots__'):
        try:
            new_obj = obj.__class__.__new__(obj.__class__)
            memo[obj_id] = new_obj
            
            if hasattr(obj, '__dict__'):
                for key, value in obj.__dict__.items():
                    setattr(new_obj, key, _perform_deepcopy(value, memo))
            
            if hasattr(obj, '__slots__'):
                for slot in obj.__slots__:
                    if hasattr(obj, slot):
                        value = getattr(obj, slot)
                        setattr(new_obj, slot, _perform_deepcopy(value, memo))
            
            return new_obj
        except:
            pass
    
    # 处理函数和方法
    if callable(obj):
        return obj
    
    # 最后尝试浅拷贝
    return obj

# ============================================================================
# 示例用法和测试
# ============================================================================

def _test_tools():
    """测试工具模块的功能"""
    print("=== 测试threading.Lock ===")
    
    # 测试Lock
    lock = threading.Lock()
    print(f"初始状态 - 锁定: {lock.locked()}")
    
    # 使用acquire/release
    success = lock.acquire()
    print(f"获取锁成功: {success}, 锁定状态: {lock.locked()}")
    lock.release()
    print(f"释放锁后 - 锁定: {lock.locked()}")
    
    # 使用上下文管理器
    with lock:
        print(f"上下文管理器内 - 锁定: {lock.locked()}")
    print(f"上下文管理器外 - 锁定: {lock.locked()}")
    
    print("\n=== 测试functools.wraps ===")
    
    def original_function():
        """这是原始函数的文档"""
        return "original"
    
    @functools.wraps(original_function)
    def wrapper_function():
        """这是包装器函数的文档"""
        return "wrapped: " + original_function()
    
    print(f"包装器函数名: {wrapper_function.__name__}")
    print(f"包装器函数文档: {wrapper_function.__doc__}")
    print(f"包装器函数调用: {wrapper_function()}")
    print(f"原始函数引用: {wrapper_function.__wrapped__}")
    
    print("\n=== 测试enum.Enum ===")
    
    # 定义枚举类
    class GradMode(Enum):
        TRAINING = auto()
        INFERENCE = auto()
    
    print(f"TRAINING: {GradMode.TRAINING}")
    print(f"INFERENCE: {GradMode.INFERENCE}")
    print(f"TRAINING.name: {GradMode.TRAINING.name}")
    print(f"TRAINING.value: {GradMode.TRAINING.value}")
    print(f"INFERENCE.name: {GradMode.INFERENCE.name}")
    print(f"INFERENCE.value: {GradMode.INFERENCE.value}")
    
    # 测试比较
    print(f"TRAINING == TRAINING: {GradMode.TRAINING == GradMode.TRAINING}")
    print(f"TRAINING == INFERENCE: {GradMode.TRAINING == GradMode.INFERENCE}")
    
    # 测试迭代
    print("所有枚举成员:")
    for mode in GradMode:
        print(f"  {mode}")

if __name__ == "__main__":
    # 运行测试
    _test_tools() 