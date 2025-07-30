"""dlt1 深度学习训练简易版 常用方法 

"""
import numpy as np 

# PyTorch 三组件
import torch
from torch import nn
from torch.nn import functional as F

# 数据打包工具
from torch.utils.data import Dataset
from torch.utils.data import DataLoader


class DsReg(Dataset):
    """回归问题最简数据集
    """
    def __init__(self, X, y):
        """超参
        """
        self.X = X
        self.y = y
    
    def __getitem__(self, idx):
        """根据索引返回一对数据 (x, y)
        """
        return torch.tensor(data=self.X[idx]).float(), torch.tensor(data=self.y[idx]).float()
    
    
    def __len__(self):
        """数据总数
        """
        return len(self.X)
    
    

class DatasetCls(Dataset):
    """回归问题最简数据集
    """
    def __init__(self, X, y):
        """超参
        """
        self.X = X
        self.y = y
    
    def __getitem__(self, idx):
        """根据索引返回一对数据 (x, y)
        """
        return torch.tensor(data=self.X[idx]).float(), torch.tensor(data=self.y[idx]).long()
    
    
    def __len__(self):
        """数据总数
        """
        return len(self.X)

class LinearRegression(nn.Module):
    """模型定义
    """
    
    def __init__(self, in_features, out_features):
        """参数网络设计
        - 总体来说，做的事件是将数据从一个维度转换到另外一个维度
        """
        super().__init__()
        
        self.linear = nn.Linear(in_features=in_features, out_features=out_features)
        
    def forward(self, X):
        """正向传播
        - 调用定义的参数网络
        - 让数据流过参数网络，常量数据流过不过的参数产生不同的值
        - 这个过程参数本身不会变
        - 让参数变化的是后面的优化器 
        """
        out = self.linear(X)
        
        return out


def loss_monitor(dataset, model, loss_fn, batch_size=128, retain_precision=4):
    """整个数据集的损失均值
    - 批次计算损失，再求均值，最终返回整个数据集损失的均值 
    """
    dataloader = DataLoader(dataset=dataset, batch_size=batch_size, shuffle=False)
    model.eval()
    with torch.no_grad():
        batch_loss = []
        for X, y in dataloader:
            y_out = model(X)
            loss = loss_fn(y_out, y)
            batch_loss.append(loss.item())
        mean_loss = np.array(batch_loss).mean()
        return mean_loss.round(retain_precision)
    
    
