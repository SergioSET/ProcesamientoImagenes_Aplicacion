import tkinter as tk
from tkinter import filedialog, colorchooser, messagebox, ttk
from PIL import Image, ImageDraw, ImageTk
import nibabel as nib
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt


class GUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Procesamiento de imágenes")

        self.canvas = tk.Canvas(self.root, width=600, height=400, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.canvas.bind("<B1-Motion>", self.draw)

        self.file_path = None
        self.shape = None

        self.color1 = "red"
        self.color2 = "green"
        self.current_color = self.color1
        self.brush_size = 5
        self.image = None
        self.image_visible = True
        self.drawings_visible = True
        self.drawing_objects = []
        self.image_id = None
        self.nib_img = None
        self.data = None

        self.setup_menu()
        self.setup_toolbar()

    def setup_menu(self):
        menu_bar = tk.Menu(self.root)
        self.root.config(menu=menu_bar)

        file_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Archivo", menu=file_menu)
        file_menu.add_command(label="Cargar imagen", command=self.open_image)

        edit_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Editar", menu=edit_menu)
        edit_menu.add_command(label="Limpiar dibujos", command=self.clear_draws_canvas)
        edit_menu.add_command(label="Limpiar canvas", command=self.clear_canvas)
        edit_menu.add_command(label="Toggle Dibujos", command=self.toggle_drawings)
        edit_menu.add_command(label="Toggle Imagen", command=self.toggle_image)

        algorithms_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Segmentación", menu=algorithms_menu)
        algorithms_menu.add_command(
            label="Umbralización", command=self.umbralizacion_image
        )
        algorithms_menu.add_command(label="Isodata", command=self.isodata_image)
        algorithms_menu.add_command(
            label="Crecimiento de regiones", command=self.crecimiento_image
        )
        algorithms_menu.add_command(label="K-means", command=self.kmeans_image)

        help_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Ayuda", menu=help_menu)
        help_menu.add_command(label="Acerca de", command=self.show_about_dialog)

    def setup_toolbar(self):
        toolbar = tk.Frame(self.root)
        toolbar.pack(pady=5)

        color_label = tk.Label(toolbar, text="Color:")
        color_label.grid(row=0, column=0)

        self.color_button1 = tk.Button(
            toolbar,
            bg=self.color1,
            width=5,
            command=lambda: self.change_color(self.color1),
        )
        self.color_button1.grid(row=0, column=1)

        self.color_button2 = tk.Button(
            toolbar,
            bg=self.color2,
            width=5,
            command=lambda: self.change_color(self.color2),
        )
        self.color_button2.grid(row=0, column=2)

        brush_label = tk.Label(toolbar, text="Tamaño del pincel:")
        brush_label.grid(row=0, column=3)

        self.brush_slider = tk.Scale(
            toolbar, from_=1, to=20, orient=tk.HORIZONTAL, command=self.set_brush_size
        )
        self.brush_slider.set(self.brush_size)
        self.brush_slider.grid(row=0, column=4)

        toggle_drawings_button = tk.Button(
            toolbar, text="Toggle Dibujos", command=self.toggle_drawings
        )
        toggle_drawings_button.grid(row=0, column=5)

        toggle_image_button = tk.Button(
            toolbar, text="Toggle Imagen", command=self.toggle_image
        )
        toggle_image_button.grid(row=0, column=6)

        self.combobox = ttk.Combobox(
            toolbar,
            values=[f"Dimensión {i+1}" for i in range(0)],
            state="readonly",
        )
        self.combobox.grid(row=1, column=2)
        self.combobox.bind("<<ComboboxSelected>>", self.show_slider)
        self.combobox.grid_remove()

        self.layer_slider = tk.Scale(
            toolbar, from_=0, to=100, orient=tk.HORIZONTAL, command=self.update_image
        )
        self.layer_slider.grid(row=1, column=4)
        self.layer_slider.grid_remove()

    def draw(self, event):
        if self.drawings_visible:
            x1, y1 = (event.x - self.brush_size), (event.y - self.brush_size)
            x2, y2 = (event.x + self.brush_size), (event.y + self.brush_size)
            drawing_object = self.canvas.create_oval(
                x1, y1, x2, y2, fill=self.current_color, outline=self.current_color
            )
            self.drawing_objects.append(drawing_object)

    def change_color(self, color):
        self.current_color = color

    def set_brush_size(self, val):
        self.brush_size = int(val)

    def clear_canvas(self):
        self.canvas.delete("all")
        self.root.geometry("600x400")
        self.drawing_objects = []

    def clear_draws_canvas(self):
        for drawing_object in self.drawing_objects:
            self.canvas.delete(drawing_object)
        self.drawing_objects = []

    def toggle_image(self):
        if self.image is not None:
            if self.image_visible:
                self.canvas.itemconfig(self.image_id, state="hidden")
            else:
                self.canvas.itemconfig(self.image_id, state="normal")
            self.image_visible = not self.image_visible

    def toggle_drawings(self):
        if self.drawings_visible:
            for drawing_object in self.drawing_objects:
                self.canvas.itemconfig(drawing_object, state="hidden")
        else:
            for drawing_object in self.drawing_objects:
                self.canvas.itemconfig(drawing_object, state="normal")
        self.drawings_visible = not self.drawings_visible

    def show_combobox(self):
        if self.file_path:
            self.nib_img = nib.load(self.file_path)
            self.data = self.nib_img.get_fdata()
            dimensions = len(self.data.shape)
        else:
            dimensions = 0

        self.combobox["values"] = [f"Dimensión {i+1}" for i in range(dimensions)]
        self.combobox.grid()

    def open_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Archivo NIIfTI", "*.nii;")])

        if file_path:
            self.file_path = file_path
            self.shape = nib.load(self.file_path).shape
            self.show_combobox()

    def update_image(self, event=None):
        try:
            if self.nib_img is not None:
                value = self.layer_slider.get()

                selected_dimension_index = self.combobox.current()

                if selected_dimension_index == 0:
                    data_slice = np.rot90(self.data[value, :, :])
                elif selected_dimension_index == 1:
                    data_slice = np.rot90(self.data[:, value, :])
                elif selected_dimension_index == 2:
                    data_slice = np.rot90(self.data[:, :, value])

                image = Image.fromarray(data_slice)

                image = image.resize((image.width * 2, image.height * 2))

            self.image = ImageTk.PhotoImage(image)

            if self.image_id is not None:
                self.canvas.delete(self.image_id)
            self.image_id = self.canvas.create_image(
                0, 0, anchor=tk.NW, image=self.image
            )

        except Exception as e:
            messagebox.showerror("Error", f"Error al cargar el archivo NIfTI: {str(e)}")

    def show_slider(self, event=None):
        value = self.shape[self.combobox.current()]

        self.layer_slider["to"] = value - 1
        self.layer_slider.set(0)
        self.layer_slider.grid()

    def umbralizacion_image(self):
        print("Umbralización")

    def isodata_image(self):
        print("Isodata")

    def crecimiento_image(self):
        print("Crecimiento")

    def kmeans_image(self):
        print("K-means")

    def show_about_dialog(self):
        about_text = "Procesamiento de imágenes\n\nVersión 1.0\nDesarrollado por Sergio Escudero Tabares"
        messagebox.showinfo("Acerca de", about_text)


root = tk.Tk()
app = GUI(root)
root.mainloop()
