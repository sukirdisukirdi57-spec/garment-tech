from pathlib import Path
from datetime import datetime
import shutil
import sys

T = Path("templates/component_detail.html")
C = Path("static/style.css")
MARK = "component-diagram-viewer-v1"

html = T.read_text(encoding="utf-8")
css = C.read_text(encoding="utf-8")

old = '''        {% if component["image_path"] %}
        <div class="component-image">
            <img
                src="{{ url_for('static', filename=component['image_path']) }}"
                alt="{{ component['component_name'] }}"
            >
        </div>
        {% endif %}'''

new = '''        {% if component["image_path"] %}
        <div class="component-image">
            <button type="button" id="diagram-open"
                    class="diagram-open"
                    aria-label="Perbesar diagram {{ component['component_name'] }}">
                <img
                    src="{{ url_for('static', filename=component['image_path']) }}"
                    alt="{{ component['component_name'] }}"
                    loading="lazy">
                <span>🔍 Ketuk gambar untuk memperbesar</span>
            </button>
        </div>
        {% endif %}'''

if MARK in html or MARK in css:
    sys.exit("BATAL: patch tampaknya sudah terpasang.")
if html.count(old) != 1 or html.count("</body>") != 1:
    sys.exit("BATAL: struktur template tidak sesuai; tidak ada file diubah.")

viewer = r'''
<!-- component-diagram-viewer-v1 -->
{% if component["image_path"] %}
<div id="diagram-viewer" class="diagram-viewer" role="dialog"
     aria-modal="true" aria-label="Diagram komponen" hidden>
  <div class="diagram-bar">
    <span id="diagram-zoom-label">Zoom 100%</span>
    <button type="button" data-act="out">−</button>
    <button type="button" data-act="in">+</button>
    <button type="button" data-act="reset">Reset</button>
    <button type="button" data-act="close" aria-label="Tutup">✕</button>
  </div>
  <div id="diagram-stage" class="diagram-stage">
    <img id="diagram-large"
         src="{{ url_for('static', filename=component['image_path']) }}"
         alt="{{ component['component_name'] }}" draggable="false">
  </div>
  <p class="diagram-help">Cubit untuk zoom · Geser untuk melihat detail · Esc untuk menutup</p>
</div>
<script>
(function () {
  "use strict";
  const viewer = document.getElementById("diagram-viewer");
  const opener = document.getElementById("diagram-open");
  const stage = document.getElementById("diagram-stage");
  const img = document.getElementById("diagram-large");
  const label = document.getElementById("diagram-zoom-label");
  if (!viewer || !opener || !stage || !img || !label) return;

  let s = 1, x = 0, y = 0, focusBefore;
  let pts = new Map(), sx = 0, sy = 0, px = 0, py = 0;
  let pinchD = 1, pinchS = 1, pinchMid = null;
  const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
  const distance = (a,b) => Math.hypot(a.x-b.x, a.y-b.y);
  const middle = (a,b) => ({x:(a.x+b.x)/2, y:(a.y+b.y)/2});

  function draw() {
    img.style.transform = `translate(${x}px,${y}px) scale(${s})`;
    img.style.cursor = s > 1 ? "grab" : "zoom-in";
    label.textContent = "Zoom " + Math.round(s*100) + "%";
  }
  function reset() { s=1; x=0; y=0; draw(); }
  function zoom(next, cx, cy) {
    const r=stage.getBoundingClientRect();
    cx-=r.left+r.width/2; cy-=r.top+r.height/2;
    next=clamp(next,1,6);
    const ratio=next/s;
    x=cx-(cx-x)*ratio; y=cy-(cy-y)*ratio; s=next;
    if (s===1) { x=0; y=0; }
    draw();
  }
  function close() {
    viewer.hidden=true;
    document.body.classList.remove("diagram-viewer-active");
    pts.clear(); reset();
    if (focusBefore) focusBefore.focus();
  }
  opener.addEventListener("click", () => {
    focusBefore=document.activeElement;
    reset(); viewer.hidden=false;
    document.body.classList.add("diagram-viewer-active");
    viewer.querySelector('[data-act="close"]').focus();
  });
  viewer.querySelectorAll("[data-act]").forEach(b => b.addEventListener("click", () => {
    const a=b.dataset.act;
    if (a==="close") close();
    if (a==="reset") reset();
    if (a==="in" || a==="out") {
      const r=stage.getBoundingClientRect();
      zoom(s*(a==="in"?1.25:0.8),r.left+r.width/2,r.top+r.height/2);
    }
  }));
  viewer.addEventListener("click", e => { if(e.target===viewer) close(); });
  document.addEventListener("keydown", e => {
    if(viewer.hidden) return;
    if(e.key==="Escape") close();
    if(e.key==="+" || e.key==="=") zoom(s*1.25,innerWidth/2,innerHeight/2);
    if(e.key==="-") zoom(s*0.8,innerWidth/2,innerHeight/2);
  });
  stage.addEventListener("wheel", e => {
    e.preventDefault();
    zoom(s*(e.deltaY<0?1.12:1/1.12),e.clientX,e.clientY);
  },{passive:false});

  stage.addEventListener("pointerdown", e => {
    if(e.pointerType==="mouse" && e.button!==0) return;
    e.preventDefault();
    stage.setPointerCapture(e.pointerId);
    pts.set(e.pointerId,{x:e.clientX,y:e.clientY});
    if(pts.size===1) {
      sx=e.clientX; sy=e.clientY; px=x; py=y;
    } else if(pts.size===2) {
      const p=[...pts.values()];
      pinchD=distance(p[0],p[1])||1;
      pinchS=s; pinchMid=middle(p[0],p[1]);
    }
  });
  stage.addEventListener("pointermove", e => {
    if(!pts.has(e.pointerId)) return;
    pts.set(e.pointerId,{x:e.clientX,y:e.clientY});
    if(pts.size>=2) {
      const p=[...pts.values()], d=distance(p[0],p[1])||1;
      const m=middle(p[0],p[1]), r=stage.getBoundingClientRect();
      const next=clamp(pinchS*d/(pinchD||1),1,6);
      const ox=pinchMid.x-r.left-r.width/2;
      const oy=pinchMid.y-r.top-r.height/2;
      const nx=m.x-r.left-r.width/2, ny=m.y-r.top-r.height/2;
      const ratio=next/s;
      x=nx-(ox-x)*ratio; y=ny-(oy-y)*ratio; s=next;
      pinchD=d; pinchS=s; pinchMid=m; draw();
    } else if(s>1) {
      x=px+e.clientX-sx; y=py+e.clientY-sy; draw();
    }
  });
  function end(e) {
    pts.delete(e.pointerId);
    if(pts.size===1) {
      const p=[...pts.values()][0];
      sx=p.x; sy=p.y; px=x; py=y;
    }
  }
  stage.addEventListener("pointerup",end);
  stage.addEventListener("pointercancel",end);
  stage.addEventListener("lostpointercapture",end);
  draw();
})();
</script>
{% endif %}
<!-- end component-diagram-viewer-v1 -->
'''

