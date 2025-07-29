# Molactivity INSTRUCTIONS

## INSTALL

```bash
pip install molactivity
```

## HOW TO USE

### 方式1: 命令行使用
```bash
# 训练模型
mol-train

# 进行预测
mol-predict
```

### 方式2: Python代码使用

#### 训练模型
```python
import train

# 开始训练 (需要 training_dataset.csv 文件)
train.training()
```

#### 预测活性
```python
import predict

# 进行预测 (需要 predicting_dataset.csv 文件和训练好的模型)
predict.main()
```

#### 使用 Transformer 模型
```python
import Transformer

# 创建模型
model = Transformer.MolecularTransformer(
    input_features=2048,
    output_features=1,
    embedding_size=128,
    layer_count=2,
    head_count=2,
    hidden_size=64,
    dropout_rate=0.1
)
```

## FORMAT OF DATASETS

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

## MODULES AVAILABLE

安装 molactivity 后，你可以直接导入以下模块：

- `train` - 模型训练
- `predict` - 活性预测
- `Transformer` - Transformer模型类
- `pure_data_loader` - 数据加载器
- `chem_features` - 化学特征提取
- `tensor_T` - 自定义张量操作
- `operations_T` - 张量运算
- `optimizer_T` - 优化器
- `model_save_load` - 模型保存/加载
- ... 以及其他40+个支持模块

## TIPS

1. **数据准备**: 确保CSV文件格式正确
2. **模型训练**: 先运行 `mol-train` 或 `train.training()`
3. **预测**: 训练完成后运行 `mol-predict` 或 `predict.main()`
4. **结果查看**: 预测结果保存在 `dataset_with_predictions_pure.csv`

## Q&A

**Q: 导入模块失败？**
A: 确保使用 `pip install molactivity` 正确安装，然后直接 `import train`

**Q: 找不到数据文件？**
A: 确保 `training_dataset.csv` 和 `predicting_dataset.csv` 在当前工作目录

**Q: 模型加载失败？**  
A: 确保先完成训练，生成 `model_1.dict` 文件

## QUESTIONS?

如有问题，请联系：Dr. Jiang at yale2011@163.com 