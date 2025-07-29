from .tensor_T import Tensor, Parameter
from . import math1 as math
from . import arrays
from .module_list_T import Module

class Linear(Module):
    """线性层"""
    def __init__(self, in_features: int, out_features: int, bias: bool = True, 
                 device: str = 'cpu', dtype: str = 'float32'):
        super().__init__()
        self.in_features = in_features
        self.out_features = out_features
        self.use_bias = bias
        self.device = device
        self.dtype = dtype

        # 使用 Kaiming 初始化
        weight = arrays.randn(out_features, in_features).astype(float)
        # Kaiming 初始化
        fan_in = in_features
        gain = math.sqrt(2.0)  # ReLU 的推荐值
        std = gain / math.sqrt(fan_in)
        bound = math.sqrt(3.0) * std
        weight_array = arrays.random.uniform(-bound, bound, (out_features, in_features))
        weight = arrays.array(weight_array.data, dtype=float).reshape(out_features, in_features)
        self.weight = Parameter(weight)
        
        # bias 初始化为 0
        if bias:
            bias_array = arrays.zeros(out_features, dtype='float32')
            self.bias = Parameter(arrays.array(bias_array.data, dtype=float))
        else:
            self.bias = None

    def forward(self, input: Tensor) -> Tensor:
        """前向传播"""
        if not input.requires_grad:
            input.requires_grad = True
        # 确保输入是二维的
        if input.ndim == 1:
            input = input.reshape((1, -1))
        
        # 执行线性变换
        output = input @ self.weight.T
        if self.use_bias and self.bias is not None:
            output = output + self.bias
        return output

    def extra_repr(self) -> str:
        """额外的字符串表示"""
        return f'in_features={self.in_features}, out_features={self.out_features}, bias={self.bias is not None}'
