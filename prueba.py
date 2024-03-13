import tkinter as tk
from tkinter import filedialog, messagebox
import nibabel as nib
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

class NiiFileSelector:
    def __init__(self, master):
        self.master = master
        self.master.title("Selector de Archivo NIfTI")
        self.file_path = None

        # Etiqueta para mostrar la ruta del archivo seleccionado
        self.label = tk.Label(master, text="Archivo seleccionado:")
        self.label.pack(pady=10)

        # Botón para abrir el cuadro de diálogo de selección de archivo
        self.select_button = tk.Button(master, text="Seleccionar Archivo", command=self.select_file)
        self.select_button.pack(pady=10)

        # Frame para contener los sliders
        self.slider_frame = tk.Frame(master)
        self.slider_frame.pack(pady=10)

        # Botón para mostrar la información del archivo NIfTI seleccionado
        self.info_button = tk.Button(master, text="Mostrar Información", command=self.show_info, state=tk.DISABLED)
        self.info_button.pack(pady=10)

    def select_file(self):
        file_path = filedialog.askopenfilename()

        if file_path:
            self.file_path = file_path
            self.label.config(text=f"Archivo seleccionado: {self.file_path}")
            self.info_button.config(state=tk.NORMAL)
            self.show_sliders()

    def show_info(self):
        if self.file_path:
            try:
                nii_img = nib.load(self.file_path)
                data_shape = nii_img.shape

                info_str = f"Información del Archivo NIfTI:\n\n"
                info_str += f"Dimensiones de datos: {len(data_shape)}\n"
                info_str += f"Forma de datos: {data_shape}\n"

                messagebox.showinfo("Información del Archivo", info_str)
            except Exception as e:
                messagebox.showerror("Error", f"Error al cargar el archivo NIfTI: {str(e)}")

    def show_sliders(self):
        nii_img = nib.load(self.file_path)
        data = nii_img.get_fdata()
        num_dims = len(data.shape)

        # Eliminar sliders anteriores si existen
        for widget in self.slider_frame.winfo_children():
            widget.destroy()

        self.slider_vars = []

        for dim in range(num_dims):
            dim_length = data.shape[dim]

            label = tk.Label(self.slider_frame, text=f"Dimensión {dim+1}")
            label.grid(row=dim, column=0, padx=5, pady=5)

            slider_var = tk.IntVar()
            slider_var.set(0)
            self.slider_vars.append(slider_var)

            slider = tk.Scale(self.slider_frame, from_=0, to=dim_length-1, orient=tk.HORIZONTAL, variable=slider_var, command=self.update_image)
            slider.grid(row=dim, column=1, padx=5, pady=5)

        self.update_image()

    def update_image(self, *args):
        if self.file_path:
            try:
                nii_img = nib.load(self.file_path)
                data = nii_img.get_fdata()

                indices = [slider_var.get() for slider_var in self.slider_vars]

                if len(indices) == 3:
                    img_slice = data[indices[0], :, :]
                elif len(indices) == 4:
                    img_slice = data[indices[0], indices[1], :, :]
                else:
                    img_slice = data

                plt.imshow(img_slice, cmap='gray')
                plt.axis('off')
                plt.tight_layout()

                if hasattr(self, 'canvas'):
                    self.canvas.get_tk_widget().destroy()

                self.canvas = FigureCanvasTkAgg(plt.gcf(), master=self.master)
                self.canvas.draw()
                self.canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
            except Exception as e:
                messagebox.showerror("Error", f"Error al actualizar la imagen: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = NiiFileSelector(root)
    root.mainloop()
