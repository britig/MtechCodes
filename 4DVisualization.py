# Python-matplotlib Commands
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
import matplotlib.pyplot as plt
import numpy as np

fig = plt.figure()
ax = fig.gca(projection='3d')
X = np.arange(-5, 5, .25)
Y = np.arange(-5, 5, .25)
Z = np.arange(-5, 5, .25)
X, Y = np.meshgrid(X, Y)
R = np.sqrt(X**2 + Y**2)
K = np.sin(R)
#Z = np.arange(-5, 5, .25)
Gx, Gy = np.gradient(K) # gradients with respect to x and y
G = (Gx**2+Gy**2)**.5  # gradient magnitude
#G = np.gradient(Z)
N = G/G.max()  # normalize 0..1
surf = ax.plot_surface(X, Y, K, rstride=1, cstride=1, facecolors=cm.jet(N), linewidth=0, antialiased=False, shade=False)
plt.show()