"""
Title:  算法服务类
Company: 北京领雁科技股份有限公司
@author lkl
"""
import sys
import shap
import joblib
import torch 
from torch import nn 

import numpy as np
from tpf.mlib import COPODModel
from tpf.mlib import MLib as ml
from tpf.mlib.lightgbm.lightgbm import dataset_pre
from tpf.mlib.seq import SeqOne 
from tpf import pkl_load,pkl_save 

class MyModel():
    def __init__(self, model_path, alg_type):
        self.model_path = model_path
        self.alg_type = alg_type

    def predict_proba(self, X):
        y_probs = AM.predict_proba(X, model_path=self.model_path, model_type=self.alg_type)
        return y_probs


class AM():
    seq_lgbm_name_list = ["LightGBM".lower(), "lgbm"]

    @classmethod
    def model_load(cls,model_path, model=None, params=None):
        """深度学习参数文件以.dict保存 
        """
        if model_path.endswith(".dict"):
            if model is None:
                if "seqone" in model_path.lower():
                    seq_len    = params["seq_len"]
                    model = SeqOne(seq_len=seq_len, out_features=2)
            model.load_state_dict(torch.load(model_path,weights_only=False))
        else:
            model = pkl_load(file_path=model_path, use_joblib=True)
        return model

    @staticmethod
    def model_save(model, model_path):
        if model_path.endswith(".dict"):
            lg(f"深度学习模型参数保存...{model_path}")
            torch.save(model.state_dict(), model_path)
        else:
            pkl_save(model, file_path=model_path, use_joblib=True)

    @staticmethod
    def train(alg_type="lgbm",
              X_train=None, y_train=None, X_test=None, y_test=None,
              cat_features=None):
        """算法模型调用
        返回算法实现类【实现类默认为方法名称小写】

        params
        ------------------------------------
        - alg_type:可以选择的算法,有["lgbm","copod","svc"]

        :return: 返回算法实现类
        """
        # -------------- 模型训练 开始--------------------
        alg_types = ["lgbm", "copod", "svm", "svc", "lr", "LR", "SVM", "LightGBM", "COPOD"]
        if alg_type.lower() in AM._lgbm_name_list:
            cat_features = list(set(cat_features))
            X_train[cat_features] = X_train[cat_features].astype("category")
            X_test[cat_features] = X_test[cat_features].astype("category")
            model = ml.lgbm_baseline(X_train, y_train, X_test, y_test,
                                     cat_features=cat_features,
                                     num_boost_round=3)

        elif alg_type.lower() in ["svm", "svc"]:
            model = ml.svc_base_line(X_train, y_train, C=1.0, kernel='rbf')

        elif alg_type.lower() in ["lr"]:
            model = ml.lr_base_line(X_train, y_train, max_iter=1000)

        elif alg_type.lower() in ["copod"]:
            model = COPODModel(contamination=0.05)

        else:
            error_msg = f"python_fail_begin=alg_type={alg_type},Currently only supported types:{alg_types},and not partitioned by case, case insensitive=python_fail_end"
            print(error_msg)
            sys.exit()
        return model

    @classmethod
    def predict_proba(cls, data, model_path=None, model_type=None, model=None, cat_features=None):
        """二分类模型，根据模型的路径加载模型，然后预测
        - model_type: 可选参数有["lgbm","lightgbm", None]，即是lgbm or 不是
        - model:具体的模型对象，此时仅返回
        """
        y_probs = []

        if model is None:
            if model_type is None:
                y_probs = cls.cls2_predict_proba(data, model_path=model_path)
            elif model_type.lower() in ["lgbm", "lightgbm"]:
                y_probs = cls.lgbm_predict_proba(data, model_path=model_path, cat_features=cat_features)
            else:  # 二分类，概率返回
                y_probs = cls.cls2_predict_proba(data, model_path=model_path)

            if len(y_probs) > 0 and isinstance(y_probs[0], np.int64):
                raise Exception(f"期望返回浮点型概率，但目前返回的是Int64类型的标签:{y_probs[0]}")
            return y_probs
        else:
            if hasattr(model, 'predict_proba') and callable(getattr(model, 'predict_proba')):
                print("obj has a callable my_method")
                y_porbs = model.predict_proba(data)
                if isinstance(y_porbs, np.ndarray) and y_porbs.ndim == 1:
                    return y_porbs
                return y_porbs[:, 1]
            else:
                raise Exception("仅支持predict_proba方法调用")

    @classmethod
    def lgbm_predict_proba(cls, data, model_path, cat_features=None):
        """二分类问题
        """
        model_lgbm = joblib.load(model_path)
        if cat_features is None:
            y_porbs = model_lgbm.predict(data)
        else:
            data = dataset_pre(data_pd=data, cat_features=cat_features)
            y_porbs = model_lgbm.predict(data)

        return y_porbs

    @classmethod
    def cls2_predict_proba(cls, data, model_path):
        """二分类问题
        - 适用返回2列概率的场景，包括深度学习
        """
        model = joblib.load(model_path)
        y_porbs = model.predict_proba(data)
        if isinstance(y_porbs, np.ndarray) and y_porbs.ndim == 1:
            return y_porbs
        return y_porbs[:, 1]

    @staticmethod
    def shap_value(model_path, alg_type, data, cat_features):
        """模型shap value
        - 仅针对2分类问题，做的通用处理
        """
        model = joblib.load(model_path)

        if alg_type.lower() in AM.seq_lgbm_name_list:
            cat_features = list(set(cat_features))
            data[cat_features] = data[cat_features].astype("category")
            # 使用SHAP解释模型
            explainer = shap.TreeExplainer(model)
            print("using TreeExplainer")

        else:
            model = MyModel(model_path=model_path, alg_type=alg_type)
            explainer = shap.KernelExplainer(model.predict_proba, data)
            print("using KernelExplainer")

        _shap_values = explainer.shap_values(data)
        if _shap_values.ndim == 3 and _shap_values.shape[1] > 1:
            shap_values = _shap_values[0, 1, :]
        elif _shap_values.ndim == 2:
            shap_values = _shap_values[0]
        elif _shap_values.ndim == 1:
            shap_values = _shap_values
        else:
            print(f"shape 维度异常,{_shap_values},可以根据第3个参数expected_value自行生成shap_values")

        print("explainer.expected_value type:", type(explainer.expected_value))
        expected_value = explainer.expected_value
        if isinstance(expected_value, np.ndarray) and len(expected_value) > 1:
            expected_value = expected_value[1]
        return expected_value, shap_values, explainer

