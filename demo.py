import numpy as np
from PIL import Image
import tkinter
import tkinter.messagebox
import customtkinter
import nibabel
import numpy
import matplotlib.pyplot
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from scipy import ndimage
from queue import Queue
from skimage import io, img_as_ubyte
from scipy.signal import find_peaks
import SimpleITK as sitk
from scipy.ndimage import laplace
import numpy as np
from scipy.sparse import spdiags
from scipy.sparse.linalg import spsolve

customtkinter.set_appearance_mode("Dark")
customtkinter.set_default_color_theme("green")


class GUI(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("DEMO")
        self.geometry(f"{500}x{200}")
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure((2, 3), weight=0)
        self.grid_rowconfigure((0, 1), weight=1)

        self.file_path = None
        self.image = None
        self.modified_image = None

        self.colors = [
            ["red", "green", "blue", "yellow", "purple", "orange"],
            ["Rojo", "Verde", "Azul", "Amarillo", "Morado", "Naranja"],
        ]
        self.current_color = self.colors[0][0]
        self.brush_size = 3
        self.drawn_objects = []

        self.current_stroke = []
        self.setup_menu()

    def setup_menu(self):
        self.open_file_button = customtkinter.CTkButton(
            self, text="Abrir imagen", font=("Arial", 20), command=self.open_file
        )
        self.open_file_button.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")

        self.load_default_file_button = customtkinter.CTkButton(
            self,
            text="Cargar imagen por defecto",
            font=("Arial", 20),
            command=self.load_default_file,
        )
        self.load_default_file_button.grid(
            row=1, column=1, padx=20, pady=20, sticky="nsew"
        )

    def open_file(self):
        file_path = customtkinter.filedialog.askopenfilename(
            filetypes=[("NIfTI files", "*.nii")]
        )
        if file_path:
            self.file_path = file_path
            self.image = io.imread(file_path)
            self.setup_sidebar()
        else:
            print("No file selected")

    def load_default_file(self):
        file_path = "image.jpg"
        if file_path:
            self.file_path = file_path
            self.image = io.imread(file_path)
            self.setup_sidebar()
        else:
            print("No file selected")

    def setup_sidebar(self):
        self.geometry(f"{1100}x{580}")
        self.modified_image = self.image.copy()

        self.open_file_button.destroy()
        self.load_default_file_button.destroy()
        self.sidebar_frame = customtkinter.CTkScrollableFrame(
            self, width=230, corner_radius=0
        )
        self.sidebar_frame.grid(row=0, column=3, rowspan=6, sticky="nsew")

        self.colors_label = customtkinter.CTkLabel(
            self.sidebar_frame,
            text="Colores",
            font=customtkinter.CTkFont(size=20, weight="bold"),
        )
        self.colors_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.start_processing_ = customtkinter.CTkButton(
            self.sidebar_frame, text="Procesar", command=self.start_processing
        )
        self.start_processing_.grid(row=1, column=0, padx=20, pady=(10, 20))

        self.color_select = customtkinter.CTkOptionMenu(
            self.sidebar_frame,
            state="disabled",
            values=self.colors[1],
            command=self.update_color,
        )
        self.color_select.grid(row=2, column=0, padx=20, pady=10)

        self.drawing_label = customtkinter.CTkLabel(
            self.sidebar_frame,
            text="Dibujar",
            font=customtkinter.CTkFont(size=20, weight="bold"),
        )
        self.drawing_label.grid(row=3, column=0, padx=20, pady=(20, 10))

        self.brush_size_label = customtkinter.CTkLabel(
            self.sidebar_frame, text="Tamaño del pincel: 3", anchor="w"
        )
        self.brush_size_label.grid(row=4, column=0, padx=20, pady=(10, 0))

        self.brush_size_slider = customtkinter.CTkSlider(
            self.sidebar_frame,
            from_=1,
            to=10,
            number_of_steps=9,
            state="disabled",
            command=self.update_brush_size,
        )
        self.brush_size_slider.set(3)
        self.brush_size_slider.grid(row=5, column=0, padx=20, pady=10)

        self.clear_draws_button = customtkinter.CTkButton(
            self.sidebar_frame, text="Limpiar dibujos", command=self.clear_draws
        )
        self.clear_draws_button.grid(row=6, column=0, padx=20, pady=(10, 20))

        self.restore_file_button = customtkinter.CTkButton(
            self.sidebar_frame, text="Restaurar archivo", command=self.restore_file
        )
        self.restore_file_button.grid(row=7, column=0, padx=20, pady=(10, 20))

        self.save_file_button = customtkinter.CTkButton(
            self.sidebar_frame, text="Guardar archivo", command=self.save_file
        )
        self.save_file_button.grid(row=8, column=0, padx=20, pady=(10, 20))

        self.color_select.configure(state="normal")
        self.brush_size_slider.configure(state="normal")

        self.update_image()

    def update_image(self):
        if not hasattr(self, "fig"):
            self.fig = matplotlib.pyplot.Figure(figsize=(5, 5))
            self.ax = self.fig.add_subplot(111)
            self.canvas = FigureCanvasTkAgg(self.fig, master=self)
            self.canvas.get_tk_widget().grid(row=0, column=1, rowspan=6, sticky="nsew")

        self.ax.clear()

        if self.drawn_objects is not None:
            for drawn_object in self.drawn_objects:
                self.ax.add_patch(drawn_object)

        self.ax.imshow(self.modified_image, cmap="gray")
        self.ax.set_xlabel("X")
        self.ax.set_ylabel("Y")
        self.ax.axis("off")

        self.fig.canvas.mpl_connect("button_press_event", self.on_click)
        self.fig.canvas.mpl_connect("motion_notify_event", self.on_drag)
        self.fig.canvas.mpl_connect("button_release_event", self.on_release)
        self.canvas.draw()

    def update_color(self, *args):
        self.current_color = self.colors[0][
            self.colors[1].index(self.color_select.get())
        ]

    def update_brush_size(self, *args):
        self.brush_size = int(self.brush_size_slider.get())
        self.brush_size_label.configure(text=f"Tamaño del pincel: {self.brush_size}")

    def on_click(self, event):
        if event.inaxes == self.ax:
            self.current_stroke = []  # Inicia un nuevo trazo
            x, y = int(event.xdata), int(event.ydata)
            self.current_stroke.append((x, y))

    def on_drag(self, event):
        if event.inaxes == self.ax and event.button == 1:
            x, y = int(event.xdata), int(event.ydata)
            self.current_stroke.append((x, y))
            self.draw_current_stroke()

    def on_release(self, event):
        if event.inaxes == self.ax and event.button == 1:
            self.drawn_objects.append(self.current_stroke)
            print(self.current_stroke)
            self.current_stroke = []

    def draw_current_stroke(self):
        if len(self.current_stroke) > 1:
            for i in range(1, len(self.current_stroke)):
                x1, y1 = self.current_stroke[i - 1]
                x2, y2 = self.current_stroke[i]
                line = matplotlib.lines.Line2D(
                    [x1, x2],
                    [y1, y2],
                    linewidth=self.brush_size,
                    color=self.current_color,
                )
                self.ax.add_line(line)
            self.canvas.draw()

    def clear_draws(self):
        self.drawn_objects = []
        self.update_image()

    def restore_file(self):
        self.modified_image = self.image
        self.update_image()

    def save_file(self):
        matplotlib.pyplot.imsave("modified_image.jpg", self.modified_data, cmap="gray")

    def start_processing(self):

        print(self.drawn_objects)


        # def laplacian_matrix(W):
        #     D = np.diag(np.sum(W, axis=1))
            
        #     L = D - W
            
        #     return L

        # W = np.array([[0, 1, 0, 0],
        #             [1, 0, 1, 1],
        #             [0, 1, 0, 0],
        #             [0, 1, 0, 0]])

        # L = laplacian_matrix(W)
        # print("Laplacian Matrix L:")
        # print(L)


def main():
    app = GUI()
    app.mainloop()


if __name__ == "__main__":
    main()
