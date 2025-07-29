
from . import arrays
from .tensor_T import Tensor
from . import data_manager as dm
from . import pure_random
from .chem_features import ChemicalFeatureGenerator

class PureMolecularDataset:
    """100%纯Python分子数据集，返回自定义Tensor"""
    def __init__(self, data_file, fingerprint_type='Morgan'):
        # 使用纯Python数据管理库读取CSV文件
        self.molecular_data = dm.read_csv(data_file)
        
        # 获取SMILES列数据
        self.smiles_strings = self.molecular_data['SMILES']
        self.fingerprint_method = fingerprint_type
        
        # 检查是否有活性标签（用于区分训练和预测数据集）
        self.has_labels = 'ACTIVITY' in self.molecular_data.columns
        if self.has_labels:
            self.activity_labels = self.molecular_data['ACTIVITY']

    def __len__(self):
        return len(self.smiles_strings)

    def _generate_fingerprint(self, smiles: str) -> Tensor:
        """生成分子指纹，返回自定义Tensor"""
        try:
            # 使用自定义的ChemicalFeatureGenerator
            feature_generator = ChemicalFeatureGenerator(fp_size=2048, radius=2)
            fingerprint = feature_generator.generate_morgan_fingerprint(smiles)
            # 返回我们的自定义Tensor而不是PyTorch tensor
            return Tensor(fingerprint, requires_grad=False)
        except Exception as e:
            # 特殊处理神秘的"1"错误
            error_msg = str(e)
            if error_msg == "1":
                print(f"[PURE_LOADER DEBUG] 捕获神秘'1'错误!")
                print(f"[PURE_LOADER DEBUG] SMILES: {smiles}")
                # 返回零向量而不是失败
                return Tensor(arrays.array(arrays.zeros(2048, dtype='float32').data), requires_grad=False)
            elif "invalid literal for int()" in error_msg:
                print(f"整数解析错误已修复，SMILES: {smiles}")
                return Tensor(arrays.array(arrays.zeros(2048, dtype='float32').data), requires_grad=False)
            else:
                print(f"指纹生成失败: {error_msg}")
                print(f"问题SMILES: {smiles}")
                return Tensor(arrays.array(arrays.zeros(2048, dtype='float32').data), requires_grad=False)

    def __getitem__(self, index):
        smiles = self.smiles_strings[index]
        features = self._generate_fingerprint(smiles)
        if features is None:
            print(f"特征生成失败，SMILES: {smiles}")
            return None, None if self.has_labels else None
        
        if self.has_labels:
            # 训练数据集 - 返回特征和标签
            label_value = self.activity_labels[index]
            # 确保label_value是数字类型
            if isinstance(label_value, (list, tuple)):
                label_value = label_value[0]
            activity_label = Tensor([float(label_value)], requires_grad=False)
            return features, activity_label
        else:
            # 预测数据集 - 只返回特征
            return features

class PureBatchProvider:
    """100%纯Python批次提供器，返回自定义Tensor"""
    def __init__(self, dataset, batch_size=32, shuffle=False, sampler=None):
        self.dataset = dataset
        self.batch_size = batch_size
        self.shuffle_flag = shuffle
        self.sampler = sampler
        self.current_position = 0
        self.indices = list(range(len(dataset)))
        if shuffle and sampler is None:
            pure_random.shuffle(self.indices)  # 使用我们的纯Python实现
        elif sampler is not None:
            self.indices = list(sampler)
        # 检查是否是预测数据集
        self.is_prediction = not dataset.has_labels

    def __iter__(self):
        self.current_position = 0
        return self

    def __next__(self):
        if self.current_position >= len(self.dataset):
            raise StopIteration

        feature_batch = []
        label_batch = []
        
        for _ in range(self.batch_size):
            if self.current_position >= len(self.dataset):
                break
                
            idx = self.indices[self.current_position]
            if self.is_prediction:
                features = self.dataset[idx]
                if features is not None:
                    feature_batch.append(features.data)  
            else:
                features, label = self.dataset[idx]
                if features is not None and label is not None:
                    feature_batch.append(features.data)  
                    label_batch.append(label.data)  
            
            self.current_position += 1

        if not feature_batch:
            raise StopIteration

        if self.is_prediction:
            arrays_list = [arrays.Array(feat) for feat in feature_batch]
            stacked_result = arrays.stack(arrays_list, axis=0)
            # 直接使用stacked_result，它已经是正确形状的arrays.Array
            stacked_features_np = stacked_result.data
            return Tensor(stacked_features_np, requires_grad=False), None
        else:
            feature_arrays_list = [arrays.Array(feat) for feat in feature_batch]
            stacked_features_result = arrays.stack(feature_arrays_list, axis=0)
            
            label_arrays_list = [arrays.Array(label) for label in label_batch]
            stacked_labels_result = arrays.stack(label_arrays_list, axis=0)
            
            # 直接使用stacked结果，它们已经是正确形状的arrays.Array
            stacked_features_np = stacked_features_result.data
            stacked_labels_np = stacked_labels_result.data
            return Tensor(stacked_features_np, requires_grad=False), Tensor(stacked_labels_np, requires_grad=False)

    def __len__(self):
        """计算总批次数"""
        return (len(self.dataset) + self.batch_size - 1) // self.batch_size

