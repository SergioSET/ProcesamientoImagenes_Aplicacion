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

        self.colors = [["red", "green", "blue", "yellow", "purple", "orange"], ["Rojo", "Verde", "Azul", "Amarillo", "Morado", "Naranja"]]
        self.current_color = self.colors[0][0]
        self.brush_size = 3
        self.drawn_objects_dict = {}
        
        self.setup_menu()

    def setup_menu(self):
        self.open_file_button = customtkinter.CTkButton(self, text="Abrir archivo .nii", command=self.open_file)
        self.open_file_button.grid(row=0, column=0, padx=20, pady=20)
        self.load_default_file_button = customtkinter.CTkButton(self, text="Cargar archivo .nii por defecto", command=self.load_default_file)
        self.load_default_file_button.grid(row=1, column=0, padx=20, pady=20)

    def open_file(self):
        file_path = customtkinter.filedialog.askopenfilename(filetypes=[("NIfTI files", "*.nii")])
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
        # self.sidebar_frame.grid_rowconfigure(8, weight=1)

        self.dimensiones_label = customtkinter.CTkLabel(self.sidebar_frame, text="Dimensiones", font=customtkinter.CTkFont(size=20, weight="bold"))
        self.dimensiones_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        self.dimension_select = customtkinter.CTkOptionMenu(self.sidebar_frame, values=["Dimensión 1", "Dimensión 2", "Dimensión 3"], command=self.update_dimension)
        self.dimension_select.grid(row=1, column=0, padx=20, pady=(20, 10))

        self.layer_label = customtkinter.CTkLabel(self.sidebar_frame, text="Layer:", anchor="w")
        self.layer_label.grid(row=2, column=0, padx=20, pady=(10, 0))
        self.layer_slider = customtkinter.CTkSlider(self.sidebar_frame, from_=0, to=100, state="disabled", command=self.update_layer)
        self.layer_slider.grid(row=3, column=0, padx=20, pady=10)

        self.umbralizacion_label = customtkinter.CTkLabel(self.sidebar_frame, text="Segmentación", font=customtkinter.CTkFont(size=20, weight="bold"))
        self.umbralizacion_label.grid(row=4, column=0, padx=20, pady=(20, 10))
        self.umbralizacion_select = customtkinter.CTkOptionMenu(self.sidebar_frame, state="disabled", values=["No seleccionado", "Umbralización", "Isodata", "Crecimiento de regiones", "K-means"], command=self.thresholding_menu)
        self.umbralizacion_select.grid(row=5, column=0, padx=20, pady=10)

        self.color_select = customtkinter.CTkOptionMenu(self.sidebar_frame, state="disabled", values=self.colors[1], command=self.update_color)
        self.color_select.grid(row=6, column=0, padx=20, pady=10)

        self.drawing_label = customtkinter.CTkLabel(self.sidebar_frame, text="Dibujar", font=customtkinter.CTkFont(size=20, weight="bold"))
        self.drawing_label.grid(row=7, column=0, padx=20, pady=(20, 10))

        self.brush_size_label = customtkinter.CTkLabel(self.sidebar_frame, text="Tamaño del pincel: 3", anchor="w")
        self.brush_size_label.grid(row=8, column=0, padx=20, pady=(10, 0))
        self.brush_size_slider = customtkinter.CTkSlider(self.sidebar_frame, from_=1, to=10, number_of_steps=9, state="disabled", command=self.update_brush_size)
        self.brush_size_slider.set(3)
        self.brush_size_slider.grid(row=9, column=0, padx=20, pady=10)
        self.clear_draws_button = customtkinter.CTkButton(self.sidebar_frame, text="Limpiar dibujos", command=self.clear_draws)
        self.clear_draws_button.grid(row=10, column=0, padx=20, pady=(10, 20))

        self.restore_file_button = customtkinter.CTkButton(self.sidebar_frame, text="Restaurar archivo", command=self.restore_file)
        self.restore_file_button.grid(row=11, column=0, padx=20, pady=(10, 20))

        self.save_file_button = customtkinter.CTkButton(self.sidebar_frame, text="Guardar archivo", command=self.save_file)
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
        self.layer = int(self.file_shape[self.dimension]//2)
        self.layer_slider.configure(number_of_steps=self.file_shape[self.dimension]-1)
        self.layer_slider.configure(from_=0, to=self.file_shape[self.dimension]-1)
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

        if not hasattr(self, 'fig'):
            self.fig = matplotlib.pyplot.Figure(figsize=(5, 5))
            self.ax = self.fig.add_subplot(111)
            self.canvas = FigureCanvasTkAgg(self.fig, master=self)
            self.canvas.get_tk_widget().grid(row=0, column=1, rowspan=6, sticky="nsew")

        self.ax.clear()

        if self.dimension in self.drawn_objects_dict and self.layer in self.drawn_objects_dict[self.dimension]:
            for drawn_object in self.drawn_objects_dict[self.dimension][self.layer]:
                self.ax.add_patch(drawn_object)

        self.ax.imshow(slice_data, cmap="gray")
        self.ax.set_xlabel("X")
        self.ax.set_ylabel("Y")
        self.ax.axis("off")

        self.fig.canvas.mpl_connect('button_press_event', self.on_click)
        self.fig.canvas.mpl_connect('motion_notify_event', self.on_drag)
        self.canvas.draw()

    def update_color(self, *args):
        self.current_color = self.colors[0][self.colors[1].index(self.color_select.get())]

    def update_brush_size(self, *args):
        self.brush_size = int(self.brush_size_slider.get())
        self.brush_size_label.configure(text=f"Tamaño del pincel: {self.brush_size}")

    def on_click(self, event):
        if event.inaxes == self.ax:
            x, y = int(event.xdata), int(event.ydata)
            circle = matplotlib.patches.Circle((x, y), radius=self.brush_size, color=self.current_color)
            
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
            circle = matplotlib.patches.Circle((x, y), radius=self.brush_size, color=self.current_color)
            
            if self.dimension not in self.drawn_objects_dict:
                self.drawn_objects_dict[self.dimension] = {}
            
            if self.layer not in self.drawn_objects_dict[self.dimension]:
                self.drawn_objects_dict[self.dimension][self.layer] = []
            
            self.drawn_objects_dict[self.dimension][self.layer].append(circle)
            
            self.ax.add_patch(circle)
            self.canvas.draw()

            # if self.dimension == 0:
            #     modified_layer = numpy.array(self.ax.figure.canvas.renderer.buffer_rgba())
                
            #     modified_image_gray = modified_layer[:, :]
            #     pil_image = Image.fromarray(modified_image_gray)


            #     resized_image = pil_image.resize((192, 192))
            #     self.modified_data[self.layer, :, :] = resized_image
            # elif self.dimension == 1:
            #     self.modified_data[:, self.layer, :]
            # else:
            #     self.modified_data[:, :, self.layer]

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
        nibabel.save(modified_img, 'modified_image.nii')

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

    def no_threshold(self):
        if hasattr(self, 'threshold_frame'):
            self.threshold_frame.destroy()

    def umbralizacion(self):
        def umbralizar(*args):
            self.tau_label.configure(text=f"Tau: {int(self.tau_slider.get())}")
            tau = int(self.tau_slider.get())
            self.modified_data = self.data.copy()
            self.modified_data = (self.modified_data > tau).astype(int) * 255
            self.update_image()

        def umbralizar2(*args):
            self.tau_label.configure(text=f"Tau: {int(self.tau_input.get())}")
            tau = int(self.tau_input.get())
            self.modified_data = self.data.copy()
            self.modified_data = (self.modified_data > tau).astype(int) * 255
            self.update_image()

        self.no_threshold()
        self.threshold_frame = customtkinter.CTkFrame(self, width=140, corner_radius=0)
        self.threshold_frame.grid(row=0, column=0, rowspan=6, sticky="nsew")
        # self.threshold_frame.grid_rowconfigure(8, weight=1)

        self.titulo_label = customtkinter.CTkLabel(self.threshold_frame, text="Umbralización", font=customtkinter.CTkFont(size=20, weight="bold"))
        self.titulo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.tau_label = customtkinter.CTkLabel(self.threshold_frame, text="Tau: 50", anchor="w")
        self.tau_label.grid(row=1, column=0, padx=20, pady=(10, 0))
        self.tau_slider = customtkinter.CTkSlider(self.threshold_frame, from_=1, to=300, number_of_steps=299, command=umbralizar)
        self.tau_slider.set(50)
        self.tau_slider.grid(row=2, column=0, padx=20, pady=10)
        self.tau_input = customtkinter.CTkEntry(self.threshold_frame)
        self.tau_input.grid(row=3, column=0, padx=20, pady=(0, 10))

        self.umbralizar_button = customtkinter.CTkButton(self.threshold_frame, text="Umbralizar", command=umbralizar2)
        self.umbralizar_button.grid(row=4, column=0, padx=20, pady=(10, 20))
    
    def isodata(self):
        def isodata(*args):

            t = 0
            delta_tau = 1
            tau = numpy.mean(self.data)
            while delta_tau > 0.1:
                g1 = self.data[self.data > tau]
                g2 = self.data[self.data <= tau]
                new_tau = (numpy.mean(g1) + numpy.mean(g2)) / 2
                delta_tau = abs(tau - new_tau)
                tau = new_tau

            self.tau_label.configure(text=f"Tau: {int(tau)}")
            self.modified_data = self.data.copy()
            self.modified_data = (self.modified_data > tau).astype(int) * 255
            self.update_image()

        self.no_threshold()
        self.threshold_frame = customtkinter.CTkFrame(self, width=140, corner_radius=0)
        self.threshold_frame.grid(row=0, column=0, rowspan=6, sticky="nsew")
        # self.sidebar_frame.grid_rowconfigure(8, weight=1)

        self.titulo_label = customtkinter.CTkLabel(self.threshold_frame, text="Isodata", font=customtkinter.CTkFont(size=20, weight="bold"))
        self.titulo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.tau_label = customtkinter.CTkLabel(self.threshold_frame, text="Tau: 50", anchor="w")
        self.tau_label.grid(row=1, column=0, padx=20, pady=(10, 0))

        self.isodata_button = customtkinter.CTkButton(self.threshold_frame, text="Isodata", command=isodata)
        self.isodata_button.grid(row=2, column=0, padx=20, pady=(10, 20))

    def is_similar(self, pixel_value, region_color, threshold=50):
        # Check similarity based on color distance threshold
        return numpy.linalg.norm(pixel_value - region_color) <= threshold

    def crecimiento_regiones(self):
        def crecimiento_regiones(*args):
            print("Crecimiento de regiones")
            if not hasattr(self, 'drawn_objects_dict'):
                tkinter.messagebox.showerror("Error", "No hay dibujos en la imagen.")
                return
            
            # Step 1: Collect seed points from drawn objects
            seeds = []
            for layer in self.drawn_objects_dict[self.dimension]:
                for drawn_object in self.drawn_objects_dict[self.dimension][layer]:
                    if isinstance(drawn_object, matplotlib.patches.Circle):
                        x, y = drawn_object.center
                        color = drawn_object.get_facecolor()
                        seeds.append((x, y, layer, color))

            # Step 2: Apply region growing algorithm
            for seed in seeds:
                x, y, z, color = seed
                region_color = (color[0], color[1], color[2])  # Extract RGB color from matplotlib color format
                region_mask = numpy.zeros_like(self.modified_data, dtype=bool)  # Initialize a mask for the region
                region_masked = numpy.zeros_like(self.modified_data)  # Initialize an array to store region pixels

                # Perform region growing using a queue
                q = Queue()
                q.put((x, y, z))  # Start from seed point

                while not q.empty():
                    cx, cy, cz = q.get()
                    if region_mask[cx, cy, cz]:
                        continue  # Skip if pixel already visited
                    region_mask[cx, cy, cz] = True  # Mark pixel as visited

                    # Check if pixel belongs to region based on similarity condition (e.g., color similarity)
                    if self.is_similar(self.modified_data[cx, cy, cz], region_color):
                        region_masked[cx, cy, cz] = self.modified_data[cx, cy, cz]  # Assign pixel value to region
                        # Add neighboring pixels to the queue for further exploration
                        for dx in range(-1, 2):
                            for dy in range(-1, 2):
                                for dz in range(-1, 2):
                                    if 0 <= cx + dx < self.file_shape[0] and 0 <= cy + dy < self.file_shape[1] and 0 <= cz + dz < self.file_shape[2]:
                                        q.put((cx + dx, cy + dy, cz + dz))

                # Update modified data with region pixels
                self.modified_data[region_mask] = region_masked[region_mask]

            self.update_image()

        self.no_threshold()
        self.threshold_frame = customtkinter.CTkFrame(self, width=140, corner_radius=0)
        self.threshold_frame.grid(row=0, column=0, rowspan=6, sticky="nsew")

        self.titulo_label = customtkinter.CTkLabel(self.threshold_frame, text="Crecimiento de regiones", font=customtkinter.CTkFont(size=20, weight="bold"))
        self.titulo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.crecimiento_regiones_button = customtkinter.CTkButton(self.threshold_frame, text="Crecimiento de regiones", command=crecimiento_regiones)
        self.crecimiento_regiones_button.grid(row=1, column=0, padx=20, pady=(10, 20))

    def kmeans(self):
        def kmeans(*args):
            self.modified_data = self.data.copy()
            self.modified_data = self.modified_data.reshape(-1, 1)
            self.modified_data = self.modified_data / 255

            # Perform K-means clustering
            from sklearn.cluster import KMeans
            kmeans = KMeans(n_clusters=int(self.cluster_input.get()), random_state=0).fit(self.modified_data)
            cluster_centers = kmeans.cluster_centers_
            cluster_labels = kmeans.labels_
            self.modified_data = cluster_centers[cluster_labels].reshape(self.file_shape)

            self.update_image()

        def update_label(*args):
            self.cluster_label.configure(text=f"Número de clusters: {int(self.cluster_input.get())}")

        self.no_threshold()
        self.threshold_frame = customtkinter.CTkFrame(self, width=140, corner_radius=0)
        self.threshold_frame.grid(row=0, column=0, rowspan=6, sticky="nsew")

        self.titulo_label = customtkinter.CTkLabel(self.threshold_frame, text="K-means", font=customtkinter.CTkFont(size=20, weight="bold"))
        self.titulo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.cluster_label = customtkinter.CTkLabel(self.threshold_frame, text="Número de clusters: 2", anchor="w")
        self.cluster_label.grid(row=1, column=0, padx=20, pady=(10, 0))

        self.cluster_input = customtkinter.CTkSlider(self.threshold_frame, from_=2, to=10, number_of_steps=8, command=update_label)
        self.cluster_input.set(2)
        self.cluster_input.grid(row=2, column=0, padx=20, pady=(10, 0))

        self.kmeans_button = customtkinter.CTkButton(self.threshold_frame, text="K-means", command=kmeans)
        self.kmeans_button.grid(row=3, column=0, padx=20, pady=(10, 20))

def main():
    app = GUI()
    app.mainloop()

if __name__ == "__main__":
    main()
