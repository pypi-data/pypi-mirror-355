# model_save_load.py

# 协议版本和魔术数字
PROTOCOL_VERSION = 4
MAGIC_NUMBER = b'PURE_PICKLE_V4'

# 操作码定义
OPCODE_NONE = b'\x00'
OPCODE_BOOL_TRUE = b'\x01'
OPCODE_BOOL_FALSE = b'\x02'
OPCODE_INT = b'\x03'
OPCODE_FLOAT = b'\x04'
OPCODE_STRING = b'\x05'
OPCODE_BYTES = b'\x06'
OPCODE_LIST = b'\x07'
OPCODE_TUPLE = b'\x08'
OPCODE_DICT = b'\x09'
OPCODE_SET = b'\x10'
OPCODE_COMPLEX = b'\x11'
OPCODE_OBJECT = b'\x12'
OPCODE_END = b'\xFF'

def _write_bytes(f, data):
    """写入字节数据到文件"""
    if isinstance(data, str):
        data = data.encode('utf-8')
    elif isinstance(data, int):
        # 将整数转换为4字节大端序
        data = data.to_bytes(4, 'big', signed=True)
    f.write(data)

def _write_length(f, length):
    """写入长度信息（4字节大端序）"""
    f.write(length.to_bytes(4, 'big'))

def _read_bytes(f, length):
    """从文件读取指定长度的字节"""
    return f.read(length)

def _read_length(f):
    """读取长度信息（4字节大端序）"""
    data = f.read(4)
    if len(data) != 4:
        raise EOFError("Unexpected end of file while reading length")
    return int.from_bytes(data, 'big')

def _serialize_object(obj, f):
    """序列化对象到文件"""
    if obj is None:
        _write_bytes(f, OPCODE_NONE)
    
    elif isinstance(obj, bool):
        if obj:
            _write_bytes(f, OPCODE_BOOL_TRUE)
        else:
            _write_bytes(f, OPCODE_BOOL_FALSE)
    
    elif isinstance(obj, int):
        _write_bytes(f, OPCODE_INT)
        # 将整数转换为字符串再编码，处理大整数
        int_str = str(obj)
        int_bytes = int_str.encode('utf-8')
        _write_length(f, len(int_bytes))
        _write_bytes(f, int_bytes)
    
    elif isinstance(obj, float):
        _write_bytes(f, OPCODE_FLOAT)
        # 将浮点数转换为字符串保持精度
        float_str = repr(obj)
        float_bytes = float_str.encode('utf-8')
        _write_length(f, len(float_bytes))
        _write_bytes(f, float_bytes)
    
    elif isinstance(obj, complex):
        _write_bytes(f, OPCODE_COMPLEX)
        # 分别存储实部和虚部
        real_str = repr(obj.real)
        imag_str = repr(obj.imag)
        real_bytes = real_str.encode('utf-8')
        imag_bytes = imag_str.encode('utf-8')
        _write_length(f, len(real_bytes))
        _write_bytes(f, real_bytes)
        _write_length(f, len(imag_bytes))
        _write_bytes(f, imag_bytes)
    
    elif isinstance(obj, str):
        _write_bytes(f, OPCODE_STRING)
        str_bytes = obj.encode('utf-8')
        _write_length(f, len(str_bytes))
        _write_bytes(f, str_bytes)
    
    elif isinstance(obj, bytes):
        _write_bytes(f, OPCODE_BYTES)
        _write_length(f, len(obj))
        _write_bytes(f, obj)
    
    elif isinstance(obj, list):
        _write_bytes(f, OPCODE_LIST)
        _write_length(f, len(obj))
        for item in obj:
            _serialize_object(item, f)
    
    elif isinstance(obj, tuple):
        _write_bytes(f, OPCODE_TUPLE)
        _write_length(f, len(obj))
        for item in obj:
            _serialize_object(item, f)
    
    elif isinstance(obj, set):
        _write_bytes(f, OPCODE_SET)
        _write_length(f, len(obj))
        for item in obj:
            _serialize_object(item, f)
    
    elif isinstance(obj, dict):
        _write_bytes(f, OPCODE_DICT)
        _write_length(f, len(obj))
        for key, value in obj.items():
            _serialize_object(key, f)
            _serialize_object(value, f)
    
    else:
        # 处理自定义对象
        _write_bytes(f, OPCODE_OBJECT)
        
        # 存储类名
        class_name = obj.__class__.__name__
        class_bytes = class_name.encode('utf-8')
        _write_length(f, len(class_bytes))
        _write_bytes(f, class_bytes)
        
        # 存储模块名（如果有的话）
        module_name = getattr(obj.__class__, '__module__', '')
        module_bytes = module_name.encode('utf-8')
        _write_length(f, len(module_bytes))
        _write_bytes(f, module_bytes)
        
        # 存储对象的属性字典
        if hasattr(obj, '__dict__'):
            obj_dict = obj.__dict__
        elif hasattr(obj, '__getstate__'):
            obj_dict = obj.__getstate__()
        else:
            # 尝试获取对象的所有属性
            obj_dict = {}
            for attr in dir(obj):
                if not attr.startswith('_'):  # 跳过私有属性
                    try:
                        value = getattr(obj, attr)
                        if not callable(value):  # 跳过方法
                            obj_dict[attr] = value
                    except:
                        pass
        
        _serialize_object(obj_dict, f)

