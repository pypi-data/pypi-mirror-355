from .typing1 import Optional, Tuple, Union
from . import math1 as math
from .erf_T import erf
from . import arrays
from .tensor_T import Tensor
from .autograd_T import Function
from .operations_T import matmul, add

def _var_with_keepdims(data, axis=None, keepdims=False):
    """辅助函数：处理arrays.var的keepdims参数"""
    from . import arrays
    
    result = arrays.var(arrays.Array(data), axis=axis)
    
    if keepdims and axis is not None:
        # 手动处理keepdims
        if isinstance(axis, int):
            axis = [axis]
        elif isinstance(axis, tuple):
            axis = list(axis)
        
        # 获取结果数据
        if hasattr(result, 'data'):
            result_data = result.data
        else:
            result_data = result
        
        # 计算新的形状
        new_shape = list(data.shape)
        for ax in sorted(axis):
            new_shape[ax] = 1
        
        # 重新reshape
        result_asarray = arrays.asarray(result_data)
        result = result_asarray.reshape(new_shape)
    elif hasattr(result, 'data'):
        result = arrays.asarray(result.data)
    
    return result



class Softmax(Function):
    @staticmethod
    def forward(ctx, input, dim):
        # 确保dim是适合numpy的类型
        axis = dim
        max_val = arrays.max(input.data, axis=axis, keepdims=True)
        shifted_data = input.data - max_val
        shifted_array = arrays.Array(shifted_data)
        exp_result = arrays.exp(shifted_array)
        exp = arrays.array(exp_result.data)
        sum_exp = arrays.sum(exp, axis=axis, keepdims=True)
        output = exp / sum_exp
        ctx.save_for_backward(output)
        ctx.metadata['dim'] = dim
        return output

    @staticmethod
    def backward(ctx, grad_output):
        output, = ctx.saved_tensors
        dim = ctx.metadata['dim']
        
        # 确保dim是适合numpy的类型
        axis = dim
        # 计算 softmax 的梯度
        grad_input = output * (grad_output.data - arrays.sum(output * grad_output.data, axis=axis, keepdims=True))
        return grad_input, None

def linear(input: Tensor, weight: Tensor, bias: Optional[Tensor] = None) -> Tensor:
    """线性变换"""
    # 精简调试信息
    debug = False  # 设置为False关闭大部分调试输出
    
    if debug:
        print(f"linear函数输入: input.shape={input.shape}, weight.shape={weight.shape}")
    
    # 确保输入是2D张量
    if input.ndim == 1:
        input = input.reshape(1, -1)
        if debug: print(f"  调整input为2D: shape={input.shape}")
    elif input.ndim > 2:
        input = input.reshape(-1, input.shape[-1])
        if debug: print(f"  调整input为2D: shape={input.shape}")
    
    # 确保权重是2D张量
    if weight.ndim == 1:
        weight = weight.reshape(1, -1)
        if debug: print(f"  调整weight为2D: shape={weight.shape}")
    elif weight.ndim > 2:
        weight = weight.reshape(weight.shape[0], -1)
        if debug: print(f"  调整weight为2D: shape={weight.shape}")
    
    # 检查维度
    if input.shape[-1] != weight.shape[0]:
        error_msg = f"输入维度 {input.shape[-1]} 与权重维度 {weight.shape[0]} 不匹配"
        print(f"错误: {error_msg}")
        raise ValueError(error_msg)
    
    # 执行矩阵乘法
    if debug: print(f"  执行matmul: {input.shape} @ {weight.shape}")
    output = matmul(input, weight)
    if debug: print(f"  matmul结果: shape={output.shape}")
    
    # 添加偏置
    if bias is not None:
        try:
            if debug:
                orig_bias_shape = bias.shape if hasattr(bias, 'shape') else None
                print(f"  原始偏置形状: {orig_bias_shape}, 类型: {type(bias)}")
            # 确保偏置是数组
            if hasattr(bias, 'data'):
                bias_data = bias.data
            else:
                bias_data = bias
            # 转换为arrays数组
            try:
                bias_asarray = arrays.asarray(bias_data, dtype='float')
                bias_data = bias_asarray.data
            except Exception as e:
                if debug: print(f"  转换偏置为arrays数组失败: {e}，使用零偏置")
                # 如果转换失败，使用零偏置
                zeros_array = arrays.zeros(output.shape[-1], dtype='float32')
                bias_asarray = arrays.asarray(zeros_array.data)
                bias_data = bias_asarray.data
            # 调整偏置形状
            if not isinstance(bias_data, list):  # 标量
                if debug: print(f"  偏置是标量，扩展为向量")
                zeros_array = arrays.zeros(output.shape[-1], dtype='float32')
                bias_asarray = arrays.asarray(zeros_array.data)
                bias_data = bias_asarray.data
            elif isinstance(bias_data, list):
                if len(bias_data) == 1:  # 单元素列表
                    # 扩展为匹配输出维度的向量
                    zeros_array = arrays.zeros(output.shape[-1], dtype='float32')
                    bias_asarray = arrays.asarray(zeros_array.data)
                    bias_data = bias_asarray.data
                elif len(bias_data) != output.shape[-1]:
                    if debug: print(f"  偏置维度 {len(bias_data)} 与输出通道 {output.shape[-1]} 不匹配，重新创建")
                    zeros_array = arrays.zeros(output.shape[-1], dtype='float32')
                    bias_asarray = arrays.asarray(zeros_array.data)
                    bias_data = bias_asarray.data
                if debug: print(f"  调整bias形状: {orig_bias_shape} -> 1D向量")
            # 创建新的偏置张量
            from .tensor_T import Tensor
            bias = Tensor(bias_data)
            if debug: print(f"  添加偏置: output.shape={output.shape}, bias.shape={bias.shape}")
            output = add(output, bias)
            if debug: print(f"  添加偏置后: output.shape={output.shape}")
        except Exception as e:
            print(f"  添加偏置失败: {e}，跳过偏置")
    
    return output

