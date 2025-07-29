from .typing1 import Optional
from . import pure_random
from . import arrays
from .tensor_T import Tensor
from .module_list_T import Module
from . import strong_array_reshape_final

class Dropout(Module):
    def __init__(
        self,
        p: float = 0.5,
        inplace: bool = False,
        generator: Optional[pure_random.PureRandom] = None
    ) -> None:
        """
        Dropout 层实现
        
        Args:
            p:        每个神经元被置零的概率 (default: 0.5)
            inplace:  是否原地修改输入张量 (default: False)
            generator: 随机数生成器 (default: None)
        
        Raises:
            ValueError: 如果 p 不在 [0, 1) 区间
        """
        super(Dropout, self).__init__()
        if p < 0 or p >= 1:
            raise ValueError(f"dropout probability必须在[0, 1)之间，当前为 {p}")
            
        self.p = p
        self.inplace = inplace
        self.generator = generator if generator is not None else pure_random.PureRandom()
        self.training = True  # 默认处于训练模式
        self._mask = None

    def forward(self, input: Tensor) -> Tensor:
        """
        前向传播：
        - 训练模式：以概率p随机置零输入
        - 推理模式：原样返回输入（自动缩放）
        
        Args:
            input: 输入张量
            
        Returns:
            输出张量（训练时随机置零部分值，推理时返回原输入）
        """
        if not self.training or self.p == 0:
            if not self.inplace:
                return input.clone()
            return input

        # 生成随机mask  
        mask_data = []
        total_elements = 1
        for dim in input.shape:
            total_elements *= dim
        
        # 生成随机值并比较
        for _ in range(total_elements):
            mask_data.append(self.generator.random() > self.p)
        
        mask_array = arrays.array(mask_data).reshape(*input.shape)
        # 将mask转换为与input.data兼容的numpy格式
        if hasattr(input.data, 'shape'):
            # input.data是numpy数组，需要确保mask也是相同形状的numpy数组
            self._mask = strong_array_reshape_final.perfect_array(mask_array.data, dtype=float, shape=input.shape)
        else:
            # input.data是列表，保持列表格式
            self._mask = mask_array.data
        scale = 1.0 / (1.0 - self.p)
        
        if self.inplace:
            input.data *= self._mask * scale
            return input
        else:
            output = input.clone()
            output.data = input.data * self._mask * scale
        return output

    def backward(self, grad_output: Tensor) -> Tensor:
        if not self.training or self.p == 0:
            return grad_output.clone()
            
        scale = 1.0 / (1.0 - self.p)
        grad_input = grad_output.clone()
        grad_input.data *= self._mask * scale
        return grad_input

    def train(self, mode: bool = True) -> None:
        """设置训练/推理模式"""
        self.training = mode

    def eval(self) -> None:
        """切换到推理模式"""
        self.train(False)

    def reset_seed(self, seed: Optional[int] = None) -> None:
        """重置随机种子"""
        self.generator = pure_random.PureRandom(seed)

    def extra_repr(self) -> str:
        return f'p={self.p}, inplace={self.inplace}, training={self.training}'

    def __repr__(self) -> str:
        return f'Dropout({self.extra_repr()})'

    def __call__(self, input: Tensor) -> Tensor:
        return self.forward(input)
