#!/usr/bin/env python
import os, re, cv2, shlex, pwd, stat, subprocess, time
import customtkinter as ctk
from CTkMessagebox import CTkMessagebox
from pathlib import Path
from PIL import Image 
import tkinter as tk
from CTkToolTip import *
from typing import Literal, Optional, TextIO, List

from numpy import size 

class _System():
    
    def __init__(self) -> None:
        pass


    @staticmethod
    def GetPath(path=None) -> str:
        if path is None:
            path = os.getcwd()
        return f"   {path}" if path == os.getenv('HOME') else path
    
    @staticmethod
    def parse_path(path):
        
        if path.startswith('~'):
            path = os.path.expanduser('~')

        if path == '.':
            path = Path.cwd()

        return path

class DrawApp():

    def __init__(self, 
                 method : str,
                 filetypes: Optional[List[str]] = None, 
                 bufering: int = 1,
                 encoding: str = 'utf-8',
                 current_path : str = str(Path.cwd()),
                 hidden: bool = False, 
                 preview_img: bool = False,
                 autocomplete: bool = False,
                 video_preview: bool = False,
                 tool_tip: bool = False) -> None:

        self.current_path = Path(_System.parse_path(path=current_path)) if not current_path else Path.cwd() #Path(current_path) if current_path else Path.cwd()
        self.autocomplete = autocomplete
        self.preview_img = preview_img
        self.bufering = bufering
        self.encoding = encoding
        self.hidden = hidden
        self.video_preview = video_preview
        self.suggest = []
        self.tool_tip = tool_tip
        self._all_buttons = []
        self.filetypes = filetypes
        self.tab_index = -1
        self._BASE_DIR = Path(__file__).parent
        self.method = method 
        self.current_theme = ctk.get_appearance_mode()
        self.app = ctk.CTkToplevel()
        self.app.geometry('1320x720')
        self.selected_file = '' 
        self.selected_objects : list = [] 
        self._load_icons()
        self.TopSide(master=self.app)
        self.LeftSide(master=self.app)
        self.CenterSide(master=self.app)
        self.app.grab_set()

    @staticmethod
    def _is_image(image : str) -> bool :
        try:

            with Image.open(image) as img:

                img.verify()

            return True
        except:
            return False

    def _load_icons(self):
        icon_path = self._BASE_DIR / "icons"  
        # Cargar imágenes con PIL y convertirlas a CTkImage (suponiendo que usas customtkinter)
        self.iconos = {
            "folder": ctk.CTkImage(Image.open(icon_path / "folder.png"), size=(40, 40)),
            "bash": ctk.CTkImage(Image.open(icon_path / "bash.png"), size=(40, 40)),
            "image": ctk.CTkImage(Image.open(icon_path / "image.png"), size=(40, 40)),
            "python": ctk.CTkImage(Image.open(icon_path / "python.png"), size=(40, 40)),
            "text": ctk.CTkImage(Image.open(icon_path / "text.png"), size=(40, 40)),
            "markdown": ctk.CTkImage(Image.open(icon_path / "markdown.png"), size=(40, 40)),
            "javascript": ctk.CTkImage(Image.open(icon_path / "javascript.png"), size=(40, 40)),
            "php": ctk.CTkImage(Image.open(icon_path / "php.png"), size=(40, 40)),
            "html": ctk.CTkImage(Image.open(icon_path / "html.png"), size=(40, 40)),
            "css": ctk.CTkImage(Image.open(icon_path / "css.png"), size=(40, 40)),
            "ini": ctk.CTkImage(Image.open(icon_path / "ini.png"), size=(40, 40)),
            "conf": ctk.CTkImage(Image.open(icon_path / "conf.png"), size=(40, 40)),
            "exe": ctk.CTkImage(Image.open(icon_path / "exe.png"), size=(40, 40)),
            "odt": ctk.CTkImage(Image.open(icon_path / "odt.png"), size=(40, 40)),
            "pdf": ctk.CTkImage(Image.open(icon_path / "pdf.png"), size=(40, 40)),
            "json": ctk.CTkImage(Image.open(icon_path / "json.png"), size=(40, 40)),
            "gz": ctk.CTkImage(Image.open(icon_path / "gz.png"), size=(40, 40)),
            "video": ctk.CTkImage(Image.open(icon_path / "video.png"), size=(40, 40)),
            "awk": ctk.CTkImage(Image.open(icon_path / "bash.png"), size=(40, 40)),
            "default": ctk.CTkImage(Image.open(icon_path / "text.png"), size=(40, 40)),  # ícono por defecto
        }

        # Extensiones que reconoces, mapa a iconos
        self.extensiones_iconos = {
            ".awk": "bash",
            ".mp4": "video",
            ".mvk": "video",
            ".sh": "bash",
            ".zsh": "bash",
            ".py": "python",
            ".png": "image",
            ".jpg": "image",
            ".jpeg": "image",
            ".txt": "text",
            ".js": "javascript",
            ".md": "markdown",
            ".php": "php",
            ".html": "html",
            ".css": "css",
            ".ini": "ini",
            ".conf": "conf",
            ".json": "json", 
            ".odt": "odt",
            ".pdf": "pdf",
            ".exe": "exe",
            ".gz": "gz",
        }
    
    def __BAR__(self):
        text = self.PathEntry.get()

        if text and os.path.isdir(text) and not text.endswith('/'):
            self.PathEntry.delete(0, tk.END)
            self.PathEntry.insert(0, text + '/')

    def update_entry(self, ruta) -> None:
        self.PathEntry.configure(state='normal')
        self.PathEntry.delete(0, 'end')
        self.PathEntry.insert(0, ruta)

    def fix_name(self, nombre : str,
                 max_len : int = 18) -> str:

        if len(nombre) > max_len:

            return nombre[:max_len - 3]
        return nombre
    
    @staticmethod
    def _fix_format(s):
        return shlex.quote(s)

    def btn_retrocess(self, master: ctk.CTkToplevel):
        if self.current_path != self.current_path.parent:
            self.current_path = self.current_path.parent
            self.update_entry(ruta=self.current_path)
            self.__list__(master)

    def navigate_to(self, ruta: str, master):
        try: 
            if os.path.isdir(ruta):
                if self.method == 'askdirectory':
                    self.selected_file = ruta
                self.current_path = Path(ruta)
                self.update_entry(ruta=self.current_path)
                self.__list__(master)

                return 

            if self.method == 'asksaveasfile':

                if os.path.isfile(ruta) and os.path.exists(ruta):
                    msg = CTkMessagebox(
                        message='Este archivo existe. ¿Deseas sobreescribirlo?',
                        icon='warning',
                        title='Advertencia',
                        option_1='Yes',
                        option_2='No'
                    )
                    if msg.get() == 'No':
                        return
                
                self.selected_file = ruta 
                self.close_app()

            elif self.method == 'asksaveasfilename':
                if os.path.isfile(ruta):
                    msg = CTkMessagebox(message='Este archivo existe ¿Deseas sobreescribirlo?', icon='warning', title='Avertencia', option_1='Yes', option_2='No')
                    
                    if msg.get() == 'No':
                        return

                    self.selected_file = ruta 
                    self.close_app()

            elif self.method == 'askopenfile':
                try:
                    
                    if not os.path.isfile(path=ruta): 
                        raise FileNotFoundError(f"{ruta}: No such file or directory!")

                    self.selected_file = ruta
                    self.close_app()
                except FileNotFoundError:
                    self.__BAR__()
                    CTkMessagebox(message='Directorio no encontrado!', title='Error', icon='cancel')

            elif os.path.isfile(ruta):
                self.selected_file = ruta
                self.update_entry(self.selected_file)

            else:
                self.PathEntry.delete(0, 'end')
                self.PathEntry.insert(0, self.current_path)
                self.PathEntry.configure(state='normal')
                self.__BAR__()
                CTkMessagebox(message='No such file or directory!', title='Error', icon='cancel')
        except PermissionError:
            self.__BAR__()
            CTkMessagebox(message='Permiso denegado!', title='Error', icon='cancel')

    def close_app(self):

        if self.method == 'asksaveasfilename':
            if not os.path.isdir(self.PathEntry.get()): self.selected_file = self.PathEntry.get()

        if self.selected_file:

            self.app.destroy()
            if self.method == 'asksaveasfile':
                return self.selected_file 
            elif self.method == 'askopenfile':
                return self.selected_file 
            else:
                selected_file = self._fix_format(self.selected_file)
                return selected_file

        elif len(self.selected_objects) >= 1:
            self.app.destroy()
            if self.method == "askopenfilenames":
                selected_objects = [f for f in self.selected_objects if self._fix_format(f)]

            return self.selected_objects if self.method == 'askopenfiles' else selected_objects
    
    @staticmethod
    def _is_video(video: str):

        try:

            cap = cv2.VideoCapture(video)
            valid = cap.isOpened()
            cap.release()
            return valid # Es un video valido
        except:

            return False
                

    def __COMPLETE__(self, event):
        
        ruta = self.current_path 
        files_path = []
        for archivo in self.archivos:
            ruta_completa = os.path.join(ruta, archivo)
            files_path.append(ruta_completa)

        if not files_path:
            return "break"

        max_index = len(self.archivos)

        if event.keysym == 'Up':
            self.tab_index = (self.tab_index - 1) % max_index
        else:
            self.tab_index = (self.tab_index + 1) % max_index

        path = files_path[self.tab_index]
        self.PathEntry.delete(0, ctk.END)
        self.PathEntry.insert(0, path)
        
        self.selected_file = path

        return "break"

    def TopSide(self, master: ctk.CTkToplevel) -> None:
        TopBar = ctk.CTkFrame(master=master, height=40, fg_color="transparent")
        TopBar.pack(side='top', fill='x')
        
        def btn_exit():
            msg = CTkMessagebox(message='¿Deseas salir?', title='Salir', option_1='Yes', option_2='No', icon='warning')
            if msg.get() == 'Yes':
                master.destroy()

        # Botón Salir
        ButtonExit = ctk.CTkButton(master=TopBar, text='Exit', font=('Hack Nerd Font', 15), width=70, command=btn_exit, hover_color='red')
        ButtonExit.pack(side='left', fill='x')

         # Campo Path
        self.PathEntry = ctk.CTkEntry(master=TopBar, width=1070, corner_radius=0, insertwidth=0)
        self.PathEntry.insert(index=0, string=_System.GetPath(str(self.current_path)))
        self.PathEntry.pack(side='right', fill='y', padx=10, pady=10)
        self.PathEntry.bind('<Return>', command = lambda _: self.navigate_to(ruta=self.PathEntry.get(), master=master))
      
        # Botón Retroceso
        ButtonRetroces = ctk.CTkButton(master=TopBar, text='', font=('Hack Nerd Font', 15), width=70, command = lambda path=self.PathEntry.get(): self.btn_retrocess(master=master))
        ButtonRetroces.pack(side='left', fill='x', padx=10, pady=10)

        # Boton de Ok 
        ButtonOk = ctk.CTkButton(master=TopBar, text='Ok', font=('Hack Nerd Font', 15), width=70, command = lambda: self.close_app())
        ButtonOk.pack(side='left', fill='x', padx=10, pady=10)
        self.app.bind('<Return>', lambda _: self.navigate_to(ruta=self.PathEntry.get(), master=master))

        if self.autocomplete:
            
            self.PathEntry.bind('<Down>', lambda event: self.__COMPLETE__(event))
            self.PathEntry.bind('<Up>', lambda event: self.__COMPLETE__(event))
            self.PathEntry.bind('<Tab>', lambda event: self.__COMPLETE__(event))
    
    def _get_video_frame(self, path: str, frame_number: int = 1) -> Image.Image | None:
        if not self._is_video(path):
            return None

        try:
            cap = cv2.VideoCapture(path)
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            ret, frame = cap.read()
            cap.release()
            if ret:
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                return Image.fromarray(frame)
        except:
            return None
    
         
    def LeftSide(self, master) -> None:

        # Frame principal
        LeftSideFrame = ctk.CTkFrame(master=master, width=200)
        LeftSideFrame.pack(side='left', fill='y', padx=10, pady=10)
        LeftSideFrame.pack_propagate(False)

        # Primero el HOME del usuario
        home = os.path.expanduser("~")
        carpetas = {f"{str(os.getenv('HOME')).replace('/home/', '')}": home}

        # Cargar el archivo user-dirs.dirs
        dir_file = os.path.join(home, ".config/user-dirs.dirs")
        pattern = re.compile(r'XDG_\w+_DIR="(.+?)"')

        if os.path.exists(dir_file):
            with open(dir_file, 'r') as f:
                for line in f:
                    if not line.startswith('#') and line.strip():
                        match = pattern.search(line)
                        if match:
                            ruta = os.path.expandvars(match.group(1))
                            nombre = os.path.basename(os.path.normpath(ruta))
                            if nombre != f"{os.getenv('USER')}":  # Evitar duplicado
                                carpetas[nombre] = ruta
        else:
            raise FileNotFoundError(f"El archivo {dir_file} es importante para la ejecución del programa!")

        # Título
        LabelSide = ctk.CTkLabel(master=LeftSideFrame, text='Lugares', font=('Hack Nerd Font', 15))
        LabelSide.pack(side='top', padx=5, pady=5)

        iconos = {
            os.getenv("USER"): "",  # HOME del usuario
            "Desktop": "", "Escritorio": "",
            "Downloads": "", "Descargas": "",
            "Documents": "", "Documentos": "",
            "Pictures": "", "Imágenes": "",
            "Music": "", "Música": "",
            "Videos": "", "Vídeos": "",
            "Templates": "", "Plantillas": "",
            "Public": "", "Público": "",
        }
        # Botones por cada carpeta
        for nombre, ruta in carpetas.items():
            icono = iconos.get(nombre, "")  # Icono por defecto si no está en el diccionario
            texto_boton = f"    {icono}  {nombre}"  # Espacio entre icono y nombre
            DirectorySide = ctk.CTkButton(
                master=LeftSideFrame,
                text=texto_boton,
                font=("Hack Nerd Font", 14),
                anchor="w",
                fg_color="transparent",
                hover_color="#8da3ae",
                text_color="#000000" if self.current_theme.lower() == 'light' else '#cccccc',
                corner_radius=2,
                border_width=0,
                command=lambda r=ruta, n=nombre: self.navigate_to(ruta=r, master=master)#print(f"{n} => {r}")
            )
            DirectorySide.pack(fill="x", pady=4)
    def event_scroll(self, event=None):
        canvas = self.CenterSideFrame._parent_canvas
        # Windows y Linux (con X11)
        canvas.bind_all("<MouseWheel>", lambda event: canvas.yview_scroll(-int(event.delta/120), "units"))
        # macOS usa evento diferente
        canvas.bind_all("<Button-4>", lambda event: canvas.yview_scroll(-1, "units"))
        canvas.bind_all("<Button-5>", lambda event: canvas.yview_scroll(1, "units"))

    def CenterSide(self, master: ctk.CTkToplevel) -> None:
        self.CenterSideFrame = ctk.CTkScrollableFrame(master=master)
        self.CenterSideFrame.pack(expand=True, side='top', fill='both', padx=10, pady=10)
        
        self.event_scroll()

        self.content_frame = ctk.CTkFrame(master=self.CenterSideFrame)
        self.content_frame.pack(side='top', fill='both', expand=True, padx=20, pady=10)

        self.__list__(master=master)

    def __clear__(self):

        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def _handle_click(self, event, r, master, boton, tool_tip=None):

        if not event.state & 0x0004: self.selected_objects.clear()

        if event.state & 0x0004:

            self._all_buttons.append(boton)

            if self.method == 'askopenfiles':

                if r not in self.selected_objects: 
                    if not os.path.isdir(r): self.selected_objects.append(r)

                boton.configure(fg_color="blue")

            elif self.method == 'askopenfilenames':

                if (r not in self.selected_objects) and (not os.path.isdir(r)): self.selected_objects.append(r)
                boton.configure(fg_color="blue")

        else:
            self.selected_objects.clear()
            if self.method == 'askopenfilenames': self.selected_objects.append(r)
            for btn in self._all_buttons:
                if btn.winfo_exists():
                    btn.configure(fg_color="transparent",
                    hover_color="#8da3ae",
                    text_color="#000000" if self.current_theme.lower() == 'light' else '#cccccc',
        )
            if os.path.isdir(r): 
                self.navigate_to(ruta=r, master=master)
            else:
                self.selected_objects.append(r)

    @staticmethod
    def _get_info(ruta: str) -> str:
        try:
            st = os.stat(ruta)

            # Usuario propietario
            usuario = pwd.getpwuid(st.st_uid).pw_name

            # Permisos (ej: -rw-r--r--)
            permisos = stat.filemode(st.st_mode)
    
            # Fecha legible
            fecha = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(st.st_ctime))

            # Tamaño en KB/MB
            if os.path.isdir(ruta):
                try:
                    resultado = subprocess.run(
                        ["du", "-sb", ruta],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        check=True
                    )
                    size_bytes = int(resultado.stdout.split()[0])
                    tamaño = size_bytes
                except Exception as e:
                    print("Error al calcular el tamaño:", e)
                    tamaño = 0 
                else:
                    if tamaño != 0:
                        tamaño = f"{tamaño / 1024 / 1024:.2f} MB"
            else:
                size_bytes = st.st_size
                tamaño = f"{size_bytes/1024:.1f} KB" if size_bytes < 1024**2 else f"{size_bytes/1024/1024:.1f} MB"
    
            return f"""File: {os.path.basename(ruta)}
    Size: {tamaño}
    Owner: {usuario}
    Permissions: {permisos}
    creation: {fecha}
                    """
        except Exception as e:
            return f"Error al obtener info: {e}"

    def __list__(self, master : ctk.CTkToplevel) -> None:
        self.selected_objects.clear()
        self._all_buttons.clear()
        self.__BAR__()
        self.CenterSideFrame._parent_canvas.yview_moveto(0)
        self.__clear__()

        ruta = str(Path(self.current_path)) 
        _ruta = Path(self.current_path)

        
        self.archivos = [
            f.name for f in _ruta.iterdir()
            if (
                (f.is_dir() or (self.method != 'askdirectory' and f.is_file())) and
                (self.hidden or not f.name.startswith('.')) and
                (
                    f.is_dir() or not self.filetypes or 
                    any(f.name.endswith(ext) for ext in self.filetypes)
                )
            )
            ]
        columnas = 5  # Número de columnas en la grilla
        row = 0
        col = 0

        if not self.archivos:
            return 

        for archivo in self.archivos:

            ruta_completa = os.path.join(ruta, archivo)
            if self.method == 'askdirectory' and os.path.isfile(path=ruta_completa):
                continue
            if os.path.isdir(ruta_completa):
                icono = self.iconos["folder"]
            else:
                if self.preview_img and self._is_image(ruta_completa):
                    try:
                        img = Image.open(ruta_completa)
                        img.thumbnail((32, 32))  # tamaño de la previsualización
                        icono = ctk.CTkImage(light_image=img, dark_image=img, size=(32, 32))
                    except:
                        icono = self.iconos.get("image", self.iconos["default"])
                elif self.video_preview and self._is_video(ruta_completa):
                    frame = self._get_video_frame(ruta_completa, frame_number=10)
                    if frame:
                        frame.thumbnail((32, 32))
                        icono = ctk.CTkImage(light_image=frame, dark_image=frame, size=(32, 32))
                    else:
                        icono = self.iconos.get("video", self.iconos["default"])
                else:
                    ext = os.path.splitext(archivo)[1].lower()
                    icon_key = self.extensiones_iconos.get(ext, "default")
                    icono = self.iconos.get(icon_key, self.iconos["default"])            

            archivo_fixeado = self.fix_name(nombre=archivo)

            if self.method not in ['askopenfilenames']:
                command = lambda r=ruta_completa: self.navigate_to(ruta=r, master=master)
            else:
                command = None
            
            boton = ctk.CTkButton(
                master=self.content_frame,
                text=archivo_fixeado,
                image=icono,
                compound="left",
                width=180,
                height=60,
                anchor="w",
                fg_color="transparent",
                hover_color="#8da3ae",
                text_color="#000000" if self.current_theme.lower() == 'light' else '#cccccc',
                command=command
            )

            if self.tool_tip:
                try:
                    CTkToolTip(widget=boton, delay=0.5, message=f'{self._get_info(ruta_completa)}')
                except tk.TclError: 
                    pass

            boton.grid(row=row, column=col, padx=10, pady=10)

            if self.method in ['askopenfilenames', 'askopenfiles']:
                boton.bind('<Button-1>', lambda event, r=ruta_completa, b=boton: self._handle_click(event, r, master, b))

            col += 1
            if col >= columnas:
                col = 0
                row += 1
