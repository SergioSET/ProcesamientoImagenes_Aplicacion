import tkinter as tk
from tkinter import filedialog
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from scipy.spatial.distance import pdist, squareform
import scipy
import scipy.sparse as sp
from scipy.sparse.linalg import spsolve, factorized
from PIL import Image

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

        self.figura.canvas.mpl_connect("button_press_event", self.on_click)
        self.figura.canvas.mpl_connect("motion_notify_event", self.on_drag)
        self.figura.canvas.mpl_connect("button_release_event", self.on_release)

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
        ruta_imagen = filedialog.askopenfilename(title="Abrir imagen", filetypes=[("Archivos de imagen", "*.png;*.jpg;*.jpeg")])
        if ruta_imagen:
            self.imagen = Image.open(ruta_imagen).convert('L')
            self.imagen = np.array(self.imagen)

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
    
    def on_click(self, event):
        if event.inaxes == self.ax:
            x = int(round(event.xdata))
            y = int(round(event.ydata))
            color = 'g' if event.button == 1 else 'r'
            self.coordenadas.append((y, x, color))
            self.ax.plot(x, y, marker='o', markersize=5, color=color)
            self.figura.canvas.draw()

    def on_drag(self, event):
        if event.inaxes == self.ax and event.button == 1:
            x = int(round(event.xdata))
            y = int(round(event.ydata))
            color = 'g' if event.button == 1 else 'r'
            self.coordenadas.append((y, x, color))
            self.ax.plot(x, y, marker='o', markersize=5, color=color)
            self.figura.canvas.draw()

    def on_release(self, event):
        if event.inaxes == self.ax:
            self.figura.canvas.draw()

    def limpiar_dibujo(self):
        self.coordenadas = []
        
        for line in self.ax.lines:
            line.remove()
            
        self.figura.canvas.draw()

    def procesar(self):
        if not self.coordenadas:
            return
        print("Procesando...")
        # print(self.coordenadas)

        h, w = self.imagen.shape
        
        def laplacian_coordinates_weights(img, epsilon=10e-6):
            weights = sp.lil_matrix((h*w, h*w))

            sigma = np.max(np.abs(np.diff(self.imagen.flatten())))
            print("Sigma: ", sigma)

            for i in range(h):
                for j in range(w):
                    idx = i*w + j
                    if i > 0:
                        weights[idx, (i-1)*w+j] = np.exp(- epsilon * ((img[i,j] - img[i-1,j])**2).sum() / sigma)
                    if i < h-1:
                        weights[idx, (i+1)*w+j] = np.exp(- epsilon * ((img[i,j] - img[i+1,j])**2).sum() / sigma)
                    if j > 0:
                        weights[idx, i*w+j-1] = np.exp(- epsilon * ((img[i,j] - img[i,j-1])**2).sum() / sigma)
                    if j < w-1:
                        weights[idx, i*w+j+1] = np.exp(- epsilon * ((img[i,j] - img[i,j+1])**2).sum() / sigma)

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
            if color == 'g':
                xB += self.imagen[i, j]
            else:
                xF += self.imagen[i, j]

        xB = xB / len([c for c in self.coordenadas if c[2] == 'g'])
        xF = xF / len([c for c in self.coordenadas if c[2] == 'r'])

        print("xB: ", xB)
        print("xF: ", xF)
        
        Is = sp.lil_matrix((h*w, h*w))
        L_2 = L.dot(L)
        b = np.zeros(h*w)
        
        indices = np.array([[i*w+j for j in range(w)] for i in range(h)])
        for (i, j, color) in self.coordenadas:
            index = indices[i, j]
            Is[index, index] = 1
            b[index] = xB if color == 'g' else xF
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
        self.figura.canvas.draw()


if __name__ == "__main__":
    ventana_principal = tk.Tk()
    aplicacion = AplicacionDibujo(ventana_principal)
    ventana_principal.mainloop()
