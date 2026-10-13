from __future__ import annotations

import os
import queue
import subprocess
import sys
import threading
import tkinter as tk
import webbrowser
from pathlib import Path
from tkinter import messagebox

ROOT = Path(__file__).resolve().parent
INNO_URL = "https://jrsoftware.org/isdl.php"


class BuilderApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Physics + Math Pocket 3.1.4 Beta 설치 파일 만들기")
        self.geometry("820x590")
        self.minsize(680, 480)
        self.configure(bg="#10171A")
        self.queue = queue.Queue()
        self.process = None

        header = tk.Frame(self, bg="#10171A")
        header.pack(fill="x", padx=24, pady=(22, 10))
        tk.Label(header, text="⚛", bg="#10171A", fg="#35D0AD", font=("Segoe UI Symbol", 30, "bold")).pack(side="left", padx=(0, 12))
        title = tk.Frame(header, bg="#10171A")
        title.pack(side="left", fill="x", expand=True)
        tk.Label(title, text="Physics + Math Pocket 3.1.4 Beta 빌드 도우미", bg="#10171A", fg="#F4FAFC", font=("Malgun Gothic", 18, "bold")).pack(anchor="w")
        tk.Label(title, text="앱 EXE와 Windows 설치 마법사를 순서대로 만듭니다.", bg="#10171A", fg="#9FB2B9", font=("Malgun Gothic", 9)).pack(anchor="w", pady=(3, 0))

        info = tk.Frame(self, bg="#182226", highlightthickness=1, highlightbackground="#34464D")
        info.pack(fill="x", padx=24, pady=8)
        text = "필요 조건: Windows 10/11 · Python 3.9 이상 · Inno Setup 6/7 · 첫 빌드 시 인터넷 연결"
        tk.Label(info, text=text, bg="#182226", fg="#DDE9ED", font=("Malgun Gothic", 9), anchor="w", padx=14, pady=11).pack(fill="x")

        buttons = tk.Frame(self, bg="#10171A")
        buttons.pack(fill="x", padx=24, pady=8)
        self.build_button = self._button(buttons, "Setup.exe 만들기", lambda: self.start_build([]), accent=True)
        self.build_button.pack(side="left", padx=(0, 8))
        self.app_button = self._button(buttons, "앱 EXE만 만들기", lambda: self.start_build(["--app-only"]))
        self.app_button.pack(side="left", padx=(0, 8))
        self._button(buttons, "Inno Setup 받기", lambda: webbrowser.open(INNO_URL)).pack(side="left", padx=(0, 8))
        self._button(buttons, "release 폴더", self.open_release).pack(side="left")

        self.status = tk.StringVar(value="준비됨")
        tk.Label(self, textvariable=self.status, bg="#10171A", fg="#65E6FF", font=("Malgun Gothic", 9, "bold"), anchor="w").pack(fill="x", padx=26, pady=(7, 4))

        log_wrap = tk.Frame(self, bg="#182226", highlightthickness=1, highlightbackground="#34464D")
        log_wrap.pack(fill="both", expand=True, padx=24, pady=(0, 22))
        self.log = tk.Text(log_wrap, bg="#0B1012", fg="#D5E2E6", insertbackground="#FFFFFF", relief="flat", wrap="word", font=("Consolas", 9), padx=12, pady=12)
        scroll = tk.Scrollbar(log_wrap, command=self.log.yview)
        self.log.configure(yscrollcommand=scroll.set)
        self.log.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.append("빌드 버튼을 누르면 진행 상황이 여기에 표시됩니다.\n")
        self.after(100, self.poll_queue)

    def _button(self, master: tk.Misc, text: str, command, accent: bool = False) -> tk.Button:
        bg = "#00A884" if accent else "#253238"
        active = "#18BC99" if accent else "#34464D"
        return tk.Button(master, text=text, command=command, bg=bg, fg="#FFFFFF", activebackground=active, activeforeground="#FFFFFF", relief="flat", bd=0, font=("Malgun Gothic", 9, "bold"), padx=14, pady=9, cursor="hand2")

    def append(self, text: str) -> None:
        self.log.insert("end", text)
        self.log.see("end")

    def set_busy(self, busy: bool) -> None:
        state = "disabled" if busy else "normal"
        self.build_button.configure(state=state)
        self.app_button.configure(state=state)

    def start_build(self, args: list[str]) -> None:
        if os.name != "nt":
            messagebox.showerror("Windows 필요", "Windows용 설치 파일은 Windows PC에서 만들어야 합니다.", parent=self)
            return
        if self.process is not None:
            return
        self.log.delete("1.0", "end")
        self.status.set("빌드 준비 중…")
        self.set_busy(True)
        thread = threading.Thread(target=self.worker, args=(args,), daemon=True)
        thread.start()

    def worker(self, args: list[str]) -> None:
        command = [sys.executable, "-X", "utf8", str(ROOT / "build_release.py")] + args
        env = os.environ.copy()
        env["PYTHONUTF8"] = "1"
        try:
            self.process = subprocess.Popen(
                command,
                cwd=str(ROOT),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=env,
            )
            assert self.process.stdout is not None
            for line in self.process.stdout:
                self.queue.put(("line", line))
            code = self.process.wait()
            self.queue.put(("done", code))
        except Exception as exc:
            self.queue.put(("error", str(exc)))
        finally:
            self.process = None

    def poll_queue(self) -> None:
        try:
            while True:
                kind, value = self.queue.get_nowait()
                if kind == "line":
                    self.append(value)
                    self.status.set(value.strip()[:100] or "빌드 중…")
                elif kind == "done":
                    self.set_busy(False)
                    if value == 0:
                        self.status.set("완료! release 폴더를 확인하세요.")
                        messagebox.showinfo("빌드 완료", "설치 파일 만들기가 끝났습니다.\nrelease 폴더를 확인하세요.", parent=self)
                    else:
                        self.status.set("빌드 실패 · build_release.log를 확인하세요.")
                        messagebox.showerror("빌드 실패", "빌드가 끝나지 못했습니다. 화면의 마지막 오류와 build_release.log를 확인하세요.", parent=self)
                elif kind == "error":
                    self.set_busy(False)
                    self.status.set("실행 오류")
                    self.append("\n[ERROR] " + value + "\n")
                    messagebox.showerror("실행 오류", value, parent=self)
        except queue.Empty:
            pass
        self.after(100, self.poll_queue)

    def open_release(self) -> None:
        path = ROOT / "release"
        path.mkdir(exist_ok=True)
        try:
            os.startfile(str(path))  # type: ignore[attr-defined]
        except Exception:
            webbrowser.open(path.resolve().as_uri())


if __name__ == "__main__":
    BuilderApp().mainloop()
