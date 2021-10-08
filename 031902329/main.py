from Pin_yin import Pinyin
import itertools
from Tran_slate import Translate
import numpy as np
import sys

pinyin = Pinyin()
translate = Translate()
read_dictionary = np.load('my_words.npy', allow_pickle=True).item()
"""
载入npy格式的汉字拆分字典my_words.npy
"""
duiying = {}
"""
将重组后的敏感词与最初的敏感词放在字典中，形成对应关系，便于最后输出时找到对应的最初敏感词,
如{"falungong":"法轮功","f轮功":"法轮功","xie教":"邪教","邪j":"邪教"}
"""
xieyin = {}
"""
记录各个敏感词的读音，方便后面处理待检测文本的谐音字时，将各个谐音字改为对应的敏感词
如{"fa":"法","lun":"轮","gong":"功"}
"""
ans = []
"""
记录检测结果，以(敏感词，文本中敏感词初始位置，文本中敏感词末位置加1)的三元组形式存在
"""
cai = []
"""
记录各个敏感词的拆分情况，如"工夫"
"""
ansyong = []
"""
用来存储源文本，用于最后的输出
"""
def take_second(a):
    """
    用于sort函数排序时指定按哪个元素排序
    因为检测结果以三元组保存时是无序的，所以要将三元组按照第二个元素升序排序
    """
    return a[1]

def is_chinese(uchar):
    """
    用于判断一个字符是否是汉字
    """
    for l in uchar:
        if u'\u4e00' <= l <= u'\u9fa5':
            continue
        else:
            return False
    return True


def getword(path1):
    """
    提取敏感词，并将敏感词的拼音替换、拼音首字母替换、繁体形式、敏感词拆分偏旁部首等情况进行重组
    最后存入wordcreat列表中
    """
    wordcreat = []
    with open(path1, "r", encoding="utf-8") as file:
        for line in file:
            a = line.strip()
            b = a
            if is_chinese(a[0]):
                ALL = []
                for i in a:
                    one_word = []
                    one_word.append(pinyin.GetPinyin(i))
                    """
                    获取敏感词的拼音
                    """
                    xieyin[pinyin.GetPinyin(i)] = i
                    one_word.append(i)
                    one_word.append(pinyin.GetPinyin(i)[0])
                    """
                    获取敏感词的拼音首字母
                    """
                    one_word.append(translate.ToTraditionalChinese(i))
                    """
                    获取敏感词的繁体形式
                    """
                    if i in read_dictionary:
                        one_word.append(read_dictionary[i])
                        """
                        获取敏感词的拆分偏旁部首形式
                        """
                        cai.append(read_dictionary[i])
                    ALL.append(one_word)
                for i in range(0, len(ALL) - 1):
                    """
                    利用itertools库将敏感词的各种形式进行快速重组
                    """
                    if i == 0:
                        g = [k for k in itertools.product(ALL[i], ALL[i + 1])]
                    else:
                        g = [k for k in itertools.product(g, ALL[i + 1])]
                ALL.clear()
                for i in g:
                    ALL.append(''.join(e for e in str(i) if e.isalnum()))
            if is_chinese(b[0]):
                """
                如果敏感词是中文，则将敏感词的各种形式都加入到wordcreat列表中
                如果敏感词是英文，则直接把敏感词加入wordcreat列表中
                """
                j = 0
                while j < len(ALL):
                    ALL[j] = ALL[j].lower()
                    duiying[ALL[j]] = b
                    wordcreat.append(ALL[j])
                    j += 1
            else:
                wordcreat.append(b)
                duiying[b] = b
    return wordcreat


