import customtkinter as ctk
from tkinter import filedialog
import cv2
from PIL import Image, ImageTk, ImageDraw
from moviepy import VideoFileClip
import os

OUTPUT_DIR = "output"
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

class VideoCropApp(ctk.CTkToplevel):
    def __init__(self, main=None):
        super().__init__()
        self.title("Open Clip - Recortar Video")
        self.geometry("1000x600")
        self.main = main

        self.video_path = None
        self.frame = None
        self.rect_start = None
        self.rect_id = None
        self.crop_coords_list = []
        self.preview_images = []

        # Botones
        self.import_button = ctk.CTkButton(self, text="Importar Video", command=self.importar_video)
        self.import_button.pack(pady=10)

        self.mode_frame = ctk.CTkFrame(self)
        self.mode_frame.pack(pady=5)
        self.mode = ctk.StringVar(value="custom")
        ctk.CTkRadioButton(self.mode_frame, text="1:1", variable=self.mode, value="square").pack(side="left", padx=5)
        ctk.CTkRadioButton(self.mode_frame, text="9:16", variable=self.mode, value="vertical").pack(side="left", padx=5)
        ctk.CTkRadioButton(self.mode_frame, text="Personalizado", variable=self.mode, value="custom").pack(side="left", padx=5)

        # Canvases lado a lado
        self.canvas_frame = ctk.CTkFrame(self)
        self.canvas_frame.pack(pady=10)

        self.original_canvas = ctk.CTkCanvas(self.canvas_frame, width=400, height=450, bg="black")
        self.original_canvas.pack(side="left", padx=10)

        self.preview_canvas = ctk.CTkCanvas(self.canvas_frame, width=405, height=720, bg="gray")
        self.preview_canvas.pack(side="right", padx=10)

        self.original_canvas.bind("<Button-1>", self.marcar_inicio)
        self.original_canvas.bind("<B1-Motion>", self.dibujar_rectangulo)
        self.original_canvas.bind("<ButtonRelease-1>", self.marcar_fin)

        self.crop_button = ctk.CTkButton(self, text="Añadir Recorte", command=self.recortar_video, state="disabled")
        self.crop_button.pack(pady=5)

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
        img = img.resize((400, 450))
        self.tk_img = ImageTk.PhotoImage(image=img)
        self.original_canvas.create_image(0, 0, anchor="nw", image=self.tk_img)

    def marcar_inicio(self, event):
        self.rect_start = (event.x, event.y)

    def dibujar_rectangulo(self, event):
        if self.rect_id:
            self.original_canvas.delete(self.rect_id)

        x0, y0 = self.rect_start
        x1, y1 = event.x, event.y

        mode = self.mode.get()
        if mode == "square":
            size = min(abs(x1 - x0), abs(y1 - y0))
            x1 = x0 + size if x1 > x0 else x0 - size
            y1 = y0 + size if y1 > y0 else y0 - size
        elif mode == "vertical":
            height = abs(y1 - y0)
            width = int(height * 9 / 16)
            x1 = x0 + width if x1 > x0 else x0 - width

        self.rect_id = self.original_canvas.create_rectangle(x0, y0, x1, y1, outline="red")

    def marcar_fin(self, event):
        x0, y0 = self.rect_start
        x1, y1 = event.x, event.y
        self.crop_coords_list.append((min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)))
        self.actualizar_vista_previa()

    def actualizar_vista_previa(self):
        # Crear imagen 9:16 de 405x720 con recortes
        preview_img = Image.new("RGB", (405, 720), (50, 50, 50))

        for i, crop_coords in enumerate(self.crop_coords_list):
            if self.frame is None:
                return
            frame_rgb = cv2.cvtColor(self.frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            img = img.resize((400, 450))
            cropped = img.crop(crop_coords)
            cropped = cropped.resize((405, 360))

            overlay = Image.new("RGB", (405, 360), (0, 0, 255) if i == 0 else (255, 0, 0))
            blended = Image.blend(overlay, cropped, 0.5)
            preview_img.paste(blended, (0, 0 if i == 0 else 360))

        self.tk_preview_img = ImageTk.PhotoImage(preview_img)
        self.preview_canvas.create_image(0, 0, anchor="nw", image=self.tk_preview_img)

    def recortar_video(self):
        if not self.crop_coords_list or not self.video_path:
            return

        cap = cv2.VideoCapture(self.video_path)
        width_real = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height_real = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)

        x_scale = width_real / 400
        y_scale = height_real / 450

        clips = []
        temp_paths = []

        for i, coords in enumerate(self.crop_coords_list):
            x0, y0, x1, y1 = coords
            crop_rect = (int(x0 * x_scale), int(y0 * y_scale), int(x1 * x_scale), int(y1 * y_scale))
            crop_width = crop_rect[2] - crop_rect[0]
            crop_height = crop_rect[3] - crop_rect[1]

            output_path = os.path.join(OUTPUT_DIR, f"recorte_{i}.mp4")
            temp_paths.append(output_path)

            fourcc = cv2.VideoWriter_fourcc(*'mp4v')
            out = cv2.VideoWriter(output_path, fourcc, fps, (crop_width, crop_height))
            cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                cropped = frame[crop_rect[1]:crop_rect[3], crop_rect[0]:crop_rect[2]]
                out.write(cropped)
            out.release()

        cap.release()

        try:
            original = VideoFileClip(self.video_path)
            final_clips = []
            for path in temp_paths:
                clip = VideoFileClip(path).resize((405, 360))
                final_clips.append(clip)

            from moviepy import CompositeVideoClip
            if len(final_clips) > 1:
                composite = CompositeVideoClip([
                    final_clips[0].set_position((0, 0)),
                    final_clips[1].set_position((0, 360))
                ], size=(405, 720))
                composite = composite.set_audio(original.audio)
                final_output = os.path.join(OUTPUT_DIR, "video_final_9x16.mp4")
                composite.write_videofile(final_output, codec="libx264", audio_codec="aac")
            else:
                final_output = os.path.join(OUTPUT_DIR, "video_final.mp4")
                final_clips[0].set_audio(original.audio).write_videofile(final_output, codec="libx264", audio_codec="aac")

        except Exception as e:
            print(f"Error al añadir audio o unir clips: {e}")

        if self.main:
            self.main.deiconify()
            self.main.actualizar_lista()
        self.destroy()
