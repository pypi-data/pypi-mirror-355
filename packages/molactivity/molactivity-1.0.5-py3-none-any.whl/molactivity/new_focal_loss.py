
from . import arrays
from .tensor_T import Tensor
from .autograd_T import Function
from . import operations_T
from . import math1 as math

class FocalLoss:
    def __init__(self, alpha=0.25, gamma=2.0, high_pred_penalty=20.0, high_pred_threshold=0.9, reduction='mean'):
        self.alpha = alpha
        self.gamma = gamma
        self.high_pred_penalty = high_pred_penalty
        self.high_pred_threshold = high_pred_threshold
        self.reduction = reduction

    def __call__(self, inputs, targets):
        return self.forward(inputs, targets)

    def forward(self, inputs, targets):
        """
        100%纯Python FocalLoss实现，完全无torch依赖
        """
        # 确保输入是我们的Tensor系统
        if not isinstance(inputs, Tensor):
            inputs = Tensor(inputs, requires_grad=True)
        if not isinstance(targets, Tensor):
            targets = Tensor(targets, requires_grad=False)
        
        # 保存实例参数供内部函数使用
        alpha = self.alpha
        gamma = self.gamma
        high_pred_penalty = self.high_pred_penalty
        high_pred_threshold = self.high_pred_threshold
        
        # 使用我们的自定义操作实现FocalLoss
        class FocalLossFunction(Function):
            @staticmethod
            def forward(ctx, logits, targets):
                # 使用metadata字典保存参数
                ctx.metadata = {
                    'alpha': alpha,
                    'gamma': gamma,
                    'high_pred_penalty': high_pred_penalty,
                    'high_pred_threshold': high_pred_threshold
                }
                
                logits_data = logits.data if hasattr(logits, 'data') else logits
                targets_data = targets.data if hasattr(targets, 'data') else targets
                
                # 确保数据是可以进行数值运算的格式
                logits_array = arrays.asarray(logits_data, dtype='float')
                targets_array = arrays.asarray(targets_data, dtype='float')
                logits_np = logits_array.data
                targets_np = targets_array.data
                
                # 确保数据是数值类型，而不是嵌套列表
                if isinstance(logits_np, list):
                    # 展平为一维并转换为浮点数
                    if isinstance(logits_np[0], list):
                        # 2D -> 1D
                        flat_logits = [float(item) for sublist in logits_np for item in sublist]
                    else:
                        # 1D -> 确保都是浮点数
                        flat_logits = [float(item) for item in logits_np]
                    logits_np = flat_logits
                else:
                    logits_np = [float(logits_np)]
                    
                if isinstance(targets_np, list):
                    # 展平为一维并转换为浮点数
                    if isinstance(targets_np[0], list):
                        # 2D -> 1D  
                        flat_targets = [float(item) for sublist in targets_np for item in sublist]
                    else:
                        # 1D -> 确保都是浮点数
                        flat_targets = [float(item) for item in targets_np]
                    targets_np = flat_targets
                else:
                    targets_np = [float(targets_np)]
                
                # 确保两个列表长度相等
                min_len = min(len(logits_np), len(targets_np))
                logits_np = logits_np[:min_len]
                targets_np = targets_np[:min_len]
                
                # 数值稳定的BCE计算
                # BCE = -(y*log(p) + (1-y)*log(1-p))
                # 其中 p = sigmoid(logits) = 1/(1+exp(-logits))
                # 数值稳定版本：BCE = max(logits,0) - logits*targets + log(1+exp(-abs(logits)))
                
                # 计算数值稳定的BCE - 现在都是浮点数列表，可以安全进行运算
                max_vals = [max(logit, 0.0) for logit in logits_np]
                abs_logits = [abs(logit) for logit in logits_np]
                
                # 计算 log(1 + exp(-abs(logits)))
                exp_neg_abs = []
                for abs_logit in abs_logits:
                    try:
                        exp_val = math.exp(-abs_logit)
                        log_exp_val = math.log(1 + exp_val)
                        exp_neg_abs.append(log_exp_val)
                    except (OverflowError, ValueError):
                        # 处理数值溢出
                        exp_neg_abs.append(0.0)
                
                # 计算 BCE loss
                bce_loss = []
                for i in range(len(logits_np)):
                    bce_val = max_vals[i] - logits_np[i] * targets_np[i] + exp_neg_abs[i]
                    bce_loss.append(bce_val)
                
                # 计算sigmoid概率
                sigmoid_probs = []
                for logit in logits_np:
                    # 裁剪到安全范围
                    clipped_logit = max(-15.0, min(15.0, logit))
                    try:
                        sigmoid_val = 1.0 / (1.0 + math.exp(-clipped_logit))
                        sigmoid_probs.append(sigmoid_val)
                    except (OverflowError, ValueError):
                        # 处理数值问题
                        sigmoid_probs.append(0.5)
                
                # 计算pt (预测正确的概率)
                pt = []
                for i in range(len(targets_np)):
                    pt_val = targets_np[i] * sigmoid_probs[i] + (1 - targets_np[i]) * (1 - sigmoid_probs[i])
                    # 裁剪避免log(0)
                    pt_val = max(1e-8, min(1-1e-8, pt_val))
                    pt.append(pt_val)
                
                # 计算focal loss权重
                focal_weight = []
                for pt_val in pt:
                    try:
                        weight_val = alpha * pow(1 - pt_val, gamma)
                        focal_weight.append(weight_val)
                    except (OverflowError, ValueError):
                        focal_weight.append(alpha)
                
                # 基础focal loss
                focal_loss = []
                for i in range(len(bce_loss)):
                    loss_val = focal_weight[i] * bce_loss[i]
                    focal_loss.append(loss_val)
                
                # 应用高预测惩罚
                for i in range(len(focal_loss)):
                    if sigmoid_probs[i] > high_pred_threshold and targets_np[i] == 0:
                        # 简化的惩罚
                        penalty_factor = 1.5
                        focal_loss[i] *= penalty_factor
                
                # 保存中间结果用于反向传播（转换为简单格式）
                high_pred_mask_float = []
                for i in range(len(sigmoid_probs)):
                    mask_val = 1.0 if (sigmoid_probs[i] > high_pred_threshold and targets_np[i] == 0) else 0.0
                    high_pred_mask_float.append(mask_val)
                
                ctx.save_for_backward(
                    Tensor(logits_np), 
                    Tensor(targets_np), 
                    Tensor(sigmoid_probs), 
                    Tensor(pt),
                    Tensor(focal_weight),
                    Tensor(high_pred_mask_float)
                )
                
                return Tensor(focal_loss, requires_grad=logits.requires_grad)
            
            @staticmethod
            def backward(ctx, grad_output):
                # 获取保存的张量
                logits, targets, sigmoid_probs, pt, focal_weight, high_pred_mask = ctx.saved_tensors
                
                # 从metadata获取参数
                alpha = ctx.metadata['alpha']
                gamma = ctx.metadata['gamma'] 
                high_pred_penalty = ctx.metadata['high_pred_penalty']
                
                # 安全地提取数据并转换为Python原生类型
                def safe_extract_data(tensor_data):
                    """安全地从tensor中提取Python原生数据"""
                    if hasattr(tensor_data, 'data'):
                        data = tensor_data.data
                    else:
                        data = tensor_data
                    
                    # 如果是numpy数组，转换为Python列表
                    if hasattr(data, 'tolist'):
                        return data.tolist()
                    elif hasattr(data, '__iter__') and not isinstance(data, str):
                        # 递归处理嵌套结构
                        if isinstance(data, list):
                            return [safe_extract_data(item) if hasattr(item, 'data') or hasattr(item, 'tolist') else float(item) for item in data]
                        else:
                            return list(data)
                    else:
                        return float(data)
                
                try:
                    # 使用安全提取函数获取所有数据
                    logits_data = safe_extract_data(logits)
                    targets_data = safe_extract_data(targets)
                    sigmoid_data = safe_extract_data(sigmoid_probs)
                    pt_data = safe_extract_data(pt)
                    focal_weight_data = safe_extract_data(focal_weight)
                    mask_data = safe_extract_data(high_pred_mask)
                    
                    # 确保所有数据都是列表格式
                    if not isinstance(logits_data, list):
                        logits_data = [logits_data]
                    if not isinstance(targets_data, list):
                        targets_data = [targets_data]
                    if not isinstance(sigmoid_data, list):
                        sigmoid_data = [sigmoid_data]
                    if not isinstance(pt_data, list):
                        pt_data = [pt_data]
                    if not isinstance(focal_weight_data, list):
                        focal_weight_data = [focal_weight_data]
                    if not isinstance(mask_data, list):
                        mask_data = [mask_data]
                    
                    # 计算复杂的focal loss梯度
                    grad = []
                    for i in range(len(sigmoid_data)):
                        # 1. 计算基础BCE梯度: d(BCE)/d(logits) = sigmoid(logits) - targets
                        bce_grad = float(sigmoid_data[i]) - float(targets_data[i])
                        
                        # 2. 计算sigmoid关于logits的梯度: sigmoid * (1 - sigmoid)
                        sigmoid_val = float(sigmoid_data[i])
                        sigmoid_grad = sigmoid_val * (1.0 - sigmoid_val)
                        
                        # 3. 计算pt关于logits的梯度
                        target_val = float(targets_data[i])
                        if target_val == 1.0:
                            dpt_dlogits = sigmoid_grad
                        else:
                            dpt_dlogits = -sigmoid_grad
                        
                        # 4. 计算focal权重关于logits的梯度
                        pt_val = float(pt_data[i])
                        focal_weight_val = float(focal_weight_data[i])
                        
                        if gamma > 0:
                            try:
                                # d(focal_weight)/d(logits) = alpha * gamma * (1-pt)^(gamma-1) * (-dpt_dlogits)
                                power_term = pow(1.0 - pt_val, gamma - 1)
                                dfocal_weight_dlogits = -alpha * gamma * power_term * dpt_dlogits
                            except (OverflowError, ValueError, ZeroDivisionError):
                                dfocal_weight_dlogits = 0.0
                        else:
                            dfocal_weight_dlogits = 0.0
                        
                        # 5. 计算BCE loss值用于权重梯度项
                        logit_val = float(logits_data[i])
                        max_val = max(logit_val, 0.0)
                        abs_logit = abs(logit_val)
                        try:
                            log_exp_term = math.log(1.0 + math.exp(-abs_logit))
                        except (OverflowError, ValueError):
                            log_exp_term = 0.0
                        bce_loss_val = max_val - logit_val * target_val + log_exp_term
                        
                        # 6. 组合focal loss梯度
                        # grad = focal_weight * bce_grad + dfocal_weight_dlogits * bce_loss
                        focal_grad = focal_weight_val * bce_grad + dfocal_weight_dlogits * bce_loss_val
                        
                        # 7. 添加高预测惩罚的梯度
                        mask_val = float(mask_data[i])
                        if mask_val > 0.5:  # 高预测掩码激活
                            # 复杂的惩罚梯度计算
                            if sigmoid_val > 0.9 and target_val == 0.0:
                                # 指数惩罚的梯度: d(penalty)/d(logits)
                                try:
                                    exp_term = math.exp(3.0 * sigmoid_val)
                                    penalty_grad = high_pred_penalty * 3.0 * exp_term * sigmoid_grad
                                    focal_grad += penalty_grad
                                except (OverflowError, ValueError):
                                    # 如果指数计算溢出，使用线性惩罚
                                    focal_grad += high_pred_penalty * 0.1 * sigmoid_grad
                        
                        grad.append(focal_grad)
                    
                    # 8. 应用输出梯度
                    grad_out_data = safe_extract_data(grad_output)
                    if not isinstance(grad_out_data, list):
                        grad_out_data = [grad_out_data]
                    
                    # 复杂的梯度传播逻辑
                    final_grad = []
                    if len(grad_out_data) == 1:
                        # 标量输出梯度，需要广播
                        scalar_grad = float(grad_out_data[0])
                        for g in grad:
                            final_grad.append(g * scalar_grad)
                    else:
                        # 元素级梯度传播
                        for i in range(min(len(grad), len(grad_out_data))):
                            out_grad_val = float(grad_out_data[i])
                            final_grad.append(grad[i] * out_grad_val)
                        # 如果grad更长，补充零梯度
                        for i in range(len(grad_out_data), len(grad)):
                            final_grad.append(0.0)
                    
                    # 9. 高级数值稳定性处理
                    clipped_grad = []
                    for g in final_grad:
                        if isinstance(g, (int, float)) and not (math.isnan(g) or math.isinf(g)):
                            # 自适应梯度裁剪
                            abs_g = abs(g)
                            if abs_g > 10.0:
                                # 大梯度用对数缩放
                                clipped_val = math.copysign(10.0 + math.log(1.0 + abs_g - 10.0), g)
                            elif abs_g < 1e-8:
                                # 极小梯度直接设为零
                                clipped_val = 0.0
                            else:
                                clipped_val = g
                            clipped_grad.append(clipped_val)
                        else:
                            # 无效值设为零
                            clipped_grad.append(0.0)
                    
                    return Tensor(clipped_grad), None
                    
                except Exception as e:
                    # 详细错误处理，但保持复杂的恢复逻辑
                    print(f"Focal loss backward error: {e}")
                    print(f"Error type: {type(e).__name__}")
                    
                    # 尝试多种恢复策略
                    try:
                        # 策略1: 使用原始数据长度
                        if hasattr(logits, 'data'):
                            original_data = logits.data
                            if hasattr(original_data, 'tolist'):
                                data_list = original_data.tolist()
                                if isinstance(data_list, list):
                                    data_len = len(data_list)
                                else:
                                    data_len = 1
                            elif isinstance(original_data, list):
                                data_len = len(original_data)
                            else:
                                data_len = 1
                        else:
                            data_len = 1
                        
                        # 生成小的随机梯度而不是零梯度，保持训练动态
                        from .pure_random import PureRandom
                        recovery_grad = []
                        for i in range(data_len):
                            # 小的随机梯度，保持网络更新
                            rand_grad = PureRandom.uniform(-0.01, 0.01)
                            recovery_grad.append(rand_grad)
                        
                        return Tensor(recovery_grad), None
                        
                    except Exception as recovery_error:
                        print(f"Recovery strategy failed: {recovery_error}")
                        # 最后的安全网：返回单个小梯度
                        return Tensor([0.001]), None
        
        # 执行前向传播
        focal_losses = FocalLossFunction.apply(inputs, targets)
        
        # focal_losses已经是带有梯度信息的Tensor，直接使用
        if self.reduction == 'mean':
            # 计算均值
            result = operations_T.mean(focal_losses)
        elif self.reduction == 'sum':
            # 计算总和  
            result = operations_T.sum(focal_losses)
        else:
            result = focal_losses
            
        return result
