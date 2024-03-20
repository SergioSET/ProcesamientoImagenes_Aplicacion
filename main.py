import tkinter as tk
from tkinter import filedialog, messagebox, ttk, Toplevel
from tkinter.ttk import *
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import numpy as np
import nibabel as nib
import cv2
from sklearn.cluster import KMeans


class GUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Procesamiento de imágenes médicas")
        self.root.geometry("800x600")

        self.file_path = None

        self.slice_data = None
        self.data = None
        self.segmented_data = None

        self.dimension = 0
        self.layer = 0

        self.setup_menu()
        self.setup_toolbar()

    def setup_menu(self):
        menu_bar = tk.Menu(self.root)
        self.root.config(menu=menu_bar)

        file_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Archivo", menu=file_menu)
        file_menu.add_command(label="Abrir archivo .nii", command=self.open_file)
        file_menu.add_command(
            label="Cargar archivo .nii por defecto", command=self.load_default_file
        )
        file_menu.add_command(label="Salir", command=self.root.quit)

        segmentation_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Segmentación", menu=segmentation_menu)
        segmentation_menu.add_command(
            label="Umbralización manual", command=self.thresholding_image
        )
        # segmentation_menu.add_command(
        #     label="Umbralización Isodata", command=self.isodata_thresholding_image
        # )
        # segmentation_menu.add_command(
        #     label="Crecimiento de regiones",
        #     command=self.region_growing_image,
        # )
        # segmentation_menu.add_command(
        #     label="K-means", command=self.kmeans_thresholding_image
        # )

    def setup_toolbar(self):
        toolbar = tk.Frame(self.root)
        toolbar.pack(side="bottom")

        self.combobox = ttk.Combobox(
            toolbar,
            values=[f"Dimensión {i+1}" for i in range(1)],
            state="readonly",
        )
        self.combobox.grid(row=0, column=0)
        self.combobox.current(0)
        self.combobox.bind("<<ComboboxSelected>>", self.show_toolbar)
        self.combobox.grid_remove()

        self.layer_slider = tk.Scale(
            toolbar,
            from_=0,
            to=0,
            orient="horizontal",
            command=self.update_image,
        )
        self.layer_slider.grid(row=1, column=0)
        self.layer_slider.grid_remove()

        self.layer_entry = tk.Entry(toolbar)
        self.layer_entry.grid(row=0, column=1)
        self.layer_entry.grid_remove()

        self.apply_layer_button = tk.Button(
            toolbar, text="Aplicar", command=self.apply_layer_value
        )
        self.apply_layer_button.grid(row=1, column=1)
        self.apply_layer_button.grid_remove()

    def open_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("NIfTI files", "*.nii"), ("All files", "*")]
        )

        if file_path:
            self.file_path = file_path
            self.data = nib.load(self.file_path).get_fdata()
            self.show_toolbar()

    def load_default_file(self):
        self.file_path = "sub-01_T1w.nii"
        self.data = nib.load(self.file_path).get_fdata()
        self.show_toolbar()

    def show_toolbar(self):
        dimensions = len(self.data.shape)

        self.combobox["values"] = [f"Dimensión {i+1}" for i in range(dimensions)]
        self.combobox.grid()

        self.layer_slider["to"] = self.data.shape[self.combobox.current()] - 1
        self.layer_slider.set(0)
        self.layer_slider.grid()

        self.layer_entry.grid()

        self.apply_layer_button.grid()

        self.dimension = self.combobox.current()
        self.layer = int(self.layer_slider.get())

        self.update_image()

    def apply_layer_value(self):
        try:
            value = int(self.layer_entry.get())
            if 0 <= value <= self.layer_slider["to"]:
                self.layer_slider.set(value)
            else:
                self.layer_entry.delete(0, "end")
                self.layer_entry.insert(0, int(self.layer_slider["to"]))
        except ValueError:
            self.layer_entry.delete(0, "end")
            self.layer_entry.insert(0, self.layer_slider.get())
        self.update_image()

    def update_image(self, *args):
        self.dimension = self.combobox.current()
        self.layer = self.layer_slider.get()

        if self.dimension == 0:
            self.slice_data = np.rot90(self.data[self.layer, :, :])
        elif self.dimension == 1:
            self.slice_data = np.rot90(self.data[:, self.layer, :])
        else:
            self.slice_data = np.rot90(self.data[:, :, self.layer])

        if not hasattr(self, "fig"):
            self.fig = plt.figure(figsize=(6, 6))
            self.ax = self.fig.add_subplot(111)

        self.ax.clear()
        self.ax.imshow(self.slice_data, cmap="gray")
        self.ax.set_xlabel("X")
        self.ax.set_ylabel("Y")
        self.ax.axis("off")
        self.ax.set_title(
            "Dimensión {} en la capa {}".format(self.dimension + 1, self.layer)
        )

        if not hasattr(self, "canvas"):
            self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
            self.canvas_widget = self.canvas.get_tk_widget()
            self.canvas_widget.pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        else:
            self.canvas.draw()

    def thresholding_image(self):
        thresholding_canvas = Toplevel(self.root)
        thresholding_canvas.title("Umbralización manual")
        thresholding_toolbar = tk.Frame(thresholding_canvas)
        thresholding_toolbar.grid(row=0, column=0, columnspan=2)

        dimension = self.combobox.current()
        layer = self.layer_slider.get()
        thresholded = False

        fig, ax = plt.subplots()
        ax.imshow(self.slice_data, cmap="gray")
        ax.axis("off")
        ax.set_title("Umbralización manual")
        fig.tight_layout()

        thresholding_image = FigureCanvasTkAgg(fig, master=thresholding_canvas)
        thresholding_image.get_tk_widget().grid(row=1, column=0, columnspan=2)
        thresholding_image.draw()

        def update_image(*args):
            dimension = combobox.current()
            layer = layer_slider.get()

            if thresholded == True:
                data = self.segmented_data
            else:
                data = self.data

            if dimension == 0:
                slice_data = np.rot90(data[layer, :, :])
            elif dimension == 1:
                slice_data = np.rot90(data[:, layer, :])
            else:
                slice_data = np.rot90(data[:, :, layer])

            ax.clear()
            ax.imshow(slice_data, cmap="gray")
            ax.axis("off")
            ax.set_title("Umbralización manual")
            fig.tight_layout()
            thresholding_image.draw()

        combobox = ttk.Combobox(
            thresholding_toolbar,
            values=[f"Dimensión {i+1}" for i in range(len(self.data.shape))],
            state="readonly",
        )
        combobox.grid(row=0, column=0)
        combobox.current(self.combobox.current())
        combobox.bind("<<ComboboxSelected>>", update_image)

        layer_slider = tk.Scale(
            thresholding_toolbar,
            from_=0,
            to=self.data.shape[combobox.current()] - 1,
            orient="horizontal",
            command=update_image,
        )
        layer_slider.set(self.layer_slider.get())
        layer_slider.grid(row=1, column=0)

        layer_entry = tk.Entry(thresholding_toolbar)
        layer_entry.grid(row=0, column=1)

        def apply_layer_value():
            try:
                value = int(layer_entry.get())
                if 0 <= value <= layer_slider["to"]:
                    layer_slider.set(value)
                else:
                    layer_entry.delete(0, "end")
                    layer_entry.insert(0, int(layer_slider["to"]))
            except ValueError:
                layer_entry.delete(0, "end")
                layer_entry.insert(0, layer_slider.get())
            update_image()

        apply_layer_button = tk.Button(
            thresholding_toolbar, text="Aplicar", command=apply_layer_value
        )
        apply_layer_button.grid(row=1, column=1)

        tau_slider = tk.Scale(
            thresholding_canvas,
            from_=0,
            to=255,
            orient="horizontal",
        )
        tau_slider.grid(row=2, column=0)

        entry_tau = tk.Entry(thresholding_canvas)
        entry_tau.grid(row=2, column=1)

        button_threshold = tk.Button(
            thresholding_canvas,
            text="Umbralizar",
            command=lambda: threshold_image(fig, ax),
        )
        button_threshold.grid(row=3, column=1)

        button_save = tk.Button(
            thresholding_canvas,
            text="Guardar archivo nii",
            command=lambda: self.save_nii("Manual", fig),
        )
        button_save.grid(row=3, column=0)

        def threshold_image(fig, ax):
            nonlocal thresholded
            thresholded = True
            tau = tau_slider.get()
            self.segmented_data = np.where(self.data > tau, 255, 0)
            update_image()
            print("Thresholded")

    def isodata_thresholding_image(self):
        pass

    def region_growing_image(self):
        pass

    def kmeans_thresholding_image(self):
        pass

    def save_nii(self, method, fig):
        file_path = filedialog.asksaveasfilename(
            filetypes=[("NIfTI files", "*.nii"), ("All files", "*")]
        )

        if file_path:
            nib.save(nib.Nifti1Image(self.segmented_data, np.eye(4)), file_path)
            messagebox.showinfo(
                "Archivo guardado",
                f"El archivo ha sido guardado con el método de segmentación {method}",
            )


root = tk.Tk()
app = GUI(root)
root.mainloop()
