import tkinter as tk
from tkinter import filedialog, ttk
import nibabel as nib
from tkinter.ttk import *
import matplotlib.pyplot as plt
import tkinter as tk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import nibabel as nib
import tkinter as tk
from tkinter import Toplevel, filedialog, messagebox, ttk
from PIL import Image, ImageTk
import nibabel as nib
import numpy as np
from tkinter.ttk import *
from skimage import filters
import matplotlib.pyplot as pltd
import cv2


class GUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Procesamiento de imágenes")
        self.root.geometry("800x600")

        self.file_path = None
        self.file_shape = None

        self.color1 = "red"
        self.color2 = "green"
        self.current_color = self.color1
        self.brush_size = 3
        self.drawing_objects = []

        self.image = None
        self.nib_image = None
        self.data = None
        self.segmented_image = None

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
            label="Umbralización", command=self.segmented_image
        )
        segmentation_menu.add_command(
            label="Isodata", command=self.isodata_thresholding_image
        )
        segmentation_menu.add_command(
            label="Crecimiento de regiones",
            command=self.region_growing_image,
        )
        segmentation_menu.add_command(
            label="K-means", command=self.kmeans_thresholding_image
        )

        help_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Ayuda", menu=help_menu)
        help_menu.add_command(label="Acerca de", command=self.show_about)

    def setup_toolbar(self):
        toolbar = tk.Frame(self.root, bg="white")
        toolbar.pack(side="bottom")

        self.combobox = ttk.Combobox(
            toolbar,
            values=[f"Dimensión {i+1}" for i in range(1)],
            state="readonly",
        )
        self.combobox.grid(row=0, column=0)
        self.combobox.current(0)
        self.combobox.bind("<<ComboboxSelected>>", self.show_combobox_slider)
        self.combobox.grid_remove()

        self.layer_slider = tk.Scale(
            toolbar,
            from_=0,
            to=0,
            orient="horizontal",
            label="Capa",
            command=self.update_image,
        )
        self.layer_slider.grid(row=0, column=1)
        self.layer_slider.grid_remove()

        self.layer_entry = tk.Entry(toolbar)
        self.layer_entry.grid(row=0, column=2)
        self.layer_entry.grid_remove()

        self.apply_layer_button = tk.Button(
            toolbar, text="Aplicar", command=self.apply_layer_value
        )
        self.apply_layer_button.grid(row=0, column=3)
        self.apply_layer_button.grid_remove()

    def open_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("NIfTI files", "*.nii"), ("All files", "*")]
        )

        if file_path:
            self.file_path = file_path
            self.nib_image = nib.load(file_path)
            self.data = self.nib_image.get_fdata()
            self.file_shape = self.data.shape
            self.show_combobox_slider()

    def load_default_file(self):
        self.file_path = "sub-01_T1w.nii"
        self.nib_image = nib.load(self.file_path)
        self.data = self.nib_image.get_fdata()
        self.file_shape = self.data.shape
        self.show_combobox_slider()

    def change_color(self, color):
        self.current_color = color

    def change_brush_size(self, size):
        self.brush_size = int(size)

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

    def show_combobox_slider(self, *args):
        dimensions = len(self.data.shape)

        self.combobox["values"] = [f"Dimensión {i+1}" for i in range(dimensions)]
        self.combobox.grid()

        self.layer_slider["to"] = self.file_shape[self.combobox.current()] - 1
        self.layer_slider.set(0)
        self.layer_slider.grid()

        self.layer_entry.grid()

        self.apply_layer_button.grid()

        self.update_image()

    def update_image(self, *args):
        self.dimension = self.combobox.current()
        self.layer = self.layer_slider.get()

        if self.dimension == 0:
            slice_data = np.rot90(self.data[self.layer, :, :])
        elif self.dimension == 1:
            slice_data = np.rot90(self.data[:, self.layer, :])
        else:
            slice_data = np.rot90(self.data[:, :, self.layer])

        if not hasattr(self, "fig"):
            self.fig = plt.figure(figsize=(6, 6))
            self.ax = self.fig.add_subplot(111)

        self.ax.clear()
        self.ax.imshow(slice_data, cmap="gray")
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
        thresholding_canvas.title("Umbralización")

        if self.dimension == 0:
            slice_data = np.rot90(self.data[self.layer, :, :])
        elif self.dimension == 1:
            slice_data = np.rot90(self.data[:, self.layer, :])
        else:
            slice_data = np.rot90(self.data[:, :, self.layer])

        fig, ax = plt.subplots()
        ax.imshow(slice_data, cmap="gray")
        ax.axis("off")
        ax.set_title("Umbralización")
        fig.tight_layout()

        thresholding_image = FigureCanvasTkAgg(fig, master=thresholding_canvas)
        thresholding_image.draw()
        thresholding_image.get_tk_widget().grid(row=0, column=0)

        entry_tau = Entry(thresholding_canvas)
        entry_tau.grid(row=1, column=0)

        button_thresholding = Button(
            thresholding_canvas,
            text="Umbralizar",
            command=lambda: thresholding(),
        )
        button_thresholding.grid(row=2, column=0)

        button_save = Button(
            thresholding_canvas,
            text="Guardar imagen",
            command=lambda: self.save_image("Manual"),
        )
        button_save.grid(row=3, column=0)

        def thresholding():
            try:
                tau = float(entry_tau.get())
                segmented_image = slice_data > tau
                ax.imshow(segmented_image, cmap="gray")
                self.segmented_image = segmented_image
                thresholding_image.draw()
                ax.set_title("Umbralización con tau = {}".format(tau))
            except ValueError:
                messagebox.showerror("Error", "Por favor, ingrese un valor numérico")

    def isodata_thresholding_image(self):
        thresholding_canvas = Toplevel(self.root)
        thresholding_canvas.title("Isodata")

        if self.dimension == 0:
            slice_data = np.rot90(self.data[self.layer, :, :])
        elif self.dimension == 1:
            slice_data = np.rot90(self.data[:, self.layer, :])
        else:
            slice_data = np.rot90(self.data[:, :, self.layer])

        fig, ax = plt.subplots()
        ax.imshow(slice_data, cmap="gray")
        ax.axis("off")
        ax.set_title("Isodata")
        fig.tight_layout()

        def calcular_isodata(image):
            t = 0
            delta_tau = 1
            tau = np.mean(image)

            while True:
                segmented_image = image > tau

                m_foreground = np.mean(image[segmented_image])
                m_background = np.mean(image[~segmented_image])

                new_tau = 0.5 * (m_foreground + m_background)

                if abs(new_tau - tau) < delta_tau:
                    break

                tau = new_tau
                t += 1

            return tau

        tau = calcular_isodata(slice_data)

        thresholding_image = FigureCanvasTkAgg(fig, master=thresholding_canvas)
        thresholding_image.draw()
        thresholding_image.get_tk_widget().grid(row=0, column=0)

        segmented_image = slice_data > tau
        ax.imshow(segmented_image, cmap="gray")
        self.segmented_image = segmented_image
        thresholding_image.draw()
        ax.set_title("Umbralización con tau = {}".format(tau))

        button_save = Button(
            thresholding_canvas,
            text="Guardar imagen",
            command=lambda: self.save_image("Isodata"),
        )
        button_save.grid(row=2, column=0)

    def region_growing_image(self):
        region_growing_canvas = Toplevel(self.root)
        region_growing_canvas.title("Crecimiento de regiones")

        if self.dimension == 0:
            slice_data = np.rot90(self.data[self.layer, :, :])
        elif self.dimension == 1:
            slice_data = np.rot90(self.data[:, self.layer, :])
        else:
            slice_data = np.rot90(self.data[:, :, self.layer])

        fig, ax = plt.subplots()
        ax.imshow(slice_data, cmap="gray")
        ax.axis("off")
        ax.set_title("Crecimiento de regiones")
        fig.tight_layout()

        thresholding_image = FigureCanvasTkAgg(fig, master=region_growing_canvas)
        thresholding_image.draw()
        thresholding_image.get_tk_widget().grid(row=0, column=0)

        toolbar = tk.Frame(region_growing_canvas, bg="white")
        toolbar.grid(row=1, column=0)

        color_button1 = tk.Button(
            toolbar,
            text="Color 1",
            bg=self.color1,
            command=lambda: self.change_color(self.color1),
        )
        color_button1.grid(row=0, column=0)

        color_button2 = tk.Button(
            toolbar,
            text="Color 2",
            bg=self.color2,
            command=lambda: self.change_color(self.color2),
        )
        color_button2.grid(row=0, column=1)

        brush_size_slider = tk.Scale(
            toolbar,
            from_=1,
            to=10,
            orient="horizontal",
            label="Tamaño del pincel",
            command=self.change_brush_size,
        )
        brush_size_slider.set(self.brush_size)
        brush_size_slider.grid(row=0, column=2)

        def clean_drawing(ax):
            for patch in ax.patches:
                patch.remove()
                circles[self.color1] = None
                circles[self.color2] = None
            plt.draw()

        clean_button = tk.Button(
            toolbar, text="Limpiar", command=lambda: clean_drawing(ax)
        )
        clean_button.grid(row=0, column=3)

        button_region_growth = tk.Button(
            toolbar, text="Umbralizar", command=lambda: region_growth()
        )
        button_region_growth.grid(row=1, column=1)

        button_save = Button(
            toolbar,
            text="Guardar imagen",
            command=lambda: self.save_image("Region_growing"),
        )
        button_save.grid(row=1, column=2)

        circles = {
            self.color1: None,
            self.color2: None,
        }
        active_circle = None

        def on_click(event):
            nonlocal circles, active_circle
            x = int(event.xdata)
            y = int(event.ydata)
            color = self.current_color
            brush_size = self.brush_size

            if circles[color]:
                if circles[color] in ax.patches:
                    circles[color].remove()

            circle = plt.Circle((x, y), brush_size, color=color, fill=True)
            ax.add_patch(circle)
            circles[color] = circle
            active_circle = circle
            thresholding_image.draw()

        def on_drag(event):
            nonlocal circles, active_circle
            if event.inaxes:
                x = int(event.xdata)
                y = int(event.ydata)

                circle = active_circle

                if circle:
                    circle.center = x, y
                    thresholding_image.draw()

        def on_release(event):
            nonlocal active_circle
            active_circle = None

        fig.canvas.mpl_connect("button_press_event", on_click)
        fig.canvas.mpl_connect("motion_notify_event", on_drag)
        fig.canvas.mpl_connect("button_release_event", on_release)

        def region_growth():
            pass

    def kmeans_thresholding_image(self):
        pass

    def save_image(self, method):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            initialfile="Dimension_{}_Layer_{}_{}".format(
                self.dimension + 1, self.layer, method
            ),
            filetypes=[("PNG files", "*.png"), ("All files", "*")],
        )

        image = self.segmented_image

        if file_path:
            plt.imsave(file_path, image, cmap="gray")

    def show_about(self):
        messagebox.showinfo(
            "Acerca de",
            "Esta aplicación fue desarrollada por el grupo 1 de la materia de Procesamiento de Imágenes Médicas",
        )


root = tk.Tk()
app = GUI(root)
root.mainloop()
