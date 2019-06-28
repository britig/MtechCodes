import numpy as np

def fn_my_black_box_function(x1, x2):
    y = -abs(np.sin(x1)*np.cos(x2)*np.exp(abs(1-(np.sqrt(x1**2+x2**2))/np.pi)))#-(x2 + 47) * np.sin(np.sqrt(abs(x1 / 2.0 + (x2 + 47.0)))) - (x1 * np.sin(np.sqrt(abs(x1 - (x2 + 47.0)))))
    return y

if __name__=='__main__':
    res = fn_my_black_box_function(8, -1.49)
    print(res)
