import numpy as np
import tkinter.messagebox
import customtkinter
import nibabel
import matplotlib.pyplot
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import scipy.sparse as sp
from scipy.sparse.linalg import factorized
from PIL import Image

customtkinter.set_appearance_mode("Dark")
customtkinter.set_default_color_theme("green")


class GUI(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("Laplacian Coordinates")
        self.geometry(f"{500}x{200}")
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure((2, 3), weight=0)
        self.grid_rowconfigure((0, 1), weight=1)

        self.coordenadas = []

        self.file_path = None
        self.file_shape = None

        self.imagen = None
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
        self.sidebar_frame = customtkinter.CTkScrollableFrame(
            self, width=230, corner_radius=0
        )
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
            text="Laplacian Coordinates",
            font=customtkinter.CTkFont(size=20, weight="bold"),
        )
        self.procesamiento_label.grid(row=4, column=0, padx=20, pady=(20, 10))

        self.establecer_button = customtkinter.CTkButton(
            self.sidebar_frame, text="Establecer imagen", command=self.establecer
        )
        self.establecer_button.grid(row=5, column=0, padx=20, pady=(20, 10))

        self.procesar_button = customtkinter.CTkButton(
            self.sidebar_frame, text="Procesar", command=self.procesar
        )

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
            self.sidebar_frame, text="Limpiar dibujos", command=self.limpiar_dibujo
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

        self.ax.imshow(slice_data, cmap="gray")
        self.ax.set_xlabel("X")
        self.ax.set_ylabel("Y")
        self.ax.axis("off")

        if self.moving_image:
            self.ax.title.set_text("Fixed")

        self.fig.canvas.mpl_connect("button_press_event", self.on_click)
        self.fig.canvas.mpl_connect("motion_notify_event", self.on_drag)
        self.fig.canvas.mpl_connect("button_release_event", self.on_release)
        self.canvas.draw()

    def update_brush_size(self, *args):
        self.brush_size = int(self.brush_size_slider.get())
        self.brush_size_label.configure(text=f"Tamaño del pincel: {self.brush_size}")

    def dibujar(self, event):
        if event.inaxes == self.ax:
            x = int(round(event.xdata))
            y = int(round(event.ydata))
            if event.button == 1:  # Click izquierdo
                color = "g"  # Verde
            elif event.button == 3:  # Click derecho
                color = "r"  # Rojo
            else:
                return
            self.coordenadas.append((x, y, color))
            for coord in self.coordenadas:
                self.ax.plot(
                    coord[0], coord[1], marker="o", markersize=5, color=coord[2]
                )
            self.fig.canvas.draw()

    def on_click(self, event):
        if event.inaxes == self.ax:
            x = int(round(event.xdata))
            y = int(round(event.ydata))
            color = "g" if event.button == 1 else "r"
            self.coordenadas.append((y, x, color))
            self.ax.plot(x, y, marker="o", markersize=5, color=color)
            self.fig.canvas.draw()

    def on_drag(self, event):
        if event.inaxes == self.ax and event.button == 1:
            x = int(round(event.xdata))
            y = int(round(event.ydata))
            color = "g" if event.button == 1 else "r"
            self.coordenadas.append((y, x, color))
            self.ax.plot(x, y, marker="o", markersize=5, color=color)
            self.fig.canvas.draw()

    def on_release(self, event):
        if event.inaxes == self.ax:
            self.fig.canvas.draw()

    def limpiar_dibujo(self):
        self.coordenadas = []

        for line in self.ax.lines:
            line.remove()

        self.fig.canvas.draw()

    def restore_file(self):
        self.modified_data = self.data

        self.update_image()

    def save_file(self):
        modified_img = nibabel.Nifti1Image(self.modified_data, self.nib_image.affine)
        nibabel.save(modified_img, "modified_image.nii")

    def establecer(self):
        self.procesar_button.grid(row=6, column=0, padx=20, pady=(10, 20))
        self.layer_slider.configure(state="disabled")
        self.dimension_select.configure(state="disabled")
        self.establecer_button.destroy()

        if self.image is not None:
            matplotlib.pyplot.imsave("current_image.png", self.image, cmap="gray")

        ruta_imagen = "current_image.png"
        self.imagen = Image.open(ruta_imagen).convert("L")
        self.imagen = np.array(self.imagen)

        self.ax.imshow(self.imagen)
        self.ax.set_axis_off()
        self.fig.canvas.draw()

    def procesar(self):
        if not self.coordenadas:
            return
        print("Procesando...")
        # print(self.coordenadas)

        h, w = self.imagen.shape

        def laplacian_coordinates_weights(img, epsilon=10e-6):
            weights = sp.lil_matrix((h * w, h * w))

            sigma = np.max(np.abs(np.diff(self.imagen.flatten())))
            print("Sigma: ", sigma)

            for i in range(h):
                for j in range(w):
                    idx = i * w + j
                    if i > 0:
                        weights[idx, (i - 1) * w + j] = np.exp(
                            -epsilon * ((img[i, j] - img[i - 1, j]) ** 2).sum() / sigma
                        )
                    if i < h - 1:
                        weights[idx, (i + 1) * w + j] = np.exp(
                            -epsilon * ((img[i, j] - img[i + 1, j]) ** 2).sum() / sigma
                        )
                    if j > 0:
                        weights[idx, i * w + j - 1] = np.exp(
                            -epsilon * ((img[i, j] - img[i, j - 1]) ** 2).sum() / sigma
                        )
                    if j < w - 1:
                        weights[idx, i * w + j + 1] = np.exp(
                            -epsilon * ((img[i, j] - img[i, j + 1]) ** 2).sum() / sigma
                        )

            return weights

        weights = laplacian_coordinates_weights(self.imagen)
        print("Tamaño matrix de pesos: ", weights.shape)

        # plt.imshow(weights, cmap='gray')
        # plt.colorbar()
        # plt.show()

        def laplacian_coordinates_matrix(weights):
            D = sp.diags(weights.sum(axis=1).A.ravel())
            return D - weights

        L = laplacian_coordinates_matrix(weights)
        print("Tamaño matrix de Laplacian: ", L.shape)

        xB = 0
        xF = 0

        for i, j, color in self.coordenadas:
            if color == "g":
                xB += self.imagen[i, j]
            else:
                xF += self.imagen[i, j]

        # xB = xB / len([c for c in self.coordenadas if c[2] == 'g'])
        # xF = xF / len([c for c in self.coordenadas if c[2] == 'r'])

        xB = -1
        xF = 1

        print("xB: ", xB)
        print("xF: ", xF)

        Is = sp.lil_matrix((h * w, h * w))
        L_2 = L.dot(L)
        b = np.zeros(h * w)

        indices = np.array([[i * w + j for j in range(w)] for i in range(h)])
        for i, j, color in self.coordenadas:
            index = indices[i, j]
            Is[index, index] = 1
            b[index] = xB if color == "g" else xF
            # print(i, j, color)

        print("Tamaño matrix de Is: ", Is.shape)

        A = sp.csr_matrix(Is + L_2)
        solve = factorized(A)
        x = solve(b)

        segmented_image = x.reshape((h, w))

        tau = (xB + xF) / 2

        segmented_image = np.where(segmented_image < tau, self.imagen, 0)

        self.ax.imshow(segmented_image)
        self.limpiar_dibujo()
        self.fig.canvas.draw()


def main():
    app = GUI()
    app.mainloop()


if __name__ == "__main__":
    main()
