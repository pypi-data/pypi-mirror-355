import os
import random
import string
import pandas as pd
import numpy as np
from sklearn import preprocessing
from sklearn.model_selection import train_test_split

from tpf.d1 import DataDeal as dt

from tpf import pkl_save,pkl_load
from tpf.d1 import DataDeal as dt
from tpf.d1 import read,write
from tpf.box.fil import  parentdir
from tpf.link.toolml import str_pd
from tpf.link.feature import FeatureEval
from tpf.link.toolml import null_deal_pandas
from tpf.link.toolml import std7


def drop_cols(df_all, columns=["dt"]):
    """多余字段删除"""
    # 多了一个dt日期 这里做删除处理
    df_all.drop(columns=columns,inplace=True)


def file_counter(file_path, add_num=0.01, reset0=False,format_float=None,return_int=False,max_float_count=4):
    """临时文件计数器
    - file_path:文本文件路径
    - add_num: 每次读取增加的数值
    - reset0:为True会将文件的数字置为0
    - format_float:指定小数位格式，比如，".2f"，效果类似0.10，最后一位是0也会保留
    -return_int:返回整数
    - max_float_count:最大小数位，最多保留几位小数

    examples
    -------------------------
    file_path = '.tmp_model_count.txt'
    count = file_counter(file_path, add_num=0.01, reset0=False)

    count = file_counter(file_path, add_num=0.01, reset0=False, format_float=".2f")
    """
    if reset0:
        write(0, file_path)

    # 检查文件是否存在
    if not os.path.exists(file_path):
        # 如果文件不存在，则创建文件并写入0
        write(0, file_path)
        current_count = 0
    else:
        # 如果文件存在，则读取文件中的数字，然后+1
        current_count = read(file_path)
        current_count += add_num
        # 将+1后的数字写入文件
        current_count=round(current_count, max_float_count)
        write(current_count, file_path)
    if return_int:
        return round(current_count)
    elif format_float is not None:
        return  f"{current_count:.2f}"

    # 返回+1后的数字
    return  current_count


def min_max_scaler(X, num_type=[], model_path=f"min_max_scaler.pkl", reuse=False):
        """针对指定的数字数据类型做min max scaler，通常是float32，float64,int64类型的数据
        
        params
        ---------------------------
        - num_type:需要做归一化的数字列，如果为空，则取数据X的所有列
        - reuse:False就不需要复用，也不会保存文件，此时model_path参数不起作用，比如一些无监督，特征选择等场景
        
        """
        if len(num_type) == 0:
            num_type = X.columns
    
        if reuse:
            if os.path.exists(model_path):
                scaler_train = pkl_load(file_path=model_path,use_joblib=True)
            else:
                # 仅对数值型的特征做标准化处理
                scaler_train = preprocessing.MinMaxScaler().fit(X[num_type])
                pkl_save(scaler_train,file_path=model_path,use_joblib=True)
        else:
            scaler_train = preprocessing.MinMaxScaler().fit(X[num_type])
        X[num_type] = scaler_train.transform(X[num_type])


def read_data():
    file10000 = "data/feature_10000.csv"
    if os.path.exists(file10000):
        df_all = pd.read_csv(file10000)
    else:
        file_path="data/feature.csv"
        df = pd.read_csv(file_path)
        print(df.shape)
        df = df[:10000]
        df_all = df.rename(columns=lambda x: x.lower())
        df_all['is_black_sample'] = np.random.randint(low=0,high=2,size=(df_all.shape[0]))  #随机生成标签
        df_all.to_csv(file10000,index=False)
    return df_all


def make_data(df_all):
    """数据制造
    """
    col_type_int = ['is_team_ip', 'is_self_ml', 'is_ii_metal', 'is_outlier_sum_amt_up_atm',
           'is_lvt_mental', 'is_merch_diff_opp', 'is_empty_id',
           'is_diff_open_location', 'is_cash_then_tran_fore', 'is_fre_fore_cash',
           'is_trans_atm_opp_sus', 'is_outlier_cnt_txn_up_atm',
           'is_free_trade_zone', 'is_salary_fre', 'is_diff_open_state','id_ddl_day_count', 'id_ddl_day_count','trace_day_1','trace_day_3','trace_day_10','trace_day_30']
    
    for ci in col_type_int:
        df_all[ci] = random.choices(string.digits, k=df_all.shape[0])
    
    col_type_cat = ['id_type', 'country_residence', 'occupation', 'industry', 'cur_risk_level','nationality','count_country_trans']
    for cc in col_type_cat:
        df_all[cc] = random.choices(string.digits, k=df_all.shape[0])
    
    col_remove = ['prop_merch_sus_count', 'is_id_expire', 'is_ctoi_sus', 'is_same_corp_tel']
    for cc in col_remove:
        df_all[cc] = random.choices(string.digits, k=df_all.shape[0])
    
    cor_remove_corr = ['out_count', 'third_trans_count', 'count_e_trans', 'sum_of_total_amt_receive', 'sum_of_total_amt_pay', 'sum_e_trans', 'is_non_resident', 'is_fore_open', 'sum_country_trans', 'trans_directcity_count', 'count_of_trans_opp_pay', 'is_rep_is_share', 'prop_merch_special_amt']
    for cc in cor_remove_corr:
        df_all[cc] = random.choices(string.digits, k=df_all.shape[0])
    
    not_in_cols = ['count_multi_open', 'in_count', 'count_of_opp_region', 'trans_city_count', 'count_ii_iii_acct', 'trace_day_10.0', 'trans_directcountry_count', 'trace_day_3.0', 'trans_country_count', 'is_overage', 'trace_day_30.0', 'is_reg_open_intrenal', 'trace_day_1.0']
    for cc in not_in_cols:
        df_all[cc] = np.random.randint(low=0,high=2,size=(df_all.shape[0]))