css_add = r'''
/* component-diagram-viewer-v1 */
.diagram-open {
  display:inline-flex; flex-direction:column; align-items:center; gap:8px;
  max-width:100%; padding:0; border:0; background:transparent;
  color:#334155; font:inherit; cursor:zoom-in; touch-action:manipulation;
}
.diagram-open img {
  display:block; max-width:100%; width:auto; height:auto;
  max-height:440px; object-fit:contain; border-radius:8px; background:#fff;
}
.diagram-open span {font-size:.9rem;color:#475569}
.diagram-viewer[hidden] {display:none!important}
.diagram-viewer {
  position:fixed; inset:0; z-index:10000; display:flex; flex-direction:column;
  box-sizing:border-box;
  padding:max(10px,env(safe-area-inset-top))
          max(10px,env(safe-area-inset-right))
          max(10px,env(safe-area-inset-bottom))
          max(10px,env(safe-area-inset-left));
  background:rgba(7,12,22,.97); color:#f8fafc;
}
body.diagram-viewer-active {overflow:hidden}
.diagram-bar {
  display:flex; flex-wrap:wrap; align-items:center; justify-content:flex-end;
  gap:8px; padding:4px 2px 10px;
}
#diagram-zoom-label {margin-right:auto;font-variant-numeric:tabular-nums}
.diagram-bar button {
  min-width:42px; min-height:42px; padding:8px 12px;
  border:1px solid #64748b; border-radius:9px;
  background:#1e293b;color:white;font:inherit;cursor:pointer;
}
.diagram-stage {
  flex:1; min-height:0; width:100%; overflow:hidden;
  display:flex; align-items:center; justify-content:center;
  touch-action:none; overscroll-behavior:contain;
  user-select:none;-webkit-user-select:none;
}
#diagram-large {
  display:block; flex:0 0 auto; max-width:100%; max-height:100%;
  width:auto;height:auto;object-fit:contain;transform-origin:center;
  will-change:transform;-webkit-user-drag:none;user-select:none;
}
.diagram-help {margin:8px 0 2px;text-align:center;color:#cbd5e1;font-size:.85rem}
@media(max-width:600px) {
  .diagram-bar {gap:5px}
  .diagram-bar button {min-width:38px;min-height:40px;padding:7px 9px}
  .diagram-help {font-size:.78rem}
}
/* end component-diagram-viewer-v1 */
'''

updated_html = html.replace(old, new, 1).replace("</body>", viewer+"\n</body>", 1)
updated_css = css + "\n" + css_add
stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
bt = T.with_name(T.name + ".bak_viewer_" + stamp)
bc = C.with_name(C.name + ".bak_viewer_" + stamp)

shutil.copy2(T, bt)
shutil.copy2(C, bc)
try:
    T.write_text(updated_html, encoding="utf-8")
    C.write_text(updated_css, encoding="utf-8")
except Exception:
    shutil.copy2(bt, T)
    shutil.copy2(bc, C)
    raise

print("PATCH BERHASIL")
print("Backup template:", bt)
print("Backup CSS:", bc)
print("Marker template:", updated_html.count(MARK))
print("Marker CSS:", updated_css.count(MARK))
