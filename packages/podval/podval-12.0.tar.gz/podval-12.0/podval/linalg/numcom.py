import pyperclip as pc

def naivn_alg():
    text='''
def matmult(a, b):
    n = len(a)
    k = len(a[0])
    m = len(b[0])
    c = np.zeros((n, m))
    for i in range(n):
        for j in range(m):
            for s in range(k):
                c[i, j] += a[i][s] * b[s][j]
    return c
    '''
    pc.copy(text)
    
def strassen_alg():
    text='''
def next_power_of_two(x):
    # Найти ближайшую степень двойки, не меньшую заданного числа
    return 1 if x == 0 else 2**(x - 1).bit_length()

def pad_matrix(A, size):
    padded = np.zeros((size, size))  # Создаем новую матрицу заданного размера, заполненную нулями
    padded[:A.shape[0], :A.shape[1]] = A  # Копируем исходную матрицу в новую
    return padded

def strassen(A, B):
    # Преобразуем входные данные в массивы NumPy (если это не так)
    A = np.array(A)
    B = np.array(B)

    # Определяем максимальный размер среди входных матриц
    n = max(A.shape[0], A.shape[1], B.shape[0], B.shape[1])
    new_size = next_power_of_two(n)  # Находим ближайшую степень двойки

    # Дополняем матрицы до ближайшей степени двойки
    A_padded = pad_matrix(A, new_size)
    B_padded = pad_matrix(B, new_size)

    # Выполняем алгоритм Штрассена на дополненных матрицах
    C_padded = strassen_recursive(A_padded, B_padded)

    # Обрезаем результат до исходного размера
    return C_padded[:A.shape[0], :B.shape[1]]

def strassen_recursive(A, B):
    n = len(A)  # Размер текущей матрицы

    # Базовый случай: для маленьких матриц используем обычное умножение
    if n <= 2:
        return np.dot(A, B)

    mid = n // 2  # Находим середину для разделения матрицы

    # Разделяем матрицы на 4 подматрицы
    A11 = A[:mid, :mid]
    A12 = A[:mid, mid:]
    A21 = A[mid:, :mid]
    A22 = A[mid:, mid:]
    B11 = B[:mid, :mid]
    B12 = B[:mid, mid:]
    B21 = B[mid:, :mid]
    B22 = B[mid:, mid:]

    # Вычисляем вспомогательные матрицы P1-P7
    P1 = strassen_recursive(A11, B12 - B22)
    P2 = strassen_recursive(A11 + A12, B22)
    P3 = strassen_recursive(A21 + A22, B11)
    P4 = strassen_recursive(A22, B21 - B11)
    P5 = strassen_recursive(A11 + A22, B11 + B22)
    P6 = strassen_recursive(A12 - A22, B21 + B22)
    P7 = strassen_recursive(A11 - A21, B11 + B12)

    # Собираем подматрицы в итоговую матрицу C
    C11 = P5 + P4 - P2 + P6
    C12 = P1 + P2
    C21 = P3 + P4
    C22 = P5 + P1 - P3 - P7

    # Объединяем C11, C12, C21, C22 в одну матрицу
    C = np.vstack((np.hstack((C11, C12)), np.hstack((C21, C22))))
    return C  
    '''
    pc.copy(text)
    
def iterat_met():
    text='''
X = [[1.6, 0.7, 0.8, 2.2], [0.7,1.6, 0.3, 1.2], [0.8,0.3,1.6,1.3], [2.2, 1.2, 3.2, 3.3]]

A = X
x = np.matrix([[2,5,1,5]]).T #Исходный вектор
tol = 0.001
max_iter = 100

lam_prev = 0

for i in range(max_iter):
    x = strassen(A, x) / np.sqrt(np.sum((strassen(A, x))**2))
    
    lam = (strassen(strassen(x.T,A),x)) / (strassen(x.T,x))
    
    if np.abs(lam - lam_prev) < tol:
        break
    
    lam_prev = lam
    
print(lam) # максимальное по модулю собст знач
print(x)  # собств вектор

# np.array(lam) * np.array(x)
# matmult(A,x)

# np.linalg.eig(np.array(A, dtype=complex))
    '''
    pc.copy(text)
    