def data_split(df_all, v_date = '2015-08-01', split=0.8, col_lable="is_black_sample"):
    """
    return
    ---------------------
    - X_train,Y_train,X_test,Y_test,X_valid,Y_valid,df_train,df_test
    - df_train,df_test是正负样本客户分开的训练集与测试集，从中拆分出了X_train,Y_train,X_test,Y_test
    - 
    
    """
    # 本代码中将标签当作了数字而不是类型
    df_all[col_lable]  =df_all[col_lable].astype(int)
    
    # 将回溯日期大于2023-08-26的好样本划分为验证集
    df_validation = df_all[(df_all['target_dt']> v_date) & (df_all[col_lable] == 0) ]
    print("df_validation.shape",df_validation.shape)

    # 对于剩下的数据，按客户号的划分出好样本涉及的客户，与坏样本涉及的客户池
    white_pool = pd.unique(df_all[(df_all['target_dt']<= v_date) & (df_all[col_lable]== 0)]['index_id'])
    black_pool = pd.unique(df_all[df_all[col_lable]== 1]['index_id'])  #这里以全局的角度看客户 如果一个客户出现过坏样本 那它就是坏客户，这两个集合应该会有交集  应该做去重 但这里没有做


    # 从好样本池与坏样本池中分别抽取出80%的客户
    np.random.seed(1)
    white_train = np.random.choice(white_pool,round(len(white_pool)*split),replace = False) # white party_id used for train_set
    black_train = np.random.choice(black_pool,round(len(black_pool)*split),replace = False) # black party_id used for train_set
    

    # 上述客户分别将作为好坏样本加入训练集
    df_train = df_all[(df_all['target_dt'] <= v_date) & 
                      (
                      ((df_all[col_lable] == 0) & df_all['index_id'].isin(white_train)) | 
                      ((df_all[col_lable] == 1) & df_all['index_id'].isin(black_train)) 
                      )
                     ]


    # 将好样本池与坏样本池中余下的20%客户分别作为好坏样本加入测试集
    df_test = df_all[(df_all['target_dt'] <= v_date) & 
                      (
                      ((df_all[col_lable] == 0) & (~df_all['index_id'].isin(white_train))) | 
                      ((df_all[col_lable] == 1) & (~df_all['index_id'].isin(black_train))) 
                      )
                     ]

    # 剔除无关变量，定义训练集、测试集、验证集中的潜在入模特征“X”与目标变量“Y”
    Y_train = df_train[col_lable]
    Y_test = df_test[col_lable]
    df_valid = df_validation
    Y_valid = df_validation[col_lable]
    df_train.drop(columns=[col_lable],inplace=True)
    df_test.drop(columns=[col_lable],inplace=True)
    df_valid.drop(columns=[col_lable],inplace=True)
    return df_train,Y_train,df_test,Y_test,df_valid,Y_valid
        

def append_csv(new_data, file_path):
    """追加写csv文件，适合小数据量
    
    """
    if os.path.exists(file_path):
        # 读取现有的 CSV 文件
        existing_df = pd.read_csv(file_path)
    
        # 将新数据追加到现有的 DataFrame
        updated_df = pd.concat([existing_df, new_data], ignore_index=True)
    else:
        updated_df = new_data
    
    # 将更新后的 DataFrame 写回到 CSV 文件
    updated_df.to_csv(file_path, index=False)

