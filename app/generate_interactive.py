"""
互动交付物生成器：把 data/*.json 里 format=="interactive" 的测试，
生成「场景式互动」自包含 HTML —— 买家打开就是一场小游戏：

  故事开场 → 逐幕场景（夜色车窗 + 流动灯火动效）→ 分支推进 → 结局报告

v2 支持（数据契约见 AGENTS.md）：
  - questions[].show_if = {q: 前置题id, in: [key,...]}：不满足则跳过该题（剧情分支）
  - questions[].options[].flag = "cat"：选中即埋下隐藏标记
  - results[].secret = true：隐藏结局；主类型命中后再查 <key>2 隐藏变体
  - results[].rarity / note / partner：稀有度、NPC 留言、契合提示（结果页自动渲染）
  - 计分：A/B/C/D 票数最多者为主类型（并列取先出现者，与 engine.py 一致）；
    持有 cat 标记 → 命中主类型的隐藏结局（A2/B2/C2/D2）

零依赖：纯 HTML+CSS+JS，自包含，任何浏览器直接打开。
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
.badge.secret{color:#ffe9f7;border-color:#ff8ad4;background:rgba(255,138,212,.12);box-shadow:0 0 18px rgba(255,138,212,.35);}
h1.title{font-size:27px;font-weight:800;letter-spacing:1px;line-height:1.4;}
.sub{color:var(--muted);font-size:14px;margin-top:6px;}
.intro-text{font-size:15.5px;margin-top:16px;color:#efe9db;}
.meta{font-size:12px;color:var(--muted);margin-top:14px;}
.meta .hint{color:var(--glow);}
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
.opt.cat{border-color:rgba(255,138,212,.5);}
.opt.cat .k{background:rgba(255,138,212,.25);color:#ffb3e2;}
.caret{display:inline-block;width:2px;height:1em;background:var(--glow);vertical-align:-2px;animation:blink .8s steps(1) infinite;}
@keyframes blink{50%{opacity:0}}
.flash{position:fixed;inset:0;background:radial-gradient(circle,rgba(255,138,212,.35),transparent 70%);
opacity:0;pointer-events:none;z-index:9;}
.flash.go{animation:flash 1.4s ease-out;}
@keyframes flash{0%{opacity:0}18%{opacity:1}100%{opacity:0}}
.toast{position:fixed;top:18px;left:50%;transform:translateX(-50%) translateY(-70px);z-index:10;
background:rgba(28,18,48,.92);border:1px solid #ff8ad4;color:#ffd6f2;font-size:13px;font-weight:700;
padding:9px 18px;border-radius:30px;transition:transform .45s cubic-bezier(.2,.8,.3,1);white-space:nowrap;}
.toast.show{transform:translateX(-50%) translateY(0);}

/* —— 结果 —— */
.rtype{font-size:28px;font-weight:800;margin-top:14px;line-height:1.35;
background:linear-gradient(135deg,var(--glow),var(--accent));-webkit-background-clip:text;background-clip:text;color:transparent;}
.rarity{display:inline-block;margin-top:10px;font-size:12px;color:var(--muted);
border:1px dashed var(--line);border-radius:14px;padding:3px 12px;}
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
.note{margin-top:18px;background:rgba(255,255,255,.05);border-left:3px solid var(--glow);
border-radius:0 12px 12px 0;padding:12px 14px;font-size:13.5px;color:var(--muted);font-style:italic;}
.partner{margin-top:10px;background:rgba(255,138,212,.08);border:1px solid rgba(255,138,212,.25);
border-radius:12px;padding:12px 14px;font-size:13.5px;color:#f6d9ee;}
.partner b{color:#ffb3e2;}

/* —— 足迹回放 —— */
.jline{display:flex;gap:12px;margin-bottom:12px;align-items:flex-start;}
.jstop{flex:none;width:24px;height:24px;border-radius:50%;display:grid;place-items:center;
font-size:12px;font-weight:800;background:rgba(255,255,255,.1);color:var(--glow);
border:1px solid var(--line);margin-top:2px;}
.jline .jscene{font-size:12.5px;color:var(--muted);font-style:italic;line-height:1.6;}
.jline .jpick{font-size:14px;color:#efe9db;margin-top:2px;}
.jline.jcat .jstop{background:rgba(255,138,212,.22);color:#ffb3e2;border-color:rgba(255,138,212,.5);}
.jline.jcat .jpick{color:#ffd6f2;font-weight:600;}
.jsum{margin-top:6px;font-size:13px;color:var(--muted);background:rgba(255,255,255,.05);
border-radius:12px;padding:10px 12px;}
.jsum b{color:var(--glow);}
.foot{text-align:center;color:var(--muted);font-size:12px;margin-top:22px;letter-spacing:.5px;}
.share-tip{margin-top:16px;font-size:13px;color:var(--muted);text-align:center;}
@media print{body{background:#171233;-webkit-print-color-adjust:exact;print-color-adjust:exact;}.btn{display:none;}}
"""


