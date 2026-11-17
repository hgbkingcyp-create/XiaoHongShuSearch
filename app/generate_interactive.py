"""
互动交付物生成器：把 data/*.json 里 format=="interactive" 的测试，
生成「场景式互动」自包含 HTML —— 买家打开就是一场小游戏：

  故事开场 → 一屏一个场景（夜色车窗 + 流动灯火动效）→ 点选推进 → 出完整报告

与传统静态试卷包（generate_deliverable.py）的区别：
  - 体验：沉浸式的逐场景选择，像在玩文字冒险，截图分享率远高于"一份文档"
  - 内容：买家已付费，所以报告直接完整解锁，无需再看付费墙
  - 零依赖：纯 HTML+CSS+JS，计分逻辑内嵌，微信/小红书画板/任何浏览器都能打开

题库 JSON 需要的互动字段（其余字段与传统格式一致）：
  format: "interactive"
  intro:  开场故事文案
  theme:  {sky1, sky2, glow, accent, text}  场景配色
  questions[]: 每题多一个 scene（场景旁白），text 为本幕问题
  results[]:   同传统格式（type/tagline/hook/portrait/strengths/blindspot/advice）

用法：python3 generate_interactive.py  →  deliverables/<id>.html
"""
import json
from pathlib import Path

DATA = Path(__file__).parent / "data"
OUT = Path(__file__).parent / "deliverables"


def esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