def visual_vec():
    text='''
# Визуализация на комплексной плоскости
eigval = lam  # Собственное значение
eigvec = x.flatten()  # Собственный вектор

# Собственные значения
plt.scatter([eigval.real], [eigval.imag], color='blue', label='Eigenvalue', marker='x')

# Собственный вектор
plt.quiver(0, 0, eigvec[0].real, eigvec[0].imag, angles='xy', scale_units='xy', scale=1,
           color='orange', alpha=0.8, label='Eigenvector')

# Настройки графика
plt.axhline(0, color='black', linewidth=0.5, linestyle='--')
plt.axvline(0, color='black', linewidth=0.5, linestyle='--')
plt.xlabel('Real part')
plt.ylabel('Imaginary part')
plt.title('Eigenvalue and Eigenvector on the Complex Plane')
plt.legend()
plt.grid(alpha=0.3)
plt.show()
    '''
    pc.copy(text)
    

def vrash_met():
    text='''
import math
import numpy as np

def spin_method(A: np.array, eps: float = 0.0001):
    A = np.array(A)
    
    A_0 = A.copy()
    k = 0
    H_list = [] # Список с матрицами вращений
    while True:
        # Выделение макс по модулю элемента в верхней наддиаг. части матрицы
        max_index = np.argmax(abs(np.triu(A_0, 1)))
        i, j = np.unravel_index(max_index, A_0.shape) # нахождение координат в матрице
        a_ij_max = A_0[i,j]
        
        # Выход из цикла, определение собств значений и собств векторов 
        if eps >= abs(a_ij_max):
            nu_k = H_list[0]
            if k > 0:
                for H in H_list[1:]:
                    nu_k = matmult(nu_k, H)
            return np.diagonal(A_0), nu_k            
        
        # Нахождение угла поворота
        if A_0[i,i] == A_0[j,j]:
            phi = math.pi / 4
        else:
            P_k = (2 * a_ij_max) / (A_0[i,i] - A_0[j,j])
            phi = math.atan(P_k) / 2            
        
        # Составление матрицы вращения
        H_k = np.eye(A_0.shape[0])
        H_k[i,i] = math.cos(phi)
        H_k[j,j] = math.cos(phi)
        H_k[i,j] = -math.sin(phi)
        H_k[j,i] = math.sin(phi)
        H_list.append(H_k)
        
        # Вычисление приближения
        A_0 = matmult(matmult(H_k.T, A_0), H_k)
        k += 1
        
X = [[1.6, 0.7, 1.4, 0.4], [0.7, 1.6, 1.4, 0.5], [0.8, 0.3, 1.0, 2.2], [0.6, 0.3, 1.6, 3.3]]
lambds, x_s = spin_method(X)
# np.linalg.eig(np.array(X, dtype=complex))
print(lambds)
print(x_s)
    '''
    pc.copy(text)
    
def qr_alg():
    text='''
def householder(x):
    e = np.zeros_like(x)
    e[0] = 1
    norm_x = np.sqrt((np.array(x) ** 2).sum())
    u = x - norm_x * e
    u = u.reshape(-1, 1)  # Обеспечиваем двумерную форму (n, 1)
    
    u_sq_sum = (matmult(u.T, u)).item()
    v = u / np.sqrt(u_sq_sum) if u_sq_sum > 1e-10 else np.zeros_like(u)

    I = np.eye(v.shape[0])
    H = I - 2.0 * matmult(v, v.T)
    return H

def matrices_are_close(A, A_new, tol):
    n, m = A.shape
    for i in range(n):
        for j in range(m):
            if abs(A[i, j] - A_new[i, j]) > tol:
                return False
    return True

def qr_decomp(matrix):
    n, m = matrix.shape
    Q = np.eye(n)
    R = matrix.copy()
    for i in range(min(n, m)):
        H_sub = householder(R[i:, i])
        H = np.eye(n)
        H[i:, i:] = H_sub
        R = matmult(H, R)
        Q = matmult(Q, H.T)
    return Q, R

def qr_alg(matrix, iterations=1000, tol=1e-10):
    n, m = matrix.shape
    A = matrix.copy()
    Q_total = np.eye(n)
    for _ in range(iterations):
        Q, R = qr_decomp(A)
        A_new = matmult(R, Q)
        Q_total = matmult(Q_total, Q)  # Накапливаем Q, чтобы получить собственные векторы

        if matrices_are_close(A, A_new, tol):
            break
            
        A = A_new

    eigenvalues = np.diag(A)  # Собственные значения на диагонали A
    eigenvectors = Q_total    # Собственные векторы
    return eigenvalues, eigenvectors

# Пример
M = np.array([[1.2, 2.0, 0.5, 0.8], [1.6, 1.6, 1.7, 0.4], [0.4, 0.3, 1.4, 2.0], [0.5, 1.7, 1.7, 0.3]], dtype=complex)
eigenvalues, eigenvectors = qr_alg(M, tol=0.001)
eigenvalues, eigenvectors
    '''
    pc.copy(text)
    

