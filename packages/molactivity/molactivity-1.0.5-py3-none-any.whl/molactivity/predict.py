
from .tensor_T import Tensor
from .operations_T import sigmoid
from .pure_data_loader import prepare_pure_predicting_dataset
from .autograd_T import no_grad
from .Transformer import MolecularTransformer
from .model_save_load import load
from . import arrays
from . import data_manager as dm

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
                nested_result = flatten_nested_dict(value, new_key, separator)
                if nested_result is not None:
                    flattened.update(nested_result)
            else:
                flattened[new_key] = value
    except Exception as e:
        return {}
        
    return flattened

def load_trained_network_pure(network, model_file):
    """Load trained network model parameters using pure Python approach"""
    print(f"开始加载模型文件: {model_file}")

     
    try:
        with open(model_file, 'rb') as f:
            saved_state = load(f)
                
        print(f"模型加载完成")
            
        if 'model_parameters' not in saved_state:
            print(f"保存的状态中缺少 'model_parameters' 键")
            print(f"可用键: {list(saved_state.keys()) if saved_state else 'saved_state为None'}")
            return False
                
        if saved_state['model_parameters'] is None:
            print(f"模型参数为None")
            return False
            
        saved_parameters = saved_state['model_parameters']
        if not isinstance(saved_parameters, dict):
            print(f"模型参数应该是字典类型，但得到: {type(saved_parameters)}")
            return False
                
        if len(saved_parameters) == 0:
            print(f"模型参数字典为空")
            return False
                
        print(f"加载了 {len(saved_parameters)} 个模块")
            
        try:
            flattened_params = flatten_nested_dict(saved_parameters)
            if flattened_params is None:
                print(f"[ERROR] 参数展开结果为None")
                return False
            print(f"[DEBUG] 展开后总参数数: {len(flattened_params)}")
        except AttributeError as e:
            print(f"参数展开失败: {e}")
            print(f"问题参数类型: {type(saved_parameters)}")
            print(f"问题参数内容: {saved_parameters}")
            return False
        except Exception as e:
            print(f"参数展开时发生未知错误: {e}")

            return False
            
        param_dict = dict(network.named_parameters())
        print(f"[DEBUG] 网络参数数: {len(param_dict)}")
            
        loaded_count = 0
        missing_params = []
        for name, param in param_dict.items():
            if name in flattened_params:
                saved_param = flattened_params[name]
                    
                if isinstance(saved_param, dict) and saved_param.get('__type__') == 'FinalArrayCompatible':
                        # 重建FinalArrayCompatible对象
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
                    if hasattr(saved_param, 'data'):
                        array_data = saved_param.data
                        param.data = arrays.asarray_numpy_compatible(array_data).data
                    else:
                        param.data = arrays.asarray_numpy_compatible(saved_param).data
                loaded_count += 1
            else:
                missing_params.append(name)
            
        print(f"成功加载 {loaded_count}/{len(param_dict)} 个参数")
        if missing_params:
            print(f"[WARNING] 未找到的参数数量: {len(missing_params)}")
            if len(missing_params) <= 5:  # 只显示前5个缺失的参数
                for mp in missing_params:
                    print(f"[WARNING] 缺失参数: {mp}")
                        
        return loaded_count > 0  # 只要加载了至少一些参数就算成功
            
    except Exception as e:
        print(f"[ERROR] 模型加载失败: {str(e)}")
        return False


def create_network():
    """创建与训练时相同的网络架构"""
    print("[DEBUG] 创建网络...")
    
    network = MolecularTransformer(
        input_features=2048, 
        output_features=1, 
        embedding_size=128, #512
        layer_count=2,
        head_count=2,  #4
        hidden_size=64, #512
        dropout_rate=0.1
    )
    
    return network