def build_html(test, css):
    payload = json.dumps(test, ensure_ascii=False, separators=(",", ":"))
    payload = payload.replace("</", "<\\/")
    meta_line = test.get("meta_note", "")
    return (
        "<!DOCTYPE html><html lang=\"zh-CN\"><head><meta charset=\"utf-8\">"
        "<meta name=\"viewport\" content=\"width=device-width,initial-scale=1\">"
        f"<title>{esc(test['title'])}</title>"
        f"<style>{css}</style></head><body>"
        "<div class=\"flash\" id=\"flash\"></div><div class=\"toast\" id=\"toast\"></div>"
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
        "<div class=\"meta\">"
        f"{len({q['id'] for q in test['questions']})} 站 · 约 4 分钟 · {esc(test.get('disclaimer', '仅供娱乐'))}"
        + (f"<br><span class=\"hint\">🕯 {esc(meta_line)}</span>" if meta_line else "")
        + "</div>"
        "<button class=\"btn\" onclick=\"begin()\">🚂 登上这趟列车</button>"
        "</div></div>"

        # —— 答题 ——
        "<div class=\"screen\" id=\"quiz\">"
        "<div class=\"q-top\"><b id=\"stop\"></b><span id=\"total\"></span></div>"
        "<div class=\"progress\"><i id=\"bar\"></i></div>"
        "<div class=\"scene\" id=\"scene\"></div>"
        "<div class=\"qtext\" id=\"qtext\"></div>"
        "<div id=\"opts\"></div>"
        "</div>"

        # —— 结果 ——
        "<div class=\"screen\" id=\"result\"><div class=\"card\" id=\"rcard\"></div>"
        "<div class=\"share-tip\">📸 截图分享你的结局 —— 你的路线，可能和别人不一样</div>"
        "<button class=\"btn\" onclick=\"location.reload()\">↻ 重新上车</button></div>"

        "<div class=\"foot\">" + esc(test.get("disclaimer", "仅供娱乐")) + " · 愿你到站时眼里有光 ✨</div>"
        "</div>"

        "<script>\nconst TEST=" + payload + ";\n" + RUNTIME_JS + "\n</script>"
        "</body></html>"
    )


