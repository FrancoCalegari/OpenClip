import customtkinter as ctk
import os
import subprocess
from video_cropper import VideoCropApp

OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

class MainMenu(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Open Clip - Menú Principal")
        self.geometry("1000x600")

        ctk.CTkLabel(self, text="Menú Principal", font=("Arial", 20)).pack(pady=10)

        ctk.CTkButton(self, text="Crear un Videomix", command=self.abrir_cropper).pack(pady=10)
        ctk.CTkButton(self, text="Ver Carpeta", command=self.abrir_carpeta).pack(pady=10)

        self.videos_frame = ctk.CTkScrollableFrame(self, width=700, height=400)
        self.videos_frame.pack(pady=10)

        self.actualizar_lista()

    def abrir_cropper(self):
        self.withdraw()
        VideoCropApp(main=self)

    def abrir_carpeta(self):
        path = os.path.abspath(OUTPUT_DIR)
        if os.name == "nt":
            os.startfile(path)
        else:
            subprocess.call(["xdg-open", path])

    def actualizar_lista(self):
        for widget in self.videos_frame.winfo_children():
            widget.destroy()

        for archivo in os.listdir(OUTPUT_DIR):
            if archivo.endswith(".mp4"):
                ctk.CTkLabel(self.videos_frame, text=archivo).pack()
