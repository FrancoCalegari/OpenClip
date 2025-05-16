import customtkinter as ctk
from tkinter import filedialog
import cv2
from PIL import Image, ImageTk
#from moviepy.editor import VideoFileClip
from moviepy.editor import VideoFileClip, AudioFileClip
import os

ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")


class VideoCropApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Open Clip - Inicio")
        self.geometry("900x600")

        self.import_button = ctk.CTkButton(self, text="Importar Video", command=self.importar_video)
        self.import_button.pack(pady=10)

        self.canvas = ctk.CTkCanvas(self, width=800, height=450, bg="black")
        self.canvas.pack()

        self.crop_button = ctk.CTkButton(self, text="Recortar Video", command=self.recortar_video, state="disabled")
        self.crop_button.pack(pady=10)

        self.video_path = None
        self.frame = None
        self.rect_start = None
        self.rect_id = None
        self.crop_coords = None

        self.canvas.bind("<Button-1>", self.marcar_inicio)
        self.canvas.bind("<B1-Motion>", self.dibujar_rectangulo)
        self.canvas.bind("<ButtonRelease-1>", self.marcar_fin)

    def importar_video(self):
        path = filedialog.askopenfilename(filetypes=[("Videos", "*.mp4 *.avi *.mov")])
        if path:
            self.video_path = path
            cap = cv2.VideoCapture(path)
            success, frame = cap.read()
            cap.release()

            if success:
                self.frame = frame
                self.mostrar_frame(frame)
                self.crop_button.configure(state="normal")

    def mostrar_frame(self, frame):
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        img = img.resize((800, 450))
        self.tk_img = ImageTk.PhotoImage(image=img)
        self.canvas.create_image(0, 0, anchor="nw", image=self.tk_img)

    def marcar_inicio(self, event):
        self.rect_start = (event.x, event.y)

    def dibujar_rectangulo(self, event):
        if self.rect_id:
            self.canvas.delete(self.rect_id)
        x0, y0 = self.rect_start
        x1, y1 = event.x, event.y
        self.rect_id = self.canvas.create_rectangle(x0, y0, x1, y1, outline="red")

    def marcar_fin(self, event):
        x0, y0 = self.rect_start
        x1, y1 = event.x, event.y
        self.crop_coords = (min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1))
        print(f"Región seleccionada: {self.crop_coords}")

    def recortar_video(self):
        if not self.crop_coords or not self.video_path:
            return

        cap = cv2.VideoCapture(self.video_path)
        width_real = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height_real = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)

        x_scale = width_real / 800
        y_scale = height_real / 450

        x0, y0, x1, y1 = self.crop_coords
        crop_rect = (
            int(x0 * x_scale),
            int(y0 * y_scale),
            int(x1 * x_scale),
            int(y1 * y_scale)
        )
        crop_width = crop_rect[2] - crop_rect[0]
        crop_height = crop_rect[3] - crop_rect[1]

        output_path = filedialog.asksaveasfilename(defaultextension=".mp4", filetypes=[("MP4", "*.mp4")])
        if not output_path:
            return

        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (crop_width, crop_height))

        print(f"Exportando video recortado a: {output_path}")
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            cropped = frame[crop_rect[1]:crop_rect[3], crop_rect[0]:crop_rect[2]]
            out.write(cropped)

        cap.release()
        out.release()

        # Reinsertar audio usando moviepy
        print("Añadiendo audio al video recortado...")
        try:
            original = VideoFileClip(self.video_path)
            recortado = VideoFileClip(output_path)
            recortado = recortado.set_audio(original.audio)
            final_output = output_path.replace(".mp4", "_final.mp4")
            recortado.write_videofile(final_output, codec="libx264", audio_codec="aac")
            print("Exportación final con audio completada.")
        except Exception as e:
            print(f"Error al añadir audio: {e}")
        print("Video exportado correctamente.")


if __name__ == "__main__":
    app = VideoCropApp()
    app.mainloop()

