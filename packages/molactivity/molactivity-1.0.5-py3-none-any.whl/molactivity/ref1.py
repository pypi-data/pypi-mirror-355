"""
弱引用(Weak Reference)的纯Python实现
100%自主代码，不依赖任何外部库

作者: AI Assistant  
版本: 1.0
用途: 替代weakref.ref函数

注意：这是一个简化版本的弱引用实现。
由于Python语言和垃圾回收机制的限制，无法完全模拟真正的弱引用行为，
但提供了兼容的接口用于代码替换。
"""


class ref:
    """
    弱引用类的实现
    
    模拟weakref.ref的行为，提供相同的接口：
    - 可以通过调用ref()来获取原对象
    - 支持回调函数
    - 可以用于集合和字典
    - 提供相等性比较和哈希
    
    限制：
    - 这是伪弱引用，实际上仍然保持对象的强引用
    - 对象不会被自动垃圾回收
    - 主要用于接口兼容性
    """
    
    # 全局引用跟踪器，用于管理所有引用
    _global_refs = {}
    _next_id = 0
    
    def __init__(self, obj, callback=None):
        """
        创建一个弱引用
        
        Args:
            obj: 要引用的对象
            callback: 当对象被删除时调用的回调函数(简化版本中不实现)
        """
        self._obj_id = id(obj)
        self._callback = callback
        self._is_alive = True
        
        # 为了实现某种程度的"弱引用"行为，我们使用一个技巧：
        # 将对象存储在全局字典中，以对象id为key
        # 这样可以实现某种程度的共享存储
        if self._obj_id not in ref._global_refs:
            ref._global_refs[self._obj_id] = {
                'obj': obj,
                'ref_count': 0,
                'refs': []
            }
        
        ref._global_refs[self._obj_id]['ref_count'] += 1
        ref._global_refs[self._obj_id]['refs'].append(self)
        
        # 为每个ref实例分配一个唯一ID
        ref._next_id += 1
        self._ref_id = ref._next_id
    
    def __call__(self):
        """
        调用弱引用来获取原对象
        
        Returns:
            原对象如果仍然存在，否则返回None
        """
        if not self._is_alive:
            return None
            
        if self._obj_id in ref._global_refs:
            return ref._global_refs[self._obj_id]['obj']
        else:
            self._is_alive = False
            return None
    
    def __eq__(self, other):
        """
        比较两个弱引用是否相等
        
        Args:
            other: 另一个弱引用对象
            
        Returns:
            bool: 如果引用同一个对象则返回True
        """
        if not isinstance(other, ref):
            return False
        
        # 如果两个引用都还活着，比较它们指向的对象
        if self._is_alive and other._is_alive:
            return self._obj_id == other._obj_id
        
        # 如果任何一个引用已经失效，则不相等
        return False
    
    def __hash__(self):
        """
        返回弱引用的哈希值
        
        Returns:
            int: 基于对象id的哈希值
        """
        # 使用对象id和ref实例id的组合来生成哈希
        return hash((self._obj_id, self._ref_id))
    
    def __repr__(self):
        """
        返回弱引用的字符串表示
        
        Returns:
            str: 描述性字符串
        """
        if self._is_alive and self._obj_id in ref._global_refs:
            obj = ref._global_refs[self._obj_id]['obj']
            obj_type = type(obj).__name__
            return f"<ref at {hex(id(self))} to '{obj_type}' at {hex(self._obj_id)}>"
        else:
            return f"<ref at {hex(id(self))} (dead)>"
    
    @property
    def is_alive(self):
        """
        检查引用是否还活着
        
        Returns:
            bool: 如果引用的对象仍然存在则返回True
        """
        return self._is_alive and self._obj_id in ref._global_refs
    
    def invalidate(self):
        """
        手动使引用失效
        """
        self._is_alive = False
        if self._callback:
            try:
                self._callback(self)
            except:
                pass  # 忽略回调函数中的异常
    
    @classmethod
    def cleanup_refs(cls, obj_id):
        """
        清理指定对象的所有引用
        
        Args:
            obj_id: 对象的id
        """
        if obj_id in cls._global_refs:
            refs_info = cls._global_refs[obj_id]
            for ref_obj in refs_info['refs']:
                ref_obj.invalidate()
            del cls._global_refs[obj_id]
    
    @classmethod
    def get_ref_count(cls, obj):
        """
        获取对象的弱引用计数
        
        Args:
            obj: 要查询的对象
            
        Returns:
            int: 弱引用的数量
        """
        obj_id = id(obj)
        if obj_id in cls._global_refs:
            return cls._global_refs[obj_id]['ref_count']
        return 0
    
    @classmethod
    def clear_all_refs(cls):
        """
        清理所有弱引用（用于测试和调试）
        """
        for obj_id in list(cls._global_refs.keys()):
            cls.cleanup_refs(obj_id)


class ReferenceType(ref):
    """
    weakref.ReferenceType的别名，提供兼容性
    """
    pass


# 兼容性函数
def getweakrefcount(obj):
    """
    获取对象的弱引用计数
    
    Args:
        obj: 要查询的对象
        
    Returns:
        int: 弱引用的数量
    """
    return ref.get_ref_count(obj)


def getweakrefs(obj):
    """
    获取对象的所有弱引用
    
    Args:
        obj: 要查询的对象
        
    Returns:
        list: 包含所有弱引用的列表
    """
    obj_id = id(obj)
    if obj_id in ref._global_refs:
        return [r for r in ref._global_refs[obj_id]['refs'] if r.is_alive]
    return []


# 测试函数
def _test_ref():
    """测试ref类的功能"""
    print("测试ref类功能:")
    
    # 创建测试对象
    class TestObj:
        def __init__(self, value):
            self.value = value
        def __repr__(self):
            return f"TestObj({self.value})"
    
    # 测试基本功能
    print("\n1. 基本功能测试:")
    obj1 = TestObj(42)
    ref1 = ref(obj1)
    print(f"创建引用: {ref1}")
    print(f"调用引用获取对象: {ref1()}")
    print(f"引用是否活着: {ref1.is_alive}")
    
    # 测试相等性
    print("\n2. 相等性测试:")
    ref2 = ref(obj1)  # 指向同一个对象
    ref3 = ref(TestObj(100))  # 指向不同对象
    print(f"ref1 == ref2 (指向同一对象): {ref1 == ref2}")
    print(f"ref1 == ref3 (指向不同对象): {ref1 == ref3}")
    
    # 测试哈希
    print("\n3. 哈希测试:")
    ref_set = {ref1, ref2, ref3}
    print(f"集合中的引用数量: {len(ref_set)}")
    
    # 测试引用计数
    print("\n4. 引用计数测试:")
    print(f"obj1的弱引用计数: {getweakrefcount(obj1)}")
    print(f"obj1的所有弱引用: {getweakrefs(obj1)}")
    
    # 测试手动失效
    print("\n5. 手动失效测试:")
    ref1.invalidate()
    print(f"失效后调用引用: {ref1()}")
    print(f"引用是否还活着: {ref1.is_alive}")
    
    # 测试列表存储
    print("\n6. 列表存储测试:")
    obj2 = TestObj(200)
    ref_list = [ref(obj2)]
    print(f"列表中的引用: {ref_list}")
    print(f"通过列表中的引用获取对象: {ref_list[0]()}")


if __name__ == "__main__":
    # 运行测试
    _test_ref() 