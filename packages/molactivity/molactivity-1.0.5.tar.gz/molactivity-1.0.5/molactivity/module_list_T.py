


class Module:
    """Base module class for neural network components"""
    def __init__(self):
        """Initialize module"""
        self._parameters = {}
        self._modules = {}
        self._buffers = {}
        self._is_training = True

    def __call__(self, *args, **kwargs):
        """Forward pass with module reference attachment"""
        result = self.forward(*args, **kwargs)
        
        # 如果结果是张量，附加模块引用
        if hasattr(result, 'attach_module_reference'):
            result.attach_module_reference(self)
        
        return result

    def forward(self, *args, **kwargs):
        """Forward pass implementation"""
        raise NotImplementedError("子类必须实现forward方法")

    def register_parameter(self, name, param):
        """Register a parameter"""
        if param is None:
            self._parameters[name] = None
        else:
            # 在参数中添加对当前模块的引用，方便反向传播
            param._module = self
            param.requires_grad = True
            self._parameters[name] = param

    def register_buffer(self, name, tensor):
        """Register a buffer (non-trainable tensor)"""
        self._buffers[name] = tensor

    def add_module(self, name, module):
        """Add a module"""
        self._modules[name] = module

    def train(self, mode=True):
        """Set training mode"""
        self._is_training = mode
        for module in self.children():
            module.train(mode)
        return self

    def eval(self):
        """Set evaluation mode"""
        return self.train(False)

    def requires_grad_(self, requires_grad=True):
        """Set if parameters require gradient"""
        for param in self.parameters():
            param.requires_grad = requires_grad
        return self

    def zero_grad(self):
        """Zero all gradients"""
        for param in self.parameters():
            if param.grad is not None:
                param.grad.zero_()

    def parameters(self):
        """Iterator over all parameters"""
        for name, param in self.named_parameters():
            yield param

    def named_parameters(self, prefix=''):
        """Iterator over named parameters"""
        for name, param in self._parameters.items():
            if param is not None:
                yield prefix + ('.' if prefix else '') + name, param

        for mname, module in self._modules.items():
            for name, param in module.named_parameters(prefix=prefix + ('.' if prefix else '') + mname):
                yield name, param

    def children(self):
        """Iterator over immediate children modules"""
        for _, module in self._modules.items():
            yield module

    def named_children(self):
        """Iterator over immediate named children modules"""
        for name, module in self._modules.items():
            yield name, module

    def state_dict(self):
        """返回模块的状态字典（只包含可序列化内容）"""
        def make_pickle_safe(data):
            """将数据转换为pickle安全的格式"""
            # 检查是否是FinalArrayCompatible对象
            if hasattr(data, '__class__') and data.__class__.__name__ == 'FinalArrayCompatible':
                return {
                    '__type__': 'FinalArrayCompatible',
                    'data': data._data,
                    'shape': data._shape,
                    'dtype': data._dtype
                }
            elif hasattr(data, 'tolist'):
                return data.tolist()
            elif hasattr(data, 'copy'):
                return data.copy()
            elif isinstance(data, (list, tuple)):
                return data.copy() if hasattr(data, 'copy') else list(data)
            else:
                return data
        
        state = {}
        # 保存参数
        for name, param in self._parameters.items():
            if param is not None and hasattr(param, 'data'):
                state[name] = make_pickle_safe(param.data)
        # 保存缓冲区
        for name, buf in self._buffers.items():
            if buf is not None and hasattr(buf, 'data'):
                state[name] = make_pickle_safe(buf.data)
        # 保存子模块
        for name, module in self._modules.items():
            if hasattr(module, 'state_dict'):
                state[name] = module.state_dict()
        return state

    def load_state_dict(self, state_dict):
        """加载状态字典"""
        # 加载参数
        for name, param in self._parameters.items():
            if param is not None and name in state_dict:
                param.data = state_dict[name]
        # 加载缓冲区
        for name, buf in self._buffers.items():
            if buf is not None and name in state_dict:
                buf.data = state_dict[name]
        # 加载子模块
        for name, module in self._modules.items():
            if name in state_dict and hasattr(module, 'load_state_dict'):
                module.load_state_dict(state_dict[name])

    def named_buffers(self, prefix=''):
        """Iterator over named buffers"""
        for name, buf in self._buffers.items():
            if buf is not None:
                yield prefix + ('.' if prefix else '') + name, buf

        for mname, module in self._modules.items():
            for name, buf in module.named_buffers(prefix=prefix + ('.' if prefix else '') + mname):
                yield name, buf

    def buffers(self):
        """Iterator over all buffers"""
        for name, buf in self.named_buffers():
            yield buf

    def __setattr__(self, name, value):
        """Set attribute with special handling for parameters, modules, and buffers"""
        from .tensor_T import Tensor

        # 如果是Parameter对象
        if isinstance(value, Tensor) and name != '_parameters' and name != '_buffers' and name != '_modules':
            # 确保参数与模块建立关联
            value._module = self
            value.requires_grad = True
            self.register_parameter(name, value)
        # 如果是Module对象
        elif isinstance(value, Module) and name != '_parameters' and name != '_buffers' and name != '_modules':
            self.add_module(name, value)
        else:
            object.__setattr__(self, name, value)

    def __getattr__(self, name):
        """Get attribute with special handling for parameters, modules, and buffers"""
        if '_parameters' in self.__dict__:
            _parameters = self.__dict__['_parameters']
            if name in _parameters:
                return _parameters[name]
        if '_buffers' in self.__dict__:
            _buffers = self.__dict__['_buffers']
            if name in _buffers:
                return _buffers[name]
        if '_modules' in self.__dict__:
            _modules = self.__dict__['_modules']
            if name in _modules:
                return _modules[name]
        raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    def create_parameter_index(self):
        """创建参数索引表用于快速查找
        
        创建两种索引:
        1. 按形状索引 - 可以通过张量形状找到匹配的参数
        2. 按ID索引 - 可以通过参数ID直接查找参数
        
        Returns:
            索引字典
        """
        self._param_index = {}
        
        # 按形状索引
        shape_index = {}
        for name, param in self.named_parameters():
            shape_key = str(param.shape)
            if shape_key not in shape_index:
                shape_index[shape_key] = []
            shape_index[shape_key].append((name, param))
            
            # 按ID索引
            self._param_index[id(param)] = (name, param)
        
        # 将形状索引添加到主索引
        self._param_index['by_shape'] = shape_index
        
        return self._param_index
    
    def find_parameters_by_shape(self, shape):
        """根据形状查找参数
        
        Args:
            shape: 要查找的参数形状
            
        Returns:
            匹配形状的参数列表 [(name, param), ...]
        """
        if not hasattr(self, '_param_index'):
            self.create_parameter_index()
            
        shape_key = str(shape)
        shape_index = self._param_index.get('by_shape', {})
        
        # 首先查找精确匹配
        exact_matches = shape_index.get(shape_key, [])
        if exact_matches:
            return exact_matches
            
        # 如果没有精确匹配，尝试通过其他方式查找可能的候选参数
        # 例如，如果shape是广播兼容的
        candidate_params = []
        for param_name, param in self.named_parameters():
            # 检查广播兼容性
            if len(param.shape) == len(shape):
                compatible = True
                for dim_param, dim_shape in zip(param.shape, shape):
                    if dim_param != dim_shape and dim_param != 1 and dim_shape != 1:
                        compatible = False
                        break
                if compatible:
                    candidate_params.append((param_name, param))
                    
        return candidate_params

