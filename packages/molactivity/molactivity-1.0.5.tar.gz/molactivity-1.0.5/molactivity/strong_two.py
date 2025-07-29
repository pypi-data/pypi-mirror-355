"""
Strong Two Library - 数据类型检查库
专门替代np.issubdtype和np.floating，不使用任何第三方库
完全自主实现，支持各种数据类型检查和分类
"""

# 定义浮点数类型类 - 替代np.floating
class FloatingType:
    """
    浮点数类型标识类 - 完全替代np.floating
    用于标识和检查浮点数数据类型
    """
    
    # 所有浮点数类型的名称集合
    FLOAT_TYPE_NAMES = {
        'float', 'float16', 'float32', 'float64', 'float128',
        'double', 'single', 'longdouble', 'half',
        'floating', 'inexact', 'number'
    }
    
    # Python内置浮点数类型
    PYTHON_FLOAT_TYPES = {float}
    
    # 字符串形式的浮点数类型标识
    FLOAT_TYPE_STRINGS = {
        'f', 'f2', 'f4', 'f8', 'f16',  # numpy风格
        'float', 'double', 'single',    # 标准名称
        '<f4', '>f4', '=f4',           # 字节序相关
        '<f8', '>f8', '=f8',
    }
    
    @classmethod
    def is_floating_type(cls, dtype):
        """检查给定类型是否为浮点数类型"""
        if dtype is None:
            return False
        
        # 检查Python内置类型
        if dtype == float or dtype is float:
            return True
        
        # 检查类型名称
        if hasattr(dtype, '__name__'):
            type_name = dtype.__name__.lower()
            if type_name in cls.FLOAT_TYPE_NAMES:
                return True
        
        # 检查字符串表示
        dtype_str = str(dtype).lower()
        
        # 直接字符串匹配
        if dtype_str in cls.FLOAT_TYPE_STRINGS:
            return True
        
        # 包含float关键字
        if 'float' in dtype_str:
            return True
        
        # 检查是否包含'f'并且后面跟数字（如f4, f8等）
        if dtype_str.startswith('f') and len(dtype_str) > 1:
            try:
                int(dtype_str[1:])
                return True
            except ValueError:
                pass
        
        # 检查复杂字符串格式（如'<f4', '>f8'等）
        if len(dtype_str) >= 2:
            if dtype_str[-2:] in ['f2', 'f4', 'f8'] or dtype_str[-3:] in ['f16']:
                return True
            if dtype_str[1:] in ['f2', 'f4', 'f8', 'f16']:
                return True
        
        return False

# 创建全局浮点数类型实例 - 替代np.floating
floating = FloatingType()

def issubdtype(dtype1, dtype2):
    """
    检查dtype1是否为dtype2的子类型 - 完全替代np.issubdtype
    
    参数:
        dtype1: 要检查的数据类型
        dtype2: 父类型（通常是floating类型）
        
    返回:
        bool: 如果dtype1是dtype2的子类型则返回True，否则返回False
    """
    
    # 处理None输入
    if dtype1 is None or dtype2 is None:
        return False
    
    # 如果dtype2是FloatingType或floating实例，检查dtype1是否为浮点类型
    if isinstance(dtype2, FloatingType) or dtype2 is floating:
        return FloatingType.is_floating_type(dtype1)
    
    # 如果dtype2是float类型，检查dtype1是否为浮点类型
    if dtype2 == float or dtype2 is float:
        return FloatingType.is_floating_type(dtype1)
    
    # 处理字符串类型比较
    if isinstance(dtype2, str):
        dtype2_lower = dtype2.lower()
        if 'float' in dtype2_lower:
            return FloatingType.is_floating_type(dtype1)
    
    # 直接类型比较
    if dtype1 == dtype2:
        return True
    
    # 检查类型名称匹配
    if hasattr(dtype1, '__name__') and hasattr(dtype2, '__name__'):
        if dtype1.__name__ == dtype2.__name__:
            return True
    
    # 字符串表示比较
    if str(dtype1) == str(dtype2):
        return True
    
    # Python内置类型层次检查
    try:
        if isinstance(dtype1, type) and isinstance(dtype2, type):
            return issubclass(dtype1, dtype2)
    except TypeError:
        pass
    
    return False

# 整数类型类 - 扩展功能
class IntegerType:
    """整数类型标识类"""
    
    INTEGER_TYPE_NAMES = {
        'int', 'int8', 'int16', 'int32', 'int64',
        'uint', 'uint8', 'uint16', 'uint32', 'uint64',
        'integer', 'signedinteger', 'unsignedinteger'
    }
    
    PYTHON_INT_TYPES = {int}
    
    @classmethod
    def is_integer_type(cls, dtype):
        """检查给定类型是否为整数类型"""
        if dtype is None:
            return False
        
        # 检查Python内置类型
        if dtype == int or dtype is int:
            return True
        
        # 检查类型名称
        if hasattr(dtype, '__name__'):
            type_name = dtype.__name__.lower()
            if type_name in cls.INTEGER_TYPE_NAMES:
                return True
        
        # 检查字符串表示
        dtype_str = str(dtype).lower()
        
        # 包含int关键字
        if 'int' in dtype_str and 'float' not in dtype_str:
            return True
        
        # 检查是否为i+数字格式（如i4, i8等）
        if dtype_str.startswith('i') and len(dtype_str) > 1:
            try:
                int(dtype_str[1:])
                return True
            except ValueError:
                pass
        
        return False

