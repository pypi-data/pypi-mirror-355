
import numpy as np 
import random
import pandas as pd 
import wave, os
import string

from tpf.box.fil import parentdir
from tpf.box.fil import iswin



import random
import string

def random_str(n):
    """随机字符(仅数字与字母)
    - n:表示字符串长度为n
    """
    # 定义可能的字符集：数字 + 小写字母 + 大写字母
    characters = string.ascii_letters + string.digits
    # 使用列表推导式和 random.choice 从字符集中随机选择字符
    random_characters = [random.choice(characters) for _ in range(n)]
    # 将列表转换为字符串（如果需要）
    random_string = ''.join(random_characters)
    return random_string

def random_str_numpy(n):
    """随机字符(仅数字与字母),numpy生成
    - n:表示字符串长度为n
    """
    characters = string.ascii_letters + string.digits
    indices = np.random.choice(len(characters), n, replace=True)
    random_characters = [characters[i] for i in indices]
    random_string = ''.join(random_characters)
    return random_string


# 定义生成随机字符串的函数
def random_str_lower(length=3):
    """定义生成随机字符串的函数
    """
    # 生成一个由小写字母和数字组成的随机字符串
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))
    
def random_str_p(seq_len=(1,3)):
    """随机生成seq_len[0]到 seq_len[1]长度的字符串
    - 字符串由字母与数字组成

    """
    # 单词集合，对应键盘上的字母
    words = [
        '0', '1', '2', '3', '4', '5', '6', '7', '8', '9', 
        'q', 'w', 'e', 'r',  't', 'y',  'u', 'i', 'o', 'p', 
        'a', 's', 'd', 'f',  'g', 'h',  'j', 'k', 'l', 
        'z', 'x', 'c', 'v',  'b', 'n',  'm'
    ]
        
    # 每个词被选中的概率，随机初始化的概率
    # p = np.array([
    #     1, 2, 3, 4, 5, 6, 7, 8, 9, 10,
    #     1,   2,  3,  4,  5,  6,  7,  8,  9, 10,
    #     11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26
    # ])
    p = np.random.randint(low=1, high=100, size=len(words), dtype=int)
    
    # 转概率，所有单词的概率之和为1
    _p = p / p.sum()
    
    # 随机选n个词
    # Return random integer in range [a, b], including both end points.
    _n = random.randint(seq_len[0], seq_len[1])

    _x = np.random.choice(words, size=_n, replace=True, p=_p)

    return "".join(_x)

def random_str_list(n=5,seq_len=(1,3)):
    """生成字符串列表
    """
    tmp = []
    for i in range(n):
        tmp.append(random_str_p(seq_len))
    return tmp 


def data_sample_small(x, y, batch_size=1):
    '''下采样
    从原样本中随机取出部分数据

    batch_size为取出的行数
    0表示全部数据


    from data_sample import data_sample_small

    X_train = [[1,2],[1,2],[1,2]]

    y_train = [1,2,3]

    X_train = np.array(aa)

    y_train = np.array(b)


    X_train, y_train = data_sample_small(X_train, y_train, batch_size=16)

    print(X_train)
    
    print(y_train)
    '''
    
    x_row_count = len(x)
    if batch_size > x_row_count or batch_size == 0:
        return x, y

    #  随机取batch_size个不重复索引下标
    index_list =  random.sample(range(x_row_count), batch_size) 
    x_samll = [0 for x in range(len(index_list))]
    y_samll = [0 for x in range(len(index_list))]
    
    for i,elem in enumerate(index_list):
        x_samll[i] = x[elem]
        y_samll[i] = y[elem]
        
    return np.array(x_samll), np.array(y_samll)


def pd1(row_num):
    x = np.random.normal(0,1,[row_num,1])
    y = 0.3*x + 0.7

    x1 = pd.DataFrame(x,columns=list("A"))
    y1 = pd.DataFrame(y,columns=list("B"))

    data1 = pd.concat([x1,y1],axis=1)
    return data1

def pd2(row_num):
    x = np.random.normal(0,1,[row_num,1])
    y1 = 0.3*x + 0.7
    y2 = 1.2 * x**2 - 0.3*x + 0.7

    x1 = pd.DataFrame(x,columns=list("A"))
    y1 = pd.DataFrame(y1,columns=list("B"))
    y2 = pd.DataFrame(y2,columns=list("C"))

    data1 = pd.concat([x1,y1,y2],axis=1)
    return data1



