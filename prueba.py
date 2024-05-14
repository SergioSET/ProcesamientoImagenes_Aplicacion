import tkinter as tk
from tkinter import filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from scipy.spatial.distance import pdist, squareform

class AplicacionDibujo:
    def __init__(self, ventana):
        self.ventana = ventana
        self.ventana.title("Dibujar sobre imagen")

        self.figura, self.ax = plt.subplots()
        self.canvas = FigureCanvasTkAgg(self.figura, master=self.ventana)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        self.ax.set_axis_off()

        self.image = None

        self.coordenadas = []

        self.figura.canvas.mpl_connect('button_press_event', self.dibujar)

        self.menu = tk.Menu(ventana)
        self.ventana.config(menu=self.menu)
        self.menu_archivo = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="Archivo", menu=self.menu_archivo)
        self.menu_archivo.add_command(label="Abrir imagen", command=self.abrir_imagen)
        self.menu_archivo.add_command(label="Coordenadas", command=self.mostrar_coordenadas)
        self.menu_archivo.add_command(label="Procesar", command=self.procesar)
        self.menu_archivo.add_separator()
        self.menu_archivo.add_command(label="Salir", command=ventana.quit)

    def mostrar_coordenadas(self):
        print(self.coordenadas)

    def abrir_imagen(self):
        ruta_imagen = filedialog.askopenfilename(title="Abrir imagen", filetypes=[("Archivos de imagen", "*.png;*.jpg;*.jpeg")])
        if ruta_imagen:
            self.imagen = plt.imread(ruta_imagen)
            self.ax.imshow(self.imagen)
            self.ax.set_axis_off()
            self.figura.canvas.draw()

    def dibujar(self, event):
        if event.inaxes == self.ax:
            x = int(round(event.xdata))
            y = int(round(event.ydata))
            if event.button == 1:  # Click izquierdo
                color = 'g'  # Verde
            elif event.button == 3:  # Click derecho
                color = 'r'  # Rojo
            else:
                return
            self.coordenadas.append((x, y, color))
            for coord in self.coordenadas:
                self.ax.plot(coord[0], coord[1], marker='o', markersize=5, color=coord[2])
            self.figura.canvas.draw()

    def procesar(self):
        if not self.coordenadas:
            return
        print("Procesando...")
        print(self.coordenadas)
        
        def laplacian_coordinates_weights(img, sigma=0.1, epsilon=10e-6):
            h, w = img.shape[:2]
            weights = np.zeros((h*w, h*w))

            for i in range(h):
                for j in range(w):
                    idx = i*w + j
                    if i > 0:
                        weights[idx, (i-1)*w+j] = np.exp(-((img[i,j] - img[i-1,j])**2).sum() / (sigma + epsilon))
                    if i < h-1:
                        weights[idx, (i+1)*w+j] = np.exp(-((img[i,j] - img[i+1,j])**2).sum() / (sigma + epsilon))
                    if j > 0:
                        weights[idx, i*w+j-1] = np.exp(-((img[i,j] - img[i,j-1])**2).sum() / (sigma + epsilon))
                    if j < w-1:
                        weights[idx, i*w+j+1] = np.exp(-((img[i,j] - img[i,j+1])**2).sum() / (sigma + epsilon))

            return weights

        # img = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])  # Ejemplo de una imagen
        img = np.array(self.imagen  * 255, dtype=np.uint8)

        weights = laplacian_coordinates_weights(img)
        print("Tamaño matrix de pesos: ", weights.shape)
        # plt.imshow(weights, cmap='gray')
        # plt.colorbar()
        # plt.show()

        

               





if __name__ == "__main__":
    ventana_principal = tk.Tk()
    aplicacion = AplicacionDibujo(ventana_principal)
    ventana_principal.mainloop()
