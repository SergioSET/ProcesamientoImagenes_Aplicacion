import numpy as np
import matplotlib.pyplot as plt

# Definir el número de nodos
n = 500

# Crear un gráfico lineal con los nodos
x = np.arange(n)

# Definir los pesos de los bordes
weights1 = np.ones(n)
weights1[n//4:3*n//4] = np.linspace(1, 0, n//2)
weights1[3*n//4:] = np.linspace(0, 1, n//4)

weights2 = np.ones(n)
weights2[n//4:3*n//4] = np.linspace(1, 0, n//2)
weights2[n//8:5*n//8] = np.linspace(0, 1, 3*n//8)  # Corrected line
weights2[5*n//8:7*n//8] = np.linspace(1, 0, n//4)
weights2[7*n//8:] = np.linspace(0, 1, n//8)

# Definir las semillas
seeds = np.zeros(n)
seeds[0] = 1  # Semilla amarilla
seeds[-1] = -1  # Semilla púrpura

# Calcular la solución usando Laplacian Coordinates
L = np.diag(weights1) - np.diag(weights1[:-1], 1) - np.diag(weights1[:-1], -1)
solution_lc = np.linalg.solve(L, seeds)

# Calcular la solución usando Random Walker
D = np.diag(np.sum(weights2, axis=1))
L = D - np.diag(weights2)
solution_rw = np.linalg.solve(L, seeds)

# Generar la figura 2
fig, ax = plt.subplots(4, 2, figsize=(10, 8))

# Graficar el gráfico lineal
ax[0, 0].plot(x, seeds, 'o-')
ax[0, 0].set_title('Gráfico lineal')

# Graficar los pesos de los bordes
ax[1, 0].plot(weights1)
ax[1, 0].set_title('Distribución de pesos 1')
ax[1, 1].plot(weights2)
ax[1, 1].set_title('Distribución de pesos 2')

# Graficar las soluciones
ax[2, 0].plot(solution_lc)
ax[2, 0].set_title('Solución Laplacian Coordinates')
ax[2, 1].plot(solution_rw)
ax[2, 1].set_title('Solución Random Walker')

# Graficar las soluciones con pesos uniformes
L = np.diag(np.ones(n)) - np.diag(np.ones(n-1), 1) - np.diag(np.ones(n-1), -1)
solution_lc_uniform = np.linalg.solve(L, seeds)
ax[3, 0].plot(solution_lc_uniform)
ax[3, 0].set_title('Solución Laplacian Coordinates (pesos uniformes)')
ax[3, 1].plot(solution_rw)
ax[3, 1].set_title('Solución Random Walker (pesos uniformes)')

plt.tight_layout()
plt.show()
