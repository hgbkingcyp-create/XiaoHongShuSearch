"""
交付物生成器：把 data/*.json 的测试，转成自包含的 HTML「测试包」。

这就是买家下单后自动发货的内容（简版：零后端）。用途：
  - 直接当"发货内容"（文字/图文）
  - 转 PDF / 截图成图片
  - 上传到任意静态托管，作为链接发货

用法：python3 generate_deliverable.py  →  生成 deliverables/<id>.html（所有测试）
"""
import json
from pathlib import Path

DATA = Path(__file__).parent / "data"
OUT = Path(__file__).parent / "deliverables"

CSS = """
:root{--rose:#ff5c7a;--violet:#b44ce0;--ink:#2b2430;--muted:#9a8f9e;--line:#f0e8f2;}
*{box-sizing:border-box;margin:0;padding:0;}
body{font-family:-apple-system,"PingFang SC","Microsoft YaHei",sans-serif;color:var(--ink);line-height:1.8;background:#faf8fb;padding:32px 16px;}
.page{max-width:640px;margin:0 auto;background:#fff;border-radius:20px;padding:40px 32px;box-shadow:0 8px 30px rgba(180,76,224,.08);}
.cover{text-align:center;padding-bottom:28px;border-bottom:2px solid var(--line);margin-bottom:28px;}
.cover .badge{display:inline-block;background:linear-gradient(135deg,#ff5c7a,#c44ce0);color:#fff;font-size:12px;font-weight:700;padding:5px 14px;border-radius:20px;letter-spacing:2px;}
.cover h1{font-size:28px;font-weight:800;margin:14px 0 6px;}
.cover .sub{color:var(--muted);font-size:14px;}
.cover .meta{margin-top:12px;font-size:12px;color:var(--muted);}
h2.sec{font-size:18px;font-weight:800;margin:28px 0 16px;padding-left:12px;border-left:4px solid;border-image:linear-gradient(180deg,#ff5c7a,#c44ce0) 1;}
.q{margin-bottom:22px;}
.q .qn{font-weight:700;font-size:15px;margin-bottom:8px;}
.q .qn i{display:inline-grid;place-items:center;width:22px;height:22px;border-radius:7px;background:linear-gradient(135deg,#ff5c7a,#c44ce0);color:#fff;font-style:normal;font-size:13px;margin-right:8px;}
.q .opts{display:grid;grid-template-columns:1fr 1fr;gap:8px;}
.q .op{background:#faf7fc;border:1px solid var(--line);border-radius:10px;padding:8px 12px;font-size:14px;}
.q .op b{color:var(--violet);margin-right:6px;}
.scoring{background:linear-gradient(135deg,#fff7f9,#f7f0ff);border-radius:14px;padding:18px 20px;font-size:15px;}
.scoring b{color:var(--rose);}
.result{border:1px solid var(--line);border-radius:16px;padding:24px;margin-bottom:20px;}
.result .rhead{margin-bottom:12px;}
.result .rtype{font-size:20px;font-weight:800;background:linear-gradient(135deg,#ff5c7a,#c44ce0);-webkit-background-clip:text;background-clip:text;color:transparent;}
.result .rtag{color:var(--muted);font-size:13px;}
.result .hook{font-size:15px;font-weight:600;color:#4a4152;margin-bottom:12px;}
.result h4{font-size:13px;color:var(--rose);margin:12px 0 4px;}
.result p,.result li{font-size:14px;color:#4a4152;}
.result ul{list-style:none;padding:0;}
.result li{padding-left:16px;position:relative;margin-bottom:4px;}
.result li::before{content:"✦";color:var(--rose);position:absolute;left:0;font-size:12px;}
.foot{text-align:center;color:var(--muted);font-size:12px;margin-top:28px;padding-top:16px;border-top:1px solid var(--line);}
@media print{body{background:#fff;padding:0;}.page{box-shadow:none;}}
"""


def esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def render_questions(questions):
    out = ['<h2 class="sec">一、测试题目</h2>']
    for q in questions:
        opts = "".join(
            f'<div class="op"><b>{o["key"]}</b>{esc(o["text"])}</div>'
            for o in q["options"]
        )
        out.append(
            f'<div class="q"><div class="qn"><i>{q["id"]}</i>{esc(q["text"])}</div>'
            f'<div class="opts">{opts}</div></div>'
        )
    return "".join(out)


def render_results(results):
    out = ['<h2 class="sec">三、结果对照</h2>',
           '<p style="color:#9a8f9e;font-size:13px;margin-bottom:16px;">根据你计分最多的字母，找到对应类型阅读。</p>']
    for r in results:
        strengths = "".join(f"<li>{esc(s)}</li>" for s in r["strengths"])
        out.append(
            f'<div class="result"><div class="rhead">'
            f'<div class="rtype">{esc(r["type"])}</div>'
            f'<div class="rtag">{esc(r["tagline"])}</div></div>'
            f'<div class="hook">{esc(r["hook"])}</div>'
            f'<h4>性格画像</h4><p>{esc(r["portrait"])}</p>'
            f'<h4>你的三个隐藏优势</h4><ul>{strengths}</ul>'
            f'<h4>一个要警惕的盲区</h4><p>{esc(r["blindspot"])}</p>'
            f'<h4>给你的建议</h4><p>{esc(r["advice"])}</p></div>'
        )
    return "".join(out)


def render_test(test):
    scoring = ("<div class=\"scoring\"><b>计分方式：</b>数一下你选的 "
               "<b>A、B、C、D</b> 各有多少个，<b>最多的那个字母</b>就是你的类型。"
               "例如 8 个 A、3 个 B、1 个 C、0 个 D，那你就是 A 型。</div>")
    return (
        "<!DOCTYPE html><html lang=\"zh-CN\"><head><meta charset=\"utf-8\">"
        f"<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
        f"<title>{esc(test['title'])}</title><style>{CSS}</style></head><body>"
        f"<div class=\"page\">"
        f"<div class=\"cover\"><span class=\"badge\">{esc(test['category'])}</span>"
        f"<h1>{esc(test['title'])}</h1>"
        f"<div class=\"sub\">{esc(test['subtitle'])}</div>"
        f"<div class=\"meta\">共 {len(test['questions'])} 题 · 约 3 分钟 · 仅供娱乐</div></div>"
        f"{render_questions(test['questions'])}"
        f"<h2 class=\"sec\">二、计分方式</h2>{scoring}"
        f"{render_results(test['results'])}"
        f"<div class=\"foot\">仅供娱乐 · 愿你更懂自己 ✨</div>"
        f"</div></body></html>"
    )


def main():
    OUT.mkdir(exist_ok=True)
    for path in sorted(DATA.glob("*.json")):
        with open(path, encoding="utf-8") as f:
            test = json.load(f)
        html = render_test(test)
        out_path = OUT / f"{test['id']}.html"
        out_path.write_text(html, encoding="utf-8")
        print(f"✅ 生成 {out_path.relative_to(OUT.parent)} ({len(html)} 字节)")


if __name__ == "__main__":
    main()
