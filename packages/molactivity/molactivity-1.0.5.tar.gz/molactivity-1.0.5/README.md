# Molactivity

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)
![Status](https://img.shields.io/badge/status-beta-orange.svg)

## INTRODUCTION

Molactivity 是一个基于Transformer神经网络的分子活性预测工具包。该项目使用纯Python实现了完整的深度学习框架，专门用于分子性质预测任务。

### HIGHLIGHTS

- **Transformer架构**: 采用注意力机制的Transformer模型进行分子活性预测
- **化学信息学**: 支持Morgan分子指纹和其他化学特征提取
- **数据处理**: 完整的数据加载、预处理和批处理功能
- **自定义损失**: 实现了Focal Loss等专门针对分子预测的损失函数
- **模型管理**: 支持模型保存、加载和继续训练
- **结果分析**: 提供详细的预测结果分析和质量评估

## INSTRUCTIONS

### 安装

#### 从PyPI安装
```bash
pip install molactivity
```


### 基本使用

#### 1. 模型训练

使用命令行工具：
```bash
# 基本训练
mol-train

# 指定参数训练
mol-train --num_networks 2 --activation gelu

# 继续训练现有模型
mol-train --continue_training --model_file model_1.dict --additional_epochs 5
```

或者在Python代码中使用：
```python
import train

# 开始训练
train.training()
```

#### 2. 分子活性预测

使用命令行工具：
```bash
mol-predict
```

或者在Python代码中使用：
```python
import predict

# 进行预测
result = predict.main()
```

## DATASETS

### 训练数据 (training_dataset.csv)
```csv
SMILES,Activity
CCO,1
CCN,0
c1ccccc1,1
```

### 预测数据 (predicting_dataset.csv)
```csv
SMILES
CCO
CCN
CCC
```

## DETAILED INSTRUCTIONS

### 核心类和函数

#### MolecularTransformer
```python
import Transformer

model = Transformer.MolecularTransformer(
    input_features=2048,      # 输入特征维度
    output_features=1,        # 输出特征维度
    embedding_size=128,       # 嵌入层大小
    layer_count=2,           # Transformer层数
    head_count=2,            # 注意力头数
    hidden_size=64,          # 隐藏层大小
    dropout_rate=0.1         # Dropout率
)
```

#### 训练函数
```python
import train

# 使用默认参数训练
train.training()
```

#### 预测函数
```python
import predict

# 进行预测并返回结果
success = predict.main()
```

## SETUP

### 训练参数

| 参数 | 类型 | 默认值 | 描述 |
|------|------|--------|------|
| `--num_networks` | int | 1 | 训练的网络数量 |
| `--activation` | str | 'gelu' | 激活函数 ('relu' 或 'gelu') |
| `--continue_training` | bool | False | 是否继续训练现有模型 |
| `--model_file` | str | 'model_1.dict' | 模型文件路径 |
| `--additional_epochs` | int | 1 | 继续训练的轮数 |

### 模型参数

```python
optimal_parameters = {
    'learning_rate': 0.001,
    'transformer_depth': 2,
    'attention_heads': 2,
    'hidden_dimension': 64
}
```

## RESULTS ANALYSIS

预测完成后，系统会自动生成：

1. **预测结果文件**: `dataset_with_predictions_pure.csv`
2. **结果统计**: 包括预测值分布、准确性分析等
3. **质量评估**: 预测置信度和分类统计

示例输出：
```
=== 预测结果分析 ===
总预测数量: 98
有效预测数量: 98
最小预测值: 0.0234
最大预测值: 0.9876
平均预测值: 0.4521

高活性预测 (>0.7): 23 (23.5%)
中等活性预测 (0.3-0.7): 45 (45.9%)
低活性预测 (<0.3): 30 (30.6%)
```


## SUPPORT

如果您遇到问题或有任何建议，请：

- 发送邮件至: yale2011@163.com

