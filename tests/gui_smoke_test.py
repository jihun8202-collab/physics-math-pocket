"""Headless-capable GUI smoke test. On Windows it opens briefly and closes."""
from __future__ import annotations
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

_tmp = tempfile.TemporaryDirectory()
os.environ["PHYSICSMATHPOCKET_DATA_DIR"] = _tmp.name
# Keep automated UI tests isolated from network and real user settings.
import json
(Path(_tmp.name) / "settings_v3.json").write_text(json.dumps({"check_updates_on_startup": False}), encoding="utf-8")
from app import PhysicsPocketApp

app = PhysicsPocketApp()
failures = []
app.report_callback_exception = lambda kind, value, traceback: failures.append(str(value))
app.after(1450, lambda: app.search_for("이차함수"))
app.after(1800, lambda: app.show_term(app.term_by_name["이차함수"]))
app.after(2200, app.show_simulations)
app.after(2500, app.show_formulas)
app.after(2800, app.show_calculators)
app.after(3100, app.show_updates)
app.after(3400, app.show_about)
app.after(3700, app.show_help)
app.after(4000, app.show_data_manager)
app.after(4300, app.show_converter)
app.after(4700, app.show_korean)
app.after(5100, lambda: app.show_term(app.term_by_name["형태소"]))
app.after(5500, app.on_close)
app.mainloop()
_tmp.cleanup()
if failures:
    raise AssertionError("GUI callback errors: " + repr(failures))
print("GUI smoke test: OK")