def random_yyyymmdd():
    """随机生成日期,从2000年起
    - 格式：yyyy-mm-dd
    """
    from datetime import datetime, timedelta
    # 定义日期的起始和结束年份（如果需要）
    start_year = 2000
    end_year = datetime.now().year
    
    # 生成随机的年份
    year = random.randint(start_year, end_year)
    
    # 生成随机的月份
    month = random.randint(1, 12)
    
    # 生成随机的天数（注意每个月的天数不同）
    # 使用calendar模块可以帮助我们确定每个月的天数，但这里为了简单起见，我们使用datetime的date方法结合try-except来处理非法日期
    day = random.randint(1, 28)  # 先假设一个月最多28天
    
    while True:
        try:
            # 尝试创建日期对象
            random_date = datetime(year, month, day)
            # 如果成功，则跳出循环
            break
        except ValueError:
            # 如果日期非法（比如2月30日），则增加天数并重试
            day += 1
            if day > 28:  # 如果超过28天还未成功，则重置为1并从新月的天数开始检查（这里可以更加优化，比如根据月份确定最大天数）
                day = 1
                # 注意：这个简单的重置逻辑在跨月时可能不正确，因为它没有考虑到不同月份的天数差异。
                # 一个更准确的做法是使用calendar模块来确定每个月的最大天数。
                # 但为了简洁起见，这里我们假设用户不会频繁生成跨月的随机日期，或者接受偶尔的非法日期重试。
                # 在实际应用中，应该使用更精确的逻辑来确定每个月的最大天数。
                # 然而，为了这个示例的完整性，我们在这里保留这个简单的重置逻辑，并指出其潜在的不足。
    
    # 实际上，上面的while循环和重置逻辑是不完美的。下面是一个更准确的做法：
    from calendar import monthrange
    
    # 生成随机的天数（使用monthrange来确定每个月的最大天数）
    day = random.randint(1, monthrange(year, month)[1])
    random_date = datetime(year, month, day)
    
    # 格式化日期为"YYYY-MM-DD"
    formatted_date = random_date.strftime("%Y-%m-%d")
    return formatted_date

# import pandas as pd

def append_csv(new_data, file_path):
    """追加写csv文件，适合小数据量
    
    """
    if os.path.exists(file_path):
        # 读取现有的 CSV 文件
        existing_df = pd.read_csv(file_path)
    
        # 将新数据追加到现有的 DataFrame
        updated_df = pd.concat([existing_df, new_data], ignore_index=True)
    else:
        updated_df = new_data
    
    # 将更新后的 DataFrame 写回到 CSV 文件
    updated_df.to_csv(file_path, index=False)
    