class DFAUtils(object):
    """
    DFA算法
    """

    def __init__(self, word_warehouse):
        """
        算法初始化
        word_warehouse为构建好的敏感词词库
        """
        self.root = dict()
        """
        无意义词库,在检测中需要跳过的
        """
        self.skip_root = [' ', '!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '[', ']',
                          ';', ':', '"', ',', '<', '>', '.', '/', '?',
                          '{', '}', '`', '-', '_', '+', '=', '|', '\\', '\'',
                          '？', '、', '。', '，', '》', '《', '；', '：', '“', '‘',
                          '【', '】', '！', '￥', '…', '·', '~', '—',
                          '1', '2', '3', '4', '5', '6', '7', '8', '9', '0', '，']
        for word in word_warehouse:
            """
            初始化Trid树，将构建好的敏感词词库中的每一个敏感词加入树中
            """
            self.add_word(word)

    def add_word(self, word):
        """
        构建Trid树
        """
        now_node = self.root
        word_count = len(word)
        for i in range(word_count):
            char_str = word[i]
            if char_str in now_node.keys():
                """
                如果存在该key，直接赋值，用于下一个循环获取
                """
                now_node = now_node.get(word[i])
                now_node['is_end'] = False
            else:
                """
                 不存在则构建一个dict
                 """
                new_node = dict()
                if i == word_count - 1:
                    """
                    最后一个
                    """
                    new_node['is_end'] = True
                else:
                    """
                    不是最后一个
                    """
                    new_node['is_end'] = False
                now_node[char_str] = new_node
                now_node = new_node

    def findkey(self, txt, hang):
        """
        寻找文本中的敏感词，并将找到的敏感词以以(敏感词，文本中敏感词初始位置，文本中敏感词末位置加1)的三元组形式存入result中
        """
        result = set()
        for i in range(len(txt)):
            now_map = self.root
            matchword = ''
            flagjump = 0
            lenth = 0
            chu = 0
            flag = False
            for j in range(i, len(txt)):
                word = txt[j]
                if word in self.skip_root:
                    """
                     检测是否是特殊字符,如果找到了敏感词的首字，则lenth加一，继续循环；否则，跳出循环
                     """
                    if flagjump == 0:
                        break
                    elif flagjump == 1:
                        lenth += 1
                        continue
                now_map = now_map.get(word)
                if now_map:
                    """
                    若敏感词存在
                    """
                    if flagjump == 0:
                        flagjump = 1
                        chu = j
                    """
                    找到相应key，匹配标识+1
                    """
                    lenth += 1
                    matchword = matchword + word
                    if now_map.get("is_end"):
                        """
                        结束标志位为true
                        """
                        flag = True
                else:
                    """
                    不存在，直接返回
                    """
                    break
            if flagjump == 1 or flag == True:
                while (1):
                    """
                    因为采用的是最长匹配原则，若出现 '邪教#%$'的情况，循环去除后面的无效字符
                    """
                    if txt[chu + lenth - 1] in self.skip_root:
                        lenth = lenth - 1
                    else:
                        break
                if lenth >= 2:
                    """
                    找到的关键词以三元组形式存入result列表中
                    """
                    result.add((matchword, chu, chu + lenth, hang))
                elif lenth==1 and flag==True:
                    result.add((matchword, chu, chu + lenth, hang))
        return result

    def search(self, path2):
        """
        对文本内容进行读取，并调用findkey函数进行敏感词检测
        """
        hang = 0
        with open(path2, 'r', encoding="utf-8") as file:
            for query in file:
                """
                对文本内容进行处理，如：将文本中的大写字母全部转为小写，将文本中的谐音字转为对应的敏感词
                """
                hang += 1
                zji = []
                query = query.lstrip()
                query = query.strip()
                ansyong.append(query)
                query = query.lower()
                i = 0
                while i < len(query):
                    zji.append(query[i])
                    i += 1
                i = 0
                while i < len(zji):
                    if is_chinese(zji[i]):
                        pp = pinyin.GetPinyin(zji[i])
                        if pp in xieyin.keys():
                            if zji[i] not in str(cai):
                                zji[i] = xieyin[pp]
                    i += 1
                temp = ''
                i = 0
                while i < len(zji):
                    temp = temp + str(zji[i])
                    i += 1
                query = temp
                # print(query)
                res = self.findkey(query, hang)
                a = list(res)
                a.sort(key=take_second)
                """
                对每一行文本进行敏感词检测得到的三元组按三元组的第二个元素进行升序排序
                """
                if a == []:
                    continue
                else:
                    j = 0
                    while j < len(a):
                        ans.append(a[j])
                        j += 1

def output(path3):
    """
    输出函数，将结果保存在指定的文件中
    """
    fh = open(path3, 'a', encoding="utf-8")
    fh.write('Total: {}'.format(len(ans)) + '\n')
    i = 0
    while i < len(ans):
        if ans[i][0] in duiying.keys():
            """
            根据文本中获取的敏感词，在duiying字典中获取对应的原敏感词
            """
            yuanchar = duiying[ans[i][0]]
        else:
            o = 0
            zji = ''
            while o < len(ans[i][0]):
                pp = pinyin.GetPinyin(ans[i][0][o])
                if pp in xieyin.keys():
                    zji += xieyin[pp]
                else:
                    zji += ans[i][0][o]
                o += 1
            yuanchar = zji
        fh.write('Line' + str(ans[i][3]) + ': <' + str(yuanchar) + '> ')
        ggg = str(ansyong[ans[i][3] - 1])
        j = ans[i][1]
        while j < ans[i][2] - 1:
            fh.write(ggg[j])
            j += 1
        fh.write(ggg[j] + '\n')
        i += 1
    # print(ansyong)
    # print("word=",word_warehouse)
def main(argv):
    global cai
    path1 = argv[1]
    path2 = argv[2]
    path3 = argv[3]
    word_warehouse = getword(path1)
    dfa = DFAUtils(word_warehouse=word_warehouse)
    i = 0
    caiji = []
    while i < len(cai):
        j = 0
        while j < len(cai[i]):
            caiji.append(cai[i][j])
            j += 1
        i += 1
    cai = caiji
    dfa.search(path2)
    output(path3)
if __name__ == "__main__":
    if len(sys.argv) != 4:
        print('Incorrect input / output path')
    main(sys.argv)
