
from Pin_yin import Pinyin
import itertools
from Tran_slate import Translate
import numpy as np
import sys
pinyin =Pinyin()
translate = Translate()
read_dictionary = np.load('my_words.npy', allow_pickle=True).item()
duiying={}
xieyin={}
shouzimu={}
ans=[]
cai=[]
ansyong=[]
cuntxt=[]
def is_chinese(uchar):
    # 判断一个字符是否是汉字
    for l in uchar:
        if u'\u4e00' <= l <= u'\u9fa5':
            continue
        else:
            return False
    return True
class node(object):
    def __init__(self):
        self.next = {}  # 相当于指针，指向树节点的下一层节点
        self.isWord = False  # 标记，用来判断是否是一个标签的结尾
        self.word = ""  # 用来储存标签

class ac_automation(object):
    def __init__(self, user_dict_path):
        self.root = node() #创建根节点
        self.user_dict_path = user_dict_path #读取词库文件的路径

    def add(self, word):
        temp_root = self.root
        for char in word:
            if char not in temp_root.next:
                temp_root.next[char] = node()
            temp_root = temp_root.next[char]
        temp_root.isWord = True
        temp_root.word = word
    # 添加文件中的关键词
    def add_keyword(self):
        with open(self.user_dict_path, "r", encoding="utf-8") as file:
            for line in file:
                a = line.strip()
                b=a
                if is_chinese(a[0]):
                    ALL = []
                    for i in a:
                        one_word = []
                        one_word.append(pinyin.GetPinyin(i))
                        xieyin[pinyin.GetPinyin(i)]=i
                        one_word.append(i)
                        one_word.append(pinyin.GetPinyin(i)[0])
                        one_word.append(translate.ToTraditionalChinese(i))
                        if i in read_dictionary:
                            one_word.append(read_dictionary[i])
                            cai.append(read_dictionary[i])
                        ALL.append(one_word)
                    for i in range(0, len(ALL) - 1):
                        if i == 0:
                            g = [k for k in itertools.product(ALL[i], ALL[i + 1])]
                        else:
                            g = [k for k in itertools.product(g, ALL[i + 1])]
                    ALL.clear()
                    for i in g:
                        ALL.append(''.join(e for e in str(i) if e.isalnum()))
                    #print(ALL)
                if is_chinese(b[0]):
                    j=0
                    while j<len(ALL):
                        ALL[j]=ALL[j].lower()
                        duiying[ALL[j]]=b
                        self.add(ALL[j])
                        j+=1
                else:
                    duiying[b]=b
                    self.add(line.strip())
    def search(self, content,hang):
        skip_root = [' ', '!', '@', '#', '$', '%', '^', '&', '*', '(', ')','[', ']',
                    ';', ':', '"', ',', '<', '>', '.', '/', '?',
                    '{', '}', '`', '-', '_', '+', '=', '|', '\\', '\'',
                    '？', '、', '。', '，', '》', '《', '；', '：', '“', '‘',
                    '【', '】', '！', '￥', '…', '·', '~', '—',
                    '1', '2', '3', '4', '5', '6', '7', '8', '9', '0','，']
        p = self.root
        result = set()
        index = 0
        while index < len(content) - 1:
            currentposition = index
            jilu = 0
            flag = 0
            chu=0
            while currentposition < len(content):
                word = content[currentposition]
                if word in p.next:
                    p = p.next[word]
                    if flag==0:
                        flag=1
                        chu=currentposition
                else:
                    if flag==0:
                        p = self.root
                    else:
                        if word in skip_root:
                            jilu+=1
                            '''if jilu>=20:
                                break'''
                        else:
                            p=self.root
                if p.isWord:
                    end_index = currentposition + 1
                    result.add((p.word,chu,end_index,hang))
                    break
                currentposition += 1
            p = self.root
            index += 1
        return result

def takeSecond(a):
        return a[1]

def main (argv):
    path1=argv[1]
    path2 = argv[2]
    path3 = argv[3]
    hang = 0
    ac = ac_automation(user_dict_path=path1)
    ac.add_keyword()  # 添加关键词到AC自动机
    with open(path2, 'r', encoding="utf-8") as file:
        for query in file:
            hang += 1
            zji = []
            query = query.lstrip()
            query = query.lower()
            query = query.strip()
            ansyong.append(query)
            i = 0
            while i < len(query):
                zji.append(query[i])
                i += 1
            i = 0
            while i < len(zji):
                if is_chinese(zji[i]):
                    pp = pinyin.GetPinyin(zji[i])
                    if pp in xieyin.keys():
                        # if zji[i] not in str(cai):
                        zji[i] = xieyin[pp]
                i += 1
            temp = ''
            i = 0
            while i < len(zji):
                temp = temp + str(zji[i])
                i += 1
            query = temp
            res = ac.search(query, hang)
            a = list(res)
            a.sort(key=takeSecond)
            if a == []:
                continue
            else:
                j = 0
                while j < len(a):
                    ans.append(a[j])
                    j += 1

    # print(ans)
    # print(cai)
    # print(xieyin)
    fh = open(path3, 'a', encoding="utf-8")
    fh.write('Total:{}'.format(len(ans)) + '\n')
    # print(duiying)
    # print(xieyin)
    i = 0
    while i < len(ans):
        yuanchar = duiying[ans[i][0]]

        fh.write('Line' + str(ans[i][3]) + ':<' + str(yuanchar) + '>')
        ggg = str(ansyong[ans[i][3] - 1])
        j = ans[i][1]
        while j < ans[i][2] - 1:
            fh.write(ggg[j])
            j += 1
        fh.write(ggg[j] + '\n')
        i += 1
if __name__ == "__main__":
    if len(sys.argv) != 4:
        print('Incorrect input / output path')
    main(sys.argv)