class ac():
    is_regression = False 
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    
    def __init__(self):
        """精度计算方法"""
        pass 
    
    @staticmethod
    def acc_reg(pre=[], real=[], error_ratio=0.001):
        """连续型变量准确率计算
        - 预测pre与真实值real做差/real = error_ratio，误差比为0表示预测数据与真实值重合 
        - 定下一个threshold，大于为真-1，小于为假-0 
        - pre,real为torch.tensor类型 
        - 适合于模型输出非概率的情况，模型输出值与标签值直接比较 
        - 对于模型输出是概率的情况，该计算方式也是适用的 
        

        >>> 0.1914*0.05
            0.00957
        """
        with torch.no_grad():
            # print("基准：",threshold)
            pre = pre.flatten()
            a1 = real.flatten() 
            aa = pre - a1
            
            a2 = np.abs(aa.cpu())/(a1.cpu()+0.00001)  # 防分母为0
            acc_list =np.array([])
            for v in a2:
                if v.item() <= error_ratio:  # 误差线
                    acc_list=np.append(acc_list,1)
                else:
                    acc_list=np.append(acc_list,0)
            acc3 = acc_list.sum()/len(acc_list)
            # acc3 = "%.2f"%(acc3) # 前面乘100，后又保留两位有效数据，共四位有效数字
        return acc3 
    
    # 定义过程监控函数
    @classmethod
    def acc_reg_batch(cls, dataloader, model):
        """回归问题批次准确率计算
        """
        accs = []
        model = model.to(cls.device)
        model.eval()
        with torch.no_grad():
            for X4,y4 in dataloader:
                X4 = X4.to(cls.device)
                y4 = y4.to(cls.device)
                y_pred = model(X4)
     
                acc = cls.acc_reg(pre=y_pred,real=y4)
                accs.append(acc)
        return np.array(accs).mean()
    
    # 定义过程监控函数
    @classmethod
    def acc_cls(cls, dataloader, model, class_index=1):
        """分类问题准确率计算及单独某个类别的精确率，召回率 
        """
        accs = []
        model = model.to(cls.device)
        model.eval()
        pre1_list = []
        with torch.no_grad():
            for X4,y4 in dataloader:
                X4 = X4.to(cls.device)
                y4 = y4.to(cls.device)
                y_pred = model(X4)
             
                y_pred = y_pred.argmax(dim=1)
                # msg = f"\n batch size:{y4[:3]},y_pred.shape:{y_pred.shape},\n{y_pred[:3]}"
                # print(msg)
        
                #标签为1且模型预测为1的概率，二分类召回率计算 
                single_class_mean = 0 
                if class_index == 1:
                    label1_mean = y_pred[y4.reshape(-1)==class_index].float().mean()
                    single_class_mean = label1_mean
                else:
                    lablen = y_pred[y4.reshape(-1)==class_index]   #对应某个真实类型
                    lablen_count = float(lablen.shape[0])   #真实个数
                    n_pre = float(lablen[lablen == class_index].shape[0])  #真实中模型预测为真实的个数
                    single_class_mean = n_pre/lablen_count
                    
                # msg = f"\n batch size:{y4.shape[0]},acc:{(y_pred == y4).float().mean()},pre1:{single_class_mean}"
                # print(msg)
                pre1_list.append(single_class_mean.cpu().item())

                acc = (y_pred == y4).float().mean().item()
                accs.append(acc)
            acc_all = np.array(accs).mean()
            pre1_class = np.array(pre1_list).mean()
            print(f"acc:{acc_all},tpf on class index {class_index}:{pre1_class}")
        return acc_all


    # 定义过程监控函数
    @classmethod
    def _get_acc(cls, dataloader, model):
        """回归问题或二分类问题精度计算
        """
        accs = []
        model = model.to(cls.device)
        model.eval()
        with torch.no_grad():
            for X4,y4 in dataloader:
                X4 = X4.to(cls.device)
                y4 = y4.to(cls.device)
                y_pred = model(X4)
                if cls.is_regression:
                    acc = cls.acc_reg(pre=y_pred,real=y4)
                    return acc
                else:
                    y_pred = y_pred.argmax(dim=1)
                    # msg = f"\n batch size:{y4[:3]},y_pred.shape:{y_pred.shape},\n{y_pred[:3]}"
                    # print(msg)
          
                    #标签为1且模型预测为1的概率，二分类召回率计算 
                    label1_mean = y_pred[y4.reshape(-1)==1].float().mean()
                    
                    msg = f"\n batch size:{y4.shape[0]},pre right:{(y_pred == y4).float().mean()},pre1:{label1_mean}"
                    print(msg)
  
                    acc = (y_pred == y4).float().mean().item()
                    accs.append(acc)
        return np.array(accs).mean()

    