def qr_neyavn_alg():
    text='''
def householder(x):
    e = np.zeros_like(x)
    e[0] = 1
    norm_x = np.sqrt((np.array(x) ** 2).sum())
    u = x - norm_x * e
    u = u.reshape(-1, 1)  # Обеспечиваем двумерную форму (n, 1)
    
    u_sq_sum = (matmult(u.T, u)).item()
    v = u / np.sqrt(u_sq_sum) if u_sq_sum > 1e-10 else np.zeros_like(u)

    I = np.eye(v.shape[0])
    H = I - 2.0 * matmult(v, v.T)
    return H

def matrices_are_close(A, A_new, tol):
    n, m = A.shape
    for i in range(n):
        for j in range(m):
            if abs(A[i, j] - A_new[i, j]) > tol:
                return False
    return True

def qr_decomp(matrix):
    n, m = matrix.shape
    Q = np.eye(n)
    R = matrix.copy()
    for i in range(min(n, m)):
        H_sub = householder(R[i:, i])
        H = np.eye(n)
        H[i:, i:] = H_sub
        R = matmult(H, R)
        Q = matmult(Q, H.T)
    return Q, R


# Неявный QR-Алгоритм
def qr_alg_shifted(matrix, iterations=1000, tol=1e-10):
    n = matrix.shape[0]
    A = matrix.copy()
    Q_total = np.eye(n)
    for _ in range(iterations):
        # Определяем сдвиг
        s = A[n-1, n-1]
        # Применяем QR-разложение к сдвинутой матрице
        Q, R = qr_decomp(A - s * np.eye(n))
        # Обновляем A
        A_new = matmult(R, Q) + s * np.eye(n)
        Q_total = matmult(Q_total, Q)

        if matrices_are_close(A, A_new, tol):
            break
            
        A = A_new

    eigenvalues = np.diag(A)  # Собственные значения на диагонали A
    eigenvectors = Q_total    # Собственные векторы
    return eigenvalues, eigenvectors

# Пример
M = np.array([[1.2, 2.0, 0.5, 0.8], [1.6, 1.6, 1.7, 0.4], [0.4, 0.3, 1.4, 2.0], [0.5, 1.7, 1.7, 0.3]], dtype=complex)
eigenvalues, eigenvectors = qr_alg_shifted(M, tol=0.001)
eigenvalues, eigenvectors
    '''
    pc.copy(text)
    
