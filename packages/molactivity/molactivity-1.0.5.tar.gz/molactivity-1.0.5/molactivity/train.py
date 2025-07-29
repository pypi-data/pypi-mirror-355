
from .pure_data_loader import prepare_pure_training_dataset
from .Transformer import MolecularTransformer
from .operations_T import sigmoid
from .autograd_T import no_grad
from .optimizer_T import Adam
from .new_focal_loss import FocalLoss
from .tensor_T import Tensor  # 确保使用自定义Tensor
from .further_train import continue_train  # 导入继续训练功能

# 在文件顶部添加配置参数（默认值）
DEFAULT_CONTINUE_TRAIN = False  # 默认从头训练
DEFAULT_MODEL_FILE = "model_1.dict"  
DEFAULT_ADDITIONAL_EPOCHS = 1


def initialize_network_and_optimizer(optimal_parameters, activation='gelu'):
    """Initialize network and optimizer with optimal parameters"""
    network = MolecularTransformer(
        input_features=2048,#2048
        output_features=1, 
        embedding_size=128,#512
        layer_count=optimal_parameters['transformer_depth'],
        head_count=optimal_parameters['attention_heads'], 
        hidden_size=optimal_parameters['hidden_dimension'], 
        dropout_rate=0.1,
        activation=activation  # 新增激活函数参数
    )
    optimizer = Adam(network.parameters(), lr=optimal_parameters['learning_rate'])
    return network, optimizer

def conduct_individual_training(network, data_handler, optimizer, network_index, model_version, unique_id):
    """Train individual network"""
    print(f"=== 开始训练网络 {unique_id+1} ===")
    
    criterion = FocalLoss(alpha=0.25, gamma=2.0, high_pred_penalty=5.0, reduction='mean')  # 降低惩罚系数
    
    for epoch in range(1):  # 训练2个epoch
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
                print(f"异常高损失 {loss_value:.4f}，跳过参数更新")
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
        
            print(f"    批次 {batch_count}, 损失: {loss_value:.4f}")
        
        avg_loss = sum(epoch_losses) / len(epoch_losses) if epoch_losses else 0
        print(f"  Epoch {epoch+1}, 平均损失: {avg_loss:.4f}, "
              f"High Pred False: {high_pred_false_count}, "
              f"Very High Pred False: {very_high_pred_false_count}, "
              f"Extreme High Pred False: {extreme_high_pred_false_count}")
        
        # 打印预测值范围
        if all_predictions:
            min_pred = min(all_predictions)
            max_pred = max(all_predictions)
            print(f"Epoch {epoch+1} 预测值范围: [{min_pred:.4f}, {max_pred:.4f}]")
    
    model_filename = f'model_{unique_id+1}.dict'
    
    from .model_save_load import dump
    save_data = {
        'model_parameters': network.state_dict(),
        'optimizer_state': optimizer.state_dict(),
        'epoch': 2
    }
    with open(model_filename, 'wb') as f:
        dump(save_data, f)

    
    print(f"网络 {unique_id+1} 训练完成，模型已保存到 {model_filename}")
    return network

def training():
    """Main function for network training - Sequential version"""
    
    try:
        from .command_line_parser import CommandLineProcessor  
        
        config_parser = CommandLineProcessor(description='Molecular property prediction')
        config_parser.add_argument('--num_networks', type=int, default=1, 
                                 help='Quantity of networks to train')
        config_parser.add_argument('--activation', type=str, default='gelu', choices=['relu', 'gelu'],
                                 help='选择激活函数: relu 或 gelu (默认: gelu)')
        # 添加继续训练参数
        config_parser.add_argument('--continue_training', action='store_true',
                                 help=f'继续训练已有模型（默认: {DEFAULT_CONTINUE_TRAIN}）')
        config_parser.add_argument('--model_file', type=str, default=DEFAULT_MODEL_FILE,
                                 help=f'要继续训练的模型文件路径（默认: {DEFAULT_MODEL_FILE}）')
        config_parser.add_argument('--additional_epochs', type=int, default=DEFAULT_ADDITIONAL_EPOCHS,
                                 help=f'继续训练的额外轮数（默认: {DEFAULT_ADDITIONAL_EPOCHS}）')
        parameters = config_parser.parse_args()

        # 确定最终使用的参数（命令行参数优先）
        use_continue = parameters.continue_training or DEFAULT_CONTINUE_TRAIN
        model_file = parameters.model_file if parameters.model_file != DEFAULT_MODEL_FILE else DEFAULT_MODEL_FILE
        add_epochs = parameters.additional_epochs if parameters.additional_epochs != DEFAULT_ADDITIONAL_EPOCHS else DEFAULT_ADDITIONAL_EPOCHS

        if use_continue:
            print(f"加载模型: {model_file}")
            print(f"额外训练轮数: {add_epochs}")
        else:
            print(f"训练网络数量: {parameters.num_networks}")
        print(f"激活函数: {parameters.activation.upper()}")

        print("正在准备数据集...")
        data_handler = prepare_pure_training_dataset('training_dataset.csv', fingerprint_type='Morgan', 
                                                   batch_size=32, shuffle=False, balance_data=True)
        print("数据集准备完成")
        
        # 优化参数配置
        optimal_parameters = {
            'learning_rate': 0.001,
            'transformer_depth': 2,   #改成4（原来6）
            'attention_heads': 2, 
            'hidden_dimension': 64   #改成512（原来2048）
        }

        if use_continue:
            # 继续训练逻辑
            result = continue_train(
                model_file=model_file,
                data_handler=data_handler,
                additional_epochs=add_epochs,
                activation=parameters.activation,
                optimal_parameters=optimal_parameters,
                new_model_suffix='_continued'
            )
            
            if result is not None:
                trained_network, new_model_file = result
                print(f"继续训练完成")
                print(f"新模型文件: {new_model_file}")
            else:
                print(f"继续训练失败")
        else:
            # 原始的从头开始训练逻辑
            print("正在初始化网络...")
            trained_networks = []
            
            for network_idx in range(parameters.num_networks):
                print(f'\n--- 初始化网络 {network_idx+1} ---')
                network, optimizer = initialize_network_and_optimizer(optimal_parameters, parameters.activation)
                
                # 训练此网络
                trained_network = conduct_individual_training(
                    network, data_handler, optimizer, 0, 2, network_idx
                )
                trained_networks.append(trained_network)

            print(f"所有训练完成！成功训练了 {len(trained_networks)} 个网络")
            print(f"模型文件: {[f'model_{i+1}.dict' for i in range(len(trained_networks))]}")
        
    except Exception as e:

        raise

if __name__ == "__main__":
    training()
