def B01():
    print("""
    步骤1 环境部署
!pip install jieba
步骤2 导入实验模块
import os
import jieba
import warnings
warnings.simplefilter('ignore')
步骤3 探索分词模式
精确分词
print("----精确模式:----")
s=u'华为合作伙伴网络是华为与合作伙伴之间的写作框架，包括一系列的合作伙伴计划。'
cut=jieba.cut(s,cut_all=False)
print(' '.join(cut))
全模式
print("----全模式:----")
print(' '.join(jieba.cut(s,cut_all=True)))
print(' '.join(jieba.cut(s,cut_all=False)))
搜索引擎模式
print("----搜索引擎模式:----")
print(','.join(jieba.cut_for_search(s)))
步骤4 读取文本文件并分词
data_dir="/data/NLP_pri/exp-1"
text_file=os.path.join(data_dir,'huawei.txt')
with open(text_file,'r') as f:
    text=f.read()
    new_text=jieba.cut(text,cut_all=False)
    str_out = ' '.join(new_text).replace('，', '').replace('。', '').replace('？', '').replace('！', '').replace('“', '').replace('”', '').replace('：','').replace('…', '').replace('（', '').replace('）', '').replace('—', '').replace('《', '').replace('》', '').replace('、', '').replace('‘', '').replace('’', '').replace('-', '').replace('\n', '')
print(str_out[:1000])
""")