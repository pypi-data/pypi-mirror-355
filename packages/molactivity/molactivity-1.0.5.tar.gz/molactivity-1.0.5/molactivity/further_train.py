from .tensor_T import Tensor
from .Transformer import MolecularTransformer
from .optimizer_T import Adam
from .model_save_load import load, dump
from .new_focal_loss import FocalLoss
from .operations_T import sigmoid
from .autograd_T import no_grad

def flatten_nested_dict(d, prefix="", separator="."):
    """递归展开嵌套字典"""
    if d is None:
        print(f"[ERROR] flatten_nested_dict: 输入字典为None")
        return {}
        
    if not isinstance(d, dict):
        print(f"[ERROR] flatten_nested_dict: 输入不是字典类型，而是: {type(d)}")
        return {}
    
    flattened = {}
    try:
        for key, value in d.items():
            new_key = f"{prefix}{separator}{key}" if prefix else key
            if isinstance(value, dict):
                # 递归展开嵌套字典
                nested_result = flatten_nested_dict(value, new_key, separator)
                if nested_result is not None:
                    flattened.update(nested_result)
            else:
                flattened[new_key] = value
    except Exception as e:
        print(f"[ERROR] flatten_nested_dict: 处理字典时发生错误: {e}")
        print(f"[DEBUG] 问题字典内容: {d}")
        return {}
        
    return flattened

def load_model_for_continue_training(network, optimizer, model_file):
    """加载已训练的模型和优化器状态，用于继续训练"""
    print(f"🔄 尝试加载模型: {model_file}")
    try:
        # 使用pickle加载
        with open(model_file, 'rb') as f:
            saved_state = load(f)
        
        print(f"✅ 模型文件加载成功")
        
        # 加载模型参数
        saved_model_params = saved_state['model_parameters']
        flattened_params = flatten_nested_dict(saved_model_params)
        
        # 将保存的参数加载到网络中
        param_dict = dict(network.named_parameters())
        loaded_count = 0
        
        for name, param in param_dict.items():
            if name in flattened_params:
                saved_param = flattened_params[name]
                
                # 处理pickle安全格式
                if isinstance(saved_param, dict) and saved_param.get('__type__') == 'FinalArrayCompatible':
                    from .final_array import FinalArrayCompatible
                    restored_data = FinalArrayCompatible(
                        saved_param['data'], 
                        saved_param['shape'], 
                        saved_param['dtype']
                    )
                    param.data = restored_data
                elif isinstance(saved_param, Tensor):
                    param.data = saved_param.data
                elif hasattr(saved_param, 'shape'):  
                    param.data = saved_param
                else:
                    from . import arrays
                    param.data = arrays.array(saved_param)
                loaded_count += 1
        
        print(f"✅ 成功加载 {loaded_count}/{len(param_dict)} 个模型参数")
        
        # 加载优化器状态（如果存在）
        if 'optimizer_state' in saved_state and saved_state['optimizer_state']:
            try:
                optimizer.load_state_dict(saved_state['optimizer_state'])
                print("✅ 优化器状态加载成功")
            except Exception as e:
                print(f"⚠️ 优化器状态加载失败，将使用默认状态: {e}")
        
        # 获取之前的训练轮数
        previous_epochs = saved_state.get('epoch', 0)
        print(f"📊 之前训练轮数: {previous_epochs}")
        
        return True, previous_epochs
        
    except Exception as e:
        print(f"❌ 模型加载失败: {str(e)}")
        return False, 0