def train(epoch,batch_size,
            train_dataset,test_dataset,
            model,loss_fn,optim,
            loss_monitor_fn = loss_monitor):
    
    """多轮训练 
    
    examples
    -----------------------------------------------------------
    import numpy as np 
    import torch 
    from torch import nn 
    from tpf.datasets import load_boston
    from tpf.dlt1 import DsReg
    from tpf.dlt1 import LinearRegression
    from tpf.dlt1 import train

    # 加载数据
    X_train, y_train, X_test,  y_test = load_boston()
    y_train = y_train.reshape(-1,1)
    y_test = y_test.reshape(-1,1)

    # 训练集
    train_dataset = DsReg(X=X_train, y=y_train)
    test_dataset = DsReg(X=X_test, y=y_test)

    model = LinearRegression(in_features=13, out_features=1)
    loss_fn = nn.MSELoss()
    optim = torch.optim.Adam(params=model.parameters(),lr=1e-3)

    train(epoch=2,batch_size=32,
            train_dataset=train_dataset,test_dataset=test_dataset,
            model=model,loss_fn=loss_fn,optim=optim)
    
    
    """
    train_dataloader = DataLoader(dataset=train_dataset, batch_size=batch_size, shuffle=True, drop_last=True)

    for i in range(1,epoch+1):
        print(f"...第{i}轮训练开始....\n")
        # 一轮训练
        count = 0 
        for X,y in train_dataloader:
            count = count+1
            y_out = model(X)
            loss = loss_fn(y_out, y)
            
            # 交叉䊞损失函数允许标签与模型输出维度不一致 
            # if count ==1:
            #     if y_out.shape == y.shape:
            #         pass 
            #     else:
            #         raise Exception(f"模型输出shape={y_out.shape}与标签shape={y.shape}不一致")
                

            # 求当前参数在当前数据处的梯度
            loss.backward()
            if count%100==1:
                print(f"epoch={i},count={count},loss_item={round(loss.item(),4)}")

            # 下降一次，就是朝着最优解的方向前进一步
            optim.step()
            optim.zero_grad() 
        
        if test_dataset is not None:
            epoch_loss_train = loss_monitor_fn(dataset=train_dataset, model=model, loss_fn=loss_fn)
            epoch_loss_test = loss_monitor_fn(dataset=test_dataset, model=model, loss_fn=loss_fn)
            print(f"第{i}轮训练，模型输出与训练集loss：{epoch_loss_train},与测试集loss：{epoch_loss_test}")
        print("-------------------------\n")
        
        

def train_cls(epoch,batch_size,
            train_dataset,test_dataset,
            model,loss_fn,optim,
            loss_monitor_fn = loss_monitor,class_index=1):
    
    """多轮训练 
    
    examples
    -----------------------------------------------------------
    import numpy as np 
    import torch 
    from torch import nn 
    from tpf.datasets import load_boston
    from tpf.dlt1 import DsReg
    from tpf.dlt1 import LinearRegression
    from tpf.dlt1 import train

    # 加载数据
    X_train, y_train, X_test,  y_test = load_boston()
    y_train = y_train.reshape(-1,1)
    y_test = y_test.reshape(-1,1)

    # 训练集
    train_dataset = DsReg(X=X_train, y=y_train)
    test_dataset = DsReg(X=X_test, y=y_test)

    model = LinearRegression(in_features=13, out_features=1)
    loss_fn = nn.MSELoss()
    optim = torch.optim.Adam(params=model.parameters(),lr=1e-3)

    train(epoch=2,batch_size=32,
            train_dataset=train_dataset,test_dataset=test_dataset,
            model=model,loss_fn=loss_fn,optim=optim)
    
    
    """
    device = "cuda:0" if torch.cuda.is_available() else "cpu"
    
    train_dataloader = DataLoader(dataset=train_dataset, batch_size=batch_size, shuffle=True, drop_last=True)

    for i in range(1,epoch+1):
        print(f"...第{i}轮训练开始....\n")
        # 一轮训练
        count = 0 
        for X,y in train_dataloader:
            count = count+1
            y_out = model(X)
            loss = loss_fn(y_out, y)
            
            # 交叉䊞损失函数允许标签与模型输出维度不一致 
            # if count ==1:
            #     if y_out.shape == y.shape:
            #         pass 
            #     else:
            #         raise Exception(f"模型输出shape={y_out.shape}与标签shape={y.shape}不一致")
                

            # 求当前参数在当前数据处的梯度
            loss.backward()
            if count%100==1:
                print(f"epoch={i},count={count},loss_item={round(loss.item(),4)}")

            # 下降一次，就是朝着最优解的方向前进一步
            optim.step()
            optim.zero_grad() 
        
        if test_dataset is not None:
            epoch_loss_train = loss_monitor_fn(dataset=train_dataset, model=model, loss_fn=loss_fn)
            epoch_loss_test = loss_monitor_fn(dataset=test_dataset, model=model, loss_fn=loss_fn)
            print(f"第{i}轮训练，模型输出与训练集loss：{epoch_loss_train},与测试集loss：{epoch_loss_test}")
            
            test_dataloader = DataLoader(dataset=test_dataset,batch_size=batch_size,shuffle=False)
            ac.acc_cls(test_dataloader,model,class_index=1)
        print("-------------------------\n")