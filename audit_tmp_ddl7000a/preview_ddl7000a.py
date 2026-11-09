from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from jinja2 import ChoiceLoader, DictLoader
import app as app_module

proposal = Path("audit_tmp_ddl7000a/machine_detail_ddl7000a_proposal.html")

app = app_module.app
app.jinja_env.loader = ChoiceLoader([
    DictLoader({
        "machine_detail.html": proposal.read_text(encoding="utf-8")
    }),
    app.jinja_env.loader
])
app.jinja_env.cache.clear()

print("PRATINJAU DDL-7000A")
print("Buka: http://127.0.0.1:5055/machine/4")
print("Tekan CTRL+C untuk menghentikan server.")

app.run(host="127.0.0.1", port=5055, debug=False)