RUNTIME_JS = r"""
const $ = (id) => document.getElementById(id);
const esc = (s) => (s || '').replace(/[&<>"]/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const TOTAL = new Set(TEST.questions.map(q => q.id)).size;  // 实际要答的站数
let cursor = 0;          // TEST.questions 的扫描指针
let answered = 0;        // 已答站数
const byQid = {};        // 题 id -> 所选 key（供分支条件查询）
const flags = new Set(); // 隐藏标记（如 'cat'）

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

// 分支判定：show_if = {q: 前置题id, in:[key...]}
function visible(q) {
  if (!q.show_if) return true;
  const a = byQid[q.show_if.q];
  return a && q.show_if.in.indexOf(a) !== -1;
}

// 按顺序找下一道命中分支条件的题
function nextQuestion() {
  while (cursor < TEST.questions.length) {
    const q = TEST.questions[cursor];
    cursor++;
    if (visible(q)) return q;
  }
  return null;
}

function begin() {
  cursor = 0; answered = 0;
  Object.keys(byQid).forEach(k => delete byQid[k]);
  flags.clear();
  ask();
  show('quiz');
}

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

let current = null;
function ask() {
  current = nextQuestion();
  if (!current) { renderResult(); return; }
  const q = current;
  $('stop').textContent = '第 ' + (answered + 1) + ' 站 / 共 ' + TOTAL + ' 站';
  $('total').textContent = TEST.category;
  $('bar').style.width = (answered / TOTAL) * 100 + '%';
  typeScene(q.scene || '');
  $('qtext').textContent = q.text;
  $('opts').innerHTML = q.options.map((o, i) =>
    '<button class="opt' + (o.flag ? ' cat' : '') + '" onclick="pick(' + i + ')"><span class="k">' +
    (o.flag === 'cat' ? '🐈' : esc(o.key)) + '</span><span>' + esc(o.text) + '</span></button>'
  ).join('');
  window.scrollTo({ top: 0 });
}

function pick(i) {
  const q = current, o = q.options[i];
  byQid[q.id] = o.key;
  answered++;
  if (o.flag) {
    flags.add(o.flag);
    if (o.flag === 'cat') {
      const f = $('flash'), t = $('toast');
      f.classList.remove('go'); void f.offsetWidth; f.classList.add('go');
      t.textContent = '🐈 小黑猫好像……记住你了';
      t.classList.add('show');
      setTimeout(() => t.classList.remove('show'), 2400);
    }
  }
  ask();
}

// 计分：票数最多者为「主类型」（并列取先出现者）；抱过猫 → 命中该主类型的隐藏结局 <key>2
function score() {
  const order = [], count = {};
  Object.keys(byQid).forEach(qid => {
    const k = byQid[qid];
    if (!(k in count)) { count[k] = 0; order.push(k); }
    count[k]++;
  });
  let best = order[0];
  order.forEach(k => { if (count[k] > count[best]) best = k; });
  const secretKey = best + '2';
  const hit = flags.has('cat') && TEST.results.find(r => r.key === secretKey);
  return { main: best, tally: count, r: hit || TEST.results.find(x => x.key === best) };
}

// 结局彩蛋：把「你实际走过的站」回放成一段足迹（含分支路线 + 是否抱过猫）
function journey(r) {
  const lines = [];
  TEST.questions.forEach(q => {
    if (!(q.id in byQid)) return;              // 分支未命中的题，跳过
    const k = byQid[q.id];
    const o = q.options.find(x => x.key === k);
    lines.push({ scene: q.scene, text: o ? o.text : k, cat: !!o && o.flag === 'cat' });
  });
  let html = '<div class="sec"><h3>🗺 这一路的你（' + lines.length + ' 站足迹回放）</h3>';
  html += lines.map((l, i) =>
    '<div class="jline' + (l.cat ? ' jcat' : '') + '">' +
    '<span class="jstop">' + (i + 1) + '</span>' +
    '<div><div class="jscene">' + esc(l.scene) + '</div>' +
    '<div class="jpick">你的选择：' + esc(l.text) + (l.cat ? ' 🐈' : '') + '</div></div></div>').join('');
  html += '<div class="jsum">' + (r.secret
    ? '这条路线是<b>你独有的</b>——全车厢没人和你走了一模一样的站。'
    : '你的路线里有 <b>2 个岔口</b>，换一个选择，就是另一段风景。') + '</div></div>';
  return html;
}

function renderResult() {
  const s = score(), r = s.r, n = TOTAL;
  const bars = Object.keys(s.tally).sort((a, b) => s.tally[b] - s.tally[a]).map(k =>
    '<div style="display:flex;align-items:center;gap:8px;margin-bottom:6px;font-size:12.5px;color:var(--muted)">' +
    '<span style="width:16px;font-weight:800;color:var(--glow)">' + k + '</span>' +
    '<div style="flex:1;height:6px;background:rgba(255,255,255,.08);border-radius:6px;overflow:hidden">' +
    '<i style="display:block;height:100%;width:' + (s.tally[k] / n * 100) + '%;background:linear-gradient(90deg,var(--glow),var(--accent));border-radius:6px"></i></div>' +
    '<span>' + s.tally[k] + ' 票</span></div>').join('');
  $('rcard').innerHTML =
    '<span class="badge' + (r.secret ? ' secret' : '') + '">' +
    (r.secret ? '🌟 隐藏结局达成 · 你的路线独一无二' : '列车到站 · 你的专属结局') + '</span>' +
    '<div class="rtype">' + esc(r.type) + '</div>' +
    '<div class="rtag">' + esc(r.tagline) + '</div>' +
    (r.rarity ? '<span class="rarity">🎭 ' + esc(r.rarity) + '</span>' : '') +
    '<div class="hook" style="margin-top:14px">' + esc(r.hook) + '</div>' +
    '<div style="margin-top:14px">' + bars + '</div>' +
    '<div class="sec"><h3>🪞 人格画像</h3><p>' + esc(r.portrait) + '</p></div>' +
    '<div class="sec"><h3>💪 你的三个隐藏优势</h3><ul>' + r.strengths.map(x => '<li>' + esc(x) + '</li>').join('') + '</ul></div>' +
    '<div class="sec"><h3>⚠️ 一个要警惕的盲区</h3><p>' + esc(r.blindspot) + '</p></div>' +
    '<div class="sec"><h3>💡 这趟列车给你的建议</h3><p>' + esc(r.advice) + '</p></div>' +
    journey(r) +
    (r.note ? '<div class="note">🚂 ' + esc(r.note) + '</div>' : '') +
    (r.partner ? '<div class="partner"><b>🤝 下一站 · 缘分提示</b><br>' + esc(r.partner) + '</div>' : '');
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