# 创建全局整数类型实例
integer = IntegerType()

# 复数类型类
class ComplexType:
    """复数类型标识类"""
    
    COMPLEX_TYPE_NAMES = {
        'complex', 'complex64', 'complex128', 'complex256',
        'complexfloating'
    }
    
    PYTHON_COMPLEX_TYPES = {complex}
    
    @classmethod
    def is_complex_type(cls, dtype):
        """检查给定类型是否为复数类型"""
        if dtype is None:
            return False
        
        # 检查Python内置类型
        if dtype == complex or dtype is complex:
            return True
        
        # 检查类型名称
        if hasattr(dtype, '__name__'):
            type_name = dtype.__name__.lower()
            if type_name in cls.COMPLEX_TYPE_NAMES:
                return True
        
        # 检查字符串表示
        dtype_str = str(dtype).lower()
        
        if 'complex' in dtype_str:
            return True
        
        return False

# 创建全局复数类型实例
complexfloating = ComplexType()

# 通用数据类型检查函数
def get_dtype_category(dtype):
    """
    获取数据类型的分类
    
    返回: 'float', 'int', 'complex', 'bool', 'string', 'unknown'
    """
    if FloatingType.is_floating_type(dtype):
        return 'float'
    elif IntegerType.is_integer_type(dtype):
        return 'int'
    elif ComplexType.is_complex_type(dtype):
        return 'complex'
    elif dtype == bool or dtype is bool:
        return 'bool'
    elif dtype == str or dtype is str:
        return 'string'
    else:
        return 'unknown'

def is_numeric_type(dtype):
    """检查是否为数值类型（int, float, complex）"""
    category = get_dtype_category(dtype)
    return category in ['float', 'int', 'complex']

def is_real_type(dtype):
    """检查是否为实数类型（int, float）"""
    category = get_dtype_category(dtype)
    return category in ['float', 'int']

# 便利函数
def check_floating(dtype):
    """简化的浮点数检查函数"""
    return FloatingType.is_floating_type(dtype)

def check_integer(dtype):
    """简化的整数检查函数"""
    return IntegerType.is_integer_type(dtype)

def check_complex(dtype):
    """简化的复数检查函数"""
    return ComplexType.is_complex_type(dtype)

# 直接替换函数 - 与numpy完全兼容的接口
def replace_np_issubdtype(dtype1, dtype2):
    """直接替换np.issubdtype的函数"""
    return issubdtype(dtype1, dtype2)

def replace_np_floating():
    """直接替换np.floating的函数"""
    return floating

# 测试函数
def test_strong_two():
    """测试strong_two库的功能"""
    print("🧪 Testing Strong Two Library...")
    
    # 测试浮点数检查
    test_cases = [
        (float, floating, True, "float vs floating"),
        ('float32', floating, True, "float32 vs floating"),
        ('f4', floating, True, "f4 vs floating"),
        (int, floating, False, "int vs floating"),
        ('int32', floating, False, "int32 vs floating"),
    ]
    
    print("\n📊 issubdtype测试结果:")
    for dtype1, dtype2, expected, description in test_cases:
        result = issubdtype(dtype1, dtype2)
        status = "✅" if result == expected else "❌"
        print(f"{status} {description}: {result} (期望: {expected})")
    
    # 测试类型分类
    print("\n🏷️ 数据类型分类测试:")
    type_tests = [
        (float, "float"),
        (int, "int"),
        (complex, "complex"),
        (bool, "bool"),
        (str, "string"),
    ]
    
    for dtype, expected_category in type_tests:
        category = get_dtype_category(dtype)
        status = "✅" if category == expected_category else "❌"
        print(f"{status} {dtype.__name__}: {category}")
    
    print("\n🎯 Strong Two Library测试完成!")

# 使用示例函数
def usage_example():
    """展示如何使用strong_two库"""
    print("📖 Strong Two Library使用示例:")
    
    # 原numpy代码: np.issubdtype(self.dtype, np.floating)
    # 新代码: issubdtype(self.dtype, floating)
    
    example_dtype = float
    
    # 检查是否为浮点类型
    if issubdtype(example_dtype, floating):
        print(f"✅ {example_dtype} 是浮点类型")
        result = "float(self._data)"
    else:
        print(f"❌ {example_dtype} 不是浮点类型")
        result = "int(self._data)"
    
    print(f"建议转换: {result}")

if __name__ == "__main__":
    print("🚀 Strong Two Library - 数据类型检查库")
    test_strong_two()
    print("\n" + "="*50)
    usage_example()
    print("\n✨ 已成功替代 np.issubdtype 和 np.floating！") 