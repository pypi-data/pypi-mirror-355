def B06():
    print("""
    任务一： 使用jieba进行tf-idf关键词提取
步骤1 实验环境部署
!pip install jieba
步骤2 导入相关模块
import os
import jieba.analyse as analyse
步骤3 指定数据路径
# 如更换环境，请注意路径是否正确
data_dir = "/data/NLP_pri/exp-6/"
text_file_path = os.path.join(data_dir, 'huawei.txt')
步骤4加载数据
with open(text_file_path, 'r', encoding='utf-8') as f:
    dataset = f.read()
    print(dataset[:100])#查看数据
步骤5 提取并查看关键词
输出前10个关键词，不带权重
result = analyse.extract_tags(dataset, topK=10, withWeight=False)
for item in result:
print(item)
输出前10个关键词，带权重
result = analyse.extract_tags(dataset, topK=10, withWeight=True)
for item in result:
    print(item)
输出前10个关键词，不带权重，有词性约束
result = analyse.extract_tags(dataset, topK=10, withWeight=False, allowPOS=("n","vn","v"))
for item in result:
    print(item)
任务二： 动手实现tf-idf关键词提取
步骤1 导入相关模块
from collections import defaultdict
import math
import operator
步骤2 创建数据样本
dataset = [ ['my', 'dog', 'has', 'flea', 'problems', 'help', 'please'],    # 切分的词条
               ['maybe', 'not', 'take', 'him', 'to', 'dog', 'park', 'stupid'],
               ['my', 'dalmation', 'is', 'so', 'cute', 'I', 'love', 'him'],
               ['stop', 'posting', 'stupid', 'worthless', 'garbage'],
               ['mr', 'licks', 'ate', 'my', 'steak', 'how', 'to', 'stop', 'him'],
               ['quit', 'buying', 'worthless', 'dog', 'food', 'stupid'] ]
步骤3 创建基于tf-idf的关键词排序函数
def feature_select(list_words):
    #总词频统计
    doc_frequency=defaultdict(int)
    for word_list in list_words:
        for i in word_list:
            doc_frequency[i]+=1
    #计算每个词的TF值
    word_tf={}  #存储每个词的tf值
    for i in doc_frequency:
        word_tf[i]=doc_frequency[i]/sum(doc_frequency.values())
    #计算每个词的IDF值
    doc_num=len(list_words)
    word_idf={} #存储每个词的idf值
    word_doc=defaultdict(int) #存储包含该词的文档数
    for i in doc_frequency:
        for j in list_words:
            if i in j:
                word_doc[i]+=1
    for i in doc_frequency:
        word_idf[i]=math.log(doc_num/(word_doc[i]+1))
    #计算每个词的TF*IDF的值
    word_tf_idf={}
    for i in doc_frequency:
        word_tf_idf[i]=word_tf[i]*word_idf[i]
    # 对字典按值由大到小排序
dict_feature_select=sorted(word_tf_idf.items(),key=operator.itemgetter(1),reverse=True)
    return dict_feature_select
步骤4 运行输出关键词及对应tf-idf权重
features=feature_select(dataset) #所有词的TF-IDF值
print(features)
print(len(features))
    """)