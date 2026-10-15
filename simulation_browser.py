"""Paginated, responsive card catalog. A simulator is created only after a click."""
import math
import tkinter as tk
from tkinter import ttk
from scientific_catalog import MODELS, SCENARIOS
from simulations import SIM_TITLES as LEGACY, SIM_SUBJECTS as SUBJECTS
from enhanced_simulations import ENHANCED_TITLES, ENHANCED_SUBJECTS, BIOLOGY_TITLES, build_simulator

PAGE_SIZE=24

def build_simulation_browser(app, ScrollableFrame):
    app.current_page='simulations'; app.current_term=None; app._refresh_nav_state()
    frame=app._clear_center(); t=app.theme
    app._page_title(frame,'과학 실험실 · 3.5 Beta','카드를 눌러 실험을 시작하세요. 감염·면역 실험실 / 50개 모델의 5,000개 조건 실험 / 기존 도구 105개')
    toolbar=tk.Frame(frame,bg=t['bg']); toolbar.pack(fill='x',pady=(0,10))
    search=tk.StringVar(); subject=tk.StringVar(value='전체')
    entry=ttk.Entry(toolbar,textvariable=search); entry.pack(side='left',fill='x',expand=True,padx=(0,8),ipady=5)
    ttk.Combobox(toolbar,textvariable=subject,values=['전체']+sorted(set(SUBJECTS.values())),state='readonly',width=12).pack(side='left')
    clear=ttk.Button(toolbar,text='검색 지우기',command=lambda:search.set('')); clear.pack(side='left',padx=(8,0))
    holder=ScrollableFrame(frame,t['bg']); holder.pack(fill='both',expand=True)
    state={'family':None,'page':0,'active':None,'cards':[],'columns':0}
    app._simulation_browser_state=state

    def clear_content():
        for sim in list(app._active_simulators):
            if sim.winfo_exists(): sim.stop()
        app._active_simulators=[]
        for child in holder.inner.winfo_children():child.destroy()
        state['cards']=[]; state['columns']=0

    def family_rows():
        rows=[{'id':'biology_body','title':BIOLOGY_TITLES['biology_body'],'subject':'생명과학','description':'장기 지도 · 면역세포 · 사이토카인·발열 · 가상 프로필 · 지원 개입','badge':'핵심 실험실','kind':'simulation'}]
        for key,m in MODELS.items():
            rows.append({'id':key,'title':m['title'],'subject':m['subject'],'description':m['formula'],
                         'badge':'100개 조건 · '+('운동 실험' if m.get('dynamic_kind') else '관계 실험'),'kind':'family'})
        rows.append({'id':'legacy','title':'기존 학습 도구','subject':'전체','description':'충돌·파동·벡터·계산 관계 등 기존 105개 도구','badge':'기존 도구 유지','kind':'family'})
        return rows

    def rows_for_family():
        family=state['family']
        if family is None:return family_rows()
        if family=='legacy':
            titles={**ENHANCED_TITLES,**{k:v for k,v in LEGACY.items() if k not in SCENARIOS}}
            subjects={**SUBJECTS,**ENHANCED_SUBJECTS}
            return [{'id':sid,'title':title,'subject':subjects.get(sid,'과학'),'description':'조건을 바꾸며 그림과 수치를 관찰합니다.','badge':'기존 학습 도구','kind':'simulation'} for sid,title in titles.items()]
        return [{'id':sid,'title':f"조건 {s['scenario_index']:03d}",'subject':s['subject'],'description':s['condition_label'],
                 'badge':s['model_title'],'kind':'simulation'} for sid,s in SCENARIOS.items() if s['family']==family]

    def go_family(family):
        state.update(family=family,page=0,active=None); search.set(''); subject.set('전체'); render()
    def go_home():
        state.update(family=None,page=0,active=None); search.set(''); subject.set('전체'); render()
    def change_page(number):state['page']=number; render()

    def open_simulation(sid):
        clear_content(); state['active']=sid
        row=tk.Frame(holder.inner,bg=t['bg']); row.pack(fill='x',pady=(0,9))
        ttk.Button(row,text='← 실험 카드로',command=render).pack(side='left')
        if state['family'] is not None:ttk.Button(row,text='모든 모델',command=go_home).pack(side='left',padx=7)
        title=BIOLOGY_TITLES.get(sid) or ENHANCED_TITLES.get(sid) or LEGACY.get(sid,sid)
        outer=app._card(holder.inner,padx=18,pady=18); outer.pack(fill='x',pady=5); inside=app._put_card_content(outer)
        label=tk.Label(inside,text=title,bg=t['surface'],fg=t['text'],anchor='w',justify='left',wraplength=700,font=('Malgun Gothic',13,'bold'))
        label.pack(fill='x',pady=(0,12)); label.bind('<Configure>',lambda e:label.configure(wraplength=max(240,e.width-10)))
        sim=build_simulator(inside,{'simulator':sid},t,fps=int(app.settings.get('simulation_fps',30)))
        if sim is not None:
            if not app.settings.get('animations',True):sim.play_btn.configure(state='disabled',text='정적 모드')
            sim.pack(fill='x'); app._active_simulators=[sim]
        holder.to_top(); app.status_var.set('실험 중 · '+title)

    def layout_cards(event):
        grid=event.widget; width=max(240,event.width)
        columns=3 if width>=1080 else 2 if width>=680 else 1
        if state['columns']!=columns:
            for column in range(3):grid.columnconfigure(column,weight=1 if column<columns else 0,uniform='experiments')
            for i,(card,labels) in enumerate(state['cards']):card.grid(row=i//columns,column=i%columns,sticky='nsew',padx=5,pady=5)
            state['columns']=columns
        wrap=max(170,(width-20)/columns-48)
        for _,labels in state['cards']:
            for label in labels:label.configure(wraplength=wrap)

    def render(*_):
        clear_content(); state['active']=None
        header=tk.Frame(holder.inner,bg=t['bg']); header.pack(fill='x',pady=(0,8))
        family=state['family']
        if family is not None:ttk.Button(header,text='← 모든 모델',command=go_home).pack(side='left',padx=(0,10))
        title='실험 모델' if family is None else ('기존 도구' if family=='legacy' else MODELS[family]['title']+' · 조건 선택')
        tk.Label(header,text=title,bg=t['bg'],fg=t['text'],font=('Malgun Gothic',12,'bold')).pack(side='left')
        q=search.get().strip().casefold(); sub=subject.get()
        rows=[r for r in rows_for_family() if (sub=='전체' or r['subject']==sub) and (not q or q in (r['title']+' '+r['description']+' '+r['badge']+' '+r['subject']).casefold())]
        pages=max(1,math.ceil(len(rows)/PAGE_SIZE)); state['page']=min(state['page'],pages-1)
        count=f"{len(rows):,}개 · {state['page']+1}/{pages}"
        tk.Label(header,text=count,bg=t['bg'],fg=t['muted'],font=('Malgun Gothic',9)).pack(side='right')
        grid=tk.Frame(holder.inner,bg=t['bg']); grid.pack(fill='x')
        for row in rows[state['page']*PAGE_SIZE:(state['page']+1)*PAGE_SIZE]:
            outer=app._card(grid,padx=17,pady=16); inside=app._put_card_content(outer)
            command=(lambda key=row['id']:go_family(key)) if row['kind']=='family' else (lambda sid=row['id']:open_simulation(sid))
            color=t['accent2'] if row['id']=='biology_body' else t['blue']
            badge=tk.Label(inside,text=row['subject']+' · '+row['badge'],bg=t['surface'],fg=color,anchor='w',justify='left',font=('Malgun Gothic',8,'bold'),wraplength=260); badge.pack(fill='x')
            heading=tk.Label(inside,text=row['title'],bg=t['surface'],fg=t['text'],anchor='w',justify='left',font=('Malgun Gothic',12,'bold'),wraplength=260); heading.pack(fill='x',pady=(10,7))
            description=tk.Label(inside,text=row['description'],bg=t['surface'],fg=t['muted'],anchor='nw',justify='left',font=('Malgun Gothic',9),wraplength=260); description.pack(fill='x',pady=(0,12))
            button=app._button(inside,'조건 선택 →' if row['kind']=='family' else '실험 열기 →',command,kind='accent' if row['id']=='biology_body' else 'normal',padx=12,pady=7)
            button.pack(anchor='w')
            for widget in (outer,inside,badge,heading,description):
                widget.configure(cursor='hand2'); widget.bind('<Button-1>',lambda _,cmd=command:cmd())
            state['cards'].append((outer,[badge,heading,description]))
        if not rows:tk.Label(grid,text='일치하는 실험이 없습니다.',bg=t['bg'],fg=t['muted'],pady=30).pack()
        grid.bind('<Configure>',layout_cards)
        pager=tk.Frame(holder.inner,bg=t['bg']); pager.pack(fill='x',pady=12)
        if state['page']>0:ttk.Button(pager,text='← 이전',command=lambda:change_page(state['page']-1)).pack(side='left')
        if state['page']+1<pages:ttk.Button(pager,text='다음 →',command=lambda:change_page(state['page']+1)).pack(side='right')
        holder.to_top(); app.status_var.set('실험 카드 · '+title+' · '+count)

    def filter_changed(*_):state['page']=0; render()
    search.trace_add('write',filter_changed); subject.trace_add('write',filter_changed)
    # Explicit hooks for application navigation and automated interaction checks.
    app._open_simulation_card=open_simulation; app._open_simulation_family=go_family
    app._simulation_search=search; app._simulation_subject=subject
    render(); entry.focus_set()
