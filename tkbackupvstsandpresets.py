import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog
import pathlib
import sqlite3
import os
import shutil

DDL = """
create table if not exists target (
role text default 'main',
path text,
unique(role) on conflict replace);

create table if not exists paths (
id integer primary key,
path text,
unique(path) on conflict replace);
"""

DB_FILE = "tkvstcp.db"

ProgramFiles =  pathlib.Path(os.getenv("ProgramFiles"))
ProgramFilesx86 =  pathlib.Path(os.getenv("ProgramFiles(x86)"))
CommonProgramFiles = pathlib.Path(os.getenv("CommonProgramFiles"))
CommonProgramFilesx86 = pathlib.Path(os.getenv("CommonProgramFiles(x86)"))
UserProfile = pathlib.Path(os.getenv("USERPROFILE"))
vstpaths = [
    ProgramFilesx86 / "VstPlugins",
    ProgramFilesx86 / "Steinberg" / "VstPlugins",
    CommonProgramFiles / "VST2",
    ProgramFiles / "VstPlugins",
    CommonProgramFiles / "Steinberg" / "VST2",
    ProgramFiles / "Steinberg" / "VstPlugins",
    CommonProgramFilesx86 / "VST3",
    CommonProgramFiles / "VST3"
]
VitalPresetsPath = UserProfile / "Documents" / "Vital"
SurgeXTPresetsPath = UserProfile / "Documents" / "Surge XT"
SerumPresetsPath = UserProfile / "Documents" / "Xfer"
print("vstpaths:",vstpaths)
print("VitalPresetsPath:",VitalPresetsPath)
print("SurgeXTPresetsPath:",SurgeXTPresetsPath)
print("SerumPresetsPath:",SerumPresetsPath)


class Toolbar(tk.Frame):

    def app_quit(self):
        print("bye")
        self.quit()
    def add_default_paths(self):
        for p in vstpaths:
            print("adding ",p)
            self.cx.execute("insert into paths(path) values (?)",
                            (str(p),))
        self.cx.commit()
        print("OK")
        self.refresh_ui()

    def add_path(self):
        d = filedialog.askdirectory()
        newpath = pathlib.Path(d).resolve()
        print("newpath:",newpath)
        if newpath.is_dir():
            self.cx.execute("insert into paths(path) values (?)",
                            (str(newpath),))
            self.cx.commit()
        self.refresh_ui()

    def set_target(self):
        d = filedialog.askdirectory()
        print("d:",d)
        tpath = pathlib.Path(d).resolve()
        if tpath.is_dir():
            self.cx.execute("insert into target(path) values(?)",
                            (str(tpath),))
            self.cx.commit()
            print("inserted",tpath)
        self.refresh_ui()
    def refresh_ui(self):
        t = self.cu.execute(
            "select path from target where role='main'").fetchone()
        print(t)
        self.target_root.set(t)
        p = self.cu.execute(
            "select path from paths").fetchall()
        print("p:",p)
        self.paths_list.set(p)
    def copy_paths_to_target(self):
        getvital = self.also_bak_vital.get()
        getsurge = self.also_bak_surge.get()
        getserum = self.also_bak_serum.get()
        t = self.cu.execute(
            "select path from target where role='main'").fetchone()
        if not t:
            print("NO TARGET PATH SET!")
            return
        target = pathlib.Path(t)
        if not target.is_dir():
            print("TARGET PATH WAS NOT A DIRECTORY!")
            return
        print("target:",target)
        paths = []
        p = self.cu.execute(
            "select path from paths").fetchall()
        for path in p:
            paths.append(pathlib.Path(path))
        if getvital:
            paths.append(VitalPresetsPath)
        if getsurge:
            paths.append(SurgeXTPresetsPath)
        if getserum:
            paths.append(SerumPresetsPath)
        print("paths:",paths)
        for path in paths:
            dest = target / path.relative_to(path.anchor)
            print(str(path),end="->")
            shutil.copytree(path,dest)
            print(str(dest),end=" ")
        print("Copied OK!")

        

    def __init__(self,master):
        super().__init__(master)
        self.cx = sqlite3.connect(DB_FILE)
        self.cx.executescript(DDL)
        self.cx.commit()
        self.cu = self.cx.cursor()
        self.cu.row_factory = lambda c,r:r[0]

        self.target_root = tk.StringVar()
        self.paths_list = tk.StringVar()
        self.also_bak_vital = tk.IntVar()
        self.also_bak_surge = tk.IntVar()
        self.also_bak_serum = tk.IntVar()
        self.menubutton = tk.Menubutton(self,text="menu")
        self.menubutton.menu = tk.Menu(self.menubutton,tearoff=False)
        self.menubutton['menu'] = self.menubutton.menu
        self.menubutton.menu.add_command(command=self.add_path,label="add custom path")
        self.menubutton.menu.add_command(command=self.add_default_paths,label="add default paths")
        self.menubutton.menu.add_command(command=self.set_target,label="set target")
        self.menubutton.menu.add_command(command=self.copy_paths_to_target,label="copy paths to target")
        self.menubutton.menu.add_command(command=self.app_quit,label="exit")
        self.menubutton.pack(anchor="w")
        self.main_frame = tk.Frame(self)
        self.main_frame.pack(expand=True,fill="both")
        self.target_lblframe = ttk.Labelframe(self.main_frame,text="Target:")
        self.target_lblframe.pack()
        self.target_label = tk.Label(self.target_lblframe,textvariable=self.target_root)
        self.target_label.pack()
        self.paths_lblframe = ttk.Labelframe(self.main_frame,text="Paths:")
        self.paths_lblframe.pack()

        self.paths_listbox = tk.Listbox(self.paths_lblframe,listvariable=self.paths_list)
        self.paths_listbox.pack(side="left",expand=True,fill='both')
        self.paths_listbox_scrollbar = tk.Scrollbar(self.paths_lblframe,orient='vertical',command=self.paths_listbox.yview)
        self.paths_listbox.config(yscrollcommand=self.paths_listbox_scrollbar.set)
        self.paths_listbox_scrollbar.pack(side="right",expand=True,fill="y")

        self.other_options_frame = tk.Frame(self)
        self.other_options_frame.pack(expand=True,fill="both")
        self.vital_chkbox = tk.Checkbutton(self.other_options_frame,variable=self.also_bak_vital,text="Also backup Vital presets")
        self.surge_chkbox = tk.Checkbutton(self.other_options_frame,variable=self.also_bak_surge,text="Also backup Surge XT presets")
        self.serum_chkbox = tk.Checkbutton(self.other_options_frame,variable=self.also_bak_serum,text="Also backup Serum presets")
        self.vital_chkbox.pack()
        self.surge_chkbox.pack()
        self.serum_chkbox.pack()
        self.refresh_ui()


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.toolbar = Toolbar(self)
        self.toolbar.pack(expand=True,fill="x")
        print("OK")

if __name__ == "__main__":
    App().mainloop()

