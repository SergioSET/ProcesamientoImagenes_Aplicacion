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

customtkinter.set_appearance_mode("Dark")
customtkinter.set_default_color_theme("green")


class GUI(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("Procesamiento")
        self.geometry(f"{1100}x{580}")
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure((2, 3), weight=0)
        self.grid_rowconfigure((0, 1, 2), weight=1)

        self.file_path = None
        self.file_shape = None

        self.image = None
        self.nib_image = None
        self.data = None
        self.modified_data = None
        self.segmented_image = None

        self.dimension = 1
        self.layer = 0

        self.colors = [
            ["red", "green", "blue", "yellow", "purple", "orange"],
            ["Rojo", "Verde", "Azul", "Amarillo", "Morado", "Naranja"],
        ]
        self.current_color = self.colors[0][0]
        self.brush_size = 3
        self.drawn_objects_dict = {}

        self.setup_menu()

    def setup_menu(self):
        self.open_file_button = customtkinter.CTkButton(
            self, text="Abrir archivo .nii", command=self.open_file
        )
        self.open_file_button.grid(row=0, column=0, padx=20, pady=20)
        self.load_default_file_button = customtkinter.CTkButton(
            self, text="Cargar archivo .nii por defecto", command=self.load_default_file
        )
        self.load_default_file_button.grid(row=1, column=0, padx=20, pady=20)

    def open_file(self):
        file_path = customtkinter.filedialog.askopenfilename(
            filetypes=[("NIfTI files", "*.nii")]
        )
        if file_path:
            self.file_path = file_path
            self.nib_image = nibabel.load(self.file_path)
            self.data = self.nib_image.get_fdata()
            self.file_shape = self.data.shape
            self.setup_sidebar()
        else:
            print("No file selected")

    def load_default_file(self):
        file_path = "sub-01_T1w.nii"
        if file_path:
            self.file_path = file_path
            self.nib_image = nibabel.load(self.file_path)
            self.data = self.nib_image.get_fdata()
            self.file_shape = self.data.shape
            self.setup_sidebar()
        else:
            print("No file selected")

    def setup_sidebar(self):
        self.modified_data = self.data.copy()

        self.open_file_button.destroy()
        self.load_default_file_button.destroy()
        self.sidebar_frame = customtkinter.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=2, rowspan=6, sticky="nsew")

        self.dimensiones_label = customtkinter.CTkLabel(
            self.sidebar_frame,
            text="Dimensiones",
            font=customtkinter.CTkFont(size=20, weight="bold"),
        )
        self.dimensiones_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        self.dimension_select = customtkinter.CTkOptionMenu(
            self.sidebar_frame,
            values=["Dimensión 1", "Dimensión 2", "Dimensión 3"],
            command=self.update_dimension,
        )
        self.dimension_select.grid(row=1, column=0, padx=20, pady=(20, 10))

        self.layer_label = customtkinter.CTkLabel(
            self.sidebar_frame, text="Layer:", anchor="w"
        )
        self.layer_label.grid(row=2, column=0, padx=20, pady=(10, 0))
        self.layer_slider = customtkinter.CTkSlider(
            self.sidebar_frame,
            from_=0,
            to=100,
            state="disabled",
            command=self.update_layer,
        )
        self.layer_slider.grid(row=3, column=0, padx=20, pady=10)

        self.procesamiento_label = customtkinter.CTkLabel(
            self.sidebar_frame,
            text="Procesamiento",
            font=customtkinter.CTkFont(size=20, weight="bold"),
        )
        self.procesamiento_label.grid(row=4, column=0, padx=20, pady=(20, 10))
        self.procesamiento_select = customtkinter.CTkOptionMenu(
            self.sidebar_frame,
            state="disabled",
            values=[
                "Histogram",
                "Matching",
                "White Straping",
                "Intesity rescaller",
                "Zindex",
                "Mean filter",
                "Median filter",
            ],
            command=self.thresholding_menu,
        )
        self.procesamiento_select.grid(row=5, column=0, padx=20, pady=10)

        self.color_select = customtkinter.CTkOptionMenu(
            self.sidebar_frame,
            state="disabled",
            values=self.colors[1],
            command=self.update_color,
        )
        self.color_select.grid(row=6, column=0, padx=20, pady=10)

        self.drawing_label = customtkinter.CTkLabel(
            self.sidebar_frame,
            text="Dibujar",
            font=customtkinter.CTkFont(size=20, weight="bold"),
        )
        self.drawing_label.grid(row=7, column=0, padx=20, pady=(20, 10))

        self.brush_size_label = customtkinter.CTkLabel(
            self.sidebar_frame, text="Tamaño del pincel: 3", anchor="w"
        )
        self.brush_size_label.grid(row=8, column=0, padx=20, pady=(10, 0))
        self.brush_size_slider = customtkinter.CTkSlider(
            self.sidebar_frame,
            from_=1,
            to=10,
            number_of_steps=9,
            state="disabled",
            command=self.update_brush_size,
        )
        self.brush_size_slider.set(3)
        self.brush_size_slider.grid(row=9, column=0, padx=20, pady=10)
        self.clear_draws_button = customtkinter.CTkButton(
            self.sidebar_frame, text="Limpiar dibujos", command=self.clear_draws
        )
        self.clear_draws_button.grid(row=10, column=0, padx=20, pady=(10, 20))

        self.restore_file_button = customtkinter.CTkButton(
            self.sidebar_frame, text="Restaurar archivo", command=self.restore_file
        )
        self.restore_file_button.grid(row=11, column=0, padx=20, pady=(10, 20))

        self.save_file_button = customtkinter.CTkButton(
            self.sidebar_frame, text="Guardar archivo", command=self.save_file
        )
        self.save_file_button.grid(row=12, column=0, padx=20, pady=(10, 20))

        self.update_dimension()

    def update_dimension(self, *args):
        if self.dimension not in self.drawn_objects_dict:
            self.drawn_objects_dict[self.dimension] = {}

        if self.dimension_select.get() == "Dimensión 1":
            dimension = 0
        elif self.dimension_select.get() == "Dimensión 2":
            dimension = 1
        else:
            dimension = 2

        self.dimension = dimension
        self.layer = int(self.file_shape[self.dimension] // 2)
        self.layer_slider.configure(number_of_steps=self.file_shape[self.dimension] - 1)
        self.layer_slider.configure(from_=0, to=self.file_shape[self.dimension] - 1)
        self.layer_label.configure(text=f"Layer: {int(self.layer)}")
        self.layer_slider.configure(state="normal")
        self.layer_slider.set(self.layer)
        self.umbralizacion_select.configure(state="normal")
        self.color_select.configure(state="normal")
        self.brush_size_slider.configure(state="normal")

        self.update_image()

    def update_layer(self, *args):
        self.layer = int(self.layer_slider.get())
        self.layer_label.configure(text=f"Layer: {self.layer}")
        self.layer_slider.set(self.layer)
        self.update_image()

    def update_image(self):
        if self.dimension == 0:
            slice_data = numpy.rot90(self.modified_data[self.layer, :, :])
        elif self.dimension == 1:
            slice_data = numpy.rot90(self.modified_data[:, self.layer, :])
        else:
            slice_data = numpy.rot90(self.modified_data[:, :, self.layer])

        if not hasattr(self, "fig"):
            self.fig = matplotlib.pyplot.Figure(figsize=(5, 5))
            self.ax = self.fig.add_subplot(111)
            self.canvas = FigureCanvasTkAgg(self.fig, master=self)
            self.canvas.get_tk_widget().grid(row=0, column=1, rowspan=6, sticky="nsew")

        self.ax.clear()

        if (
            self.dimension in self.drawn_objects_dict
            and self.layer in self.drawn_objects_dict[self.dimension]
        ):
            for drawn_object in self.drawn_objects_dict[self.dimension][self.layer]:
                self.ax.add_patch(drawn_object)

        self.ax.imshow(slice_data, cmap="gray")
        self.ax.set_xlabel("X")
        self.ax.set_ylabel("Y")
        self.ax.axis("off")

        self.fig.canvas.mpl_connect("button_press_event", self.on_click)
        self.fig.canvas.mpl_connect("motion_notify_event", self.on_drag)
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
            x, y = int(event.xdata), int(event.ydata)
            circle = matplotlib.patches.Circle(
                (x, y), radius=self.brush_size, color=self.current_color
            )

            if self.dimension not in self.drawn_objects_dict:
                self.drawn_objects_dict[self.dimension] = {}

            if self.layer not in self.drawn_objects_dict[self.dimension]:
                self.drawn_objects_dict[self.dimension][self.layer] = []

            self.drawn_objects_dict[self.dimension][self.layer].append(circle)

            self.ax.add_patch(circle)
            self.canvas.draw()

    def on_drag(self, event):
        if event.inaxes == self.ax and event.button == 1:
            x, y = int(event.xdata), int(event.ydata)
            circle = matplotlib.patches.Circle(
                (x, y), radius=self.brush_size, color=self.current_color
            )

            if self.dimension not in self.drawn_objects_dict:
                self.drawn_objects_dict[self.dimension] = {}

            if self.layer not in self.drawn_objects_dict[self.dimension]:
                self.drawn_objects_dict[self.dimension][self.layer] = []

            self.drawn_objects_dict[self.dimension][self.layer].append(circle)

            self.ax.add_patch(circle)
            self.canvas.draw()

            self.update_image()

    def clear_draws(self):
        self.drawn_objects_dict[self.dimension][self.layer] = []
        self.update_image()

    def restore_file(self):
        self.modified_data = self.data
        self.drawn_objects_dict = {}
        self.update_image()

    def save_file(self):
        modified_img = nibabel.Nifti1Image(self.modified_data, self.nib_image.affine)
        nibabel.save(modified_img, "modified_image.nii")

    def thresholding_menu(self, *args):

        if self.umbralizacion_select.get() == "No seleccionado":
            self.no_threshold()
        elif self.umbralizacion_select.get() == "Umbralización":
            self.umbralizacion()
        elif self.umbralizacion_select.get() == "Isodata":
            self.isodata()
        elif self.umbralizacion_select.get() == "Crecimiento de regiones":
            self.crecimiento_regiones()
        elif self.umbralizacion_select.get() == "K-means":
            self.kmeans()

    def no_procesamiento(self):
        if hasattr(self, "procesamiento_frame"):
            self.procesamiento_frame.destroy()

    def histogram(self):
        if hasattr(self, "procesamiento_frame"):
            self.procesamiento_frame.destroy()

        self.procesamiento_frame = customtkinter.CTkFrame(self.sidebar_frame)
        self.procesamiento_frame.grid(row=6, column=0, padx=20, pady=10)

        self.histograma = numpy.histogram(self.modified_data, bins=50)
        self.ax.hist(self.modified_data.flatten(), bins=50)
        self.canvas.draw()
        

def main():
    app = GUI()
    app.mainloop()


if __name__ == "__main__":
    main()
