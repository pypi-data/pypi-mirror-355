"""
自主类型提示库 typing1.py
包含所有常用类型提示功能，不依赖任何外部库
提供与Python标准typing模块相同的接口
"""

# 基础类型提示类
class _GenericAlias:
    """泛型别名基类"""
    def __init__(self, origin, args):
        self._origin = origin
        self._args = args if isinstance(args, tuple) else (args,)
    
    def __repr__(self):
        if self._origin is Union:
            if len(self._args) == 2 and type(None) in self._args:
                # Optional[T] 的情况
                non_none_arg = next(arg for arg in self._args if arg is not type(None))
                return f"Optional[{non_none_arg.__name__ if hasattr(non_none_arg, '__name__') else repr(non_none_arg)}]"
            else:
                args_str = ', '.join(arg.__name__ if hasattr(arg, '__name__') else repr(arg) for arg in self._args)
                return f"Union[{args_str}]"
        elif self._origin is tuple:
            if not self._args:
                return "Tuple[()]"
            args_str = ', '.join(arg.__name__ if hasattr(arg, '__name__') else repr(arg) for arg in self._args)
            return f"Tuple[{args_str}]"
        else:
            origin_name = self._origin.__name__ if hasattr(self._origin, '__name__') else repr(self._origin)
            args_str = ', '.join(arg.__name__ if hasattr(arg, '__name__') else repr(arg) for arg in self._args)
            return f"{origin_name}[{args_str}]"
    
    def __str__(self):
        return self.__repr__()
    
    def __eq__(self, other):
        if not isinstance(other, _GenericAlias):
            return False
        return self._origin == other._origin and self._args == other._args
    
    def __hash__(self):
        return hash((self._origin, self._args))
    
    def __getitem__(self, item):
        # 支持嵌套类型提示
        if isinstance(item, tuple):
            return _GenericAlias(self._origin, self._args + item)
        else:
            return _GenericAlias(self._origin, self._args + (item,))

class _UnionType:
    """Union类型的实现"""
    def __getitem__(self, args):
        if not isinstance(args, tuple):
            args = (args,)
        return _GenericAlias(Union, args)
    
    def __repr__(self):
        return "Union"
    
    def __str__(self):
        return "Union"

class _TupleType:
    """Tuple类型的实现"""
    def __getitem__(self, args):
        if not isinstance(args, tuple):
            args = (args,)
        return _GenericAlias(tuple, args)
    
    def __repr__(self):
        return "Tuple"
    
    def __str__(self):
        return "Tuple"

class _ListType:
    """List类型的实现"""
    def __getitem__(self, arg):
        return _GenericAlias(list, (arg,))
    
    def __repr__(self):
        return "List"
    
    def __str__(self):
        return "List"

class _DictType:
    """Dict类型的实现"""
    def __getitem__(self, args):
        if not isinstance(args, tuple) or len(args) != 2:
            raise TypeError("Dict requires exactly 2 type arguments")
        return _GenericAlias(dict, args)
    
    def __repr__(self):
        return "Dict"
    
    def __str__(self):
        return "Dict"

class _SetType:
    """Set类型的实现"""
    def __getitem__(self, arg):
        return _GenericAlias(set, (arg,))
    
    def __repr__(self):
        return "Set"
    
    def __str__(self):
        return "Set"

class _CallableType:
    """Callable类型的实现"""
    def __getitem__(self, args):
        if not isinstance(args, tuple):
            args = (args,)
        return _GenericAlias(Callable, args)
    
    def __repr__(self):
        return "Callable"
    
    def __str__(self):
        return "Callable"

class _IterableType:
    """Iterable类型的实现"""
    def __getitem__(self, arg):
        return _GenericAlias(Iterable, (arg,))
    
    def __repr__(self):
        return "Iterable"
    
    def __str__(self):
        return "Iterable"

class _IteratorType:
    """Iterator类型的实现"""
    def __getitem__(self, arg):
        return _GenericAlias(Iterator, (arg,))
    
    def __repr__(self):
        return "Iterator"
    
    def __str__(self):
        return "Iterator"

class _GeneratorType:
    """Generator类型的实现"""
    def __getitem__(self, args):
        if not isinstance(args, tuple):
            args = (args,)
        return _GenericAlias(Generator, args)
    
    def __repr__(self):
        return "Generator"
    
    def __str__(self):
        return "Generator"

class _AnyType:
    """Any类型的实现 - 表示任意类型"""
    def __repr__(self):
        return "Any"
    
    def __str__(self):
        return "Any"
    
    def __eq__(self, other):
        return True  # Any 等于任何类型
    
    def __hash__(self):
        return hash("Any")

class _NoReturnType:
    """NoReturn类型的实现 - 表示函数不返回"""
    def __repr__(self):
        return "NoReturn"
    
    def __str__(self):
        return "NoReturn"

class _OptionalType:
    """Optional类型的实现 - 支持下标操作"""
    def __getitem__(self, arg):
        """Optional[T] 等价于 Union[T, None]"""
        return _GenericAlias(Union, (arg, type(None)))
    
    def __repr__(self):
        return "Optional"
    
    def __str__(self):
        return "Optional"

class _TypeVarType:
    """TypeVar类型的实现"""
    def __init__(self, name, *constraints, bound=None, covariant=False, contravariant=False):
        self.name = name
        self.constraints = constraints
        self.bound = bound
        self.covariant = covariant
        self.contravariant = contravariant
    
    def __repr__(self):
        return f"TypeVar('{self.name}')"
    
    def __str__(self):
        return self.name