class DateDeal():
    def __init__(self):
        """ 
        1. s1_data_classify,字段分类，区分出标识，数字，字符，日期等分类的列 ，不同的列按不同的方式处理
        2. s2_pd_split,s2_data_split,训练集测试集按标签拆分 
        3. s3_min_max_scaler,数字类型归一化处理
        """
        pass
        
    @staticmethod
    def s1_data_classify(data, col_type, pc, dealnull=False,dealstd=False,deallowdata=False,lowdata=10,deallog=False):
        """将pandas数表的类型转换为特定的类型
        - float64转换为float32
        - 布尔转为int64
        - 字符串日期转为pandas日期
        
        
        数据分类处理
        - 日期处理：字符串日期转为pandas 日期
        - object转string
        - 空值处理：数字空全部转为0，字符空全部转为'<PAD>'
        - 布尔处理：布尔0与1全部转为int64
        - 数字处理
            - 格式：全部转float32
            - 边界：极小-舍弃10￥以下交易，极大-重置超过7倍均值的金额
            - 分布：Log10后标准化
            - 最终的数据值不大，并且是以0为中心的正态分布

        - 处理后的数据类型：数字，日期，字符
        -
        
        params
        --------------------------------
        - data:pandas数表
        - col_type:pc参数配置中的col_type
        - pc:参数配置
        - dealnull:是否处理空值
        - dealstd:是否标准化处理
        - deallog:是否对数字列log10处理
        - deallowdata:金额低于10￥的数据全置为0
        
        example
        ----------------------------------
        data_classify_deal(data,pc.col_type_nolable,pc)
        
        """
        column_all = data.columns
        
        
        ### 日期
        date_type = [col for col in col_type.date_type if col in column_all] 
        data = str_pd(data, date_type)
        for col in date_type:
            data[col] = pd.to_datetime(data[col], errors='coerce')  

        ### 数字
        num_type = [col for col in col_type.num_type if col in column_all] 
        data[num_type] = data[num_type].astype(np.float32)
        
        
        bool_type = [col for col in col_type.bool_type if col in column_all]
        data[bool_type] = (data[bool_type].astype(np.float32)).astype(int)  # 为了处理'0.00000000'

        ### 字符-身份标识类
        cname_str_identity = pc.cname_str_identity 
        str_identity = [col for col in column_all if col in cname_str_identity]
        col_type.str_identity = str_identity
        data = str_pd(data,str_identity)

        ### 字符-分类，用于分类的列，比如渠道，交易类型,商户，地区等
        str_classification = [col for col in data.columns if col not in str_identity and col not in num_type and col not in date_type and col not in bool_type]
        col_type.str_classification = str_classification
        data = str_pd(data,str_classification)

        #空值处理
        if dealnull:
            data = null_deal_pandas(data,cname_num_type=num_type,cname_str_type=str_classification,num_padding=0, str_padding = '<PAD>')

        if len(num_type)>0:
            if deallowdata:
                #数字特征-极小值处理
                #将小于10￥的金额全部置为0，即不考虑10￥以下的交易
                for col_name in num_type:
                    data.loc[data[col_name]<lowdata,col_name] = lowdata
            
                #将lowdata以下交易剔除
                data.drop(data[data.CNY_AMT.eq(10)].index, inplace=True)
            if deallog:
                #防止后面特征组合时，两个本来就很大的数据相乘后变为inf
                data[num_type] = np.log10(data[num_type])
        
            if dealstd:
                # 数字特征-归一化及极大值处理
                #需要保存，预测时使用
                means = data[num_type].mean()
                stds = data[num_type].std()
                
                data = std7(data, num_type, means, stds)
        

        return data
        
    
    @staticmethod
    def s2_data_split(X, y,  test_size=0.2, random_state=42):
        """数据集拆分，不包含验证集，跨周期验证再额外处理
        - 或者在数据输入该方法之前，切一部分数据出现，单独作为验证集，本方法不再处理验证集
        
        return
        ---------------------
        -  X_train, X_test, y_train, y_test
        
        """
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=random_state, stratify=y)
        print("test label count:", y_test.value_counts())

        return  X_train, X_test, y_train, y_test
    
    @staticmethod
    def s2_data_split_valid(X, y,test_split=0.2):
        """验证集-跨周期验证
        - 如果数据没有数据无时间特征，即没有周期的概念，就没有必要加验证集
        - 要加也可以，可以随机取，可以切片取，比如取最后1000行数据
        """
        ss = """验证集-跨周期验证
        - 如果数据没有数据无时间特征，即没有周期的概念，就没有必要加验证集
        - 要加也可以，可以随机取，可以切片取，比如取最后1000行数据
        """
        return ss 
        
    def s2_pd_split(X, y, test_split=0.2, random_state=42,):
        """按标签类别等比随机采样，确保测试集中每类标签的数据与训练集保持等比，不会出现测试集中某个标签无数据的情况 

        params
        ------------------------------------
        - X:数据,pandas数表
        - y:标签,pandas数表 
        - lable_name:标签名称 
        - test_size:测试集占比,
        - random_state:随机因子

        examples
        ------------------------------------
        X_train,y_train,X_test,y_test = ddl.s2_pd_split(X, y, lable_name='target', test_size=0.2, random_state=42,)
        
        """
        X_train,y_train,X_test,y_test = dt.pd_data_split(X=X, y=y, test_split=test_split, random_state=random_state,)
        return X_train,y_train,X_test,y_test
    
    @staticmethod
    def s3_min_max_scaler(X, num_type=[], model_path=f"min_max_scaler.pkl", reuse=False):
        """针对指定的数字数据类型做min max scaler，通常是float32，float64,int64类型的数据
        
        params
        ---------------------------
        - num_type:需要做归一化的数字列，如果为空，则取数据X的所有列
        - reuse:False就不需要复用，也不会保存文件，此时model_path参数不起作用，比如一些无监督，特征选择等场景
        
        examples
        -------------------------------------------------
        # 训练集数字类型归一化, reuse=True时，首次执行因model_path不存在会保存preprocessing.MinMaxScaler().fit的结果
        ddl.s3_min_max_scaler(X, num_type=pc.col_type.num_type, model_path=pc.scale_path, reuse=True)

        #reuse=True且model_path存在时，直接加载文件，然后transform
        ddl.s3_min_max_scaler(X_test, num_type=pc.col_type.num_type,model_path=pc.scale_path, reuse=True)
        
        """
        # print(type(X),X.shape)
        if len(num_type) == 0:
            num_type = X.columns

        p_dir = parentdir(model_path)
        if not os.path.exists(p_dir):
            raise Exception(f"The file directory {p_dir} does not exist, unable to write files to it ")

        if reuse:
            if os.path.exists(model_path):
                scaler_train = pkl_load(file_path=model_path,use_joblib=True)
            else:
                # 仅对数值型的特征做标准化处理
                scaler_train = preprocessing.MinMaxScaler().fit(X[num_type])
                pkl_save(scaler_train,file_path=model_path,use_joblib=True)
        else:
            scaler_train = preprocessing.MinMaxScaler().fit(X[num_type])
        X[num_type] = scaler_train.transform(X[num_type])

