from __future__ import annotations
import sys, tkinter as tk
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from simulations import SIM_TITLES as LEGACY_TITLES, SIM_SUBJECTS as LEGACY_SUBJECTS
from enhanced_simulations import ENHANCED_TITLES, ENHANCED_SUBJECTS, build_simulator
SIM_TITLES={**LEGACY_TITLES, **ENHANCED_TITLES}
SIM_SUBJECTS={**LEGACY_SUBJECTS, **ENHANCED_SUBJECTS}
THEME={"surface":"#fff","surface2":"#f5f5f5","line":"#ccc","text":"#111","muted":"#666","accent":"#00a884","accent_soft":"#dff7f0","accent2":"#007a67","blue":"#2d72d9","danger":"#d94b54","green":"#248a64","orange":"#c97728"}
root=tk.Tk(); root.withdraw(); root.overrideredirect(True); root.attributes('-alpha',0)
root.geometry('1000x900+0+0'); root.deiconify(); root.update()
failed=[]
for sid,title in SIM_TITLES.items():
    f=None
    try:
        f=tk.Frame(root); f.pack(fill='x')
        sim=build_simulator(f,{"name_ko":title,"subject":SIM_SUBJECTS[sid],"simulator":sid},THEME,30)
        if sim is None: raise RuntimeError('sim None')
        sim.pack(fill='x'); root.update_idletasks(); sim.redraw(); root.update_idletasks()
        if len(sim.canvas.find_all()) < 2: raise RuntimeError('Canvas did not draw')
    except Exception as e:
        failed.append((sid,repr(e)))
    finally:
        if f is not None: f.destroy()
root.destroy()
if failed:
    print('FAILED',failed); raise SystemExit(1)
print(f'All simulator smoke test: OK ({len(SIM_TITLES)})')