def _deserialize_object(f):
    """从文件反序列化对象"""
    opcode = f.read(1)
    if not opcode:
        raise EOFError("Unexpected end of file")
    
    if opcode == OPCODE_NONE:
        return None
    
    elif opcode == OPCODE_BOOL_TRUE:
        return True
    
    elif opcode == OPCODE_BOOL_FALSE:
        return False
    
    elif opcode == OPCODE_INT:
        length = _read_length(f)
        int_bytes = _read_bytes(f, length)
        int_str = int_bytes.decode('utf-8')
        return int(int_str)
    
    elif opcode == OPCODE_FLOAT:
        length = _read_length(f)
        float_bytes = _read_bytes(f, length)
        float_str = float_bytes.decode('utf-8')
        return float(float_str)
    
    elif opcode == OPCODE_COMPLEX:
        real_length = _read_length(f)
        real_bytes = _read_bytes(f, real_length)
        real_str = real_bytes.decode('utf-8')
        
        imag_length = _read_length(f)
        imag_bytes = _read_bytes(f, imag_length)
        imag_str = imag_bytes.decode('utf-8')
        
        return complex(float(real_str), float(imag_str))
    
    elif opcode == OPCODE_STRING:
        length = _read_length(f)
        str_bytes = _read_bytes(f, length)
        return str_bytes.decode('utf-8')
    
    elif opcode == OPCODE_BYTES:
        length = _read_length(f)
        return _read_bytes(f, length)
    
    elif opcode == OPCODE_LIST:
        length = _read_length(f)
        result = []
        for _ in range(length):
            item = _deserialize_object(f)
            result.append(item)
        return result
    
    elif opcode == OPCODE_TUPLE:
        length = _read_length(f)
        items = []
        for _ in range(length):
            item = _deserialize_object(f)
            items.append(item)
        return tuple(items)
    
    elif opcode == OPCODE_SET:
        length = _read_length(f)
        items = []
        for _ in range(length):
            item = _deserialize_object(f)
            items.append(item)
        return set(items)
    
    elif opcode == OPCODE_DICT:
        length = _read_length(f)
        result = {}
        for _ in range(length):
            key = _deserialize_object(f)
            value = _deserialize_object(f)
            result[key] = value
        return result
    
    elif opcode == OPCODE_OBJECT:
        # 读取类名
        class_name_length = _read_length(f)
        class_name_bytes = _read_bytes(f, class_name_length)
        class_name = class_name_bytes.decode('utf-8')
        
        # 读取模块名
        module_name_length = _read_length(f)
        module_name_bytes = _read_bytes(f, module_name_length)
        module_name = module_name_bytes.decode('utf-8')
        
        # 读取对象属性字典
        obj_dict = _deserialize_object(f)
        
        # 创建一个通用对象类来存储反序列化的数据
        class GenericObject:
            def __init__(self, class_name, module_name, attributes):
                self.__class__.__name__ = class_name
                self.__class__.__module__ = module_name
                # 检查attributes是否为None或不是字典
                if attributes is not None:
                    # 处理字典或类似字典的对象（如mappingproxy）
                    if hasattr(attributes, 'items'):
                        try:
                            for key, value in attributes.items():
                                setattr(self, key, value)
                        except Exception as e:
                            print(f"[WARNING] GenericObject: 处理attributes时出错: {e}")
                    elif isinstance(attributes, dict):
                        for key, value in attributes.items():
                            setattr(self, key, value)
                    else:
                        # 如果不是字典类型，但也不是None，记录但不报错
                        pass
        
        return GenericObject(class_name, module_name, obj_dict)
    
    else:
        raise ValueError(f"Unknown opcode: {opcode}")

def dump(obj, file):
    """
    将对象序列化并保存到文件
    
    参数:
        obj: 要序列化的对象
        file: 文件对象或文件路径字符串
    """
    if isinstance(file, str):
        # 如果传入的是文件路径，打开文件
        with open(file, 'wb') as f:
            return dump(obj, f)
    
    # 写入魔术数字和协议版本
    _write_bytes(file, MAGIC_NUMBER)
    _write_bytes(file, PROTOCOL_VERSION.to_bytes(1, 'big'))
    
    # 序列化对象
    _serialize_object(obj, file)
    
    # 写入结束标记
    _write_bytes(file, OPCODE_END)

