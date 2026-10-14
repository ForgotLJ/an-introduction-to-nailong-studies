#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
reflow.py -- 修复章节文件中“一行一两个字”的排版损坏。

判定：一个“段落块”（连续可合并行）若行数 >= 4 且平均行长 < 20 显示列，
视为损坏块，合并为一段后按 CJK 标点折行（目标宽 70 显示列）。
表格 / tikz / 数学环境内部不参与合并；以结构命令
（\\chapter、\\section、\\item、\\begin、\\end、\\label、\\caption 等）
开头的行作为块边界单独成行。健康段落原样保留。

用法：python reflow.py file1.tex file2.tex [--dry]
"""
import sys
import re
import unicodedata

# 这些环境内部整段跳过（含环境行本身）
NO_TOUCH_ENVS = {
    "tikzpicture", "axis", "tabular", "tabularx", "longtable",
    "equation", "equation*", "align", "align*", "gather", "gather*",
    "cases", "array", "semiverbatim", "verbatim", "lstlisting",
}

CJK_BREAK_AFTER = "，。；：！？、）》」』”…—"

# 以这些命令开头的行是“结构行”：不与前后合并
STRUCT_RE = re.compile(
    r"\\(chapter|section|subsection|subsubsection|paragraph|"
    r"item|begin|end|label|caption|index|nlkeywords|printindex|"
    r"tableofcontents|clearpage|vspace|vs pace)\b"
)


def disp_len(s):
    n = 0
    for ch in s:
        n += 2 if unicodedata.east_asian_width(ch) in "WF" else 1
    return n


def is_blank(line):
    return line.strip() == ""


def is_comment(line):
    return line.lstrip().startswith("%")


def is_fence(line):
    s = line.strip()
    if STRUCT_RE.match(s):
        return True
    return False


def has_rowsep(line):
    return "\\\\" in line


def joinable(line):
    if is_fence(line) or is_comment(line) or has_rowsep(line):
        return False
    if line.rstrip().endswith("%"):
        return False
    return True


def wrap(text, width=70):
    """按 CJK 标点折行；断点向后吞并连续标点，避免孤字行。"""
    if disp_len(text) <= width:
        return [text]
    out = []
    cur = ""
    last_break = -1  # cur 中最后一个可断点（含后续标点串）之后的位置
    i = 0
    while i < len(text):
        ch = text[i]
        cur += ch
        if ch in CJK_BREAK_AFTER:
            j = i + 1
            while j < len(text) and text[j] in CJK_BREAK_AFTER:
                cur += text[j]
                j += 1
            last_break = len(cur)
            i = j
            continue
        i += 1
        if disp_len(cur) > width and last_break > 0:
            out.append(cur[:last_break])
            cur = cur[last_break:]
            last_break = -1
    if cur:
        out.append(cur)
    return [l for l in out if l]


def process(lines):
    # 标记不可动区（NO_TOUCH 环境内部）
    keep = [False] * len(lines)
    stack = []
    for i, line in enumerate(lines):
        for m in re.finditer(r"\\(begin|end)\{([^}]+)\}", line):
            kind, name = m.group(1), m.group(2)
            if kind == "begin":
                stack.append(name)
            else:
                if name in stack:
                    while stack and stack[-1] != name:
                        stack.pop()
                    if stack:
                        stack.pop()
        if any(n in NO_TOUCH_ENVS for n in stack):
            keep[i] = True

    out = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        if keep[i] or is_blank(line) or is_comment(line) or is_fence(line):
            out.append(line)
            i += 1
            continue
        # 收集段落块：连续可合并行
        block = []
        while (i < n and not keep[i] and not is_blank(lines[i])
               and joinable(lines[i])):
            block.append(lines[i])
            i += 1
        if not block:
            out.append(line)
            i += 1
            continue
        avg = sum(disp_len(b.strip()) for b in block) / len(block)
        if len(block) >= 4 and avg < 26:
            joined = " ".join(b.strip() for b in block if b.strip())
            out.extend(wrap(joined))
        else:
            out.extend(block)  # 健康块：原样保留（含缩进）
    return out


def main():
    args = [a for a in sys.argv[1:] if a != "--dry"]
    dry = "--dry" in sys.argv
    for path in args:
        with open(path, "r", encoding="utf-8-sig") as f:
            src = f.read().splitlines()
        dst = process(src)
        n_short_before = sum(1 for l in src if l.strip() and disp_len(l) < 12)
        n_short_after = sum(1 for l in dst if l.strip() and disp_len(l) < 12)
        print(f"{path}: {len(src)} -> {len(dst)} lines; "
              f"tiny-lines {n_short_before} -> {n_short_after}")
        if not dry and dst != src:
            with open(path, "w", encoding="utf-8", newline="\n") as f:
                f.write("\n".join(dst) + "\n")
            print("  written.")


if __name__ == "__main__":
    main()
