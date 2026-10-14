# -*- coding: utf-8 -*-
"""全书格式自动扫描：markdown 残留、标点、宏误用。只读，不修改任何文件。"""
import re, glob, io

FILES = sorted(glob.glob('chapters/*.tex') + glob.glob('backmatter/appendix_*.tex')
               + ['backmatter/postscript.tex', 'frontmatter/preface.tex'])

CJK = u'[\u4e00-\u9fff]'

def strip_comment(line):
    out, i = [], 0
    while i < len(line):
        c = line[i]
        if c == '\\' and i + 1 < len(line):
            out.append(line[i:i+2]); i += 2; continue
        if c == '%':
            break
        out.append(c); i += 1
    return ''.join(out)

LISTENVS = ('enumerate', 'itemize', 'description', 'nlkeypoints', 'nlexercises')
issues = []

for f in FILES:
    lines = io.open(f, encoding='utf-8').read().split('\n')
    stack = []
    for n, raw in enumerate(lines, 1):
        L = strip_comment(raw)

        def rpt(tag):
            issues.append('%s:%d: [%s] %s' % (f, n, tag, L.strip()[:88]))

        if '**' in L:
            rpt('双星号')
        if '"' in L:
            rpt('直引号')
        for m in re.finditer(CJK + u' +' + CJK, L):
            issues.append('%s:%d: [CJK间ASCII空格@%d] ...%s...' % (f, n, m.start(), L[max(0, m.start()-14):m.end()+14]))
        if re.search(u'。，|；。|，。|；；|。。|，，', L):
            rpt('重复标点')
        for m in re.finditer(r'\\conf\{([^}]*)\}', L):
            if m.group(1) not in ('A', 'B', 'C', 'M', 'A/B', 'B/C', 'A/B/C'):
                rpt('conf取值=' + m.group(1))
        for mac in ('keyw', 'en', 'term', 'fname', 'tsm'):
            if re.search(r'\\' + mac + r'\{\s*\}', L):
                rpt('空宏' + mac)
        for m in re.finditer(CJK + u'[,;:!?]', L):
            issues.append('%s:%d: [半角标点@%d] ...%s...' % (f, n, m.start(), L[max(0, m.start()-16):m.end()+16]))
        if L.count(u'\u201c') != L.count(u'\u201d'):
            rpt('弯引号不配对')

        for m in re.finditer(r'\\(begin|end)\{([a-zA-Z*]+)\}', L):
            name = m.group(2)
            if m.group(1) == 'begin':
                stack.append(name)
            elif stack and stack[-1] == name:
                stack.pop()
        if re.search(r'\\item\b', L) and not any(e in stack for e in LISTENVS):
            rpt('item不在列表环境')

with io.open('build/scan_report.txt', 'w', encoding='utf-8') as fh:
    fh.write('共 %d 条疑点\n' % len(issues))
    for i in issues:
        fh.write(i + '\n')
print('written', len(issues))
