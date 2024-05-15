import tkinter as tk
from tkinter import filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from scipy.spatial.distance import pdist, squareform
import scipy
import scipy.sparse as sp
from scipy.sparse.linalg import spsolve, factorized

class AplicacionDibujo:
    def __init__(self, ventana):
        self.ventana = ventana
        self.ventana.title("Dibujar sobre imagen")

        self.figura, self.ax = plt.subplots()
        self.canvas = FigureCanvasTkAgg(self.figura, master=self.ventana)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        self.ax.set_axis_off()

        self.imagen = None

        self.coordenadas = []

        self.figura.canvas.mpl_connect('button_press_event', self.dibujar)

        self.menu = tk.Menu(ventana)
        self.ventana.config(menu=self.menu)
        self.menu_archivo = tk.Menu(self.menu, tearoff=0)
        self.menu.add_cascade(label="Archivo", menu=self.menu_archivo)
        self.menu_archivo.add_command(label="Abrir imagen", command=self.abrir_imagen)
        self.menu_archivo.add_command(label="Coordenadas", command=self.mostrar_coordenadas)
        self.menu_archivo.add_command(label="Procesar", command=self.procesar)
        self.menu_archivo.add_command(label="Limpiar dibujo", command=self.limpiar_dibujo)
        self.menu_archivo.add_separator()
        self.menu_archivo.add_command(label="Salir", command=ventana.quit)

    def mostrar_coordenadas(self):
        print(self.coordenadas)

    def abrir_imagen(self):
        # ruta_imagen = filedialog.askopenfilename(title="Abrir imagen", filetypes=[("Archivos de imagen", "*.png;*.jpg;*.jpeg")])
        ruta_imagen = filedialog.askopenfilename(title="Abrir imagen", filetypes=[("Archivos de imagen", "*.*")])
        if ruta_imagen:
            self.imagen = plt.imread(ruta_imagen)
            # self.imagen = np.array(self.imagen  * 255, dtype=np.uint8)
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

    def limpiar_dibujo(self):
        # Borra las coordenadas almacenadas
        self.coordenadas = []
        # Elimina todas las líneas dibujadas en el gráfico
        for line in self.ax.lines:
            line.remove()
        # Redibuja la imagen original
        # self.ax.imshow(self.imagen)
        # Actualiza el lienzo
        self.figura.canvas.draw()

    def procesar(self):
        if not self.coordenadas:
            return
        print("Procesando...")
        # print(self.coordenadas)

        h, w = self.imagen.shape[:2]
        
        def laplacian_coordinates_weights(img, epsilon=10e-6):
            # weights = np.zeros((h*w, h*w))
            weights = sp.lil_matrix((h*w, h*w))

            sigma = 1

            for i in range(h):
                for j in range(w):
                    idx = i*w + j
                    if i > 0:
                        weights[idx, (i-1)*w+j] = np.exp(-((img[i,j] - img[i-1,j])**2).sum() / sigma)
                    if i < h-1:
                        weights[idx, (i+1)*w+j] = np.exp(-((img[i,j] - img[i+1,j])**2).sum() / sigma)
                    if j > 0:
                        weights[idx, i*w+j-1] = np.exp(-((img[i,j] - img[i,j-1])**2).sum() / sigma)
                    if j < w-1:
                        weights[idx, i*w+j+1] = np.exp(-((img[i,j] - img[i,j+1])**2).sum() / sigma)

            return weights

        img = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])  # Ejemplo de una imagen
        img = self.imagen

        weights = laplacian_coordinates_weights(img)
        print("Tamaño matrix de pesos: ", weights.shape)

        
        # plt.imshow(weights, cmap='gray')
        # plt.colorbar()
        # plt.show()

        def laplacian_coordinates_matrix(weights):
            D = sp.diags(weights.sum(axis=1).A.ravel())
            return D - weights
        
        L = laplacian_coordinates_matrix(weights)
        print("Tamaño matrix de Laplacian: ", L.shape)

        L2 = L.dot(L)

        I_s = sp.lil_matrix((h*w, h*w))


        b = np.zeros(h*w)

        indices = np.arange(h*w).reshape(h, w)

        xB = -1
        xF = 1
        
        for (i, j, color) in self.coordenadas:
            index = indices[i, j]
            I_s[index, index] = 1
            b[index] = xB if color == 'g' else xF
            # print(i, j, color)    

        print("Tamaño matrix de I_s: ", I_s.shape)

        A = I_s + L2

        A = sp.csr_matrix(A)

        solve = factorized(A)

        x = solve(b)

        segmented_image = x.reshape((h, w))

        self.limpiar_dibujo()

        # self.imagen = np.where(segmented_image > 0, 1, 0)
 
        self.ax.imshow(segmented_image)
        self.figura.canvas.draw()


if __name__ == "__main__":
    ventana_principal = tk.Tk()
    aplicacion = AplicacionDibujo(ventana_principal)
    ventana_principal.mainloop()
