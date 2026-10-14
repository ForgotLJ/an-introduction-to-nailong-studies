# -*- coding: utf-8 -*-
"""去除正文段落开头的 \noindent （indentfirst 已使默认缩进符合中文排版习惯）。
只处理行首的 "\noindent "（后跟空格）；\noindent\srcnote 等宏组合不受影响。
结果写入 build/noindent_report.txt（GBK 控制台会打乱中文，故落盘）。
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FILES = sorted((ROOT / "chapters").glob("*.tex")) + [
    ROOT / "frontmatter" / "preface.tex",
    ROOT / "backmatter" / "postscript.tex",
]
PAT = re.compile(r"(?m)^\\noindent ")

lines = []
total = 0
for f in FILES:
    text = f.read_text(encoding="utf-8")
    new, n = PAT.subn("", text)
    if n:
        f.write_text(new, encoding="utf-8", newline="\n")
        lines.append(f"{f.relative_to(ROOT)}: {n}")
        total += n

lines.append(f"TOTAL: {total}")
out = ROOT / "build" / "noindent_report.txt"
out.write_text("\n".join(lines) + "\n", encoding="utf-8")