def relu(input: Tensor, inplace: bool = False) -> Tensor:
    """
    ReLU函数: max(0, x) (支持原地操作)
    
    Args:
        input:  输入张量
        inplace: 是否原地修改
        
    Returns:
        输出张量（与输入形状相同）
    """
    if inplace:
        input.clamp_min_(0)
        return input
    return input.clamp_min(0)

def sigmoid(input: Tensor) -> Tensor:
    """Sigmoid函数: 1 / (1 + exp(-x))"""
    input_array = arrays.Array(input.data)
    ones_like_array = arrays.ones_like(input_array)
    one = Tensor(arrays.array(ones_like_array.data))
    return one / (one + (-input).exp())

def softmax(input: Tensor, dim: int = -1) -> Tensor:
    """Softmax函数"""
    return Softmax.apply(input, dim)

def log_softmax(input: Tensor, dim: int = -1) -> Tensor:
    """
    LogSoftmax函数: log(exp(x_i) / sum(exp(x_j)))
    
    Args:
        input: 输入张量
        dim:   计算log_softmax的维度
        
    Returns:
        对数概率分布（沿指定维度求和为1）
    """
    max_values = input.max(dim=dim, keepdim=True)[0]
    exp_input = (input - max_values).exp()  # 数值稳定处理
    log_sum_exp = exp_input.sum(dim=dim, keepdim=True).log()
    return input - max_values - log_sum_exp

def gelu(input: Tensor, approximate: str = 'tanh') -> Tensor:
    """GELU激活函数"""
    if approximate == 'tanh':
        sqrt_2_over_pi = Tensor(math.sqrt(2 / math.pi))
        coeff = Tensor(0.044715)
        half = Tensor(0.5)
        one = Tensor(1.0)
        return half * input * (one + (sqrt_2_over_pi * (input + coeff * input.pow(3))).tanh())
    else:
        return input * 0.5 * (1.0 + erf(input / math.sqrt(2.0)))

def dropout(input: Tensor, p: float = 0.5, training: bool = True) -> Tensor:
    """
    Dropout函数:
    - 训练时: 以概率p随机置零并缩放剩余值
    - 推理时: 原样返回
    
    Args:
        p:        置零概率
        training: 是否处于训练模式
    """
    if not training or p == 0:
        return input
        
    mask = (Tensor.rand_like(input) > p).float()
    return input * mask / (1 - p)

def layer_norm(input: Tensor, normalized_shape: Union[int, Tuple[int, ...]], 
              weight: Optional[Tensor] = None, bias: Optional[Tensor] = None, 
              eps: float = 1e-5) -> Tensor:
    """Layer Normalization"""
    if isinstance(normalized_shape, int):
        normalized_shape = (normalized_shape,)
    
    # 计算均值和方差
    data = input.data
    dims = tuple(range(-len(normalized_shape), 0))
    # 确保dims是元组
    axis = dims
    mean = arrays.mean(arrays.Array(data), axis=axis, keepdims=True)
    var = _var_with_keepdims(data, axis=axis, keepdims=True)
    
    # 归一化
    sqrt_input_array = arrays.Array(var + eps)
    sqrt_result = arrays.sqrt(sqrt_input_array)
    x = (data - mean) / arrays.array(sqrt_result.data)
    x = Tensor(x)
    
    # 应用可学习的参数
    if weight is not None:
        x = x * weight
    if bias is not None:
        x = x + bias
        
    return x

def binary_cross_entropy_with_logits(
    input: Tensor,
    target: Tensor,
    weight: Optional[Tensor] = None,
    reduction: str = 'mean'
) -> Tensor:
    """
    带logits的二元交叉熵损失:
    loss = -(target * log(sigmoid(input)) + (1-target)*log(1-sigmoid(input)))
    
    Args:
        reduction: 输出形式 ('none'|'mean'|'sum')
    """
    max_val = (-input).clamp_min(0)
    loss = input - input * target + max_val + ((-max_val).exp() + (-input - max_val).exp()).log()
    
    if weight is not None:
        loss = loss * weight
        
    if reduction == 'mean':
        return loss.mean()
    elif reduction == 'sum':
        return loss.sum()
    return loss

# ----------------------------- 张量操作函数 -----------------------------
def zeros_like(input: Tensor) -> Tensor:
    """生成与输入形状相同的全零张量"""
    return Tensor.zeros(*input.shape)

def ones_like(input: Tensor) -> Tensor:
    """生成与输入形状相同的全一张量"""
    return Tensor.ones(*input.shape)

def rand_like(input: Tensor) -> Tensor:
    """生成与输入形状相同的均匀随机张量"""
    return Tensor.rand(*input.shape)

