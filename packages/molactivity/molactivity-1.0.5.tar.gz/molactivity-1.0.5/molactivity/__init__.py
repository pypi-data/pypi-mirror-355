# -*- coding: utf-8 -*-
"""
Molactivity
"""

__version__ = "1.0.5"
__author__ = "Dr. Jiang at BTBU"
__email__ = "yale2011@163.com"

# 导入主要模块
from . import train
from . import predict
from . import Transformer
from . import tensor_T
from . import operations_T
from . import autograd_T
from . import optimizer_T
from . import arrays
from . import chem_utils
from . import chem_features
from . import tools
from . import further_train

# 可选：提供便捷的访问方式
from .train import training
from .predict import main as predicting

__all__ = [
    'train', 'predict', 'Transformer', 'tensor_T', 'operations_T',
    'autograd_T', 'optimizer_T', 'arrays', 'chem_utils', 'chem_features', 'tools',
    'training', 'predicting', 'further_train'
]