# 创建类型实例
Union = _UnionType()
Tuple = _TupleType()
List = _ListType()
Dict = _DictType()
Set = _SetType()
Callable = _CallableType()
Iterable = _IterableType()
Iterator = _IteratorType()
Generator = _GeneratorType()
Any = _AnyType()
NoReturn = _NoReturnType()
Optional = _OptionalType()  # 现在Optional支持下标操作

# TypeVar的实现
def TypeVar(name, *constraints, bound=None, covariant=False, contravariant=False):
    """创建类型变量"""
    return _TypeVarType(name, *constraints, bound=bound, covariant=covariant, contravariant=contravariant)

# 类型检查函数
def get_origin(tp):
    """获取泛型类型的原始类型"""
    if isinstance(tp, _GenericAlias):
        return tp._origin
    return None

def get_args(tp):
    """获取泛型类型的参数"""
    if isinstance(tp, _GenericAlias):
        return tp._args
    return ()

def get_type_hints(obj, globalns=None, localns=None):
    """获取对象的类型提示（简化实现）"""
    if hasattr(obj, '__annotations__'):
        return obj.__annotations__.copy()
    return {}

# 运行时类型检查
def isinstance_check(obj, tp):
    """检查对象是否符合类型提示"""
    if tp is Any:
        return True
    
    if isinstance(tp, _GenericAlias):
        origin = tp._origin
        args = tp._args
        
        if origin is Union:
            # Union类型检查
            return any(isinstance_check(obj, arg) for arg in args)
        elif origin is tuple:
            # Tuple类型检查
            if not isinstance(obj, tuple):
                return False
            if len(args) == 0:
                return len(obj) == 0
            if len(args) != len(obj):
                return False
            return all(isinstance_check(obj[i], args[i]) for i in range(len(obj)))
        elif origin is list:
            # List类型检查
            if not isinstance(obj, list):
                return False
            if len(args) == 1:
                return all(isinstance_check(item, args[0]) for item in obj)
        elif origin is dict:
            # Dict类型检查
            if not isinstance(obj, dict):
                return False
            if len(args) == 2:
                key_type, value_type = args
                return all(isinstance_check(k, key_type) and isinstance_check(v, value_type) 
                          for k, v in obj.items())
        elif origin is set:
            # Set类型检查
            if not isinstance(obj, set):
                return False
            if len(args) == 1:
                return all(isinstance_check(item, args[0]) for item in obj)
        else:
            # 其他泛型类型
            return isinstance(obj, origin)
    else:
        # 基础类型检查
        return isinstance(obj, tp)

# 装饰器支持
def overload(func):
    """函数重载装饰器（简化实现）"""
    if not hasattr(func, '_overloads'):
        func._overloads = []
    func._overloads.append(func)
    return func

def final(func_or_class):
    """Final装饰器，标记不可继承/重写"""
    func_or_class._final = True
    return func_or_class

# 字面量类型
class _LiteralType:
    """Literal类型的实现"""
    def __getitem__(self, values):
        if not isinstance(values, tuple):
            values = (values,)
        return _GenericAlias(Literal, values)
    
    def __repr__(self):
        return "Literal"

Literal = _LiteralType()

# 类型别名支持
class _NewType:
    """NewType的实现"""
    def __init__(self, name, tp):
        self.name = name
        self.supertype = tp
    
    def __repr__(self):
        return f"NewType('{self.name}', {self.supertype})"
    
    def __call__(self, arg):
        return arg  # 运行时直接返回原值

def NewType(name, tp):
    """创建新的类型别名"""
    return _NewType(name, tp)

# 协议支持（简化版）
class Protocol:
    """协议基类"""
    pass

# 类型守卫
def cast(tp, obj):
    """类型转换（运行时直接返回原对象）"""
    return obj

# 前向引用
class ForwardRef:
    """前向引用实现"""
    def __init__(self, arg):
        self.arg = arg
    
    def __repr__(self):
        return f"ForwardRef('{self.arg}')"

# 常用类型别名
Text = str  # Python 2/3 兼容
AnyStr = TypeVar('AnyStr', str, bytes)

# IO类型（简化）
class _IOType:
    def __getitem__(self, arg):
        return _GenericAlias(IO, (arg,))
    
    def __repr__(self):
        return "IO"

IO = _IOType()
TextIO = IO[str]
BinaryIO = IO[bytes]

# 上下文管理器类型
class _ContextManagerType:
    def __getitem__(self, arg):
        return _GenericAlias(ContextManager, (arg,))
    
    def __repr__(self):
        return "ContextManager"

ContextManager = _ContextManagerType()

# 导出所有公共接口
__all__ = [
    # 基础类型
    'Union', 'Optional', 'Tuple', 'List', 'Dict', 'Set',
    'Callable', 'Iterable', 'Iterator', 'Generator',
    'Any', 'NoReturn', 'TypeVar', 'Literal', 'Protocol',
    
    # 工具函数
    'get_origin', 'get_args', 'get_type_hints', 'cast',
    'isinstance_check', 'overload', 'final', 'NewType',
    
    # 类型别名
    'Text', 'AnyStr', 'IO', 'TextIO', 'BinaryIO',
    'ContextManager', 'ForwardRef',
    
    # 内部类（通常不直接使用）
    '_GenericAlias',
] 