def generate_predictions_pure(model, data_provider):
    """Generate predictions using pure Python model"""
    print("[DEBUG] 开始生成预测")
    model.eval()
    predictions = []
    

    
    with no_grad():
        for batch_idx, (features, _) in enumerate(data_provider):
            print(f"\n开始处理批次 {batch_idx + 1}")
            
            if features is None:
                print(f"[WARNING] 批次 {batch_idx + 1} 的特征为空")
                continue
            
            
            # 确保输入是我们的自定义Tensor
            if not isinstance(features, Tensor):
                features = Tensor(features, requires_grad=False)
            
            print(f"    开始模型推理...")
            
            try:
                outputs = model(features)
                
            except Exception as e:
                print(f"    模型推理失败: {e}")

                break
            
            try:
                outputs_squeezed = outputs.squeeze()
                
                # 确保输出数据格式正确
                if hasattr(outputs_squeezed, 'data') and hasattr(outputs_squeezed.data, 'dtype'):
                    probs_tensor = sigmoid(outputs_squeezed)
                else:
                    # 如果数据格式有问题，尝试重新构造Tensor
                    safe_data = arrays.asarray_numpy_compatible(outputs_squeezed.data).data
                    safe_tensor = Tensor(safe_data, requires_grad=False)
                    probs_tensor = sigmoid(safe_tensor)
            except Exception as sigmoid_error:
                probs_tensor = Tensor([0.5] * outputs.shape[0] if hasattr(outputs, 'shape') and len(outputs.shape) > 0 else [0.5], requires_grad=False)
            
            # 安全地将结果转换为列表并添加到预测列表
            try:
                if hasattr(probs_tensor.data, 'flatten'):
                    batch_predictions = probs_tensor.data.flatten().tolist()
                elif hasattr(probs_tensor.data, 'tolist'):
                    batch_predictions = probs_tensor.data.tolist()
                elif isinstance(probs_tensor.data, (list, tuple)):
                    batch_predictions = list(probs_tensor.data)
                else:
                    # 检查是否是标量值
                    is_scalar = isinstance(probs_tensor.data, (int, float, complex)) or (hasattr(probs_tensor.data, 'ndim') and probs_tensor.data.ndim == 0)
                    if is_scalar:
                        # 确保标量值可以转换为float
                        try:
                            scalar_val = float(probs_tensor.data)
                            batch_predictions = [scalar_val]
                        except (TypeError, ValueError):
                            print(f"   无法将标量值转换为float: {type(probs_tensor.data)}")
                            batch_predictions = [0.0]  # 使用默认值
                    else:
                        # 尝试转换为数组然后提取
                        try:
                            data_array = arrays.asarray_numpy_compatible(probs_tensor.data)
                            batch_predictions = data_array.data.flatten().tolist()
                        except Exception as conv_error:
                            print(f"   数据转换失败: {conv_error}")
                            batch_predictions = [0.0]  # 使用默认值
            except Exception as e:
                print(f"   批次预测处理失败: {e}")
                batch_predictions = [0.0]  # 使用默认值
            
            predictions.extend(batch_predictions)
            
            print(f"   批次 {batch_idx + 1} 处理完成，预测数量: {len(batch_predictions)}")
            print(f"   累计预测数量: {len(predictions)}")
    
    print(f"\n预测处理完成")
    print(f"总预测数量: {len(predictions)}")
    if predictions:
        print(f"最终预测值范围: [{min(predictions):.4f}, {max(predictions):.4f}]")
    return predictions

def analyze_predictions_pure(predictions):
    """分析预测结果"""
    if not predictions:
        print("[ERROR] 没有预测结果可分析")
        return
    
    print(f"\n预测结果分析:")
    print(f"总预测数量: {len(predictions)}")
    print(f"预测值范围: [{min(predictions):.4f}, {max(predictions):.4f}]")
    print(f"平均预测值: {sum(predictions)/len(predictions):.4f}")
    
    # 预测分布统计
    very_high = sum(1 for p in predictions if p > 0.9)
    high = sum(1 for p in predictions if 0.8 < p <= 0.9)
    medium = sum(1 for p in predictions if 0.5 < p <= 0.8)
    low = sum(1 for p in predictions if 0.2 < p <= 0.5)
    very_low = sum(1 for p in predictions if p <= 0.2)
    
    print(f"\n预测分布:")
    print(f"  极高 (>0.9): {very_high} ({very_high/len(predictions)*100:.1f}%)")
    print(f"  高 (0.8-0.9): {high} ({high/len(predictions)*100:.1f}%)")
    print(f"  中 (0.5-0.8): {medium} ({medium/len(predictions)*100:.1f}%)")
    print(f"  低 (0.2-0.5): {low} ({low/len(predictions)*100:.1f}%)")
    print(f"  极低 (<=0.2): {very_low} ({very_low/len(predictions)*100:.1f}%)")