CSS = """
:root{--sky1:%SKY1%;--sky2:%SKY2%;--glow:%GLOW%;--accent:%ACCENT%;--text:%TEXT%;
--card:rgba(255,255,255,.07);--line:rgba(255,255,255,.14);--muted:rgba(245,241,232,.55);}
*{box-sizing:border-box;margin:0;padding:0;-webkit-tap-highlight-color:transparent;}
html,body{min-height:100%;}
body{font-family:-apple-system,"PingFang SC","Hiragino Sans GB","Microsoft YaHei",sans-serif;
color:var(--text);line-height:1.75;background:linear-gradient(180deg,var(--sky1) 0%,var(--sky2) 100%);
background-attachment:fixed;display:flex;justify-content:center;padding:24px 16px 48px;}
.stage{width:100%;max-width:460px;position:relative;}

/* —— 车窗 —— */
.window{position:relative;height:200px;border-radius:18px;overflow:hidden;flex:none;
background:linear-gradient(180deg,var(--sky1) 0%,var(--sky2) 78%,rgba(0,0,0,.55) 100%);
border:6px solid rgba(20,14,40,.9);box-shadow:0 0 0 2px var(--line),0 14px 40px rgba(0,0,0,.45);}
.moon{position:absolute;top:26px;right:38px;width:38px;height:38px;border-radius:50%;
background:radial-gradient(circle at 35% 35%,#fffbe8,var(--glow));box-shadow:0 0 26px 8px rgba(255,210,122,.35);}
.star{position:absolute;width:2px;height:2px;border-radius:50%;background:#fff;animation:tw 2.6s ease-in-out infinite;}
@keyframes tw{0%,100%{opacity:.2}50%{opacity:1}}
.streak{position:absolute;left:-40%;width:40%;height:2px;border-radius:2px;
background:linear-gradient(90deg,transparent,var(--glow),transparent);opacity:.7;animation:whoosh 2.4s linear infinite;}
.streak.s2{bottom:52px;width:26%;animation-duration:3.4s;animation-delay:.9s;opacity:.45;}
.streak.s1{bottom:74px;}
@keyframes whoosh{from{transform:translateX(0)}to{transform:translateX(340%)}}
.rail{position:absolute;left:0;right:0;bottom:16px;height:3px;
background:repeating-linear-gradient(90deg,rgba(255,255,255,.4) 0 14px,transparent 14px 34px);
animation:rails .5s linear infinite;}
@keyframes rails{from{background-position-x:0}to{background-position-x:-34px}}
.window .hills{position:absolute;left:0;right:0;bottom:0;height:44px;
background:radial-gradient(120px 60px at 18% 100%,rgba(0,0,0,.5),transparent 70%),
radial-gradient(160px 70px at 58% 100%,rgba(0,0,0,.45),transparent 70%),
radial-gradient(120px 50px at 92% 100%,rgba(0,0,0,.5),transparent 70%);}

/* —— 结构 —— */
.screen{display:none;}
.screen.on{display:block;animation:fadeUp .45s cubic-bezier(.2,.8,.3,1) both;}
@keyframes fadeUp{from{opacity:0;transform:translateY(14px)}to{opacity:1;transform:none}}
.card{background:var(--card);backdrop-filter:blur(12px);border:1px solid var(--line);
border-radius:20px;padding:24px 20px;margin-top:16px;}

/* —— 开场 —— */
.badge{display:inline-block;font-size:12px;font-weight:700;letter-spacing:2px;color:var(--glow);
border:1px solid var(--glow);border-radius:20px;padding:4px 14px;margin-bottom:14px;}
h1.title{font-size:27px;font-weight:800;letter-spacing:1px;line-height:1.4;}
.sub{color:var(--muted);font-size:14px;margin-top:6px;}
.intro-text{font-size:15.5px;margin-top:16px;color:#efe9db;}
.meta{font-size:12px;color:var(--muted);margin-top:14px;}
.btn{display:block;width:100%;border:none;border-radius:18px;padding:16px;font-size:16.5px;
font-weight:800;letter-spacing:1px;cursor:pointer;margin-top:20px;color:#1c1230;
background:linear-gradient(135deg,var(--glow),var(--accent));box-shadow:0 10px 26px rgba(255,138,92,.35);
transition:transform .15s;}
.btn:active{transform:scale(.98);}

/* —— 问题 —— */
.q-top{display:flex;justify-content:space-between;align-items:center;font-size:12.5px;color:var(--muted);margin-top:18px;}
.q-top b{color:var(--glow);letter-spacing:1px;}
.progress{height:6px;background:rgba(255,255,255,.1);border-radius:8px;overflow:hidden;margin:10px 0 4px;}
.progress i{display:block;height:100%;border-radius:8px;background:linear-gradient(90deg,var(--glow),var(--accent));
transition:width .4s cubic-bezier(.2,.8,.3,1);}
.scene{font-size:14.5px;color:var(--muted);font-style:italic;margin-top:10px;min-height:44px;}
.qtext{font-size:20px;font-weight:800;line-height:1.5;margin:12px 0 6px;}
.opt{display:flex;align-items:flex-start;gap:10px;width:100%;text-align:left;margin-top:12px;
background:var(--card);border:1.5px solid var(--line);border-radius:16px;padding:14px 15px;
font-size:15.5px;color:var(--text);cursor:pointer;font-family:inherit;line-height:1.5;
transition:border-color .15s,background .15s,transform .1s;}
.opt:active{transform:scale(.985);border-color:var(--glow);background:rgba(255,210,122,.12);}
.opt .k{flex:none;width:26px;height:26px;border-radius:9px;display:grid;place-items:center;
font-size:13px;font-weight:800;background:rgba(255,255,255,.12);color:var(--glow);margin-top:1px;}
.caret{display:inline-block;width:2px;height:1em;background:var(--glow);vertical-align:-2px;animation:blink .8s steps(1) infinite;}
@keyframes blink{50%{opacity:0}}

/* —— 结果 —— */
.rtype{font-size:28px;font-weight:800;margin-top:14px;
background:linear-gradient(135deg,var(--glow),var(--accent));-webkit-background-clip:text;background-clip:text;color:transparent;}
.rtag{color:var(--muted);font-size:14px;margin:2px 0 16px;}
.hook{background:rgba(255,210,122,.09);border:1px solid rgba(255,210,122,.25);border-radius:16px;
padding:16px;font-size:16px;font-weight:600;line-height:1.7;position:relative;margin-bottom:6px;}
.hook::before{content:"“";position:absolute;top:-10px;left:10px;font-size:44px;color:var(--glow);opacity:.4;font-family:Georgia,serif;}
.sec{margin-top:18px;}
.sec h3{font-size:13.5px;font-weight:800;color:var(--glow);letter-spacing:1px;margin-bottom:6px;}
.sec p{font-size:15px;color:#efe9db;}
.sec ul{list-style:none;}
.sec li{font-size:14.5px;padding:10px 12px;background:var(--card);border:1px solid var(--line);
border-radius:12px;margin-bottom:8px;color:#efe9db;}
.sec li::before{content:"✦";color:var(--glow);margin-right:8px;}
.foot{text-align:center;color:var(--muted);font-size:12px;margin-top:22px;letter-spacing:.5px;}
.share-tip{margin-top:16px;font-size:13px;color:var(--muted);text-align:center;}
@media print{body{background:#171233;-webkit-print-color-adjust:exact;print-color-adjust:exact;}.btn{display:none;}}
"""


