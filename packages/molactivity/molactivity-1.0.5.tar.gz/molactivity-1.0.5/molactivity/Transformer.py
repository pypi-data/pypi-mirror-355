from . import arrays
from .tensor_T import Tensor
from .dropout import Dropout
from .activations_T import ReLU, GELU
from .layers_T import Linear
from .module_list_T import Module, ModuleList
from .normalization import LayerNorm
from . import operations_T  # 使用正确的tensor操作
from . import math1 as math


class AttentionMechanism(Module):
    """Multi-head attention implementation for molecular features"""
    def __init__(self, embedding_size, head_count):
        super(AttentionMechanism, self).__init__()
        self.embedding_size = embedding_size
        self.head_count = head_count
        self.per_head_dim = embedding_size // head_count
        assert self.per_head_dim * head_count == embedding_size, "Embedding size must divide evenly by head count"
        self.query_key_value = Linear(embedding_size, 3 * embedding_size)
        self.output_projection = Linear(embedding_size, embedding_size)
        self.mask = None
        self.dropout = Dropout(0.1)

    def forward(self, x):
        # Ensure input is our custom Tensor
        if not isinstance(x, Tensor):
            x = Tensor(x)
        
        # 紧急修复：如果输入是1D张量，尝试将其reshape为2D或3D
        if hasattr(x, 'shape') and len(x.shape) == 1:
            # 假设这是一个被错误展平的张量
            # 尝试基于嵌入大小重新构造形状
            total_size = x.shape[0]
            if total_size == self.embedding_size:
                # 单个样本：(embedding_size,) -> (1, 1, embedding_size)
                x = operations_T.reshape(x, (1, 1, self.embedding_size))
            elif total_size % self.embedding_size == 0:
                # 多个样本：(batch*embedding_size,) -> (batch, 1, embedding_size)
                batch_size = total_size // self.embedding_size
                x = operations_T.reshape(x, (batch_size, 1, self.embedding_size))
            else:
                # 无法确定正确形状，抛出更详细的错误
                raise ValueError(f"无法修复1D张量形状: {x.shape}, 总大小={total_size}, 嵌入大小={self.embedding_size}")
            
        # 安全的shape解包，增加错误检查
        if not hasattr(x, 'shape') or len(x.shape) == 0:
            raise ValueError(f"Invalid tensor shape in attention: {getattr(x, 'shape', 'No shape attribute')}")
        
        if len(x.shape) == 3:
            batch_size, seq_len, d_model = x.shape
        elif len(x.shape) == 2:
            # 如果是2D，添加序列维度
            batch_size, d_model = x.shape
            seq_len = 1
            x = operations_T.reshape(x, (batch_size, seq_len, d_model))
            batch_size, seq_len, d_model = x.shape
        else:
            raise ValueError(f"Unexpected tensor shape in attention: {x.shape}. Expected 2D or 3D tensor.")
        
        # Compute Q, K, V using our linear layer
        qkv = self.query_key_value(x)  # (batch_size, seq_len, 3*d_model)
        
        # Split into Q, K, V using proper tensor operations
        # 使用tensor slicing而不是直接访问.data
        q = qkv[:, :, :self.embedding_size]
        k = qkv[:, :, self.embedding_size:2*self.embedding_size]
        v = qkv[:, :, 2*self.embedding_size:]
        
        # Reshape for multi-head attention using operations_T.reshape
        q = operations_T.reshape(q, (batch_size, seq_len, self.head_count, self.per_head_dim))
        k = operations_T.reshape(k, (batch_size, seq_len, self.head_count, self.per_head_dim))
        v = operations_T.reshape(v, (batch_size, seq_len, self.head_count, self.per_head_dim))
        
        # Transpose to (batch_size, head_count, seq_len, per_head_dim)
        q = operations_T.transpose(q, (0, 2, 1, 3))
        k = operations_T.transpose(k, (0, 2, 1, 3))
        v = operations_T.transpose(v, (0, 2, 1, 3))
        
        # Compute attention scores using proper matrix multiplication
        # Q @ K^T / sqrt(d_k)
        k_transposed = operations_T.transpose(k, (0, 1, 3, 2))  # transpose last two dims
        scores = operations_T.matmul(q, k_transposed)
        
        # Scale by sqrt(d_k) for numerical stability
        scaling_factor = Tensor(arrays.array(1.0 / math.sqrt(self.per_head_dim)))
        scores = operations_T.mul(scores, scaling_factor)
        
        # Apply mask if needed
        if self.mask is not None:
            scores = operations_T.add(scores, self.mask)
            
        # Apply softmax to get attention weights using operations_T
        attention_weights = operations_T.softmax(scores, dim=-1)
        
        # Apply dropout
        attention_weights = self.dropout(attention_weights)
        
        # Compute output: attention_weights @ V
        output = operations_T.matmul(attention_weights, v)
        
        # Reshape back to (batch_size, seq_len, embedding_size)
        output = operations_T.transpose(output, (0, 2, 1, 3))
        
        # 动态计算实际的序列长度
        total_size = 1
        for dim in output.shape:
            total_size *= dim
        actual_seq_len = total_size // (batch_size * self.embedding_size)
        
        output = operations_T.reshape(output, (batch_size, actual_seq_len, self.embedding_size))
        
        # Apply output projection
        output = self.output_projection(output)
        
        return output

