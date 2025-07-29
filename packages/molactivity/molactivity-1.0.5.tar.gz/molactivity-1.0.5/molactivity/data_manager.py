# 纯Python数据管理模块 - 完全替代pandas
# 不使用任何外部库，仅使用Python内置功能

# 导入我们的纯Python随机数生成器
from .pure_random import shuffle, seed as set_random_seed


class DataTable:
    """
    自定义数据表类，用于替代pandas DataFrame的核心功能
    纯Python实现，不依赖任何外部库
    """
    
    def __init__(self, data=None):
        """
        初始化数据表
        
        Args:
            data: 字典形式的数据，键为列名，值为列数据列表
        """
        if data is None:
            data = {}
        self._data = data
        self._columns = list(data.keys())
        self._row_count = len(next(iter(data.values()))) if data else 0
        
        # 验证所有列的长度一致
        if data:
            for col_name, col_data in data.items():
                if len(col_data) != self._row_count:
                    raise ValueError(f"所有列必须具有相同的长度。列 '{col_name}' 长度为 {len(col_data)}，期望长度为 {self._row_count}")
    
    def __len__(self):
        """返回数据表的行数"""
        return self._row_count
    
    def __getitem__(self, key):
        """
        获取指定列的数据
        
        Args:
            key: 列名
            
        Returns:
            DataColumn: 包含列数据的对象
        """
        if key not in self._data:
            raise KeyError(f"列 '{key}' 不存在")
        return DataColumn(self._data[key], key)
    
    def __setitem__(self, key, value):
        """
        设置列数据
        
        Args:
            key: 列名
            value: 列数据列表
        """
        if len(value) != self._row_count and self._row_count > 0:
            raise ValueError(f"新列长度 {len(value)} 与现有行数 {self._row_count} 不匹配")
        
        self._data[key] = value
        if key not in self._columns:
            self._columns.append(key)
        if self._row_count == 0:
            self._row_count = len(value)
    
    @property
    def columns(self):
        """返回所有列名"""
        return self._columns[:]  # 返回副本
    
    def add_column(self, name, data):
        """
        添加新列
        
        Args:
            name: 列名
            data: 列数据
        """
        self[name] = data
    
    def get_row(self, index):
        """
        获取指定行的数据
        
        Args:
            index: 行索引
            
        Returns:
            包含该行所有列数据的字典
        """
        if index < 0 or index >= self._row_count:
            raise IndexError(f"行索引 {index} 超出范围 [0, {self._row_count})")
        
        return {col: self._data[col][index] for col in self._columns}
    
    def to_dict(self):
        """将数据表转换为字典格式"""
        return {k: v[:] for k, v in self._data.items()}  # 深拷贝
    
    def copy(self):
        """
        创建数据表的深拷贝
        
        Returns:
            DataTable: 新的数据表对象，包含相同的数据
        """
        # 深拷贝所有数据
        copied_data = {}
        for col_name, col_data in self._data.items():
            copied_data[col_name] = col_data[:]  # 创建列表的副本
        
        return DataTable(copied_data)
    
    def to_csv(self, filepath, index=False):
        """
        将数据表保存为CSV文件
        
        Args:
            filepath: 保存路径
            index: 是否包含索引（为了兼容pandas，但这里忽略）
        """
        try:
            with open(filepath, 'w', encoding='utf-8', newline='') as file:
                # 写入头部
                headers = self._columns
                file.write(','.join(headers) + '\n')
                
                # 写入数据行
                for row_idx in range(self._row_count):
                    row_values = []
                    for col_name in headers:
                        value = self._data[col_name][row_idx]
                        # 处理特殊字符，如果包含逗号或换行符，用引号包围
                        if isinstance(value, str) and (',' in value or '\n' in value or '"' in value):
                            # 转义内部的引号
                            escaped_value = value.replace('"', '""')
                            row_values.append(f'"{escaped_value}"')
                        else:
                            row_values.append(str(value))
                    
                    file.write(','.join(row_values) + '\n')
                    
        except Exception as e:
            raise Exception(f"保存CSV文件时发生错误: {str(e)}")
    
    def shuffle_rows(self, seed=None):
        """
        打乱行顺序 - 关键修复函数
        
        Args:
            seed: 随机种子，用于可重现的结果
        """
        if seed is not None:
            set_random_seed(seed)
        
        # 创建索引列表
        indices = list(range(self._row_count))
        shuffle(indices)
        
        # 重新排列所有列的数据
        for col_name in self._columns:
            original_data = self._data[col_name][:]  # 创建副本
            self._data[col_name] = [original_data[i] for i in indices]


