def B09():
    print("""
    任务二：提取文本数据
步骤1 安装依赖库
!pip install zhconv
!pip install jieba
!pip install gensim
步骤2 导入包
import warnings
warnings.filterwarnings("ignore") 
import os
import re
import zhconv
import jieba
import multiprocessing
from gensim.corpora import WikiCorpus
from gensim.models import word2vec
步骤3 指定数据路径
# 如更换环境，请注意路径是否正确
data_dir = "/data/NLP_pri/exp-9/data/nlp"
in_dir = data_dir
# 输出数据路径
out_dir = "./"
步骤4 加载数据并提取内容
# 输入文件路径，如更换环境，请注意路径是否正确
wiki_file_name = os.path.join(in_dir, 'zhwiki-latest-pages-articles.xml.bz2')
# 输出文件路径，如更换环境，请注意路径是否正确
corpus_cn_file = os.path.join(out_dir, 'corpus_cn.txt')
#加载数据
wiki_corpus = WikiCorpus(wiki_file_name, dictionary={})
with open(corpus_cn_file, 'w', encoding="utf8") as writer:
    count = 0
    for text in wiki_corpus.get_texts():
        writer.write(' '.join(text) + '\n')
        #print(text)
        count = count + 1
        if count <= 3:
            print(text)
        if count % 1000 == 0:
            print('已处理%d条数据' % count)
        #数据总数33w多条，这里只读取2w条数据进行演练   
        if count >= 20000:
            break
    print('处理完成！')
#查看处理结果，请注意路径是否正确
with open(corpus_cn_file, "r", encoding="utf8") as f:
    print(f.readlines()[:1])
任务三：预处理
步骤1 繁体字转简体字
corpus_cn_simple_file = os.path.join(out_dir, 'corpus_cn_simple.txt')
#读取文件
with open(corpus_cn_file, 'r', encoding='utf-8') as reader:
    lines = reader.readlines()   
    count = 0
    with open(corpus_cn_simple_file, 'w', encoding='utf-8') as writer:
        for line in lines:
            writer.write(zhconv.convert(line, 'zh-hans'))
            count += 1
            if count % 1000 == 0:
                print('已转换%d条数据' % count)
    print('处理完成！')
#查看结果,注意文件路径是否正确
with open(corpus_cn_simple_file, "r", encoding="utf8") as f:
    print(f.readlines()[:1])
步骤2 分词
corpus_cn_simple_separate_file = os.path.join(out_dir, 'corpus_cn_simple_separate.txt')
#读取文件
with open(corpus_cn_simple_file, 'r', encoding='utf-8') as reader:   
    lines = reader.readlines()
    count = 0
    with open(corpus_cn_simple_separate_file, 'w', encoding='utf-8') as writer:
        for line in lines:
            # jieba分词的结果是一个list，需要拼接，但是jieba把空格回车都当成一个字符处理
            writer.write(' '.join(jieba.cut(line.split('\n')[0].replace(' ', ''))) + '\n')
            count += 1
            if count % 1000 == 0:
                print('已分词%d条数据' % count)
    print('处理完成！')
#查看结果
with open(corpus_cn_simple_separate_file,"r",encoding="utf8") as f:
    print(f.readlines()[:1])
步骤3 去除非中文词
final_corpus_file = os.path.join(out_dir, 'final_corpus.txt')
#读取文件
with open(corpus_cn_simple_separate_file, 'r', encoding='utf-8') as reader:  
    lines = reader.readlines()    
    count = 1
    cn_reg = '^[\u4e00-\u9fa5]+$' #去除非中文的正则表达式
    with open(final_corpus_file, 'w', encoding='utf-8') as writer:
        for line in lines:
            line_list = line.split('\n')[0].split(' ')
            line_list_new = []
            for word in line_list:
                if re.search(cn_reg, word):
                    line_list_new.append(word) 
                    
            writer.write(' '.join(line_list_new) + '\n')
            count += 1
            if count % 1000 == 0:
                print('已处理%d条数据' % count)
print("处理完成！")
#查看结果
with open(final_corpus_file, "r", encoding="utf8") as f:
    print(f.readlines()[:1])
任务四：训练词向量
步骤1 训练词向量
w2v_model_file = os.path.join(out_dir, 'wordvec.model')
sentences = word2vec.LineSentence(final_corpus_file)
model = word2vec.Word2Vec(sentences,
            vector_size=300,  # 词向量长度为300
            window=5,
            min_count=5,
            sg=0,#1是skip-gram，0是CBOW
            hs=0,#1是hierarchical-softmax，0是negative sampling     
            negative=5,# 负样例的个数
            workers=multiprocessing.cpu_count())
model.save(w2v_model_file)#保存模型
print("训练模型结束...")
任务五：加载模型测试效果
步骤1 加载模型并尝试获取某个词的词向量
wordvec = word2vec.Word2Vec.load(w2v_model_file)
#获得"华为"的词向量
wordvec.wv.get_vector("华为")
步骤2 获取与“华为”语义最接近的5个词
#获得与"华为"最相近的5个词(模型重新训练过后，输出会有差异，属于正常)
wordvec.wv.most_similar("华为",topn=5)
步骤3 获取与“自然语言”最相近的5个词
#获得与"自然语言"最相近的5个词(模型重新训练过后，输出会有差异，属于正常)
wordvec.wv.most_similar("自然语言",topn=5)
""")