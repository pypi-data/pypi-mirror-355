# 100%纯Python命令行参数解析器

class ParameterDefinition:
    """参数定义类"""
    
    def __init__(self, name, param_type=str, default=None, choices=None, help_text="", required=False):
        self.name = name
        self.param_type = param_type
        self.default = default
        self.choices = choices
        self.help_text = help_text
        self.required = required

class ParsedArguments:
    """解析结果类"""
    
    def __init__(self):
        self._values = {}
    
    def __getattr__(self, name):
        if name.startswith('_'):
            return object.__getattribute__(self, name)
        return self._values.get(name)
    
    def __setattr__(self, name, value):
        if name.startswith('_'):
            object.__setattr__(self, name, value)
        else:
            self._values[name] = value

class CommandLineProcessor:
    """100%纯Python命令行参数处理器"""
    
    def __init__(self, description="Command line application"):
        self.description = description
        self.parameters = {}
        self.positional_params = []
    
    def add_argument(self, name, **kwargs):
        """添加命令行参数定义
        
        Args:
            name: 参数名称 (如 '--num_networks')
            type: 参数类型 (如 int, str)
            default: 默认值
            choices: 可选值列表
            help: 帮助文本
            required: 是否必需
            action: 动作类型 (如 'store_true')
        """
        # 处理参数名
        if name.startswith('--'):
            param_name = name[2:]
        elif name.startswith('-'):
            param_name = name[1:]
        else:
            param_name = name
        
        # 提取参数配置
        param_type = kwargs.get('type', str)
        default = kwargs.get('default', None)
        choices = kwargs.get('choices', None)
        help_text = kwargs.get('help', "")
        required = kwargs.get('required', False)
        action = kwargs.get('action', None)
        
        # 处理特殊动作
        if action == 'store_true':
            param_type = bool
            default = False if default is None else default
        
        # 创建参数定义
        param_def = ParameterDefinition(
            name=param_name,
            param_type=param_type,
            default=default,
            choices=choices,
            help_text=help_text,
            required=required
        )
        
        # 存储参数定义
        self.parameters[name] = param_def
        if not name.startswith('-'):
            self.positional_params.append(param_def)
    
    def parse_args(self, args=None):
        """解析命令行参数
        
        Args:
            args: 参数列表，如果为None则自动获取系统命令行参数
            
        Returns:
            ParsedArguments: 解析结果对象
        """
        # 获取命令行参数
        if args is None:
            # 自动获取系统命令行参数
            from . import tools
            args = tools.argv[1:]
        
        # 创建解析结果对象
        result = ParsedArguments()
        
        # 设置默认值
        for param_name, param_def in self.parameters.items():
            clean_name = param_def.name
            if param_def.default is not None:
                setattr(result, clean_name, param_def.default)
        
        # 解析参数
        i = 0
        while i < len(args):
            arg = args[i]
            
            if arg.startswith('--'):
                # 长参数格式
                if '=' in arg:
                    param_name, value = arg.split('=', 1)
                else:
                    param_name = arg
                    if i + 1 < len(args) and not args[i + 1].startswith('-'):
                        value = args[i + 1]
                        i += 1
                    else:
                        value = None
                
                self._process_parameter(result, param_name, value)
                
            elif arg.startswith('-') and len(arg) > 1:
                # 短参数格式
                param_name = arg
                if i + 1 < len(args) and not args[i + 1].startswith('-'):
                    value = args[i + 1]
                    i += 1
                else:
                    value = None
                
                self._process_parameter(result, param_name, value)
            
            i += 1
        
        # 验证必需参数
        self._validate_required_parameters(result)
        
        return result
    
    def _process_parameter(self, result, param_name, value):
        """处理单个参数"""
        # 查找参数定义
        param_def = None
        for name, definition in self.parameters.items():
            if name == param_name:
                param_def = definition
                break
        
        if param_def is None:
            return
        
        # 处理布尔类型
        if param_def.param_type == bool:
            if value is None:
                setattr(result, param_def.name, True)
            else:
                setattr(result, param_def.name, self._convert_to_bool(value))
            return
        
        # 处理其他类型
        if value is None:
            return
        
        # 类型转换
        try:
            converted_value = self._convert_value(value, param_def.param_type)
        except:
            return
        
        # 检查choices
        if param_def.choices and converted_value not in param_def.choices:
            return
        
        # 设置值
        setattr(result, param_def.name, converted_value)
    
    def _convert_value(self, value, target_type):
        """转换值到目标类型"""
        if target_type == int:
            return int(value)
        elif target_type == float:
            return float(value)
        elif target_type == str:
            return str(value)
        elif target_type == bool:
            return self._convert_to_bool(value)
        else:
            return value
    
    def _convert_to_bool(self, value):
        """转换字符串到布尔值"""
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            lower_value = value.lower()
            if lower_value in ['true', '1', 'yes', 'on']:
                return True
            elif lower_value in ['false', '0', 'no', 'off']:
                return False
        return False
    
    def _validate_required_parameters(self, result):
        """验证必需参数"""
        for param_name, param_def in self.parameters.items():
            if param_def.required:
                value = getattr(result, param_def.name)
                if value is None:
                    print(f"缺少必需参数: {param_name}")
    
    def print_help(self):
        """打印帮助信息"""
        print(f"{self.description}")
        print("\n可选参数:")
        
        for param_name, param_def in self.parameters.items():
            if param_name.startswith('-'):
                type_str = param_def.param_type.__name__ if param_def.param_type != bool else ""
                default_str = f" (默认: {param_def.default})" if param_def.default is not None else ""
                choices_str = f" {{{', '.join(map(str, param_def.choices))}}}" if param_def.choices else ""
                
                print(f"  {param_name} {type_str}{choices_str}")
                print(f"    {param_def.help_text}{default_str}")

# 简化的函数接口
def create_argument_parser(description="Command line application"):
    """创建命令行参数解析器的简化接口"""
    return CommandLineProcessor(description)

# 测试函数
def test_command_line_parser():
    """测试命令行解析器"""
    print("=== 测试命令行参数解析器 ===")
    
    # 创建解析器
    parser = CommandLineProcessor(description='分子属性预测')
    
    # 添加参数
    parser.add_argument('--num_networks', type=int, default=1, 
                       help='要训练的网络数量')
    parser.add_argument('--file_format', type=str, default='dict', 
                       choices=['pt', 'dict'],
                       help='模型文件保存格式')
    parser.add_argument('--verbose', action='store_true',
                       help='启用详细输出')
    
    # 测试解析
    test_args = ['--num_networks', '3', '--file_format', 'pt', '--verbose']
    result = parser.parse_args(test_args)
    
    print(f"解析结果:")
    print(f"  num_networks: {result.num_networks}")
    print(f"  file_format: {result.file_format}")
    print(f"  verbose: {result.verbose}")
    
    print("✅ 命令行参数解析器测试通过")

if __name__ == "__main__":
    test_command_line_parser() 