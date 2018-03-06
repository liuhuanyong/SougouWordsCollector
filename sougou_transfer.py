#!/bin/python
# -*- coding: utf-8 -*-
import os
import struct
import sys
import binascii
import pdb
import pymongo
conn = pymongo.MongoClient()

try:
    reload(sys)
    sys.setdefaultencoding('utf-8')
except:
    pass

# 搜狗的scel词库就是保存的文本的unicode编码，每两个字节一个字符（中文汉字或者英文字母）
# 找出其每部分的偏移位置即可
# 主要两部分
# 1.全局拼音表，貌似是所有的拼音组合，字典序
#       格式为(index,len,pinyin)的列表
#       index: 两个字节的整数 代表这个拼音的索引
#       len: 两个字节的整数 拼音的字节长度
#       pinyin: 当前的拼音，每个字符两个字节，总长len
#
# 2.汉语词组表
#       格式为(same,py_table_len,py_table,{word_len,word,ext_len,ext})的一个列表
#       same: 两个字节 整数 同音词数量
#       py_table_len:  两个字节 整数
#       py_table: 整数列表，每个整数两个字节,每个整数代表一个拼音的索引
#
#       word_len:两个字节 整数 代表中文词组字节数长度
#       word: 中文词组,每个中文汉字两个字节，总长度word_len
#       ext_len: 两个字节 整数 代表扩展信息的长度，好像都是10
#       ext: 扩展信息 前两个字节是一个整数(不知道是不是词频) 后八个字节全是0
#
#      {word_len,word,ext_len,ext} 一共重复same次 同音词 相同拼音表


def tansfer(file_in, file_index, file_out):

    # 拼音表偏移，
    startPy = 0x1540;

    # 汉语词组表偏移
    startChinese = 0x2628;

    # 全局拼音表

    GPy_Table = {}

    # 解析结果
    # 元组(词频,拼音,中文词组)的列表
    GTable = []


    def byte2str(data):
        '''''将原始字节码转为字符串'''
        i = 0;
        length = len(data)
        ret = u''
        while i < length:
            x = data[i] + data[i + 1]
            t = unichr(struct.unpack('H', x)[0])
            if t == u'\r':
                ret += u'\n'
            elif t != u' ':
                ret += t
            i += 2
        return ret


    # 获取拼音表
    def getPyTable(data):
        if data[0:4] != "\x9D\x01\x00\x00":
            return None
        data = data[4:]
        pos = 0
        length = len(data)
        while pos < length:
            index = struct.unpack('H', data[pos] + data[pos + 1])[0]
            # print index,
            pos += 2
            l = struct.unpack('H', data[pos] + data[pos + 1])[0]
            # print l,
            pos += 2
            py = byte2str(data[pos:pos + l])
            # print py
            GPy_Table[index] = py
            pos += l

            # 获取一个词组的拼音


    def getWordPy(data):
        pos = 0
        length = len(data)
        ret = u''
        while pos < length:
            index = struct.unpack('H', data[pos] + data[pos + 1])[0]
            ret += GPy_Table[index]
            pos += 2
        return ret


    # 获取一个词组
    def getWord(data):
        pos = 0
        length = len(data)
        ret = u''
        while pos < length:
            index = struct.unpack('H', data[pos] + data[pos + 1])[0]
            ret += GPy_Table[index]
            pos += 2
        return ret


    # 读取中文表
    def getChinese(data):
        # import pdb
        # pdb.set_trace()

        pos = 0
        length = len(data)
        while pos < length:
            # 同音词数量
            same = struct.unpack('H', data[pos] + data[pos + 1])[0]
            # print '[same]:',same,

            # 拼音索引表长度
            pos += 2
            py_table_len = struct.unpack('H', data[pos] + data[pos + 1])[0]
            # 拼音索引表
            pos += 2
            py = getWordPy(data[pos: pos + py_table_len])

            # 中文词组
            pos += py_table_len
            for i in xrange(same):
                # 中文词组长度
                c_len = struct.unpack('H', data[pos] + data[pos + 1])[0]
                # 中文词组
                pos += 2
                word = byte2str(data[pos: pos + c_len])
                # 扩展数据长度
                pos += c_len
                ext_len = struct.unpack('H', data[pos] + data[pos + 1])[0]
                # 词频
                pos += 2
                count = struct.unpack('H', data[pos] + data[pos + 1])[0]

                # 保存
                GTable.append((count, py, word))

                # 到下个词的偏移位置
                pos += ext_len


    def deal(file_name, file_index):
        print '-' * 60
        f = open(file_name, 'rb')
        data = f.read()
        f.close()

        if data[0:12] != "\x40\x15\x00\x00\x44\x43\x53\x01\x01\x00\x00\x00":
            print "确认你选择的是搜狗(.scel)词库?"
            sys.exit(0)
            # pdb.set_trace()
        info = {}

        info['dict_name'] = byte2str(data[0x130:0x338]).replace("\x00",'')  # .encode('GB18030')
        info['dict_type'] = byte2str(data[0x338:0x540]).replace("\x00",'') # .encode('GB18030')
        info['dict_desc'] = byte2str(data[0x540:0xd40]).replace("\x00",'')  # .encode('GB18030')
        info['dict_eg'] = byte2str(data[0xd40:startPy]).replace("\x00",'') # .encode('GB18030')
        info['dict_index'] = file_index
        conn['sogou_word']['data'].insert(info)

        print file_index, info['dict_name'], info['dict_type']
        getPyTable(data[startPy:startChinese])
        getChinese(data[startChinese:])
        return info['dict_type']

    dict_type = deal(file_in, file_index)
    # 保存结果
    if not os.path.exists('./dict_txt2/%s'%dict_type):
        os.makedirs('./dict_txt2/%s'%dict_type)

    if len(GTable) > 99 :
        print len(GTable)
        f = open('./dict_txt2/%s/%s.txt'%(dict_type,file_out), 'w+')
        for word in GTable:
        # GTable保存着结果，是一个列表，每个元素是一个元组(词频,拼音,中文词组)，有需要的话可以保存成自己需要个格式
        # 我没排序，所以结果是按照上面输入文件的顺序
        #f.write(unicode(word).encode('GB18030'))  # 最终保存文件的编码，可以自给改
            f.write(word[2])
            f.write('\n')
    f.close()



if __name__ == '__main__':
    file_index = 1
    for root, dirs, files in os.walk('./dict'):
        for file in files:
            try:
                file_in = os.path.join(root,file)
                file_out = file.split('.')[0]
                tansfer(file_in, file_index, file_out)
                file_index += 1
            except:
                pass

