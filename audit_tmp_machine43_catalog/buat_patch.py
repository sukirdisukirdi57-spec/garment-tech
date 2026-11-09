from pathlib import Path
import difflib
import sys

app_path = Path("app.py")
tpl_path = Path("templates/machine_detail.html")

app = app_path.read_text(encoding="utf-8")
tpl = tpl_path.read_text(encoding="utf-8")

# --- Usulan perubahan app.py ---
app_anchor = "    # Katalog Section 27 khusus JUKI AMS-210EN-2210"
if app.count(app_anchor) != 1:
    sys.exit("GAGAL: posisi penyisipan app.py tidak cocok. File asli aman.")

app_insert = '''    catalog_parts_by_page = {}

    if machine_id == 43:
        catalog_rows = conn.execute(
            """
            SELECT
                pdf_page,
                catalog_ref,
                marker,
                part_number,
                part_name,
                quantity_raw
            FROM catalog_occurrences
            WHERE machine_id = ?
            ORDER BY
                CAST(pdf_page AS INTEGER),
                CAST(catalog_ref AS INTEGER),
                id
            """,
            (machine_id,)
        ).fetchall()

        for row in catalog_rows:
            catalog_parts_by_page.setdefault(
                row["pdf_page"], []
            ).append(row)

'''
app_new = app.replace(app_anchor, app_insert + app_anchor, 1)

render_anchor = "        component_parts=component_parts,"
if app_new.count(render_anchor) != 1:
    sys.exit("GAGAL: parameter render_template tidak cocok. File asli aman.")

app_new = app_new.replace(
    render_anchor,
    render_anchor + "\n        catalog_parts_by_page=catalog_parts_by_page,",
    1
)

# --- Usulan perubahan machine_detail.html ---
tpl_anchor = "{% set component_subparts = component_parts"
if tpl.count(tpl_anchor) != 1:
    sys.exit("GAGAL: posisi blok komponen tidak cocok. File asli aman.")

component_block = '''{% if machine["id"] == 43 %}
                {% set page_catalog_parts = catalog_parts_by_page.get(component["diagram_page"], []) %}

                {% if component["image_path"] %}
                <div class="component-image">
                    <button type="button"
                            class="diagram-open machine43-diagram-open"
                            data-diagram-src="{{ url_for('static', filename=component['image_path']) }}"
                            aria-label="Perbesar diagram {{ component['component_name'] }}">
                        <img
                            src="{{ url_for('static', filename=component['image_path']) }}"
                            alt="{{ component['component_name'] }}"
                            loading="lazy">
                        <span>🔍 Ketuk gambar untuk memperbesar</span>
                    </button>
                </div>
                {% endif %}

                {% if page_catalog_parts %}
                <section class="component-info juki-catalog-parts">
                    <h3>Daftar Spare Part — PDF {{ component["diagram_page"] }}</h3>
                    <p>{{ page_catalog_parts|length }} kemunculan part dari katalog resmi JUKI.</p>
                    <div class="component-subparts-wrapper">
                        <table class="component-subparts">
                            <thead>
                                <tr>
                                    <th>Ref.</th>
                                    <th>Part Number</th>
                                    <th>Part Name</th>
                                    <th>Qty</th>
                                </tr>
                            </thead>
                            <tbody>
                            {% for part in page_catalog_parts %}
                                <tr>
                                    <td>
                                        {{ part["catalog_ref"] or "—" }}
                                        {% if part["marker"] %}
                                            <span>{{ part["marker"] }}</span>
                                        {% endif %}
                                    </td>
                                    <td><strong>{{ part["part_number"] or "—" }}</strong></td>
                                    <td>{{ part["part_name"] or "—" }}</td>
                                    <td>{{ part["quantity_raw"] or "—" }}</td>
                                </tr>
                            {% endfor %}
                            </tbody>
                        </table>
                    </div>
                </section>
                {% endif %}
                {% endif %}

                '''

tpl_new = tpl.replace(tpl_anchor, component_block + tpl_anchor, 1)

viewer_block = '''<!-- machine43-diagram-viewer -->
<div id="machine43-diagram-viewer" class="diagram-viewer"
     role="dialog" aria-modal="true"
     aria-label="Diagram komponen JUKI AMS-210EN" hidden>
  <div class="diagram-bar">
    <span id="machine43-zoom-label">Zoom 100%</span>
    <button type="button" data-act="out">−</button>
    <button type="button" data-act="in">+</button>
    <button type="button" data-act="reset">Reset</button>
    <button type="button" data-act="close" aria-label="Tutup">✕</button>
  </div>
  <div id="machine43-diagram-stage" class="diagram-stage">
    <img id="machine43-diagram-large" src=""
         alt="Diagram komponen JUKI" draggable="false">
  </div>
  <p class="diagram-help">Cubit untuk zoom · Geser untuk melihat detail · Esc untuk menutup</p>
</div>

<script>
(function () {
  "use strict";
  const viewer = document.getElementById("machine43-diagram-viewer");
  const openers = document.querySelectorAll(".machine43-diagram-open");
  const stage = document.getElementById("machine43-diagram-stage");
  const img = document.getElementById("machine43-diagram-large");
  const label = document.getElementById("machine43-zoom-label");
  if (!viewer || !openers.length || !stage || !img || !label) return;

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
  function reset() {
    s=1; x=0; y=0; draw();
  }
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

  openers.forEach(opener => opener.addEventListener("click", () => {
    focusBefore=document.activeElement;
    img.src=opener.dataset.diagramSrc;
    img.alt=opener.querySelector("img")?.alt || "Diagram komponen JUKI";
    reset();
    viewer.hidden=false;
    document.body.classList.add("diagram-viewer-active");
    viewer.querySelector('[data-act="close"]').focus();
  }));

  viewer.querySelectorAll("[data-act]").forEach(b => b.addEventListener("click", () => {
    const a=b.dataset.act;
    if (a==="close") close();
    if (a==="reset") reset();
    if (a==="in" || a==="out") {
      const r=stage.getBoundingClientRect();
      zoom(s*(a==="in"?1.25:0.8),r.left+r.width/2,r.top+r.height/2);
    }
  }));

  viewer.addEventListener("click", e => {
    if(e.target===viewer) close();
  });
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
<!-- end machine43-diagram-viewer -->

'''

if tpl.count("</body>") != 1:
    sys.exit("GAGAL: penutup body tidak ditemukan secara unik. File asli aman.")

tpl_new = tpl_new.replace("</body>", viewer_block + "\n</body>", 1)

# Buat unified diff; file sumber tetap tidak disentuh.
diff = []
diff.extend(difflib.unified_diff(
    app.splitlines(True), app_new.splitlines(True),
    fromfile="a/app.py", tofile="b/app.py"
))
diff.extend(difflib.unified_diff(
    tpl.splitlines(True), tpl_new.splitlines(True),
    fromfile="a/templates/machine_detail.html",
    tofile="b/templates/machine_detail.html"
))

out = Path("audit_tmp_machine43_catalog/machine43_catalog_display.patch")
out.write_text("".join(diff), encoding="utf-8")

print("PATCH USULAN BERHASIL DIBUAT")
print("File:", out)
print("Perubahan yang direncanakan:")
print("- app.py: query katalog mesin 43 dan parameter template")
print("- machine_detail.html: diagram, tabel katalog, dan modal pembesar")
print("File asli: TIDAK DIUBAH")
print("Database: TIDAK DIUBAH")
print("PythonAnywhere: TIDAK DISENTUH")
print("Jumlah baris patch:", len(diff))
