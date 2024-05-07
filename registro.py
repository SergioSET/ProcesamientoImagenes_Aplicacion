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

customtkinter.set_appearance_mode("Dark")
customtkinter.set_default_color_theme("green")


class GUI(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("Bordes y Registro")
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

        self.moving_image = None
        self.moving_nib_image = None
        self.moving_data = None
        self.moving_modified_data = None
        
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
        self.sidebar_frame.grid(row=0, column=3, rowspan=6, sticky="nsew")

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
                "Bordes",
                "Registro",
            ],
            command=self.registro_menu,
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
            slice_data = np.rot90(self.modified_data[self.layer, :, :])
        elif self.dimension == 1:
            slice_data = np.rot90(self.modified_data[:, self.layer, :])
        else:
            slice_data = np.rot90(self.modified_data[:, :, self.layer])

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

        if self.moving_image:
            self.ax.title.set_text("Fixed")

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

    def registro_menu(self, *args):

        if self.procesamiento_select.get() == "No seleccionado":
            self.no_registro()
        elif self.procesamiento_select.get() == "Bordes":
            self.borders()
        elif self.procesamiento_select.get() == "Registro":
            self.register()

    def no_registro(self):
        if hasattr(self, "registro_frame"):
            self.registro_frame.destroy()

    def borders(self):
        self.no_registro()

        def apply_borders():
            self.modified_data = ndimage.sobel(self.modified_data)
            self.update_image()

        self.registro_frame = customtkinter.CTkFrame(
            self, width=140, corner_radius=0
        )
        self.registro_frame.grid(row=0, column=0, rowspan=6, sticky="nsew")

        self.bordes_label = customtkinter.CTkLabel(
            self.registro_frame,
            text="Bordes",
            font=customtkinter.CTkFont(size=20, weight="bold"),
        )
        self.bordes_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.bordes_button = customtkinter.CTkButton(
            self.registro_frame, text="Aplicar Sobel", command=apply_borders
        )
        self.bordes_button.grid(row=1, column=0, padx=20, pady=(10, 20))


    def select_moving_image(self):
        file_path = customtkinter.filedialog.askopenfilename(
            filetypes=[("NIfTI files", "*.nii")]
        )
        if file_path:
            self.moving_image = nibabel.load(file_path)
            self.moving_data = self.moving_image.get_fdata()
            self.moving_shape = self.moving_data.shape
            self.select_file2.destroy()
            self.moving_layer_slider.configure(from_=0, to=self.moving_shape[self.dimension] - 1)
            self.moving_layer_slider.configure(state="normal")
            self.moving_layer_slider.set(self.moving_shape[self.dimension] // 2)
            self.register_lineal_button.configure(state="normal")
            self.moving_dimension_select.configure(state="normal")
            self.reset_register_button.configure(state="normal")
            self.update_image()
            self.show_moving_image()
        
    def show_moving_image(self, *args):
        if self.moving_canvas is None:
            self.grid_columnconfigure((0, 3), weight=0)
            self.grid_columnconfigure((1, 2), weight=1)

            self.moving_canvas = FigureCanvasTkAgg(matplotlib.pyplot.Figure(figsize=(5, 5)), master=self)
            self.moving_ax = self.moving_canvas.figure.add_subplot(111)
            self.moving_canvas.get_tk_widget().grid(row=0, column=2, rowspan=6, sticky="nsew")

        if self.moving_dimension_select.get() == "Dimensión 1":
            dimension = 0
        elif self.moving_dimension_select.get() == "Dimensión 2":
            dimension = 1
        else:
            dimension = 2
        
        layer = int(self.moving_layer_slider.get())
        self.moving_layer_label.configure(text=f"Layer: {layer}")

        if dimension == 0:
            slice_data = np.rot90(self.moving_data[layer, :, :])
        elif dimension == 1:
            slice_data = np.rot90(self.moving_data[:, layer, :])
        else:
            slice_data = np.rot90(self.moving_data[:, :, layer])

        self.moving_ax.clear()
        self.moving_ax.imshow(slice_data, cmap="gray")
        self.moving_ax.set_xlabel("X")
        self.moving_ax.set_ylabel("Y")
        self.moving_ax.title.set_text("Imagen móvil")
        self.moving_ax.axis("off")

        self.moving_canvas.draw()

    def apply_lineal_registration(self, *args):
        fixed_image = sitk.GetImageFromArray(self.data)
        moving_image = sitk.GetImageFromArray(self.moving_data)

        method = sitk.ImageRegistrationMethod()
        method.SetMetricAsMeanSquares()
        method.SetInterpolator(sitk.sitkLinear)
        method.SetOptimizerAsRegularStepGradientDescent(learningRate=0.1, minStep=1e-4, numberOfIterations=100)
        method.SetOptimizerScalesFromIndexShift()

        transformacion = sitk.AffineTransform(3)
        initial_transform = sitk.CenteredTransformInitializer(fixed_image, moving_image, transformacion)
        method.SetInitialTransform(initial_transform)
        final_transform = method.Execute(fixed_image, moving_image)

        registered_image = sitk.Resample(moving_image, fixed_image, final_transform, sitk.sitkLinear, 0.0, moving_image.GetPixelID())

        self.moving_data = sitk.GetArrayFromImage(registered_image)
        self.show_moving_image()

    def register(self):
        self.no_registro()

        def reset_register():
            self.moving_data = self.moving_image.get_fdata()
            self.show_moving_image()

        self.registro_frame = customtkinter.CTkFrame(
            self, width=140, corner_radius=0
        )
        self.registro_frame.grid(row=0, column=0, rowspan=6, sticky="nsew")

        self.registro_label = customtkinter.CTkLabel(
            self.registro_frame,
            text="Registro",
            font=customtkinter.CTkFont(size=20, weight="bold"),
        )
        self.registro_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        
        self.select_file2 = customtkinter.CTkButton(
            self.registro_frame, text="Seleccionar imagen móvil", command=self.select_moving_image
        )
        self.select_file2.grid(row=7, column=0, padx=20, pady=(10, 20))

        self.moving_dimensiones_label = customtkinter.CTkLabel(
            self.registro_frame,
            text="Dimensiones",
            font=customtkinter.CTkFont(size=20, weight="bold"),
        )
        self.moving_dimensiones_label.grid(row=8, column=0, padx=20, pady=(20, 10))

        self.moving_dimension_select = customtkinter.CTkOptionMenu(
            self.registro_frame,
            values=["Dimensión 1", "Dimensión 2", "Dimensión 3"],
            state="disabled",
            command=self.show_moving_image,
        )
        self.moving_dimension_select.grid(row=9, column=0, padx=20, pady=(20, 10))

        self.moving_layer_label = customtkinter.CTkLabel(
            self.registro_frame, text="Layer:", anchor="w"
        )
        self.moving_layer_label.grid(row=10, column=0, padx=20, pady=(10, 0))

        self.moving_layer_slider = customtkinter.CTkSlider(
            self.registro_frame,
            from_=0,
            to=100,
            state="disabled",
            command=self.show_moving_image,
        )
        self.moving_layer_slider.grid(row=11, column=0, padx=20, pady=10)

        self.register_lineal_button = customtkinter.CTkButton(
            self.registro_frame, text="Aplicar registro lineal", command=self.apply_lineal_registration, state="disabled"
        )
        self.register_lineal_button.grid(row=12, column=0, padx=20, pady=(10, 20))

        self.reset_register_button = customtkinter.CTkButton(
            self.registro_frame, text="Restaurar imagen", command=reset_register, state="disabled"
        )
        self.reset_register_button.grid(row=13, column=0, padx=20, pady=(10, 20))
        

        self.moving_canvas = None


def main():
    app = GUI()
    app.mainloop()


if __name__ == "__main__":
    main()