def data_numpy2(row_num):
    """
    返回指定行数的两组数据
    y = x**2 + 2x + 1 , 多特征时sum求和
    x 为两列, 表示数据，符合标准正态分布 
    y 为一行，表示标签
    """
    np.random.seed(111)
    x = np.random.randn(row_num, 2)
    # print(len(x))
    # print(x[:1])  # [[-1.13383833  0.38431919]]
    y = []
    for i in range(len(x)):
        d = x[i]**2 + 2*x[i] + 1
        y.append(np.sum(d))
    # print(y[:3])  # [1.9342523289452673, 6.648312741121465, 0.3373482907093769]
    return x, y


# 梯度下降多项式模型数据生成
def sgd111(row_num=1000000, col_num=3):
    """梯度下降多项式模型数据生成
    随机系数与随机样本相乘再求和，得到一批训练集与测试集
    生成几行几列的训练集测试集数据
    默认100万行数据，每行3个特征
    """
    np.random.seed(111)

    X_train = np.random.normal(0, 1, [row_num, col_num])

    theta0 = 0.01
    theta = np.random.rand(col_num)
    # theta_real.append(theta0)
    # for i in range(col_num):
    #     theta_real.append(theta[i])
    # print("theta:", theta0, theta)
    y_train = theta * X_train + theta0 + np.random.normal(0, 0.1, [row_num, col_num])

    X_test = np.random.normal(1, 1, [row_num, col_num])
    y_test = theta * X_test + theta0

    ll = len(X_train)
    y_train_new = []
    y_test_new = []

    # y定为sum的一半，也可以定为别的
    for i in range(ll):
        y_train_new.append(np.sum(y_train[i]))
        y_test_new.append(np.sum(y_test[i]))

    y_train_new = np.array(y_train_new)
    y_test_new = np.array(y_test_new)

    return X_train, X_test, y_train_new, y_test_new




def random_yyyymmdd(dt_format="%Y-%m-%d"):
    """随机日期，从2000年以来的日期
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
    formatted_date = random_date.strftime(dt_format)
    return formatted_date



import datetime
import numpy as np

def minute_one_year(minute_min=10):
    """年交易时间数据：分钟列表，
    - 依据该分钟列表，按时间相减，可得出一系列日期
    - minute_month:最小单位为分钟,minute_bymonth为一个月的分钟数
    - count_month:一个月的交易笔数
    - 伪算法
        - 以1年的总分钟数为最大尺度，10分钟为最小尺度,取一定数量的随机数
        - 每月随机发生count_month笔交易
    """
    minute_month = 24*60*30
    minute_year = minute_month*12
    count_month = np.random.randint(low=0,high=100)
    count_year = count_month*12
    a=np.random.randint(low=minute_min, high=minute_year, size=count_year)
    a.sort()
    return a.tolist()

m_time = minute_one_year()

def ymdhms_time(minute_list, max_count=10, dt_format='%Y-%m-%d %H:%M:%S'):
    """根据分钟列表，从当前日期开始生成一系列日期
    - 返回 
        - %Y-%m-%d %H:%M:%S格式 日期字符串 列表
    """
    t1 = []
    count = 0
    for m in minute_list:
        if count >= max_count:
            break 

        day1 = datetime.datetime.now() - datetime.timedelta(minutes=m*0.99)
        ss = day1.strftime(dt_format)
        t1.append(ss)
        count = count+1 
    return t1 


def year1_ymh(count=3, dt_format='%Y-%m-%d %H:%M:%S'):
    """生成count个，一年内的 随机日期字符串
    - count:随机字符串的个数


    说明
    --------------------------
    - 日期可精准的分钟级别，最小分钟间隔为10分钟，最大跨越1年
    
    
    examples
    ----------------------------
    year1_ymh(count=3, dt_format='%Y-%m-%d')
    
    """
    res = ymdhms_time(minute_list=m_time, max_count=count, dt_format=dt_format)
    return res 

if __name__ == '__main__':
    aa = [[1,2],[1,2],[1,2]]
    b = [1,2,3]
    aa = np.array(aa)
    b = np.array(b)

    x,y = data_sample_small(aa, b)
    print(x)
    print(y)