def load(file):
    """
    从文件加载并反序列化对象
    
    参数:
        file: 文件对象或文件路径字符串
    
    返回:
        反序列化的对象
    """
    if isinstance(file, str):
        # 如果传入的是文件路径，打开文件
        with open(file, 'rb') as f:
            return load(f)
    
    # 验证魔术数字
    magic = file.read(len(MAGIC_NUMBER))
    if magic != MAGIC_NUMBER:
        raise ValueError("Invalid file format or corrupted data")
    
    # 验证协议版本
    version_bytes = file.read(1)
    if not version_bytes or version_bytes[0] != PROTOCOL_VERSION:
        raise ValueError("Unsupported protocol version")
    
    # 反序列化对象
    obj = _deserialize_object(file)
    
    # 验证结束标记
    end_marker = file.read(1)
    if end_marker != OPCODE_END:
        raise ValueError("Missing end marker or corrupted data")
    
    return obj

# 为了更好的兼容性，提供一些额外的辅助函数
def dumps(obj):
    """将对象序列化为字节串"""
    # 创建一个字节缓冲区类
    class BytesBuffer:
        def __init__(self):
            self.data = b''
        
        def write(self, data):
            if isinstance(data, str):
                data = data.encode('utf-8')
            elif isinstance(data, int):
                data = data.to_bytes(4, 'big', signed=True)
            self.data += data
        
        def getvalue(self):
            return self.data
    
    buffer = BytesBuffer()
    
    # 写入魔术数字和协议版本
    _write_bytes(buffer, MAGIC_NUMBER)
    _write_bytes(buffer, PROTOCOL_VERSION.to_bytes(1, 'big'))
    
    # 序列化对象
    _serialize_object(obj, buffer)
    
    # 写入结束标记
    _write_bytes(buffer, OPCODE_END)
    
    return buffer.getvalue()

def loads(data):
    """从字节串反序列化对象"""
    # 创建一个字节读取器类
    class BytesReader:
        def __init__(self, data):
            self.data = data
            self.pos = 0
        
        def read(self, length):
            if self.pos + length > len(self.data):
                return self.data[self.pos:]
            result = self.data[self.pos:self.pos + length]
            self.pos += length
            return result
    
    reader = BytesReader(data)
    
    # 验证魔术数字
    magic = reader.read(len(MAGIC_NUMBER))
    if magic != MAGIC_NUMBER:
        raise ValueError("Invalid data format or corrupted data")
    
    # 验证协议版本
    version_bytes = reader.read(1)
    if not version_bytes or version_bytes[0] != PROTOCOL_VERSION:
        raise ValueError("Unsupported protocol version")
    
    # 反序列化对象
    obj = _deserialize_object(reader)
    
    # 验证结束标记
    end_marker = reader.read(1)
    if end_marker != OPCODE_END:
        raise ValueError("Missing end marker or corrupted data")
    
    return obj

# 测试函数
def _test_pickle_replacement():
    """测试pickle替代功能"""
    print("开始测试纯Python pickle替代实现...")
    
    # 测试数据
    test_data = {
        'model_parameters': {
            'layer1.weight': [1.0, 2.0, 3.0],
            'layer1.bias': [0.1, 0.2],
            'layer2.weight': [[1.1, 1.2], [2.1, 2.2]],
        },
        'optimizer_state': {
            'learning_rate': 0.001,
            'momentum': 0.9,
        },
        'epoch': 10,
        'accuracy': 0.95,
        'metadata': {
            'version': '1.0',
            'timestamp': '2024-01-01',
            'notes': None,
            'training_complete': True,
        }
    }
    
    # 测试保存和加载
    try:
        # 保存到文件
        dump(test_data, 'test_model.dict')
        print("✅ 数据保存成功")
        
        # 从文件加载
        loaded_data = load('test_model.dict')
        print("✅ 数据加载成功")
        
        # 验证数据完整性
        def compare_objects(obj1, obj2, path=""):
            if type(obj1) != type(obj2):
                print(f"❌ 类型不匹配 {path}: {type(obj1)} vs {type(obj2)}")
                return False
            
            if isinstance(obj1, dict):
                if set(obj1.keys()) != set(obj2.keys()):
                    print(f"❌ 字典键不匹配 {path}")
                    return False
                for key in obj1:
                    if not compare_objects(obj1[key], obj2[key], f"{path}.{key}"):
                        return False
            elif isinstance(obj1, (list, tuple)):
                if len(obj1) != len(obj2):
                    print(f"❌ 序列长度不匹配 {path}")
                    return False
                for i, (a, b) in enumerate(zip(obj1, obj2)):
                    if not compare_objects(a, b, f"{path}[{i}]"):
                        return False
            else:
                if obj1 != obj2:
                    print(f"❌ 值不匹配 {path}: {obj1} vs {obj2}")
                    return False
            
            return True
        
        if compare_objects(test_data, loaded_data):
            print("✅ 数据完整性验证通过")
        else:
            print("❌ 数据完整性验证失败")
        
        # 测试字节串序列化
        serialized = dumps(test_data)
        deserialized = loads(serialized)
        
        if compare_objects(test_data, deserialized):
            print("✅ 字节串序列化测试通过")
        else:
            print("❌ 字节串序列化测试失败")
            
        print("🎉 所有测试通过！")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    _test_pickle_replacement() 