class TransformerBlock(Module):
    """Fundamental building block of transformer architecture"""
    def __init__(self, embedding_size, head_count, hidden_size, dropout_rate, activation='gelu'):
        super(TransformerBlock, self).__init__()
        self.attention = AttentionMechanism(embedding_size, head_count)
        self.linear1 = Linear(embedding_size, hidden_size)
        
        # 根据激活函数类型选择相应的激活函数
        if activation.lower() == 'relu':
            self.activation = ReLU()
        elif activation.lower() == 'gelu':
            self.activation = GELU()
        else:
            raise ValueError(f"不支持的激活函数: {activation}。支持的选项: 'relu', 'gelu'")
        
        self.linear2 = Linear(hidden_size, embedding_size)
        self.dropout1 = Dropout(dropout_rate)
        self.normalization1 = LayerNorm(embedding_size)
        self.normalization2 = LayerNorm(embedding_size)
        self.dropout2 = Dropout(dropout_rate)

    def forward(self, x):
        # Ensure input is our custom Tensor
        if not isinstance(x, Tensor):
            x = Tensor(x)
        
        # Check and adjust input dimensions
        if len(x.shape) == 2:
            # Add sequence dimension: (batch_size, features) -> (batch_size, 1, features)
            batch_size, features = x.shape
            #print(f"[DEBUG] TransformerBlock reshape: 输入shape={x.shape}, 目标shape=({batch_size}, 1, {features})")
            #print(f"[DEBUG] 数据大小检查: 输入元素数={batch_size * features}, 目标元素数={batch_size * 1 * features}")
            x = operations_T.reshape(x, (batch_size, 1, features))
        
        # 安全的shape解包，增加错误检查
        if not hasattr(x, 'shape') or len(x.shape) == 0:
            raise ValueError(f"Invalid tensor shape: {getattr(x, 'shape', 'No shape attribute')}")
        
        if len(x.shape) == 3:
            batch_size, seq_len, features = x.shape
        elif len(x.shape) == 2:
            # 如果是2D，添加序列维度
            batch_size, features = x.shape
            seq_len = 1
            x = operations_T.reshape(x, (batch_size, seq_len, features))
        else:
            raise ValueError(f"Unexpected tensor shape: {x.shape}. Expected 2D or 3D tensor.")
        
        # Multi-head attention with residual connection
        residual = x
        x = self.normalization1(x)
        x = self.attention(x)
        x = self.dropout1(x)
        x = operations_T.add(residual, x)  # 使用operations_T.add而不是+
        
        # Feed-forward network with residual connection
        residual = x
        x = self.normalization2(x)
        
        # Reshape for linear layers: (batch_size, seq_len, features) -> (batch_size*seq_len, features)
        x_flat = operations_T.reshape(x, (-1, features))
        x_flat = self.linear1(x_flat)
        x_flat = self.activation(x_flat)
        x_flat = self.linear2(x_flat)
        
        # Reshape back: (batch_size*seq_len, features) -> (batch_size, seq_len, features)
        # 正确计算实际的批次大小
        actual_batch_seq_size = x_flat.shape[0] if hasattr(x_flat, 'shape') else len(x_flat.data) // features
        if actual_batch_seq_size == batch_size * seq_len:
            x = operations_T.reshape(x_flat, (batch_size, seq_len, features))
        else:
            # 如果计算的大小不匹配，重新计算正确的形状
            total_elements = x_flat.shape[0] * features if hasattr(x_flat, 'shape') else len(x_flat.data)
            if total_elements == batch_size * seq_len * features:
                x = operations_T.reshape(x_flat, (batch_size, seq_len, features))
            else:
                # 动态调整批次大小
                new_batch_size = total_elements // (seq_len * features)
                if new_batch_size * seq_len * features == total_elements:
                    x = operations_T.reshape(x_flat, (new_batch_size, seq_len, features))
                else:
                    # 最后的后备方案：保持x_flat的形状并调整batch_size
                    x = x_flat
                    if len(x.shape) == 2 and x.shape[1] == features:
                        # 假设这是正确的批次*序列长度
                        batch_size = x.shape[0] // seq_len
                        if batch_size * seq_len == x.shape[0]:
                            x = operations_T.reshape(x, (batch_size, seq_len, features))
                        else:
                            # 调整序列长度为1
                            x = operations_T.reshape(x, (x.shape[0], 1, features))
                            batch_size, seq_len, features = x.shape
        
        x = self.dropout2(x)
        x = operations_T.add(residual, x)  # 使用operations_T.add而不是+
        
        return x