class DataColumn:
    """
    数据列类，用于替代pandas Series的功能
    纯Python实现
    """
    
    def __init__(self, data, name=None):
        """
        初始化数据列
        
        Args:
            data: 列数据列表
            name: 列名
        """
        self._data = data
        self._name = name
    
    def __len__(self):
        """返回列的长度"""
        return len(self._data)
    
    def __getitem__(self, index):
        """获取指定索引的数据"""
        return self._data[index]
    
    def __iter__(self):
        """支持迭代"""
        return iter(self._data)
    
    @property
    def name(self):
        """返回列名"""
        return self._name
    
    def value_counts(self):
        """
        统计值的出现次数，替代pandas的value_counts功能
        纯Python实现，不使用collections.Counter
        
        Returns:
            ValueCounts对象，包含统计结果
        """
        # 手动实现计数功能
        count_dict = {}
        for value in self._data:
            if value in count_dict:
                count_dict[value] += 1
            else:
                count_dict[value] = 1
        
        return ValueCounts(count_dict)
    
    def to_list(self):
        """将列数据转换为列表"""
        return self._data[:]  # 返回副本


class ValueCounts:
    """
    值计数类，用于替代pandas Series.value_counts的返回结果
    纯Python实现
    """
    
    def __init__(self, count_dict):
        """
        初始化值计数对象
        
        Args:
            count_dict: 字典，包含值和对应的计数
        """
        self._count_dict = count_dict
        # 按照计数从高到低排序，与pandas保持一致
        sorted_items = sorted(count_dict.items(), key=lambda x: x[1], reverse=True)
        self._values = [item[0] for item in sorted_items]
        self._counts = [item[1] for item in sorted_items]
    
    def to_list(self):
        """返回计数值的列表（按照计数从高到低排序）"""
        return self._counts[:]  # 返回副本
    
    def to_dict(self):
        """返回值和计数的字典映射"""
        return self._count_dict.copy()  # 返回副本
    
    def __getitem__(self, key):
        """获取指定值的计数"""
        return self._count_dict.get(key, 0)
    
    def __len__(self):
        """返回不同值的数量"""
        return len(self._count_dict)
    
    def keys(self):
        """返回所有唯一值（按照计数从高到低排序）"""
        return self._values[:]  # 返回副本
    
    def values(self):
        """返回所有计数值（按照计数从高到低排序）"""
        return self._counts[:]  # 返回副本


