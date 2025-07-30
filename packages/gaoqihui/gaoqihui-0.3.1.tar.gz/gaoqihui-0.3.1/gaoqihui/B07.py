def B07():
    print("""
    任务一: 使用jieba进行textrank关键词提取
步骤1 实验环境部署
!pip install jieba
步骤2 导入相关模块
import os
import jieba.analyse as analyse
步骤3 指定数据路径
data_dir = "/data/NLP_pri/exp-7"
text_file_path = os.path.join(data_dir, 'huawei.txt')
步骤4 读取数据
with open(text_file_path, 'r', encoding='utf-8') as f:
    dataset = f.read()
print(dataset[:100])
步骤5 运行并输出关键词
#输出前10个关键词，不带权重
result = analyse.textrank(dataset, topK=10, withWeight=False)
for item in result:
print(item)
#输出前10个关键词，带权重
result = analyse.textrank(dataset, topK=10, withWeight=True)
for item in result:
    print(item)
#输出前10个关键词，不带权重，有词性约束
result = analyse.textrank(dataset, topK=10, withWeight=False, allowPOS=("n","vn","v"))
for item in result:
    print(item)
任务二：动手实现textrank关键词提取
步骤1 导入模块
import jieba
import jieba.posseg
from collections import defaultdict
import os
步骤2 定义图
#定义无向有权图
class UndirectWeightGraph:
    d = 0.05
    def __init__(self):
        self.graph = defaultdict(list)
    def addEdge(self, start, end, weight):  #添加无向图边
        self.graph[start].append((start, end, weight))
        self.graph[end].append((end, start, weight))
    def rank(self):   #根据文本无向图进行单词权重排序，其中包含训练过程
        ws = defaultdict(float)  #pr值列表
        outSum = defaultdict(float)  #节点出度列表
        ws_init = 1.0/(len(self.graph) or 1.0)  #pr初始值
        for word, edge_lst in self.graph.items():   #pr, 出度列表初始化
            ws[word] = ws_init
            outSum[word] = sum(edge[2] for edge in edge_lst)
        sorted_keys = sorted(self.graph.keys())
        for x in range(10):                        #多次循环计算达到马尔科夫稳定
            for key in sorted_keys:
                s = 0
                for edge in self.graph[key]:
                    s += edge[2]/outSum[edge[1]] * ws[edge[1]]
                ws[key] = (1 - self.d) + self.d * s
        min_rank, max_rank = 100, 0
        for w in ws.values():   #归一化权重
            if min_rank > w:
                min_rank = w
            if max_rank < w:
                max_rank = w
        for key, w in ws.items():
            ws[key] = (w - min_rank)*1.0/(max_rank - min_rank)
        return ws
步骤3 定义textrank方法
停用词加载
def load_stop_words(stop_word_path):
    stop_words = set()
    if not stop_word_path:
        return stop_words
    elif not os.path.isfile(stop_word_path):
        raise Exception("jieba: file does not exit: " + stop_word_path)
    with open(stop_word_path, 'r', encoding='utf-8') as f:
        for lineno, line in enumerate(f):
            stop_words.add(line.strip())  
    return stop_words
textrank方法
class TextRank():
    def __init__(self, stop_word_path=None): 
        self.tokenizer = self.postokenizer = jieba.posseg.dt # jieba分词， 词性模块
        self.stop_words = load_stop_words(stop_word_path) # 加载停用词
        self.pos_filter = frozenset(("ns", "n", "vn", "v"))
        self.span = 5 # 相邻词的窗口大小
    def pairfilter(self, wp):  # wp 格式为 (flag, word)
        state = (wp.flag in self.pos_filter) and (len(wp.word.strip()) >= 2) and (wp.word.lower() not in self.stop_words)
        #print("1:", state)
        return state
    def textrank(self, sentence, topK=20, withWeight=False, allowPOS=("ns", "n", "vn", "v")):
        if allowPOS:
            self.pos_filter = frozenset(allowPOS)
        g = UndirectWeightGraph()
        word2edge = defaultdict(int)
        words = tuple(self.tokenizer.cut(sentence)) #分词
        for i, wp in enumerate(words):        #将句子转化为边的形式
            #print(wp.flag, wp.word)
            if self.pairfilter(wp):
                for j in range(i+1, i+self.span):
                    if j >= len(words):
                        break
                    if not self.pairfilter(words[j]):
                        continue
                    word2edge[(wp.word, words[j].word)] += 1
        for terms, w in word2edge.items():
            g.addEdge(terms[0], terms[1], w)
        nodes_rank = g.rank()
        sorted_nodes = sorted(nodes_rank.items(), key=lambda x: x[1], reverse=True)
        if not withWeight:
            sorted_nodes = [node for node, weight in sorted_nodes]
        if topK:
            return sorted_nodes[: topK]
        else:
            return sorted_nodes
步骤4 运行并输出关键词
不带权重
sentence = "研究与开发华为聚焦全联接网络、智能计算、创新终端三大领域，在产品、技术、基础研究、工程能力、标准和产业生态等方面持续投入，使能客户数字化转型，构建智能社会的基石。 华为致力于把领先技术转化为更优、更有竞争力的产品解决方案，帮助客户实现商业成功, 在无线领域，华为发布了5G端到端解决方案，包括无线、传输、核心网、终端(CPE)在内的商用产品，与运营商及主流终端芯片厂商完成IODT测试，协助全 球多个运营商在多个核心城市完成5G预商用部署。在LTE领域持续演进，打造基于体验的全业务基础网络，推动WTTx、NB-IoT、车联网等业务持续发展。在新兴市场，RuralStar、TubeStar等解决方案优化站点TCO，提升客户投资效率。面向行业数字化新机会，企业无线聚焦公共安全、电力、交通等市场，与合作伙伴一起提供创新的解决方案。华为打造了未来无线网络三大基础能力：SingleRAN Pro、移动网络全云化和无线智能，帮助运营商构建一张多业务融合网络。SingleRAN Pro，提供“1+1”极简的目标网，解决多业务发展的容量、覆盖和时延要求；移动网络全云化，构建敏捷灵活的网络架构，提升多业务连接效率；无线智能，运用人工智能技术构建智能化的网络管理能力，实现高效的网络运维和多业务体验优化。华为无线的移动联合创新中心(MIC)、科技城市(TechCity)、无线应用场景实验室(Wireless X Labs)三架创新“马车”齐头并进，与运营商、合作伙伴在解决方案、商业用例领域联合研究和探索。 2017年全球移动宽带论坛上，华为发布基于三大元素的5G目标网构架，帮助运营商构筑三位一体的2020时代移动网络多业务能力，共同促进移动产业的蓬勃发展，最终实现人人皆移动、万物皆互联、无线重塑全行业的美好愿景。"
keywords_extractor = TextRank()
keywords = keywords_extractor.textrank(sentence)
print(keywords)
带权重
keywords = keywords_extractor.textrank(sentence, withWeight=True)
print(keywords)
""")