def neposr_rasv_met():
    text='''
import numpy as np
import cmath

def get_characteristic_polynomial_coefficients(matrix):
    # Определяем размерность матрицы
    n = len(matrix)
    if n == 2:  # Для матрицы 2x2
        a = 1
        b = -(matrix[0][0] + matrix[1][1])
        c = matrix[0][0] * matrix[1][1] - matrix[0][1] * matrix[1][0]
        return [a, b, c]
    elif n == 3:  # Для матрицы 3x3
        a = 1
        b = -(matrix[0][0] + matrix[1][1] + matrix[2][2])
        c = (matrix[0][0] * matrix[1][1] + matrix[1][1] * matrix[2][2] + matrix[2][2] * matrix[0][0]
             - matrix[0][1] * matrix[1][0] - matrix[1][2] * matrix[2][1] - matrix[2][0] * matrix[0][2])
        d = -(matrix[0][0] * matrix[1][1] * matrix[2][2] + matrix[0][1] * matrix[1][2] * matrix[2][0]
              + matrix[0][2] * matrix[1][0] * matrix[2][1] - matrix[0][2] * matrix[1][1] * matrix[2][0]
              - matrix[0][0] * matrix[1][2] * matrix[2][1] - matrix[0][1] * matrix[1][0] * matrix[2][2])
        return [a, b, c, d]
    else:
        raise ValueError("Matrix dimension not supported for this implementation.")

def solve_quadratic(a, b, c):
    # Решение квадратного уравнения ax^2 + bx + c = 0
    discriminant = b ** 2 - 4 * a * c
    root1 = (-b + cmath.sqrt(discriminant)) / (2 * a)
    root2 = (-b - cmath.sqrt(discriminant)) / (2 * a)
    return [root1, root2]

def compute_eigenvectors(matrix, eigenvalues):
    eigenvectors = []
    n = matrix.shape[0]
    for eigenvalue in eigenvalues:
        # Решаем систему (A - λI)v = 0
        A_shifted = matrix - eigenvalue * np.eye(n)
        # Используем SVD для поиска ненулевого вектора в nullspace
        _, _, vh = np.linalg.svd(A_shifted)
        eigenvector = vh[-1]  # Последняя строка V^H соответствует nullspace
        eigenvectors.append(eigenvector)
    return np.array(eigenvectors).T  # Собственные векторы в столбцах

# Пример использования для матрицы 2x2:
MM = np.array([[1.2, -2.0], [1.6, 1.6]], dtype=complex)
coeffs = get_characteristic_polynomial_coefficients(MM)
roots = solve_quadratic(*coeffs)
eigenvectors = compute_eigenvectors(MM, roots)

print("Коэффициенты характеристического многочлена:", coeffs)
print("Собственные значения:", roots)
print("Собственные векторы (в столбцах):\n", eigenvectors)



# Визуализация на комплексной плоскости
eigval = np.array(roots, dtype=complex)  # Собственное значение
eigvec = np.array(eigenvectors).flatten()  # Собственный вектор

# Собственные значения
plt.scatter([eigval.real], [eigval.imag], color='blue', label='Eigenvalue', marker='x')

# Собственный вектор
plt.quiver(0, 0, eigvec[2].real, eigvec[2].imag, angles='xy', scale_units='xy', scale=1,
           color='orange', alpha=0.8, label='Eigenvector')

# Настройки графика
plt.axhline(0, color='black', linewidth=0.5, linestyle='--')
plt.axvline(0, color='black', linewidth=0.5, linestyle='--')
plt.xlabel('Real part')
plt.ylabel('Imaginary part')
plt.title('Eigenvalue and Eigenvector on the Complex Plane')
plt.legend()
plt.grid(alpha=0.3)
plt.show()
    '''
    pc.copy(text)
    

def koshi_formulas():
    text='''
Прямая разность: $f'(x_0) = \frac{f(x_0 + h) - f(x_0)}{h}$

Обратная разность: $f'(x_0) = \frac{f(x_0) - f(x_0 - h)}{h}$

---

Вспомнили ряд Тейлора: $f(x_0 + h) = f(x_0) + \frac{h f'(x_0)}{1!} + \frac{h^2 f''(x_0)}{2!} + O(h^3)$

$f'(x_0) = \frac{f(x_0 + h) - f(x_0)}{h} = f'(x_0) + \frac{hf''(x_0)}{2} + O(h^2) = f'(x_0) + O(h)$

---

$f(x_0 + h) = f(x_0) + \frac{h f'(x_0)}{1!} + \frac{h^2 f''(x_0)}{2!} + O(h^3)$

$f(x_0 - h) = f(x_0) - \frac{h f'(x_0)}{1!} + \frac{h^2 f''(x_0)}{2!} - O(h^3)$

Центральная разность: $f'(x_0) = \frac{f(x_0 + h) - f(x_0 - h)}{2h} = f'(x_0) + O(h^2)$
    '''
    pc.copy(text)
    
    
def tsentr_razn():
    text='''
def func(x):
    return np.exp(x) * np.sqrt((7 * x**2 + 3))

x0 = 0

h = np.logspace(-7, 1)

estimate = (func(x0 + h) - func(x0-h)) / (2*h)
# estimate = (func(x0) - func(x0 - h)) / h #для обратной разницы 

err = np.abs(3 / np.sqrt(3) - estimate)

estimate

fig = plt.figure(figsize = (10, 6))
ax = fig.add_subplot()
ax.loglog(h, err, 'kx', label = 'Расчётные данные')
ax.set_xlabel('h')
ax.set_ylabel('$\|$ Ошибка $\|$')
ax.set_title('Сходимость оценок значения производной')
ax.legend(loc = 2)
plt.show()
    '''
    pc.copy(text)
    