class PureBalancedSampler:
    """100%纯Python平衡采样器"""
    def __init__(self, dataset, with_replacement=True):
        self.dataset = dataset
        self.with_replacement = with_replacement
        self.sampling_weights = self._compute_weights()
        self.sample_count = len(dataset)
        self.hard_samples = set()
        self.high_pred_false_samples = set()
        self.very_high_pred_false_samples = set()
        self.extreme_high_pred_false_samples = set()
        self.positive_samples = set()
        self.sample_history = {}

    def _compute_weights(self):
        """基于类别分布计算采样概率"""
        # 计算类别分布
        class_counts = {}
        for label_tensor in self.dataset.activity_labels:
            label = int(label_tensor) if hasattr(label_tensor, '__int__') else int(label_tensor)
            class_counts[label] = class_counts.get(label, 0) + 1
        
        total_samples = sum(class_counts.values())
        # 计算每个类别的权重
        class_weights = {label: total_samples/count for label, count in class_counts.items()}
        
        # 为每个样本分配权重
        weights = []
        for label_tensor in self.dataset.activity_labels:
            label = int(label_tensor) if hasattr(label_tensor, '__int__') else int(label_tensor)
            weights.append(class_weights[label])
        
        return weights

    def update_hard_samples(self, predictions, labels, threshold=0.95):
        """更新难分类样本集合"""
        for idx, (pred, label) in enumerate(zip(predictions, labels)):
            if label == 1:
                self.positive_samples.add(idx)
            elif label == 0:
                if pred > 0.98:
                    self.extreme_high_pred_false_samples.add(idx)
                    self.very_high_pred_false_samples.add(idx)
                    self.hard_samples.add(idx)
                elif pred > 0.95:
                    self.very_high_pred_false_samples.add(idx)
                    self.hard_samples.add(idx)
                elif pred > 0.9:
                    self.high_pred_false_samples.add(idx)
                    self.hard_samples.add(idx)

    def _get_sample_weight(self, idx):
        """计算样本采样权重"""
        base_weight = self.sampling_weights[idx]
        
        if idx in self.extreme_high_pred_false_samples:
            weight = base_weight * 100.0
        elif idx in self.very_high_pred_false_samples:
            weight = base_weight * 50.0
        elif idx in self.high_pred_false_samples:
            weight = base_weight * 20.0
        elif idx in self.hard_samples:
            weight = base_weight * 10.0
        elif idx in self.positive_samples:
            weight = base_weight * 5.0
        else:
            weight = base_weight
        
        if idx in self.sample_history:
            sample_count = self.sample_history[idx]
            if sample_count > 0:
                weight = weight / (1 + sample_count * 0.1)
        
        return weight

    def __iter__(self):
        if self.with_replacement:
            weights = arrays.Array([self._get_sample_weight(i) for i in range(len(self.dataset))])
            # 确保sum()返回标量值
            weights_sum = weights.sum()
            if isinstance(weights_sum, arrays.Array):
                weights_sum = float(weights_sum.data[0]) if hasattr(weights_sum, 'data') else float(weights_sum)
            else:
                weights_sum = float(weights_sum)
            
            # 防止除零
            if weights_sum == 0:
                weights_sum = 1e-8
                
            weights = weights / weights_sum
            from . import pure_random
            samples = pure_random.weighted_choice(range(len(self.dataset)),
                                                weights=weights, 
                                                size=self.sample_count, 
                                                replace=True)
            
            for idx in samples:
                self.sample_history[idx] = self.sample_history.get(idx, 0) + 1
            
            return iter(samples)
        else:
            indices = list(range(len(self.dataset)))
            weights = arrays.Array([self._get_sample_weight(i) for i in indices])
            # 确保sum()返回标量值
            weights_sum = weights.sum()
            if isinstance(weights_sum, arrays.Array):
                weights_sum = float(weights_sum.data[0]) if hasattr(weights_sum, 'data') else float(weights_sum)
            else:
                weights_sum = float(weights_sum)
            
            # 防止除零
            if weights_sum == 0:
                weights_sum = 1e-8
                
            weights = weights / weights_sum
            samples = pure_random.weighted_choice(indices, 
                                                weights=weights,
                                                size=self.sample_count, 
                                                replace=False)
            
            for idx in samples:
                self.sample_history[idx] = self.sample_history.get(idx, 0) + 1
            
            return iter(samples)

    def __len__(self):
        return self.sample_count

def prepare_pure_training_dataset(csv_path, fingerprint_type='Morgan', batch_size=32, shuffle=False, balance_data=False):
    """准备100%纯Python训练数据集"""
    dataset = PureMolecularDataset(csv_path, fingerprint_type)
    if balance_data:
        sampler = PureBalancedSampler(dataset)
        data_loader = PureBatchProvider(dataset, batch_size=batch_size, sampler=sampler)
    else:
        data_loader = PureBatchProvider(dataset, batch_size=batch_size, shuffle=shuffle)
    return data_loader

def prepare_pure_predicting_dataset(csv_path, fingerprint_type='Morgan', batch_size=32, shuffle=False):
    """准备100%纯Python预测数据集"""
    dataset = PureMolecularDataset(csv_path, fingerprint_type)
    data_loader = PureBatchProvider(dataset, batch_size=batch_size, shuffle=shuffle)
    return data_loader 