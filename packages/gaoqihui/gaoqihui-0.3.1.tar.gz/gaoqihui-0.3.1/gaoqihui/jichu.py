def jichu():
    print("""
    实验准备
终端启动Anaconda Powershell Prompt
创建环境
conda create -n course python=3.10
启动环境
conda activate course
安装jupyterlab
pip install jupyterlab
启动
jupyter lab
跳转到浏览器后，新建ipynb文件
在新建的ipynb文件里面安装如下依赖：
!pip install numpy -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple
!pip install torch -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple
!pip install torchvision -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple
!pip install matplotlib -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple
任务一： Pytorch的一些基础操作
步骤1 Pytorch的创建，与Numpy之间的转换
使用anaconda环境下，对应python3.10及以上版本。
•	Pytorch高效集成了大量的与Numpy之间的操作。
输入：
解释
import warnings
warnings.filterwarnings("ignore")


import torch
import numpy as np

# 从数据中直接构建一个张量(tensor)
x = torch.tensor([5.5, 3])
print(x)

# 构建一个零矩阵，使用long的类型
x = torch.zeros(5,3, dtype=torch.long)
print(x)

# 创建随机数tensor
x = torch.rand(5,3)
print(x)
np_data = np.arange(6).reshape((2, 3))
torch_data = torch.from_numpy(np_data)
# 利用.numpy()函数可以容易转换
tensor2array = torch_data.numpy()
print(
    '\nnumpy array:', '\n',np_data,          # [[0 1 2], [3 4 5]]
    '\ntorch tensor:','\n', torch_data,      #  0  1  2 \n 3  4  5   
    '\ntensor to array:','\n', tensor2array, # [[0 1 2], [3 4 5]]
)
步骤2 torch的矩阵计算
输入：
解释
# torch的矩阵计算
data = [[1,2], [3,4]]
tensor = torch.FloatTensor(data)  # 转换成32位浮点 tensor
print(
    '\nmatrix multiplication (matmul)',
    '\ntorch: ', torch.mm(tensor, tensor)   # [[7, 10], [15, 22]]
)
print(
    '\nmatrix addition ',
    '\ntorch: ', torch.add(tensor, tensor)   # [[2, 4], [6, 8]]
)
步骤3 torch的函数计算
包含与Numpy的对比。
输入：
解释
# abs 绝对值计算
data = [-1, -2, 1, 2]
tensor = torch.FloatTensor(data)  # 转换成32位浮点 tensor
print(
    '\nabs',
    '\nnumpy: ', np.abs(data),          # [1 2 1 2]
    '\ntorch: ', torch.abs(tensor)      # [1 2 1 2]
)

# sin   三角函数 sin
print(
    '\nsin',
    '\nnumpy: ', np.sin(data),      # [-0.84147098 -0.90929743  0.84147098  0.90929743]
    '\ntorch: ', torch.sin(tensor)  # [-0.8415 -0.9093  0.8415  0.9093]
)

# mean  均值
print(
    '\nmean',
    '\nnumpy: ', np.mean(data),         # 0.0
    '\ntorch: ', torch.mean(tensor)     # 0.0
)
步骤4 Variable相关操作
1.	Variable基础
•	梯度计算
•	Variable的转换
输入：
解释
# 创建variable
import torch
from torch.autograd import Variable # torch 中 Variable 模块

tensor = torch.FloatTensor([[1,2],[3,4]])
# 此时这个tensor成了变量可以被更新
variable = Variable(tensor, requires_grad=True)

print('tensor:',tensor)
print('variable:',variable)
# 正向计算
t_out = torch.mean(tensor*tensor)       # x^2
v_out = torch.mean(variable*variable)   # x^2
print(t_out)
print(v_out)
# grad_fn=<MeanBackward1>,表示当反向传导的时候函数是<MeanBackward1>


# 反向过程
v_out.backward()    # 模拟 v_out 的误差反向传递

# Pytorch是动态计算图
# v_out = 1/4 * sum(variable*variable) 这是计算图中的 v_out 计算步骤
# 针对于 v_out 的梯度就是, d(v_out)/d(variable) = 1/4*2*variable = variable/2
print(variable.grad)    # 初始 Variable 的梯度
# varible通常不能直接被使用，如画图，因此需要进行转换
print(variable)     #  Variable 形式
print(variable.data)    # tensor 形式
print(variable.data.numpy())    # numpy 形式
步骤5 常见的激活函数
输入：
解释
import torch
import torch.nn.functional as F     # 激励函数都在这
from torch.autograd import Variable
import matplotlib.pyplot as plt
%matplotlib inline

# 生成数据来观看图像
x = torch.linspace(-5, 5, 200)  # x data (tensor), shape=(100, 1)
x = Variable(x)

x_np = x.data.numpy()   # 换成 numpy array, 出图时用

# 几种常用的 激励函数
y_relu = F.relu(x).data.numpy()
y_sigmoid = F.sigmoid(x).data.numpy()
y_tanh = F.tanh(x).data.numpy()
y_softplus = F.softplus(x).data.numpy()
# y_softmax = F.softmax(x)  softmax 比较特殊, 不能直接显示, 不过他是关于概率的, 用于分类


plt.figure(1, figsize=(8, 6))
plt.subplot(221)
plt.plot(x_np, y_relu, c='red', label='relu')
plt.ylim((-1, 5))
plt.legend(loc='best')

plt.subplot(222)
plt.plot(x_np, y_sigmoid, c='red', label='sigmoid')
plt.ylim((-0.2, 1.2))
plt.legend(loc='best')

plt.subplot(223)
plt.plot(x_np, y_tanh, c='red', label='tanh')
plt.ylim((-1.2, 1.2))
plt.legend(loc='best')

plt.subplot(224)
plt.plot(x_np, y_softplus, c='red', label='softplus')
plt.ylim((-0.2, 6))
plt.legend(loc='best')

plt.show()
torch.manual_seed(1)    # reproducible

# 生成数据
# torch.unsqueeze升维。
x = torch.unsqueeze(torch.linspace(-1, 1, 100), dim=1)  # x data (tensor), shape=(100, 1)
# 加入噪音
y = x.pow(2) + 0.2*torch.rand(x.size())  # noisy y data (tensor), shape=(100, 1)

# 建网络
net1 = torch.nn.Sequential(
    torch.nn.Linear(1, 10),
    torch.nn.ReLU(),
    torch.nn.Linear(10, 1)
)

def Net_train():

    # 建立优化器
    optimizer = torch.optim.SGD(net1.parameters(), lr=0.5)
    # 建立损失函数
    loss_func = torch.nn.MSELoss()

    # 训练
    for t in range(100):
        prediction = net1(x)
        loss = loss_func(prediction, y)
        # 梯度清零
        optimizer.zero_grad()
        # 损失反向
        loss.backward()
        # 梯度更新
        optimizer.step()

# 训练网络
Net_train()
步骤2 模型的保存与读取
输入：
torch.save(net1, 'net.pkl')  # 保存整个网络
torch.save(net1.state_dict(), 'net_params.pkl')   # 只保存网络中的参数 (速度快, 占内存少)
def restore_net():
    # restore entire net1 to net2
    net2 = torch.load('net.pkl')
    prediction = net2(x)
    return prediction

# 返回结果
np.squeeze(restore_net().data.numpy(),axis=1)
任务三 构建一个Mnist的网络训练
步骤1 引入相关包
将本地《智能摄像机及智能边缘产品与应用》实验数据\B03 实验使用数据\Mnist_pytorch.zip数据上传到当前目录
输入：
解释
# 获取数据集，并解压
import zipfile
with zipfile.ZipFile('Mnist_pytorch.zip', 'r') as zip_ref:
    zip_ref.extractall('Mnist_pytorch')
    
import torch
# nn是network的意思
import torch.nn as nn
# 常见的函数，比如激活函数，损失函数，卷积函数等等
import torch.nn.functional as F
# datasets内部有一些开源的数据集
# transform可以用来做多种预处理
from torchvision import datasets, transforms
# dataloader使用来处理数据的流
from torch.utils.data import DataLoader

#定义一些参数
BATCH_SIZE = 64
# 训练的轮数
EPOCHS = 10
# torch.cuda.is_available可以检测是否有GPU环境
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
步骤2 获取数据并形成数据流
输入：
解释
#图像预处理
# transforms.Normalize，是对数据进行标准化
transform = transforms.Compose([
    transforms.ToTensor(),
    transforms.Normalize(mean=(0.1307,),std=(0.3081,))
    ])

#训练集，载入Mnist数据集
train_set = datasets.MNIST(root='./', train=True, transform=transform, download=True)
# dataloader是一个将原始数据集成化迭代器
train_loader = DataLoader(train_set, 
                          batch_size=BATCH_SIZE,
                          shuffle=True)

#测试集
test_set = datasets.MNIST(root='./', train=False, transform=transform, download=True)
test_loader = DataLoader(test_set,
                        batch_size=BATCH_SIZE,
                        shuffle=True)
步骤3 构建模型
输入：
#搭建模型
class ConvNet(nn.Module):
    #图像输入是(batch,1,28,28)
    def __init__(self):
        # 继承了nn.Module的属性与方法
        super().__init__() 
        # Conv2d(in_channels, out_channels, kernel_size, stride=1, padding=0)
        # 输入通道数为1，输出通道数为10，卷积核(3,3)
        self.conv1 = nn.Conv2d(1, 10, (3,3)) 
        self.conv2 = nn.Conv2d(10, 32, (3,3))
        # linear(input, weight)，全连接层
        self.fc1 = nn.Linear(12*12*32, 100)
        self.fc2 = nn.Linear(100, 10)
    
    def forward(self, x):
        x = self.conv1(x) #(batch,10,26,26)
        x = F.relu(x)
        
        x = self.conv2(x) #(batch,32,24,24)
        x = F.relu(x)
        x = F.max_pool2d(x, (2,2))  #(batch,32,12,12)
        
        # 就是拉平操作
        x = x.view(x.size(0), -1) #flatten (batch,12*12*32)
        x = self.fc1(x) #(batch,100)
        x = F.relu(x)
        x = self.fc2(x) #(batch,10)
        
        out = F.log_softmax(x, dim=1) #softmax激活并取对数，数值上更稳定
        return out
步骤4 训练与验证
输入：
解释
#定义模型和优化器
# 如果是GPU，也可以使用model.cuda()
model = ConvNet().to(DEVICE) #模型移至GPU
# 调用
optimizer = torch.optim.Adam(model.parameters()) 


#定义训练函数
def train(model, device, train_loader, optimizer, epoch): #跑一个epoch
    model.train()  #开启训练模式，即启用BatchNormalization和Dropout等
    for batch_idx, (data, target) in enumerate(train_loader): #每次产生一个batch
        data, target = data.to(device), target.to(device) #产生的数据移至GPU
        output = model(data) 
        loss = F.cross_entropy(output, target) 
        optimizer.zero_grad() #所有梯度清零
        loss.backward() #反向传播求所有参数梯度
        optimizer.step() #沿负梯度方向走一步，更新参数
        if(batch_idx+1) % 234 == 0:   # 如果张量只有一个数值，可以使用.item()获取
            print('Train Epoch: {} [{}/{} ({:.1f}%)]\tLoss: {:.6f}'.format(
                epoch, (batch_idx+1) * len(data), len(train_loader.dataset),
                100. * (batch_idx+1) / len(train_loader), loss.item()))
            
            
#定义测试函数
def test(model, device, test_loader):
    model.eval()  #测试模式，不启用BatchNormalization和Dropout
    test_loss = 0
    correct = 0
    with torch.no_grad(): #避免梯度计算
        for data, target in test_loader:
            # 需要先将tensor编程对应的模式，GPU则tensor会变成tensor.cuda
            data, target = data.to(device), target.to(device)
            output = model(data)
            test_loss += F.cross_entropy(output, target, reduction='sum').item() #将一批损失相加
            pred = torch.argmax(output, dim=1, keepdim=True) #找到概率最大的下标
            correct += pred.eq(target.view_as(pred)).sum().item() # 预测值与真实值的比较，

    test_loss /= len(test_loader.dataset)  
    #len(train_loader)为batch数，len(train_loader.dataset)为样本总数
    print('\nTest set: Average loss: {:.4f}, Accuracy: {}/{} ({:.1f}%)\n'.format(
        test_loss, correct, len(test_loader.dataset),
        100. * correct / len(test_loader.dataset)))


#开始训练
for epoch in range(1, EPOCHS + 1):
    train(model, DEVICE, train_loader, optimizer, epoch)
    test(model, DEVICE, test_loader)
步骤5 预测单例
输入：
解释
from torch.autograd import Variable 
import numpy as np
# 获取一个图片和label
image, label = next(iter(test_set))
# batchsize =1
image = torch.unsqueeze(image,dim= 0)

# 预测模式
model.eval()
output = model(Variable(image))
output = output.data.cpu()
# 得到预测结果
pred = torch.argmax(output, dim=1, keepdim=True)
# 可视化
import numpy as np
import matplotlib.pyplot as plt
%matplotlib inline

# 反归一化
image = image * 0.3081 + 0.1307
# 4维变成3维
image = np.squeeze(image,axis=0).cpu()
plt.imshow(image.squeeze(), cmap='gray')

plt.xticks([])  #去掉x轴
plt.yticks([])  #去掉y轴
plt.axis('off')  #去掉坐标轴

print(pred)
plt.show()

""")