def build_html(test, css):
    payload = json.dumps(test, ensure_ascii=False, separators=(",", ":"))
    # 防止 JSON 内容里的 "</script>" 提前闭合标签
    payload = payload.replace("</", "<\\/")
    return (
        "<!DOCTYPE html><html lang=\"zh-CN\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
        f"<title>{esc(test['title'])}</title>"
        f"<style>{css}</style></head><body>"
        "<div class=\"stage\">"
        "<div class=\"window\"><div class=\"moon\"></div><div class=\"hills\"></div>"
        "<div class=\"streak s1\"></div><div class=\"streak s2\"></div><div class=\"rail\"></div></div>"

        # —— 开场 ——
        "<div class=\"screen on\" id=\"intro\">"
        "<div class=\"card\">"
        f"<span class=\"badge\">{esc(test['category'])}</span>"
        f"<h1 class=\"title\">{esc(test['title'])}</h1>"
        f"<div class=\"sub\">{esc(test['subtitle'])}</div>"
        f"<div class=\"intro-text\">{esc(test.get('intro', ''))}</div>"
        f"<div class=\"meta\">{len(test['questions'])} 幕 · 约 3 分钟 · {esc(test.get('disclaimer', '仅供娱乐'))}</div>"
        "<button class=\"btn\" onclick=\"begin()\">🚂 登上这趟列车</button>"
        "</div></div>"

        # —— 答题（JS 渲染）——
        "<div class=\"screen\" id=\"quiz\">"
        "<div class=\"q-top\"><b id=\"stop\"></b><span id=\"total\"></span></div>"
        "<div class=\"progress\"><i id=\"bar\"></i></div>"
        "<div class=\"scene\" id=\"scene\"></div>"
        "<div class=\"qtext\" id=\"qtext\"></div>"
        "<div id=\"opts\"></div>"
        "</div>"

        # —— 结果（JS 渲染）——
        "<div class=\"screen\" id=\"result\"><div class=\"card\" id=\"rcard\"></div>"
        "<div class=\"share-tip\">📸 截图分享你的那一幕 —— 或许你的朋友也想上车</div>"
        "<button class=\"btn\" onclick=\"location.reload()\">↻ 重新上车</button></div>"

        "<div class=\"foot\">" + esc(test.get("disclaimer", "仅供娱乐")) + " · 愿你到站时眼里有光 ✨</div>"
        "</div>"

        "<script>\nconst TEST=" + payload + ";\n" + RUNTIME_JS + "\n</script>"
        "</body></html>"
    )