def pryam_razn():
    text='''
def func(x):
    return np.cos(math.pi * x)**3

x0 = 0

h = np.logspace(-7, 1)

estimate = (func(x0 + h) - func(x0)) / h
# estimate = (func(x0) - func(x0 - h)) / h #для обратной разницы 

err = np.abs(0.0 - estimate)

estimate


fig = plt.figure(figsize = (10, 6))
ax = fig.add_subplot()
ax.loglog(h, err, 'kx', label = 'Расчётные данные')
ax.set_xlabel('h')
ax.set_ylabel('$\|$ Ошибка $\|$')
ax.set_title('Сходимость оценок значения производной')
ax.legend(loc = 2)
plt.show()
    '''
    pc.copy(text)
    

def euler_met():
    text='''
import numpy as np

def method_euler(f, x_0, x_n, y_0, N):
    dx = (x_n - x_0) / N
    x = np.linspace(x_0, x_n, N+1)
    y = np.zeros((N+1, len(y_0)))  # Двумерный массив для всех значений y
    y[0, :] = y_0  # Начальное условие

    for n in range(N):
        y[n+1, :] = y[n, :] + dx * f(x[n], y[n, :])  # Метод Эйлера

    return x, y

# Определение системы уравнений
def equations(x, y):
    # Возвращаем массив вместо списка
    return np.array([np.arctan(1 / (1 + y[0]**2 + y[1]**2)), np.sin(y[0]*y[1])])

x, y = method_euler(equations, -1.0, 5.0, [-1.0, -1.0], 60000)

print("Последние значения x:", x[-1])
print("Последние значения y:", y[-1])
    '''
    pc.copy(text)
    
    
def equasions_func():
    text='''
def equations(x, y):
    # Возвращаем массив вместо списка
    return np.array([np.arctan(1 / (1 + y[0]**2 + y[1]**2)), np.sin(y[0]*y[1])])
    '''
    pc.copy(text)
    
    
def fazov_portr():
    text='''
plt.figure(figsize=(10, 6))
plt.plot(y[:, 0], y[:, 1], label="Фазовая траектория")

# Добавление осей и подписей
plt.xlabel("y[0] (переменная состояния 1)", fontsize=12)
plt.ylabel("y[1] (переменная состояния 2)", fontsize=12)
plt.title("Фазовый портрет системы", fontsize=14)
plt.axhline(0, color="black", linewidth=0.8, linestyle="--")
plt.axvline(0, color="black", linewidth=0.8, linestyle="--")
plt.grid(alpha=0.5)
plt.legend(fontsize=12)
plt.show()
    '''
    pc.copy(text)
    
def pred_conn_met():
    text='''
def euler_pc(f, x_0, x_n, y_0, N):
    dx = (x_n - x_0) / N
    x = np.linspace(x_0, x_n, N+1)
    y = np.zeros((N+1, len(y_0)))
    y[0, :] = y_0

    for n in range(N):
        yp = y[n, :] + dx * f(x[n], y[n, :])
        y[n+1, :] = y[n, :] + dx/2 * (f(x[n], y[n, :]) + f(x[n+1], yp))
    return x, y
    
x, y = euler_pc(equations, -1.0, 5.0, [-1.0, -1.0], 60000)

print("Последние значения x:", x[-1])
print("Последние значения y:", y[-1])
    '''
    pc.copy(text)
    

def runge_kut():
    text='''
def rk4_method(f, x_0, x_n, y_0, N):
    dx = (x_n - x_0) / N
    x = np.linspace(x_0, x_n, N+1)
    y = np.zeros((N+1, len(y_0)))
    y[0, :] = y_0
    k1 = np.zeros_like(y_0)
    k2 = np.zeros_like(y_0)
    k3 = np.zeros_like(y_0)
    k4 = np.zeros_like(y_0)

    for n in range(N):
        k1 = dx * f(x[n], y[n, :])
        k2 = dx * f(x[n] + dx/2, y[n, :] + k1/2)
        k3 = dx * f(x[n] + dx/2, y[n, :] + k2/2)
        k4 = dx * f(x[n] + dx, y[n, :] + k3)
        y[n+1, :] = y[n, :] + (k1 + k4 + 2*(k2 + k3))/6

    return x, y

x, y = rk4_method(equations, -1.0, 5.0, [-1.0, -1.0], 60000)

print("Последние значения x:", x[-1])
print("Последние значения y:", y[-1])
    '''
    pc.copy(text)
    