def save_predictions_to_csv(predictions, output_file='dataset_with_predictions_pure.csv'):
    """保存预测结果到CSV文件"""
    print(f"[DEBUG] 开始保存预测结果到: {output_file}")
    
    try:
        # 读取原始预测数据集
        original_data = dm.read_csv('predicting_dataset.csv')
        
        # 确保预测数量与原始数据数量匹配
        if len(predictions) != len(original_data):
            print(f"[WARNING] 预测数量({len(predictions)})与原始数据数量({len(original_data)})不匹配")
            # 如果预测数量少于原始数据，用0.0填充
            while len(predictions) < len(original_data):
                predictions.append(0.0)
            # 如果预测数量多于原始数据，截断
            if len(predictions) > len(original_data):
                predictions = predictions[:len(original_data)]
        
        # 添加预测列
        original_data_dict = original_data.to_dict()
        original_data_dict['PREDICTION'] = predictions
        
        # 创建新的数据表
        result_data = dm.DataTable(original_data_dict)
        
        # 保存到CSV文件
        result_data.to_csv(output_file)
        
        print(f"预测结果已保存到: {output_file}")
        print(f"保存了 {len(predictions)} 个预测值")
        
        # 统计保存的预测结果
        high_predictions = sum(1 for p in predictions if p > 0.8)
        medium_predictions = sum(1 for p in predictions if 0.5 <= p <= 0.8)
        low_predictions = sum(1 for p in predictions if p < 0.5)
        
        print(f"保存的预测统计:")
        print(f"  高预测值 (>0.8): {high_predictions}")
        print(f"  中预测值 (0.5-0.8): {medium_predictions}")
        print(f"  低预测值 (<0.5): {low_predictions}")
        
        return True
        
    except Exception as e:
        print(f"保存预测结果失败: {str(e)}")
        return False

