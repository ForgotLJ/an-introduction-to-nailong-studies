# -*- coding: utf-8 -*-
"""一次性修复 frontmatter/preface.tex：直引号、双星号、C 空格、直角引号。"""
import io, re

P = 'frontmatter/preface.tex'
t = io.open(P, encoding='utf-8').read()
orig = t

# 1) 配对直引号 -> 中文弯引号（文件内所有 " 均为成对使用）
n_q = 0
def sub_q(m):
    global n_q; n_q += 1
    return u'“' + m.group(1) + u'”'
t = re.sub(r'"([^"\n]*)"', sub_q, t)

# 2) markdown 双星号 -> \textbf{}
n_b = 0
def sub_b(m):
    global n_b; n_b += 1
    return r'\textbf{' + m.group(1) + '}'
t = re.sub(r'\*\*([^*\n]+)\*\*', sub_b, t)

# 3) 直角引号 -> 弯引号（与全书一致）
t = t.replace(u'「', u'“').replace(u'」', u'”')

# 4) “推荐路径为 第一章” 等 CJK 间空格
t = t.replace(u'推荐路径为 第一章', u'推荐路径为第一章')

# 5) 体例描述与实际宏对齐：假设编号 X-Y -> X.Y；术语索引表述
t = t.replace(u'标有“假设 X-Y”的编号条目', u'标有“假设 X.Y”（如“假设 7.5”）的编号条目')
t = t.replace(u'正文中黑体加粗术语表示该词已收入书末术语索引',
              u'正文中黑体术语表示关键概念，完整释义见附录 B（术语表），并可通过书末“术语与人名索引”检索')

io.open(P, 'w', encoding='utf-8').write(t)
print('quote pairs replaced:', n_q)
print('bold pairs replaced:', n_b)
print('changed:', t != orig)
