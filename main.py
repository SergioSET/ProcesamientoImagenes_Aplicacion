import tkinter as tk
from tkinter import filedialog, colorchooser, messagebox
from PIL import Image, ImageDraw, ImageTk

class GUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Procesamiento de imágenes")

        self.canvas = tk.Canvas(self.root, width=600, height=400, bg="white")
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.canvas.bind("<B1-Motion>", self.draw)

        self.color = "red"
        self.brush_size = 5
        self.image = None
        self.image_visible = True
        self.drawings_visible = True
        self.drawing_objects = []

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

        help_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Ayuda", menu=help_menu)
        help_menu.add_command(label="Acerca de", command=self.show_about_dialog)

    def setup_toolbar(self):
        toolbar = tk.Frame(self.root)
        toolbar.pack(pady=5)

        color_label = tk.Label(toolbar, text="Color:")
        color_label.grid(row=0, column=0)

        self.color_button = tk.Button(toolbar, bg=self.color, width=10, command=self.choose_color)
        self.color_button.grid(row=0, column=1)

        brush_label = tk.Label(toolbar, text="Tamaño del pincel:")
        brush_label.grid(row=0, column=2)

        self.brush_slider = tk.Scale(toolbar, from_=1, to=20, orient=tk.HORIZONTAL, command=self.set_brush_size)
        self.brush_slider.set(self.brush_size)
        self.brush_slider.grid(row=0, column=3)

        toggle_drawings_button = tk.Button(toolbar, text="Toggle Dibujos", command=self.toggle_drawings)
        toggle_drawings_button.grid(row=0, column=4)

        toggle_image_button = tk.Button(toolbar, text="Toggle Imagen", command=self.toggle_image)
        toggle_image_button.grid(row=0, column=5)

    def draw(self, event):
        if self.drawings_visible:
            x1, y1 = (event.x - self.brush_size), (event.y - self.brush_size)
            x2, y2 = (event.x + self.brush_size), (event.y + self.brush_size)
            drawing_object = self.canvas.create_oval(x1, y1, x2, y2, fill=self.color, outline=self.color)
            self.drawing_objects.append(drawing_object)

    def choose_color(self):
        self.color = colorchooser.askcolor(initialcolor=self.color)[1]
        self.color_button.config(bg=self.color)

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

    def open_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Archivos de imagen", "*.png;*.jpg;*.jpeg")])
        if file_path:
            image = Image.open(file_path)
            self.image = ImageTk.PhotoImage(image)
            self.image_id = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.image)
            self.root.geometry(f"{self.image.width()}x{self.image.height()+60}")

    def show_about_dialog(self):
        about_text = "Procesamiento de imágenes\n\nVersión 1.0\nDesarrollado por Sergio Escudero Tabares"
        messagebox.showinfo("Acerca de", about_text)

root = tk.Tk()
app = GUI(root)
root.mainloop()