def analyze_prediction_quality(output_file='dataset_with_predictions_pure.csv'):
    """分析预测质量与真实标签关系 - 从 analyze_prediction_quality.py 移植"""
    print("\n分析预测质量与真实标签关系")
    
    try:
        # 读取预测结果文件
        data = dm.read_csv(output_file)
        
        if 'PREDICTION' not in data.columns or 'ACTIVITY' not in data.columns:
            print("❌ 缺少必要的列 (PREDICTION 或 ACTIVITY)")
            return
            
        predictions = [data['PREDICTION'][i] for i in range(len(data))]
        activities = [data['ACTIVITY'][i] for i in range(len(data))]
        
        print(f"数据基本信息:")
        print(f"  总样本数: {len(predictions)}")
        print(f"  预测值范围: [{min(predictions):.4f}, {max(predictions):.4f}]")
        
        # 分析真实标签分布
        active_count = sum(1 for a in activities if a == 1)
        inactive_count = sum(1 for a in activities if a == 0)
        print(f"  活性化合物 (标签=1): {active_count} ({active_count/len(activities)*100:.1f}%)")
        print(f"  非活性化合物 (标签=0): {inactive_count} ({inactive_count/len(activities)*100:.1f}%)")
        
        # 分析预测值与真实标签的关系
        print(f"\n预测准确性分析:")
        
        # 找出预测值最高的20个样本
        indexed_predictions = [(i, pred, act) for i, (pred, act) in enumerate(zip(predictions, activities))]
        indexed_predictions.sort(key=lambda x: x[1], reverse=True)  # 按预测值降序排序
        
        print(f"预测值最高的10个样本:")
        print(f"  {'序号':<6} {'预测值':<10} {'真实标签':<8} {'正确性'}")
        print(f"  {'-'*35}")
        
        correct_high_predictions = 0
        for i in range(min(10, len(indexed_predictions))):
            idx, pred, actual = indexed_predictions[i]
            is_correct = "✅" if ((pred > 0.5 and actual == 1) or (pred <= 0.5 and actual == 0)) else "❌"
            if pred > 0.5 and actual == 1:
                correct_high_predictions += 1
            print(f"  {idx+1:<6} {pred:<10.6f} {actual:<8} {is_correct}")
        
        # 按真实标签分组分析预测值
        print(f"\n按真实标签分组的预测统计:")
        
        # 活性化合物的预测情况
        active_predictions = [pred for pred, act in zip(predictions, activities) if act == 1]
        if active_predictions:
            print(f"🟢 活性化合物 (标签=1, 共{len(active_predictions)}个):")
            print(f"  预测值范围: [{min(active_predictions):.4f}, {max(active_predictions):.4f}]")
            print(f"  平均预测值: {sum(active_predictions)/len(active_predictions):.4f}")
            high_pred_active = sum(1 for p in active_predictions if p > 0.5)
            print(f"  高预测值(>0.5): {high_pred_active} ({high_pred_active/len(active_predictions)*100:.1f}%)")
        
        # 非活性化合物的预测情况  
        inactive_predictions = [pred for pred, act in zip(predictions, activities) if act == 0]
        if inactive_predictions:
            print(f"🔴 非活性化合物 (标签=0, 共{len(inactive_predictions)}个):")
            print(f"  预测值范围: [{min(inactive_predictions):.4f}, {max(inactive_predictions):.4f}]")
            print(f"  平均预测值: {sum(inactive_predictions)/len(inactive_predictions):.4f}")
            high_pred_inactive = sum(1 for p in inactive_predictions if p > 0.5)
            print(f"  高预测值(>0.5): {high_pred_inactive} ({high_pred_inactive/len(inactive_predictions)*100:.1f}%)")
        
        
        # 使用0.5作为阈值
        threshold = 0.5
        tp = sum(1 for pred, act in zip(predictions, activities) if pred > threshold and act == 1)  # 真正例
        fp = sum(1 for pred, act in zip(predictions, activities) if pred > threshold and act == 0)  # 假正例
        tn = sum(1 for pred, act in zip(predictions, activities) if pred <= threshold and act == 0)  # 真负例
        fn = sum(1 for pred, act in zip(predictions, activities) if pred <= threshold and act == 1)  # 假负例
        
        #print(f"  阈值: {threshold}")
        #print(f"  真正例 (TP): {tp}")
        #print(f"  假正例 (FP): {fp}")
        #print(f"  真负例 (TN): {tn}")
        #print(f"  假负例 (FN): {fn}")
        
        if tp + fp > 0:
            precision = tp / (tp + fp)
            #print(f"  精确率: {precision:.4f}")
        else:
            print(f"  精确率: 无法计算 (没有正预测)")
            
        if tp + fn > 0:
            recall = tp / (tp + fn)
            #print(f"  召回率: {recall:.4f}")
        else:
            print(f"  召回率: 无法计算 (没有真实正例)")
            
        accuracy = (tp + tn) / len(predictions)
        #print(f"  准确率: {accuracy:.4f}")
        
        # 诊断
        if tp == 0 and active_count > 0:
            print(f"严重问题：模型无法识别任何活性化合物！")
            if len(active_predictions) > 0 and sum(active_predictions) / len(active_predictions) < 0.5:
                print(f"活性化合物的平均预测值很低，模型可能学反了")
        
            
    except Exception as e:
        print(f"预测质量分析失败: {e}")

def main():
    """主函数"""
    print("开始预测")
    
    # 创建网络
    network = create_network()
    
    # 加载训练好的模型
    #model_file = 'model_1_continued.dict'
    model_file = 'model_1.dict'

    if load_trained_network_pure(network, model_file):
        print("模型加载成功")
    else:
        print("模型加载失败")
        return
    
    # 准备预测数据集 - 修正文件名
    print("准备预测数据集...")
    data_provider = prepare_pure_predicting_dataset('predicting_dataset.csv', fingerprint_type='Morgan', 
                                                  batch_size=32, shuffle=False)
    print("数据集准备完成")
    
    
    # 生成预测
    predictions = generate_predictions_pure(network, data_provider)
    
    # 分析结果
    analyze_predictions_pure(predictions)
    
    # 保存预测结果到CSV文件
    output_file = 'dataset_with_predictions_pure.csv'
    if predictions:
        if save_predictions_to_csv(predictions, output_file):
            print("\n" + "="*50)
            # 运行预测质量分析
            analyze_prediction_quality(output_file)
        else:
            print("预测结果保存失败，跳过质量分析")
    else:
        print("没有预测结果可保存")
    


if __name__ == "__main__":
    main() 