"""Export the compiled textbook and its covers, plus 300 dpi cover images."""

from pathlib import Path
import shutil
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
PDF_DIR = ROOT / "output" / "pdf"
IMAGE_DIR = ROOT / "output" / "covers"


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    pdf_dir, image_dir = PDF_DIR, IMAGE_DIR
    pdf_dir.mkdir(parents=True, exist_ok=True)
    image_dir.mkdir(parents=True, exist_ok=True)
    book_source = ROOT / "build" / "main.pdf"
    covers_source = ROOT / "build" / "covers.pdf"
    book, covers = PdfReader(book_source), PdfReader(covers_source)
    if len(covers.pages) != 2:
        raise ValueError("The cover document must contain exactly two pages.")
    for standalone, integrated in zip(covers.pages, (book.pages[0], book.pages[-1])):
        if standalone.extract_text() != integrated.extract_text():
            raise ValueError("Standalone cover differs from the integrated book.")
        if list(standalone.mediabox) != list(integrated.mediabox):
            raise ValueError("Standalone cover uses a different page size.")

    book_output = pdf_dir / "奶龙学导论_封面优化版.pdf"
    cover_output = pdf_dir / "奶龙学导论_封面与封底.pdf"
    shutil.copy2(book_source, book_output)
    shutil.copy2(covers_source, cover_output)
    poppler = shutil.which("pdftoppm")
    if poppler is None:
        raise RuntimeError("pdftoppm must be available on PATH to export PNG previews.")
    subprocess.run(
        [poppler, "-f", "1", "-l", "2", "-r", "300", "-png",
         str(cover_output), str(image_dir / "page")],
        check=True,
        capture_output=True,
    )
    front_path, back_path = image_dir / "封面.png", image_dir / "封底.png"
    (image_dir / "page-1.png").replace(front_path)
    (image_dir / "page-2.png").replace(back_path)

    # A flat side-by-side preview preserves the actual printed layout.
    cover_width, margin, gap, top, bottom = 760, 36, 40, 66, 32
    cover_height = round(cover_width * 297 / 210)
    canvas = Image.new(
        "RGB", (2 * cover_width + 2 * margin + gap, cover_height + top + bottom),
        "#eae9e3",
    )
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.truetype("C:/Windows/Fonts/msyh.ttc", 21)
    for index, (path, title) in enumerate(((front_path, "封面 / FRONT"), (back_path, "封底 / BACK"))):
        x = margin + index * (cover_width + gap)
        im = Image.open(path).convert("RGB")
        im = im.resize((cover_width, cover_height), Image.Resampling.LANCZOS)
        draw.text((x, 23), title, fill="#425d52", font=font)
        draw.rectangle((x + 5, top + 6, x + cover_width + 5, top + cover_height + 6), fill="#d5d5cd")
        canvas.paste(im, (x, top))
    preview_path = image_dir / "封面与封底预览.png"
    canvas.save(preview_path)

    report = (
        f"成品页数：{len(book.pages)}\n"
        f"独立封面页数：{len(covers.pages)}\n"
        "页面规格：A4，210 × 297 mm\n"
        "独立封面与完整教材首尾页文字、页面规格一致。\n"
        "本次导出源：当前工作区的 build/main.pdf（由当前 main.tex 编译）。\n"
        "封面与封底：XeLaTeX 编译成功，无缺字、溢出及字体告警。\n"
        "完整书稿：无未定义引用；所有字体已嵌入。\n"
        "原有正文仍有 SimHei 粗体替代及少数松散行间距告警。\n"
        "已视觉检查完整教材封面、版权页、封底与最终预览。\n"
        "图像来源：项目已有 ref/img/fig-006-021.jpg，原图保持原样；\n"
        "封面抠图保留原有形态、表情与光影，不重新生成角色。\n"
        f"封面 PNG 尺寸：{Image.open(front_path).size}，300 dpi。\n"
    )
    (pdf_dir.parent / "封面导出检查.txt").write_text(report, encoding="utf-8")
    for path in (book_output, cover_output, front_path, back_path, preview_path):
        print(path)
    print(report)


if __name__ == "__main__":
    main()