RUNTIME_JS = r"""
const $ = (id) => document.getElementById(id);
const esc = (s) => (s || '').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const answers = [];
let step = 0;

// 星空
(function stars() {
  const w = document.querySelector('.window');
  for (let i = 0; i < 36; i++) {
    const s = document.createElement('div');
    s.className = 'star';
    s.style.left = Math.random() * 100 + '%';
    s.style.top = Math.random() * 60 + '%';
    s.style.animationDelay = (Math.random() * 2.6).toFixed(2) + 's';
    if (Math.random() < .2) { s.style.width = s.style.height = '3px'; }
    w.appendChild(s);
  }
})();

function show(id) {
  document.querySelectorAll('.screen').forEach(el => el.classList.remove('on'));
  $(id).classList.add('on');
}

function begin() { step = 0; renderQ(); show('quiz'); }

// 打字机旁白
let typeTimer = null;
function typeScene(text) {
  clearInterval(typeTimer);
  const el = $('scene');
  el.innerHTML = '<span class="caret"></span>';
  let i = 0;
  typeTimer = setInterval(() => {
    i++;
    el.innerHTML = esc(text.slice(0, i)) + (i < text.length ? '<span class="caret"></span>' : '');
    if (i >= text.length) clearInterval(typeTimer);
  }, 24);
}

function renderQ() {
  const q = TEST.questions[step], n = TEST.questions.length;
  $('stop').textContent = '第 ' + (step + 1) + ' 站 / 共 ' + n + ' 站';
  $('total').textContent = TEST.category;
  $('bar').style.width = (step / n) * 100 + '%';
  typeScene(q.scene || '');
  $('qtext').textContent = q.text;
  $('opts').innerHTML = q.options.map((o, i) =>
    '<button class="opt" onclick="pick(' + i + ')"><span class="k">' + esc(o.key) + '</span><span>' + esc(o.text) + '</span></button>'
  ).join('');
  window.scrollTo({ top: 0 });
}

function pick(i) {
  answers.push(TEST.questions[step].options[i].key);
  step++;
  if (step < TEST.questions.length) { renderQ(); }
  else { renderResult(); }
}

// 计分：与后端 engine.py 完全一致（次数最多者命中，并列取先出现者）
function score() {
  const order = [], count = {};
  answers.forEach(k => { if (!(k in count)) { count[k] = 0; order.push(k); } count[k]++; });
  let best = order[0];
  order.forEach(k => { if (count[k] > count[best]) best = k; });
  return TEST.results.find(r => r.key === best);
}

function renderResult() {
  const r = score(), n = TEST.questions.length;
  const dist = {};
  answers.forEach(k => dist[k] = (dist[k] || 0) + 1);
  const bars = ['A', 'B', 'C', 'D'].filter(k => dist[k]).map(k =>
    '<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;font-size:12.5px;color:var(--muted)">' +
    '<span style="width:16px;font-weight:800;color:var(--glow)">' + k + '</span>' +
    '<div style="flex:1;height:6px;background:rgba(255,255,255,.08);border-radius:6px;overflow:hidden">' +
    '<i style="display:block;height:100%;width:' + (dist[k] / n * 100) + '%;background:linear-gradient(90deg,var(--glow),var(--accent));border-radius:6px"></i></div>' +
    '<span>' + dist[k] + ' 票</span></div>').join('');
  $('rcard').innerHTML =
    '<span class="badge">列车到站 · 你的专属结局</span>' +
    '<div class="rtype">' + esc(r.type) + '</div>' +
    '<div class="rtag">' + esc(r.tagline) + '</div>' +
    '<div class="hook">' + esc(r.hook) + '</div>' +
    '<div style="margin-top:14px">' + bars + '</div>' +
    '<div class="sec"><h3>🪞 人格画像</h3><p>' + esc(r.portrait) + '</p></div>' +
    '<div class="sec"><h3>💪 你的三个隐藏优势</h3><ul>' + r.strengths.map(s => '<li>' + esc(s) + '</li>').join('') + '</ul></div>' +
    '<div class="sec"><h3>⚠️ 一个要警惕的盲区</h3><p>' + esc(r.blindspot) + '</p></div>' +
    '<div class="sec"><h3>💡 这趟列车给你的建议</h3><p>' + esc(r.advice) + '</p></div>';
  show('result');
  window.scrollTo({ top: 0 });
}
"""


def main():
    OUT.mkdir(exist_ok=True)
    made = 0
    for path in sorted(DATA.glob("*.json")):
        with open(path, encoding="utf-8") as f:
            test = json.load(f)
        if test.get("format") != "interactive":
            continue
        theme = test.get("theme", {})
        defaults = {"sky1": "#0c1230", "sky2": "#2a1e4f", "glow": "#ffd27a",
                    "accent": "#ff8a5c", "text": "#f5f1e8"}
        css = CSS
        for k in defaults:
            css = css.replace(f"%{k.upper()}%", theme.get(k, defaults[k]))
        html = build_html(test, css)
        out_path = OUT / f"{test['id']}.html"
        out_path.write_text(html, encoding="utf-8")
        print(f"✅ 互动版 {out_path.relative_to(OUT.parent)} ({len(html)} 字节)")
        made += 1
    if not made:
        print("（没有 format=interactive 的测试）")


if __name__ == "__main__":
    main()