class PureCSVReader:
    """
    纯Python CSV文件读取器，用于替代pandas的read_csv功能
    不使用任何外部库，完全自主实现CSV解析
    """
    
    @staticmethod
    def read_csv(filepath, encoding='utf-8', delimiter=',', shuffle=False, random_seed=42):
        """
        读取CSV文件并返回DataTable对象
        
        Args:
            filepath: CSV文件路径
            encoding: 文件编码，默认为utf-8
            delimiter: 分隔符，默认为逗号
            shuffle: 是否打乱行顺序，默认False
            random_seed: 随机种子
            
        Returns:
            DataTable对象包含CSV文件的数据
        """
        # 检查文件是否存在（不使用os.path.exists）
        try:
            with open(filepath, 'r', encoding=encoding) as test_file:
                pass
        except FileNotFoundError:
            raise FileNotFoundError(f"文件不存在: {filepath}")
        except UnicodeDecodeError:
            # 尝试其他编码
            try:
                return PureCSVReader.read_csv(filepath, encoding='gbk', delimiter=delimiter, shuffle=shuffle, random_seed=random_seed)
            except:
                try:
                    return PureCSVReader.read_csv(filepath, encoding='latin-1', delimiter=delimiter, shuffle=shuffle, random_seed=random_seed)
                except Exception as e:
                    raise Exception(f"无法读取文件 {filepath}，编码错误: {str(e)}")
        
        data = {}
        
        try:
            with open(filepath, 'r', encoding=encoding) as file:
                # 读取所有行
                lines = file.readlines()
                
                if not lines:
                    raise ValueError("CSV文件为空")
                
                # 解析头部（列名）
                header_line = lines[0].strip()
                headers = PureCSVReader._parse_csv_line(header_line, delimiter)
                
                # 清理列名（去除空白字符）
                headers = [header.strip() for header in headers]
                
                # 初始化数据字典
                for header in headers:
                    data[header] = []
                
                # 解析数据行
                for row_num, line in enumerate(lines[1:], start=2):
                    line = line.strip()
                    if not line:  # 跳过空行
                        continue
                    
                    row = PureCSVReader._parse_csv_line(line, delimiter)
                    
                    if len(row) != len(headers):
                        print(f"警告: 第{row_num}行列数({len(row)})与头部列数({len(headers)})不匹配，跳过该行")
                        continue
                    
                    for header, value in zip(headers, row):
                        # 尝试转换数据类型
                        processed_value = PureCSVReader._convert_value(value.strip())
                        data[header].append(processed_value)
                
        except Exception as e:
            raise Exception(f"读取CSV文件时发生错误: {str(e)}")
        
        # 创建DataTable
        table = DataTable(data)
        
        # 如果需要打乱顺序
        if shuffle:
            table.shuffle_rows(random_seed)
        
        return table
    
    @staticmethod
    def _parse_csv_line(line, delimiter=','):
        """
        解析CSV行，处理引号包围的字段
        纯Python实现，不使用csv库
        
        Args:
            line: CSV行字符串
            delimiter: 分隔符
            
        Returns:
            解析后的字段列表
        """
        fields = []
        current_field = ""
        in_quotes = False
        i = 0
        
        while i < len(line):
            char = line[i]
            
            if char == '"':
                if in_quotes:
                    # 检查是否是转义的引号
                    if i + 1 < len(line) and line[i + 1] == '"':
                        current_field += '"'
                        i += 1  # 跳过下一个引号
                    else:
                        in_quotes = False
                else:
                    in_quotes = True
            elif char == delimiter and not in_quotes:
                fields.append(current_field)
                current_field = ""
            else:
                current_field += char
            
            i += 1
        
        # 添加最后一个字段
        fields.append(current_field)
        
        return fields
    
    @staticmethod
    def _convert_value(value_str):
        """
        尝试将字符串值转换为适当的数据类型
        
        Args:
            value_str: 字符串值
            
        Returns:
            转换后的值
        """
        # 处理空值
        if not value_str or value_str.lower() in ['', 'na', 'nan', 'null', 'none']:
            return None
        
        # 尝试转换为整数
        try:
            if '.' not in value_str and value_str.lstrip('-').isdigit():
                return int(value_str)
        except:
            pass
        
        # 尝试转换为浮点数
        try:
            return float(value_str)
        except:
            pass
        
        # 处理布尔值
        if value_str.lower() in ['true', 'yes']:
            return True
        elif value_str.lower() in ['false', 'no']:
            return False
        
        # 默认返回字符串
        return value_str


# 便捷函数，模拟pandas的接口
def read_csv(filepath, encoding='utf-8', delimiter=',', shuffle=False, random_seed=42):
    """
    便捷函数，用于读取CSV文件
    
    Args:
        filepath: CSV文件路径
        encoding: 文件编码
        delimiter: 分隔符
        shuffle: 是否打乱行顺序，默认为False（与pandas一致）
        random_seed: 随机种子
        
    Returns:
        DataTable对象
    """
    return PureCSVReader.read_csv(filepath, encoding, delimiter, shuffle, random_seed)


# 用于测试的函数
def create_sample_data():
    """创建示例数据用于测试"""
    sample_data = {
        'SMILES': ['CCO', 'CC', 'CCC', 'CCCC', 'CCCCC'],
        'ACTIVITY': [1, 0, 1, 0, 1],
        'NAME': ['Ethanol', 'Methane', 'Propane', 'Butane', 'Pentane']
    }
    return DataTable(sample_data) 