# 100%纯Python Softmax实现
# 不使用torch或numpy外部库，仅使用我们自己的tensor_T
# 避免复杂的运算符重载，直接使用arrays计算

from .tensor_T import Tensor
from . import arrays

def pure_softmax_arrays(x_data, dim=-1):
    """使用arrays实现数值稳定的softmax"""
    # 处理负数维度
    if dim < 0:
        dim = len(x_data.shape) + dim
    
    # 确保dim在有效范围内
    if dim >= len(x_data.shape):
        dim = len(x_data.shape) - 1
    
    result = arrays.zeros_like(x_data)
    
    # 对每个切片分别计算softmax
    if dim == 0:  # 列方向
        for i in range(x_data.shape[1]):
            col = x_data[:, i]
            max_val = arrays.max(col)
            exp_col = arrays.exp(col - max_val)
            sum_exp = arrays.sum(exp_col)
            result[:, i] = exp_col / (sum_exp + 1e-8)
    elif dim == 1 or dim == -1:  # 行方向
        for i in range(x_data.shape[0]):
            row = x_data[i, :]
            max_val = arrays.max(row)
            exp_row = arrays.exp(row - max_val)
            sum_exp = arrays.sum(exp_row)
            result[i, :] = exp_row / (sum_exp + 1e-8)
    else:
        # 对于更高维度，我们需要更复杂的处理
        max_val = arrays.max(x_data, axis=dim, keepdims=True)
        shifted_x = x_data - max_val
        exp_x = arrays.exp(shifted_x)
        sum_exp = arrays.sum(exp_x, axis=dim, keepdims=True)
        result = exp_x / (sum_exp + 1e-8)
    
    return arrays.array(result)

def softmax(x, dim=-1):
    """100%纯Python数值稳定的softmax实现"""
    
    #if not isinstance(x, Tensor):
    x = Tensor(x) 
    x_data = x.numpy()
    result_data = pure_softmax_arrays(x_data, dim)
    
    return Tensor(result_data, requires_grad=x.requires_grad)

def log_softmax(x, dim=-1):
    """100%纯Python对数softmax实现"""

    x = Tensor(x)
    
    # 获取numpy数据
    x_data = x.numpy()
    
    # 将numpy数组转换为可处理的形式
    result = arrays.zeros_like(x_data)
    
    # 处理负数维度
    if dim < 0:
        dim = len(x_data.shape) + dim
    
    # 确保dim在有效范围内
    if dim >= len(x_data.shape):
        dim = len(x_data.shape) - 1
    
    # 对每个切片分别计算log_softmax
    if dim == 0:  # 列方向
        for i in range(x_data.shape[1]):
            col = x_data[:, i]
            max_val = arrays.max(col)
            shifted_col = col - max_val
            exp_col = arrays.exp(shifted_col)
            sum_exp = arrays.sum(exp_col) + 1e-8
            log_sum_exp = arrays.log(sum_exp)
            result[:, i] = shifted_col - log_sum_exp
    elif dim == 1 or dim == -1:  # 行方向
        for i in range(x_data.shape[0]):
            row = x_data[i, :]
            max_val = arrays.max(row)
            shifted_row = row - max_val
            exp_row = arrays.exp(shifted_row)
            sum_exp = arrays.sum(exp_row) + 1e-8
            log_sum_exp = arrays.log(sum_exp)
            result[i, :] = shifted_row - log_sum_exp
    else:
        # 对于更高维度，我们需要更复杂的处理
        max_val = arrays.max(x_data, axis=dim, keepdims=True)
        shifted_x = x_data - max_val
        exp_x = arrays.exp(shifted_x)
        sum_exp = arrays.sum(exp_x, axis=dim, keepdims=True) + 1e-8
        log_sum_exp = arrays.log(sum_exp)
        result = shifted_x - log_sum_exp
    
    arrays_result = arrays.array(result)
    
    return Tensor(result, requires_grad=x.requires_grad)

# 测试函数
def test_pure_softmax():
    """测试纯Python softmax实现"""
    print("=== 测试100%纯Python Softmax ===")
    
    # 测试1D数据
    print("\n--- 测试1D数据 ---")
    test_data_1d = [1.0, 2.0, 3.0]
    x1 = Tensor(test_data_1d)
    
    print(f"输入: {x1.numpy()}")
    
    # 测试softmax
    result1 = softmax(x1, dim=-1)
    print(f"Softmax结果: {result1.numpy()}")
    
    # 验证和是否接近1
    result_data = result1.numpy()
    total = arrays.sum(result_data)  # 暂时保留numpy求和用于测试
    print(f"结果的和: {total}")
    
    # 测试2D数据
    print("\n--- 测试2D数据 ---")
    test_data_2d = [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]
    x2 = Tensor(test_data_2d)
    
    print(f"输入: {x2.numpy()}")
    
    # 测试softmax
    result2 = softmax(x2, dim=-1)
    print(f"Softmax结果: {result2.numpy()}")
    
    # 验证每行的和是否接近1
    row_sums = arrays.sum(result2.numpy(), axis=-1)  # 暂时保留numpy求和用于测试
    print(f"每行的和: {row_sums}")
    
    # 测试log_softmax
    print("\n--- 测试Log Softmax ---")
    log_result = log_softmax(x1, dim=-1)
    print(f"Log Softmax结果: {log_result.numpy()}")
    
    print("\n✅ 100%纯Python Softmax测试完成")

if __name__ == "__main__":
    test_pure_softmax()