"""Responsive analytic experiment viewer with probes, comparison and CSV export."""
from __future__ import annotations
import csv
import math
import time
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import webbrowser
from scientific_catalog import SCENARIOS, evaluate, samples

class ScientificGraphSimulator(tk.Frame):
    def __init__(self, master, sim_id, theme, fps=30):
        super().__init__(master,bg=theme['surface'])
        self.sim_id,self.theme,self.spec=sim_id,theme,SCENARIOS[sim_id]
        self.running=False; self._job=None; self._last_clock=0; self.t=0
        self._vars={}; self._entries={}; self._cells=[]; self._ready=False
        self._data=[]; self._baseline=[]
        t,s=theme,self.spec
        self.title_label=tk.Label(self,text=s['model_title'],bg=t['surface'],fg=t['text'],font=('Malgun Gothic',13,'bold'),anchor='w',justify='left')
        self.title_label.pack(fill='x')
        self.formula=tk.Label(self,text=s['formula'],bg=t['surface'],fg=t['accent2'],font=('Malgun Gothic',11),anchor='w',justify='left')
        self.formula.pack(fill='x',pady=(5,10))
        self.controls=tk.Frame(self,bg=t['surface']); self.controls.pack(fill='x')
        for i,(label,name,lo,hi,value) in enumerate(s['sliders']):
            cell=tk.Frame(self.controls,bg=t['surface2'],padx=10,pady=8)
            cell.grid(row=i//2,column=i%2,sticky='ew',padx=4,pady=4); self._cells.append(cell)
            tk.Label(cell,text=label,bg=t['surface2'],fg=t['text'],anchor='w',font=('Malgun Gothic',9)).pack(fill='x')
            var=tk.DoubleVar(value=value); self._vars[name]=var
            row=tk.Frame(cell,bg=t['surface2']); row.pack(fill='x',pady=(4,0))
            ttk.Scale(row,from_=lo,to=hi,variable=var).pack(side='left',fill='x',expand=True,padx=(0,8))
            entry=ttk.Entry(row,width=13); entry.insert(0,f'{value:.9g}'); entry.pack(side='right'); self._entries[name]=entry
            entry.bind('<Return>',lambda e,n=name:self._set_entry(n))
            entry.bind('<FocusOut>',lambda e,n=name:self._set_entry(n))
            var.trace_add('write',lambda *_,n=name:self._changed(n))
        bar=tk.Frame(self,bg=t['surface']); bar.pack(fill='x',pady=8)
        self.bar=bar
        self.play_btn=ttk.Button(bar,text='▶ 탐침 이동',command=self.toggle)
        self._buttons=[self.play_btn,ttk.Button(bar,text='조건 초기화',command=self.reset),
                       ttk.Button(bar,text='현재 곡선 비교로 고정',command=self.pin),
                       ttk.Button(bar,text='CSV 저장',command=self.export_csv)]
        for i,button in enumerate(self._buttons): button.grid(row=0,column=i,sticky='ew',padx=3,pady=3)
        self.canvas=tk.Canvas(self,width=800,height=340,bg=t['surface2'],highlightthickness=0)
        self.canvas.pack(fill='x',pady=5); self.canvas.bind('<Configure>',lambda _:self.redraw())
        self.canvas.bind('<Button-1>',self._click_probe); self.canvas.bind('<B1-Motion>',self._click_probe)
        self.probe=tk.DoubleVar(value=0)
        ttk.Scale(self,from_=0,to=1,variable=self.probe,command=lambda _:self.redraw()).pack(fill='x')
        self.info=tk.Label(self,bg=t['surface2'],fg=t['text'],font=('Malgun Gothic',10),anchor='w',justify='left',padx=10,pady=10)
        self.info.pack(fill='x',pady=8)
        self.notes=tk.Label(self,text='모델·적용 범위  '+s['notes']+'\n곡선: 현재 조건 · 점선: 고정한 비교 조건. 탐침은 입력값을 읽는 표시입니다.\n100개 조건 실험은 같은 계산 모델의 매개변수 조합입니다. 수치 자리 수는 실제 측정 정확도를 뜻하지 않습니다.',bg=t['surface'],fg=t['muted'],font=('Malgun Gothic',9),anchor='w',justify='left')
        self.notes.pack(fill='x',pady=5)
        link=tk.Label(self,text='계산 근거 및 참고 자료 ↗',bg=t['surface'],fg=t['blue'],cursor='hand2',font=('Malgun Gothic',9,'underline'),anchor='w')
        link.pack(fill='x'); link.bind('<Button-1>',lambda _:webbrowser.open(s['source']))
        self.bind('<Configure>',self._layout)
        self._ready=True; self._recompute(); self.pin()

    def parameters(self):
        integers={p['name'] for p in self.spec['parameters'] if p.get('integer')}
        return {k:float(round(v.get()) if k in integers else v.get()) for k,v in self._vars.items()}
    def _set_entry(self,name):
        try:
            value=float(self._entries[name].get())
            _,_,lo,hi,_=next(p for p in self.spec['sliders'] if p[1]==name)
            if not math.isfinite(value) or not lo<=value<=hi: raise ValueError()
            if any(p['name']==name and p.get('integer') for p in self.spec['parameters']): value=round(value)
            self._vars[name].set(value)
        except (ValueError,tk.TclError):
            self._entries[name].delete(0,'end'); self._entries[name].insert(0,f'{self._vars[name].get():.9g}')
    def _changed(self,name):
        if not self._ready: return
        self.stop()
        if any(p['name']==name and p.get('integer') for p in self.spec['parameters']):
            actual=round(self._vars[name].get())
            if self._vars[name].get()!=actual:
                self._ready=False; self._vars[name].set(actual); self._ready=True
        entry=self._entries[name]; entry.delete(0,'end'); entry.insert(0,f'{self._vars[name].get():.9g}')
        self._recompute(); self.redraw()
    def _recompute(self): self._data=samples(self.spec,self.parameters(),count=640)
    def pin(self):
        self._baseline=list(self._data); self._baseline_params=self.parameters(); self.redraw()
    def _layout(self,event):
        if event.widget is not self: return
        width=max(240,event.width); columns=2 if width>=620 else 1
        for i,cell in enumerate(self._cells): cell.grid(row=i//columns,column=i%columns,sticky='ew',padx=4,pady=4)
        self.controls.columnconfigure(0,weight=1); self.controls.columnconfigure(1,weight=1 if columns==2 else 0)
        button_columns=4 if width>=750 else 2
        for i,button in enumerate(self._buttons): button.grid(row=i//button_columns,column=i%button_columns,sticky='ew',padx=3,pady=3)
        for i in range(4): self.bar.columnconfigure(i,weight=1 if i<button_columns else 0)
        for label in (self.title_label,self.formula,self.info,self.notes): label.configure(wraplength=width-24)
    def _click_probe(self,event):
        self.stop(); self.probe.set(min(1,max(0,(event.x-72)/(max(260,self.canvas.winfo_width())-102)))); self.redraw()
    def _curve(self,data,parameters):
        """Render held/discrete values at their exact jump locations."""
        lo,hi=self.spec['xmin'],self.spec['xmax']
        if self.spec['family']=='sampling':
            fs=parameters['sample_rate']
            boundaries=[n/fs for n in range(math.floor(lo*fs)+1,math.floor(hi*fs)+1)]
        elif self.spec.get('discrete'):
            boundaries=[n+.5 for n in range(math.floor(lo),math.ceil(hi)) if lo<n+.5<hi]
        else:return data
        points=[(lo,evaluate(self.spec,lo,parameters))]
        for x in boundaries:
            before=evaluate(self.spec,max(lo,x-1e-9),parameters)
            after=evaluate(self.spec,min(hi,x+1e-9),parameters)
            points.extend(((x,before),(x,after)))
        points.append((hi,evaluate(self.spec,hi,parameters)))
        return points
    def redraw(self):
        if not self._ready or not self._data: return
        c,t=self.canvas,self.theme; c.delete('all')
        w=max(260,c.winfo_width()); h=340; l,r,top,bottom=72,w-30,25,h-65
        lo,hi=self.spec['xmin'],self.spec['xmax']
        ys=[y for _,y in self._data+self._baseline]; low,high=min(ys),max(ys)
        pad=(high-low)*.08 if high>low else max(1,abs(high)*.1); low-=pad; high+=pad
        px=lambda x:l+(x-lo)/(hi-lo)*(r-l)
        py=lambda y:bottom-(y-low)/(high-low)*(bottom-top)
        for i in range(5):
            x=lo+(hi-lo)*i/4; y=low+(high-low)*i/4
            c.create_line(px(x),top,px(x),bottom,fill=t['line']); c.create_line(l,py(y),r,py(y),fill=t['line'])
            c.create_text(px(x),bottom+16,text=f'{x:.4g}',fill=t['muted'],font=('Consolas',8))
            c.create_text(l-8,py(y),text=f'{y:.4g}',anchor='e',fill=t['muted'],font=('Consolas',8))
        for data,color,dash in ((self._curve(self._baseline,self._baseline_params) if self._baseline else [],t['muted'],(4,4)),(self._curve(self._data,self.parameters()),t['accent'],None)):
            points=[z for x,y in data for z in (px(x),py(y))]
            if points: c.create_line(*points,fill=color,width=2,dash=dash)
        x=lo+(hi-lo)*float(self.probe.get()); y=evaluate(self.spec,x,self.parameters())
        c.create_line(px(x),top,px(x),bottom,fill=t['blue'],dash=(2,4))
        c.create_oval(px(x)-5,py(y)-5,px(x)+5,py(y)+5,fill=t['blue'],outline=t['surface2'],width=2)
        c.create_text((l+r)/2,h-15,text=self.spec['x_label'],fill=t['text'],font=('Malgun Gothic',9))
        c.create_text(14,(top+bottom)/2,text=self.spec['y_label'],fill=t['text'],angle=90,font=('Malgun Gothic',9))
        baseline=evaluate(self.spec,x,self._baseline_params) if self._baseline else y
        applied=f" (적용 정수 {round(x)})" if self.spec.get('discrete') else ''
        self.info.configure(text=f"{self.spec['x_label']} = {x:.8g}{applied}\n{self.spec['y_label']} = {y:.8g}   ·   비교값 {baseline:.8g}   ·   차이 {y-baseline:+.6g}")
    def toggle(self): self.stop() if self.running else self.start()
    def start(self):
        if self.running:return
        if self.probe.get()>=1:self.probe.set(0)
        self.running=True; self._last_clock=time.perf_counter(); self.play_btn.configure(text='❚❚ 일시정지'); self._job=self.after(33,self._tick)
    def _tick(self):
        self._job=None
        if not self.running:return
        now=time.perf_counter(); elapsed=now-self._last_clock; self._last_clock=now
        if elapsed>2:self.stop();return
        self.probe.set(min(1,self.probe.get()+elapsed/10)); self.redraw()
        if self.probe.get()>=1:self.stop()
        else:self._job=self.after(33,self._tick)
    def stop(self):
        self.running=False
        if self._job:
            try:self.after_cancel(self._job)
            except tk.TclError:pass
            self._job=None
        self.play_btn.configure(text='▶ 탐침 이동')
    def step_once(self): self.stop(); self.probe.set(min(1,self.probe.get()+1/640)); self.redraw()
    def reset(self):
        self.stop(); self._ready=False
        for _,name,_,_,value in self.spec['sliders']:
            self._vars[name].set(value); e=self._entries[name]; e.delete(0,'end'); e.insert(0,f'{value:.9g}')
        self.probe.set(0); self._ready=True; self._recompute(); self.redraw()
    def export_csv(self):
        path=filedialog.asksaveasfilename(parent=self,defaultextension='.csv',initialfile=self.sim_id+'.csv',filetypes=[('CSV','*.csv')])
        if not path:return
        try:
            with open(path,'w',newline='',encoding='utf-8-sig') as stream:
                writer=csv.writer(stream); writer.writerow(['experiment',self.sim_id]); writer.writerow(['model',self.spec['model_title']]); writer.writerow(['formula',self.spec['formula']]); writer.writerow(['assumptions',self.spec['notes']]); writer.writerow(['source',self.spec['source']]); writer.writerow(['parameters',repr(self.parameters())]); writer.writerow([self.spec['x_label'],self.spec['y_label']]); writer.writerows(self._data)
        except OSError as error:messagebox.showerror('저장 실패',str(error),parent=self)
    def destroy(self): self.stop(); super().destroy()
