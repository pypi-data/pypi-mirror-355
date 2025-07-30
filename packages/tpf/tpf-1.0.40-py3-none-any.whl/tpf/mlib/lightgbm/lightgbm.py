

import numpy as np
import lightgbm as lgb
from tpf.d1 import pkl_load,pkl_save,is_single_label


def dataset_pre(data_pd, cat_features):
    cat_features = list(set(cat_features))
    data_pd[cat_features] = data_pd[cat_features].astype("category")
    test_data = lgb.Dataset(data_pd)
    return data_pd

def lgbm_baseline(X_train, y_train, X_test, y_test, cat_features, num_boost_round, params=None):
    """
    # 创建LightGBM数据集，并指定分类特征
    # free_raw_data=False是因为在数据上设置部分列为category类型,此时lightgbm要求这个数据集不能被释放
train_data = lgb.Dataset(X_train, label=y_train, free_raw_data=False, categorical_feature=cat_features)
    test_data = lgb.Dataset(X_test, label=y_test,  reference=train_data)

    # 设置参数并训练模型
    if params is None:
        params = {
            'objective': 'binary',
            'metric': 'binary_logloss',
            'boosting_type': 'gbdt',
            'force_col_wise':True}
    lgb_model = lgb.train(params, train_data, num_boost_round=num_boost_round,  valid_sets=[test_data],)

    """
    cat_features = list(set(cat_features))
    X_train[cat_features] = X_train[cat_features].astype("category")
    X_test[cat_features] = X_test[cat_features].astype("category")

    # 创建LightGBM数据集，并指定分类特征
    # free_raw_data=False是因为在数据上设置部分列为category类型,此时lightgbm要求这个数据集不能被释放
    train_data = lgb.Dataset(X_train, label=y_train, free_raw_data=False, categorical_feature=cat_features)
    test_data = lgb.Dataset(X_test, label=y_test, reference=train_data)

    # 设置参数并训练模型
    if params is None:
        params = {
            'objective': 'binary',
            'metric': 'binary_logloss',
            'boosting_type': 'gbdt',
            'force_col_wise': True}
    lgb_model = lgb.train(params, train_data, num_boost_round=num_boost_round, valid_sets=[test_data], )
    return lgb_model