def continue_train(model_file, data_handler, additional_epochs=2, activation='gelu', 
                  optimal_parameters=None, network_index=0, new_model_suffix='_continued'):
    """
    继续训练已有的模型
    
    参数:
    - model_file: 要加载的模型文件路径
    - data_handler: 训练数据处理器
    - additional_epochs: 额外训练的轮数
    - activation: 激活函数类型
    - optimal_parameters: 优化参数配置
    - network_index: 网络索引（用于日志）
    - new_model_suffix: 新模型文件的后缀
    """
    print(f"🔄 开始继续训练模型: {model_file}")
    
    # 使用默认参数如果没有提供
    if optimal_parameters is None:
        optimal_parameters = {
            'learning_rate': 0.001,
            'transformer_depth': 2,
            'attention_heads': 2,
            'hidden_dimension': 64
        }
    
    # 创建网络架构（与训练时相同）
    print(f"🎯 创建网络架构 - 激活函数: {activation.upper()}")
    network = MolecularTransformer(
        input_features=2048,
        output_features=1, 
        embedding_size=128,
        layer_count=optimal_parameters['transformer_depth'],
        head_count=optimal_parameters['attention_heads'], 
        hidden_size=optimal_parameters['hidden_dimension'], 
        dropout_rate=0.1,
        activation=activation
    )
    
    # 创建优化器
    optimizer = Adam(network.parameters(), lr=optimal_parameters['learning_rate'])
    
    # 加载预训练模型
    success, previous_epochs = load_model_for_continue_training(network, optimizer, model_file)
    
    if not success:
        print("❌ 无法加载模型，继续训练失败")
        return None
    
    # 开始继续训练
    print(f"🚀 开始继续训练 {additional_epochs} 个轮数")
    print(f"📊 从第 {previous_epochs + 1} 轮开始")
    
    criterion = FocalLoss(alpha=0.25, gamma=2.0, high_pred_penalty=5.0, reduction='mean')
    
    for epoch in range(additional_epochs):
        current_epoch = previous_epochs + epoch + 1
        print(f"\n=== 继续训练 Epoch {current_epoch} ===")
        
        epoch_losses = []
        batch_count = 0
        high_pred_false_count = 0
        very_high_pred_false_count = 0 
        extreme_high_pred_false_count = 0
        all_predictions = []
        
        # 训练每个批次
        for batch_idx, (features, labels) in enumerate(data_handler):
            batch_count += 1
            
            # 确保输入数据是我们的自定义Tensor
            if not isinstance(features, Tensor):
                features = Tensor(features, requires_grad=False)
            if not isinstance(labels, Tensor):
                labels = Tensor(labels, requires_grad=False)
            
            # 前向传播
            outputs = network(features)  
            
            # 确保标签维度正确
            if labels.data.ndim > 1:
                labels = Tensor(labels.data.squeeze(), requires_grad=False)
            
            # 计算损失
            loss = criterion(outputs.squeeze(), labels)
            
            # 异常损失检测
            loss_value = loss.data.item() if hasattr(loss.data, 'item') else float(loss.data)
            if loss_value > 5.0: 
                print(f"⚠️ 异常高损失 {loss_value:.4f}，跳过参数更新")
                continue
            
            # 反向传播
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            epoch_losses.append(loss_value)
            
            # 计算预测准确性统计
            with no_grad():
                predictions = sigmoid(outputs.squeeze())
                all_predictions.extend(predictions.data.flatten().tolist())
                
                pred_data = predictions.data.flatten()
                label_data = labels.data.flatten()
                
                for pred, label in zip(pred_data, label_data):
                    if pred > 0.9 and label < 0.5:
                        high_pred_false_count += 1
                    if pred > 0.95 and label < 0.5:
                        very_high_pred_false_count += 1
                    if pred > 0.98 and label < 0.5:
                        extreme_high_pred_false_count += 1
            
            # 每10个批次打印损失
            if batch_count % 10 == 0:
                print(f"    批次 {batch_count}, 损失: {loss_value:.4f}")
        
        # Epoch总结
        avg_loss = sum(epoch_losses) / len(epoch_losses) if epoch_losses else 0
        print(f"  Epoch [{current_epoch}], 平均损失: {avg_loss:.4f}, "
              f"High Pred False: {high_pred_false_count}, "
              f"Very High Pred False: {very_high_pred_false_count}, "
              f"Extreme High Pred False: {extreme_high_pred_false_count}")
        
        # 打印预测值范围
        if all_predictions:
            min_pred = min(all_predictions)
            max_pred = max(all_predictions)
            print(f"  [DEBUG] Epoch {current_epoch} 预测值范围: [{min_pred:.4f}, {max_pred:.4f}]")
    
    # 生成新的模型文件名
    base_name = model_file.rsplit('.', 1)[0]  # 移除扩展名
    extension = model_file.rsplit('.', 1)[1] if '.' in model_file else 'dict'
    new_model_file = f"{base_name}{new_model_suffix}.{extension}"
    
    # 保存继续训练后的模型
    print(f"💾 保存继续训练后的模型到: {new_model_file}")
    
    # 获取模型参数，并添加验证
    model_params = network.state_dict()
    print(f"[DEBUG] 获取到模型参数，类型: {type(model_params)}")
    
    # 验证模型参数不为空
    if model_params is None:
        print(f"❌ 错误：网络状态字典为None")
        return None
    
    if not isinstance(model_params, dict):
        print(f"❌ 错误：网络状态字典不是字典类型，而是: {type(model_params)}")
        return None
        
    if len(model_params) == 0:
        print(f"❌ 错误：网络状态字典为空")
        return None
    
    print(f"[DEBUG] 模型参数验证通过，包含 {len(model_params)} 个模块")
    
    # 获取优化器状态
    try:
        optimizer_state = optimizer.state_dict()
        print(f"[DEBUG] 获取优化器状态成功")
    except Exception as e:
        print(f"⚠️ 获取优化器状态失败: {e}，将使用空状态")
        optimizer_state = {}
    
    save_data = {
        'model_parameters': model_params,
        'optimizer_state': optimizer_state,
        'epoch': previous_epochs + additional_epochs
    }
    
    try:
        with open(new_model_file, 'wb') as f:
            dump(save_data, f)
        print(f"✅ 模型保存成功: {new_model_file}")
        
        # 验证保存的文件（可选步骤，失败不影响整体流程）
        print(f"[DEBUG] 验证保存的文件...")
        try:
            with open(new_model_file, 'rb') as f:
                test_load = load(f)
                if 'model_parameters' in test_load and test_load['model_parameters'] is not None:
                    print(f"[DEBUG] 文件验证成功，包含 {len(test_load['model_parameters'])} 个模块参数")
                else:
                    print(f"⚠️ 文件验证发现问题：model_parameters 为 None 或缺失，但文件已保存")
        except Exception as verification_error:
            print(f"⚠️ 文件验证过程出现错误: {verification_error}")
            print(f"   但模型文件已成功保存到: {new_model_file}")
            print(f"   可以尝试使用该文件进行预测")
                
    except Exception as e:
        print(f"❌ 模型保存失败: {e}")

        return None
    
    print(f"🎉 继续训练完成！")
    print(f"📊 总训练轮数: {previous_epochs + additional_epochs}")
    print(f"💾 新模型文件: {new_model_file}")
    
    return network, new_model_file 