from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
import numpy as np

fig = plt.figure()
ax = fig.add_subplot(111, projection='3d')

x = np.arange(-10000,10001,1)
y = np.arange(-10000,10001,1)
z = np.arange(0,20001,1)

x1 = np.arange(-10,11,1)
y1 = np.arange(-10,11,1)
z1 = np.arange(0,21,1)

c = []
for i in x1:
    for j in y1:
        for k in z1:
          c.append(x1*y1*z1)
c = np.array(c)

ax.scatter(x, y, z, c=c, cmap=plt.hot())
plt.show()