class TransformerStack(Module):
    """Complete transformer architecture stack"""
    def __init__(self, embedding_size, layer_count, head_count, hidden_size, dropout_rate, activation='gelu'):
        super(TransformerStack, self).__init__()
        self.layers = ModuleList([
            TransformerBlock(embedding_size, head_count, hidden_size, dropout_rate, activation)
            for _ in range(layer_count)
        ])
        self.final_normalization = LayerNorm(embedding_size)

    def forward(self, x):
        # Ensure input is our custom Tensor
        if not isinstance(x, Tensor):
            x = Tensor(x)
            
        for layer in self.layers:
            x = layer(x)
            
        x = self.final_normalization(x)
        return x

class MolecularTransformer(Module):
    """Core architecture for molecular property prediction"""
    def __init__(self, input_features, output_features, embedding_size, layer_count, head_count, hidden_size, dropout_rate, activation='gelu'):
        super(MolecularTransformer, self).__init__()
        self.embedding_size = embedding_size
        self.activation_type = activation  # 保存激活函数类型用于显示
        self.feature_embedding = Linear(input_features, embedding_size)
        self.transformer = TransformerStack(embedding_size, layer_count, head_count, hidden_size, dropout_rate, activation)
        self.output_layer = Linear(embedding_size, output_features)
        
        print(f"MolecularTransformer初始化完成")

    def forward(self, x):
        # Ensure input is our custom Tensor
        if not isinstance(x, Tensor):
            x = Tensor(x)
            
        x = self.feature_embedding(x)
        x = self.transformer(x)
        
        # Global average pooling: mean across sequence dimension using operations_T
        # 检查张量维度，如果是1D则不需要mean操作
        if hasattr(x, 'shape') and len(x.shape) == 1:
            # 如果是1D张量，假设它已经是pooled的结果
            x_pooled = x
        elif hasattr(x, 'shape') and len(x.shape) == 2:
            # 如果是2D张量，假设是(batch_size, embedding_size)，不需要mean
            x_pooled = x
        elif hasattr(x, 'shape') and len(x.shape) == 3:
            # 正常的3D情况
            x_pooled = operations_T.mean(x, dim=1)  # (batch_size, embedding_size)
        else:
            # 其他情况，尝试直接使用
            x_pooled = x
        
        x_pooled = self.output_layer(x_pooled)
        return x_pooled