def adams_mult():
    text='''
def am5_method(f, x_0, x_n, y_0, N):
    # Вычисление шага dx
    dx = (x_n - x_0) / N
    # Массив точек x, равномерно распределенных от x_0 до x_n
    x = np.linspace(x_0, x_n, N + 1)
    # Массив для решения y, где каждая строка - значения y для соответствующего x
    y = np.zeros((N + 1, len(y_0)))
    # Массив для значений функции f(x, y)
    fn = np.zeros_like(y)
    # Задаем начальные условия
    y[0, :] = y_0

    # Переменные для хранения промежуточных значений метода Рунге-Кутта
    k1 = np.zeros_like(y_0)
    k2 = np.zeros_like(y_0)
    k3 = np.zeros_like(y_0)
    k4 = np.zeros_like(y_0)

    # Инициализация: метод Рунге-Кутта 4-го порядка
    for n in range(N):
        # Вычисляем значения функции в текущей точке
        fn[n, :] = f(x[n], y[n, :])
        # Этапы метода Рунге-Кутта
        k1 = dx * fn[n, :]
        k2 = dx * f(x[n] + dx / 2, y[n, :] + k1 / 2)
        k3 = dx * f(x[n] + dx / 2, y[n, :] + k2 / 2)
        k4 = dx * f(x[n] + dx, y[n, :] + k3)
        # Обновляем значение y в следующей точке
        y[n + 1, :] = y[n, :] + 1 / 6 * (k1 + 2 * k2 + 2 * k3 + k4)

    # Матрица для вычисления коэффициентов метода Адамса-Бэшфорта
    coeff_A = np.array(
        [
            [1, 1, 1, 1, 1],        # Уравнение для коэффициента b0
            [0, -1, -2, -3, -4],    # Уравнение для коэффициента b1
            [0, 0, 2, 6, 12],       # Уравнение для коэффициента b2
            [0, 0, 0, -6, -24],     # Уравнение для коэффициента b3
            [0, 0, 0, 0, 24],       # Уравнение для коэффициента b4
        ]
    )
    # Правая часть для вычисления коэффициентов
    coeff_b = np.array([1, 1 / 2, 5 / 6, 9 / 4, 251 / 30])
    # Коэффициенты метода Адамса-Бэшфорта четвертого порядка
    b_ab4 = np.linalg.solve(coeff_A, coeff_b)
    # Коэффициенты метода Адамса-Мултона пятого порядка
    b_am5 = np.array([251, 646, -264, 106, -19]) / 720

    # Основной цикл метода Адамса
    for n in range(4, N):  # Начинаем с пятой точки, так как первые 4 точки инициализированы
        # Вычисляем значение функции в текущей точке
        fn[n, :] = f(x[n], y[n, :])
        # Прогноз значения y с помощью метода Адамса-Бэшфорта (AB4)
        yp = y[n, :] + dx * (
            b_ab4[0] * fn[n, :] +
            b_ab4[1] * fn[n - 1, :] +
            b_ab4[2] * fn[n - 2, :] +
            b_ab4[3] * fn[n - 3, :] +
            b_ab4[4] * fn[n - 4, :]
        )
        # Коррекция значения y с помощью метода Адамса-Мултона (AM5)
        y[n + 1, :] = y[n, :] + dx * (
            b_am5[0] * f(x[n+1], yp) +
            b_am5[1] * fn[n, :] +
            b_am5[2] * fn[n - 1, :] +
            b_am5[3] * fn[n - 2, :] +
            b_am5[4] * fn[n - 3, :]
        )

    return x, y

# Пример использования метода
x, y = am5_method(equations, -1.0, 5.0, [-1.0, -1.0], 60000)

# Вывод результатов
print("Последние значения x:", x[-1])  # Последняя точка x
print("Последние значения y:", y[-1])  # Последние значения y в этой точке
    '''
    pc.copy(text)
    
    