class ModuleList(Module):
    """Container for sequentially arranged modules"""
    def __init__(self, modules=None):
        """Initialize ModuleList"""
        super(ModuleList, self).__init__()
        if modules is not None:
            for i, module in enumerate(modules):
                self.add_module(str(i), module)

    def __iter__(self):
        """Iterate over modules"""
        return iter(self._modules.values())

    def __len__(self):
        """Get number of modules"""
        return len(self._modules)

    def __getitem__(self, idx):
        """Get module at index"""
        if isinstance(idx, slice):
            return ModuleList([self._modules[str(i)] for i in range(len(self))[idx]])
        else:
            return self._modules[str(idx)]

    def append(self, module):
        """Append module"""
        self.add_module(str(len(self)), module)
        return self

    def extend(self, modules):
        """Extend with modules"""
        for module in modules:
            self.append(module)
        return self

    def forward(self, x):
        """Forward pass through all modules in sequence"""
        for module in self:
            x = module(x)
        return x

class Sequential(Module):
    """顺序容器，按顺序执行包含的模块"""
    
    def __init__(self, *modules):
        """
        初始化Sequential模块
        
        Args:
            *modules: 要按顺序执行的模块列表
        """
        super().__init__()
        self.modules_list = []
        for idx, module in enumerate(modules):
            self.add_module(str(idx), module)
            self.modules_list.append(module)
    
    def add_module(self, name, module):
        """
        添加命名模块
        
        Args:
            name: 模块名称
            module: 要添加的模块
        """
        # 检查是否为合法模块
        if not (isinstance(module, Module) or callable(module)):
            raise TypeError(f"Sequential只能包含Module实例或可调用对象，但得到{type(module)}")
            
        # 设置为属性并添加到_modules字典
        setattr(self, name, module)
        
        # 如果是Module实例，确保被跟踪
        if isinstance(module, Module):
            self._modules[name] = module
    
    def forward(self, x):
        """
        按顺序执行所有模块
        
        Args:
            x: 输入数据
            
        Returns:
            经过所有模块处理后的输出
        """
        for module in self.modules_list:
            # 检查是否为Module实例或可调用对象
            if isinstance(module, Module):
                if hasattr(module, 'forward'):
                    x = module.forward(x)
                else:
                    raise AttributeError(f"模块{module}没有forward方法")
            elif callable(module):
                # 直接调用函数
                x = module(x)
            else:
                raise TypeError(f"模块必须是Module实例或可调用对象，但得到{type(module)}")
        return x
    
    def __call__(self, x):
        """允许直接调用Sequential实例"""
        return self.forward(x)
    
    def __getitem__(self, idx):
        """支持索引访问模块"""
        if isinstance(idx, slice):
            # 创建一个新的Sequential包含切片的模块
            return Sequential(*self.modules_list[idx])
        else:
            return self.modules_list[idx]
    
    def __len__(self):
        """返回模块数量"""
        return len(self.modules_list)
    
    def __iter__(self):
        """允许迭代Sequential中的模块"""
        return iter(self.modules_list)
    
    def __repr__(self):
        """返回模块列表的字符串表示"""
        module_str = ', '.join(repr(m) for m in self.modules_list)
        return f"Sequential({module_str})"
        
    def train(self, mode=True):
        """设置模型为训练模式"""
        self.training = mode
        # 递归设置所有子模块的训练模式
        for module in self.modules_list:
            if isinstance(module, Module) and hasattr(module, 'train'):
                module.train(mode)
        return self
        
    def eval(self):
        """设置模型为评估模式"""
        return self.train(False)
