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

customtkinter.set_appearance_mode("Dark")
customtkinter.set_default_color_theme("green")


class GUI(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("Procesamiento")
        self.geometry(f"{500}x{200}")
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure((2, 3), weight=0)
        self.grid_rowconfigure((0, 1), weight=1)

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
            self, text="Abrir archivo .nii", font=("Arial", 20), command=self.open_file
        )
        self.open_file_button.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")

        self.load_default_file_button = customtkinter.CTkButton(
            self,
            text="Cargar archivo .nii por defecto",
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
        self.geometry(f"{1100}x{580}")
        self.modified_data = self.data.copy()

        self.open_file_button.destroy()
        self.load_default_file_button.destroy()
        self.sidebar_frame = customtkinter.CTkScrollableFrame(self, width=230, corner_radius=0)
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
                "No seleccionado",
                "Histogram Matching",
                "White Stripe",
                "Intesity rescaller",
                "Z Score",
                "Mean filter",
                "Median filter",
            ],
            command=self.procesamiento_menu,
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
        self.procesamiento_select.configure(state="normal")
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

        self.image = slice_data

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
        self.update_image()

    def save_file(self):
        modified_img = nibabel.Nifti1Image(self.modified_data, self.nib_image.affine)
        nibabel.save(modified_img, "modified_image.nii")

    def procesamiento_menu(self, *args):

        if self.procesamiento_select.get() == "No seleccionado":
            self.no_procesamiento()
        elif self.procesamiento_select.get() == "Histogram Matching":
            self.histogramMatching()
        elif self.procesamiento_select.get() == "White Stripe":
            self.white_stripe()
        elif self.procesamiento_select.get() == "Intesity rescaller":
            self.intesity_rescaller()
        elif self.procesamiento_select.get() == "Z Score":
            self.zscore()
        elif self.procesamiento_select.get() == "Mean filter":
            self.mean_filter()
        elif self.procesamiento_select.get() == "Median filter":
            self.median_filter()

    def no_procesamiento(self):
        if hasattr(self, "procesamiento_frame"):
            self.procesamiento_frame.destroy()

    def histogramMatching(self):
        self.no_procesamiento()

        def update_background(value):
            self.background_label.configure(text=f"Valor background: {int(value)}")

        def update_percentile(value):
            self.percentile_label.configure(text=f"Percentil: {int(value)}")

        def apply_histogram():

            def training_histogram():
                background = int(self.background_slider.get())
                percentiles = int(self.percentile_slider.get())

                reference_data = nibabel.load("sub-02_T1w.nii").get_fdata().flatten()

                reference = numpy.linspace(5, 95, percentiles)
                reference_landmarks = numpy.percentile(reference_data, reference)
                piece_wise_func = []

                for i in range(0, len(reference_landmarks)):
                    m = (reference_landmarks[i] - reference_landmarks[i - 1]) / (
                        reference[i] - reference[i - 1]
                    )
                    b = reference_landmarks[i - 1] - m * reference[i - 1]
                    fx = lambda x, m=m, b=b: m * x + b
                    piece_wise_func.append([m, b, fx])

                # print(piece_wise_func)

                return piece_wise_func

            def transform_histogram(piecewise_func):
                img = self.data.copy()
                img_flat = img.flatten()

                percentiles = numpy.linspace(5, 95, int(self.percentile_slider.get()))

                transformed_data = []

                for pixel_value in img_flat:
                    for segment in piecewise_func:
                        m, b, fx = segment
                        if (
                            pixel_value >= percentiles[0]
                            and pixel_value < percentiles[1]
                        ):
                            transformed_data.append(fx(pixel_value))
                            break
                    else:
                        transformed_data.append(pixel_value)

                transformed_data = numpy.array(transformed_data).reshape(img.shape)

                self.modified_data = transformed_data
                self.update_image()

            transform_histogram(training_histogram())

        self.procesamiento_frame = customtkinter.CTkFrame(
            self, width=140, corner_radius=0
        )
        self.procesamiento_frame.grid(row=0, column=0, rowspan=6, sticky="nsew")

        self.titulo_label = customtkinter.CTkLabel(
            self.procesamiento_frame,
            text="Histograma de intensidades",
            font=customtkinter.CTkFont(size=15, weight="bold"),
        )
        self.titulo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.background_label = customtkinter.CTkLabel(
            self.procesamiento_frame, text="Valor background: 10", font=("Arial", 10)
        )
        self.background_label.grid(row=1, column=0, padx=20, pady=(10, 0))

        self.background_slider = customtkinter.CTkSlider(
            self.procesamiento_frame,
            from_=0,
            to=50,
            number_of_steps=50,
            state="normal",
            command=update_background,
        )
        self.background_slider.set(10)
        self.background_slider.grid(row=2, column=0, padx=20, pady=10)

        self.percentile_label = customtkinter.CTkLabel(
            self.procesamiento_frame, text="Percentil: 10", font=("Arial", 10)
        )
        self.percentile_label.grid(row=3, column=0, padx=20, pady=(10, 0))

        self.percentile_slider = customtkinter.CTkSlider(
            self.procesamiento_frame,
            from_=1,
            to=100,
            number_of_steps=99,
            state="normal",
            command=update_percentile,
        )
        self.percentile_slider.set(10)
        self.percentile_slider.grid(row=4, column=0, padx=20, pady=10)

        self.histogram_button = customtkinter.CTkButton(
            self.procesamiento_frame,
            text="Aplicar histograma",
            command=apply_histogram,
        )
        self.histogram_button.grid(row=5, column=0, padx=20, pady=(10, 20))

    def white_stripe(self):
        self.no_procesamiento()

        def update_background(value):
            self.background_label.configure(text=f"Background: {int(value)}")

        def apply_white_stripe():

            data = self.data.copy()

            background = int(self.background_slider.get())

            histogram, edges = numpy.histogram(data[data > background].flatten(), bins=100)

            peaks, properties = find_peaks(histogram, height=10000)

            matplotlib.pyplot.plot(histogram)
            matplotlib.pyplot.plot(peaks, histogram[peaks], "o")
            matplotlib.pyplot.show()

            peakValues = edges[peaks]

            ws = peakValues[len(peakValues) - 1] - peakValues[0]
            
            image_data_rescaled = data / ws

            self.modified_data = image_data_rescaled

            self.update_image()

        self.procesamiento_frame = customtkinter.CTkFrame(
            self, width=140, corner_radius=0
        )
        self.procesamiento_frame.grid(row=0, column=0, rowspan=6, sticky="nsew")

        self.titulo_label = customtkinter.CTkLabel(
            self.procesamiento_frame,
            text="White Stripe",
            font=customtkinter.CTkFont(size=20, weight="bold"),
        )
        self.titulo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.background_label = customtkinter.CTkLabel(
            self.procesamiento_frame, text="Background: 10", font=("Arial", 10)
        )
        self.background_label.grid(row=1, column=0, padx=20, pady=(10, 0))

        self.background_slider = customtkinter.CTkSlider(
            self.procesamiento_frame,
            from_=0,
            to=100,
            number_of_steps=100,
            state="normal",
            command=update_background,
        )
        self.background_slider.set(10)
        self.background_slider.grid(row=2, column=0, padx=20, pady=10)

        self.white_stripe_button = customtkinter.CTkButton(
            self.procesamiento_frame,
            text="Aplicar White Stripe",
            command=apply_white_stripe,
        )
        self.white_stripe_button.grid(row=3, column=0, padx=20, pady=(10, 20))

    def intesity_rescaller(self):
        self.no_procesamiento()

        def apply_intensity_rescaler():

            data = self.data.copy()

            min_value = numpy.min(data)
            max_value = numpy.max(data)
            data = (data - min_value) / (max_value - min_value)

            self.modified_data = data

            self.update_image()

        self.procesamiento_frame = customtkinter.CTkFrame(
            self, width=140, corner_radius=0
        )
        self.procesamiento_frame.grid(row=0, column=0, rowspan=6, sticky="nsew")

        self.titulo_label = customtkinter.CTkLabel(
            self.procesamiento_frame,
            text="Intesity rescaller",
            font=customtkinter.CTkFont(size=20, weight="bold"),
        )
        self.titulo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.intesity_rescaler_button = customtkinter.CTkButton(
            self.procesamiento_frame,
            text="Aplicar Intesity rescaler",
            command=apply_intensity_rescaler,
        )
        self.intesity_rescaler_button.grid(row=1, column=0, padx=20, pady=(10, 20))

    def zscore(self):
        self.no_procesamiento()

        self.procesamiento_frame = customtkinter.CTkFrame(
            self, width=140, corner_radius=0
        )
        self.procesamiento_frame.grid(row=0, column=0, rowspan=6, sticky="nsew")

        self.titulo_label = customtkinter.CTkLabel(
            self.procesamiento_frame,
            text="Z Score",
            font=customtkinter.CTkFont(size=20, weight="bold"),
        )
        self.titulo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        def update_background(value):
            self.background_label.configure(text=f"Valor background: {int(value)}")

        def apply_zscore():
            background = int(self.background_slider.get())

            img = self.data.copy()

            mean_value = img[img > background].mean()
            std_value = img[img > background].std()

            img_zscore = (img - mean_value) / std_value

            img = img * img_zscore

            self.modified_data = img

            self.update_image()

        self.background_label = customtkinter.CTkLabel(
            self.procesamiento_frame, text="Valor background: 10", font=("Arial", 10)
        )
        self.background_label.grid(row=1, column=0, padx=20, pady=(10, 0))

        self.background_slider = customtkinter.CTkSlider(
            self.procesamiento_frame,
            from_=0,
            to=50,
            number_of_steps=50,
            state="normal",
            command=update_background,
        )
        self.background_slider.set(10)
        self.background_slider.grid(row=2, column=0, padx=20, pady=10)

        self.zscore_button = customtkinter.CTkButton(
            self.procesamiento_frame,
            text="Aplicar Z Score",
            command=apply_zscore,
        )
        self.zscore_button.grid(row=3, column=0, padx=20, pady=(10, 20))

    def mean_filter(self):
        self.no_procesamiento()

        def apply_mean_filter(data, neighborhood):
            filtered_data = numpy.zeros_like(data, dtype=numpy.float64)
            depth, height, width = data.shape
            n = neighborhood // 2

            padded_data = numpy.pad(data, ((n, n), (n, n), (n, n)), mode="constant")

            neighborhood_values = []
            filter_size = neighborhood**3

            for dz in range(-n, n + 1):
                for dy in range(-n, n + 1):
                    for dx in range(-n, n + 1):
                        neighborhood_values.append(
                            padded_data[
                                n + dz : n + dz + depth,
                                n + dy : n + dy + height,
                                n + dx : n + dx + width,
                            ]
                        )

            neighborhood_values = numpy.array(neighborhood_values)
            neighborhood_sums = numpy.sum(neighborhood_values, axis=0)
            filtered_data = neighborhood_sums / filter_size

            return filtered_data

        def mean_filter(*args):
            neighborhood_sizes = {
                "3x3": 3,
                "5x5": 5,
                "7x7": 7,
                "9x9": 9,
            }

            if mean_filter_select.get() == "No seleccionado":
                self.modified_data = self.data
                self.update_image()
                return

            neighborhood = neighborhood_sizes[mean_filter_select.get()]

            # self.modified_data = ndimage.uniform_filter(self.data, size=neighborhood)
            self.modified_data = apply_mean_filter(self.data, neighborhood)
            self.update_image()

        self.procesamiento_frame = customtkinter.CTkFrame(
            self, width=140, corner_radius=0
        )
        self.procesamiento_frame.grid(row=0, column=0, rowspan=6, sticky="nsew")

        self.titulo_label = customtkinter.CTkLabel(
            self.procesamiento_frame,
            text="Filtro de media",
            font=customtkinter.CTkFont(size=20, weight="bold"),
        )
        self.titulo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        mean_filter_select = customtkinter.CTkOptionMenu(
            self.procesamiento_frame,
            values=[
                "No seleccionado",
                "3x3",
                "5x5",
                "7x7",
                "9x9",
            ],
            command=mean_filter,
        )
        mean_filter_select.grid(row=1, column=0, padx=20, pady=10)

        self.update_image()

    def median_filter(self):
        self.no_procesamiento()

        def apply_median_filter(data, neighborhood):
            filtered_data = numpy.zeros_like(data, dtype=numpy.float64)
            depth, height, width = data.shape
            n = neighborhood // 2

            padded_data = numpy.pad(data, ((n, n), (n, n), (n, n)), mode="constant")

            neighborhood_values = []

            for dz in range(-n, n + 1):
                for dy in range(-n, n + 1):
                    for dx in range(-n, n + 1):
                        neighborhood_values.append(
                            padded_data[
                                n + dz : n + dz + depth,
                                n + dy : n + dy + height,
                                n + dx : n + dx + width,
                            ]
                        )

            neighborhood_values = numpy.array(neighborhood_values)
            neighborhood_median = numpy.median(neighborhood_values, axis=0)
            filtered_data = neighborhood_median

            return filtered_data

        def median_filter(*args):
            neighborhood_sizes = {
                "3x3": 3,
                "5x5": 5,
                "7x7": 7,
                "9x9": 9,
            }

            if median_filter_select.get() == "No seleccionado":
                self.modified_data = self.data
                self.update_image()
                return

            neighborhood = neighborhood_sizes[median_filter_select.get()]

            # self.modified_data = ndimage.median_filter(self.data, size=neighborhood)
            self.modified_data = apply_median_filter(self.data, neighborhood)

            self.update_image()

        self.procesamiento_frame = customtkinter.CTkFrame(
            self, width=140, corner_radius=0
        )
        self.procesamiento_frame.grid(row=0, column=0, rowspan=6, sticky="nsew")

        self.titulo_label = customtkinter.CTkLabel(
            self.procesamiento_frame,
            text="Filtro de mediana",
            font=customtkinter.CTkFont(size=20, weight="bold"),
        )
        self.titulo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        median_filter_select = customtkinter.CTkOptionMenu(
            self.procesamiento_frame,
            values=[
                "No seleccionado",
                "3x3",
                "5x5",
                "7x7",
                "9x9",
            ],
            command=median_filter,
        )
        median_filter_select.grid(row=1, column=0, padx=20, pady=10)

        self.update_image()


def main():
    app = GUI()
    app.mainloop()


if __name__ == "__main__":
    main()