def milna_met():
    text='''
import numpy as np

def milne_method(f, x_0, x_n, y_0, N):
    dx = (x_n - x_0) / N
    x = np.linspace(x_0, x_n, N + 1)
    y = np.zeros((N + 1, len(y_0)))
    fn = np.zeros_like(y)
    y[0, :] = y_0

    # Инициализация методом Рунге-Кутта 4-го порядка для первых 4 точек
    for n in range(3):
        k1 = dx * f(x[n], y[n, :])
        k2 = dx * f(x[n] + dx / 2, y[n, :] + k1 / 2)
        k3 = dx * f(x[n] + dx / 2, y[n, :] + k2 / 2)
        k4 = dx * f(x[n] + dx, y[n, :] + k3)
        y[n + 1, :] = y[n, :] + 1 / 6 * (k1 + 2 * k2 + 2 * k3 + k4)

    # Вычисляем значения функции f(x, y) для первых 4 точек
    for n in range(4):
        fn[n, :] = f(x[n], y[n, :])

    # Основной цикл метода Милна
    for n in range(3, N):
        # Предсказание (Milne predictor)
        y_pred = y[n - 3, :] + 4 * dx / 3 * (2 * fn[n, :] - fn[n - 1, :] + 2 * fn[n - 2, :])

        # Коррекция (Milne corrector)
        fn_pred = f(x[n + 1], y_pred)
        y[n + 1, :] = y[n - 1, :] + dx / 3 * (fn_pred + 4 * fn[n, :] + fn[n - 1, :])
        # Обновляем значение функции f(x, y) для нового шага
        fn[n + 1, :] = f(x[n + 1], y[n + 1, :])

    return x, y

# Определение системы уравнений
def equations(x, y):
    return np.array([np.arctan(1 / (1 + y[0]**2 + y[1]**2)), np.sin(y[0] * y[1])])

# Пример использования метода Милна
x, y = milne_method(equations, -1.0, 5.0, [-1.0, -1.0], 60000)

# Вывод результатов
print("Последние значения x:", x[-1])
print("Последние значения y:", y[-1])
    '''
    pc.copy(text)
    
def fourier_preobr():
    text='''
def FFT(x):
    N = len(x)

    if N == 1:
        return x
    else:
        X_even = FFT(x[::2])
        X_odd = FFT(x[1::2])

        factor = np.exp(-2j*np.pi*np.arange(N)/N)

        X = np.concatenate([X_even + factor[:int(N/2)]*X_odd,
                X_even + factor[int(N/2):]*X_odd])
        return X
    
def IFFT(x):
    N = len(x)
    
    if N == 1:
        return x
    
    else:
        X_even = IFFT(x[::2])
        X_odd = IFFT(x[1::2])

        factor = np.exp(2j * np.pi * np.arange(N)/N)
        X = np.concatenate([X_even + factor[:N//2] * X_odd,
                X_even + factor[N//2:] * X_odd])
        return X / 2
    
# Дискретное преобразование Фурье
def DFT(x):
    N = len(x)
    n = np.arange(N)
    X = np.zeros(N, dtype=complex)
    for k in range(N):
        X[k] = np.sum(x * np.exp(-2j * np.pi * k * n / N))
    return X

# Обратное дискретное преобразование Фурье
def IDFT(x):
    N = len(x)
    n = np.arange(N)
    X = np.zeros(N, dtype=complex)
    for k in range(N):
        X[k] = np.sum(x * np.exp(2j * np.pi * k * n / N)) / N
    return X
    '''
    pc.copy(text)
    
def fourier_prochee():
    text='''
sr = 100
ts = 1 / sr
t = np.arange(0, 1, ts)

freq = 1 # частота сигнала
x = 3*np.sin(2*np.pi*freq*t)

freq = 4 # частота сигнала
x += np.sin(2*np.pi*freq*t + 10)

freq = 7 # частота сигнала
x += 0.5*np.sin(2*np.pi*freq*t + 10)

plt.figure(figsize=(9, 9))
plt.subplot(212)
plt.plot(t, x, 'b')
plt.ylabel('Амплитуда')

plt.xlabel('Время')
plt.show()


X = DFT(x)
N = len(X)
n = np.arange(N)
T = N/sr
freq = n/T

plt.figure(figsize=(8, 6))
plt.stem(freq, abs(X), 'b', markerfmt=' ', basefmt='-b')

plt.xlabel('Частота (Гц)')
plt.ylabel('Амплитуда DFT')
plt.show()
    '''
    pc.copy(text)
    
def links():
    text='''
https://drive.google.com/drive/folders/1KA-ROqqSW9ajDWfvd5va12WkDdbwdg?usp=sharing
https://github.com/amkatrutsa/nla2019_ozon/blob/master/lectures/lecture8/lecture-8.ipynb
    '''
    pc.copy(text)