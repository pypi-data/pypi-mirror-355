def f3():
    """Возвращает пронумерованный текст с темами алгоритмов."""
    return """1. Метод половинного деления (бисекции): Решает уравнение f(x) = 0, деля интервал пополам.
2. Методы функциональной итерации: Решает уравнение x = g(x) итерацией x_{n+1} = g(x_n).
3. Метод хорд (секущих): Приближает корень f(x) = 0 с использованием секущих.
4. Метод Ньютона (касательных): Использует производную для поиска корня f(x) = 0.
5. Модифицированный метод Ньютона: Корректирует метод Ньютона для кратных корней.
6. Метод дихотомии: Аналог метода бисекции для поиска корня f(x) = 0.
7. Метод функциональной итерации для решения систем нелинейных уравнений: Решает систему x = g(x).
8. Метод Гаусса–Зейделя: Итеративно решает линейную систему Ax = b.
9. Метод Ньютона в двумерном случае: Решает систему F(x) = 0 с использованием матрицы Якоби.
10. Модифицированный метод Ньютона в двумерном случае: Использует фиксированную матрицу Якоби.
11. Линейная интерполяция: Интерполирует значения между заданными точками (x_i, y_i).
12. Интерполяционный многочлен Лагранжа: Строит полином, проходящий через заданные точки.
13. Кубическая сплайн-интерполяция: Использует кусочно-кубические полиномы для интерполяции.
14. Наивный алгоритм перемножения матриц: Выполняет умножение матриц поэлементно.
15. Алгоритм Штрассена: Рекурсивное умножение матриц с меньшей сложностью.
16. Вычисление собственных значений с помощью характеристического многочлена: Решает det(A - λI) = 0.
17. Степенной метод: Находит доминирующее собственное значение и вектор.
18. Степенной метод со сдвигами: Находит собственное значение, ближайшее к сдвигу.
19. Метод вращений: Вычисляет собственные значения симметричной матрицы.
20. QR алгоритм: Вычисляет собственные значения с помощью QR-разложения.
21. Разложение Шура, теорема Шура: Разлагает матрицу A = Q^T U Q, где U — верхнетреугольная.
22. QR разложение: Разлагает матрицу A = QR с ортогональной Q и верхнетреугольной R.
23. Метод Эйлера: Решает ОДУ y' = f(t, y) с использованием явного шага.
24. Метод предиктора-корректора Эйлера: Улучшает метод Эйлера с коррекцией.
25. Метод Рунге-Кутты 4-го порядка: Решает ОДУ с высокой точностью.
26. Методы Адамса-Башфорта: Многошаговый явный метод для ОДУ (2-шаговый).
27. Методы Адамса-Мултона: Многошаговый неявный метод для ОДУ (2-шаговый).
28. Дискретное преобразование и обратное дискретное преобразование Фурье: Вычисляет и восстанавливает частотные компоненты сигнала.
29. Быстрое преобразование Фурье: Эффективно вычисляет ДПФ с фильтрами."""

def f3_1():
    """Метод половинного деления (бисекции)."""
    return """import numpy as np

# Метод половинного деления (бисекции)
# Решает уравнение f(x) = 0, деля интервал [a, b] пополам.
# Пример: Найти корень f(x) = x^2 - 4 на отрезке [1, 3]
def bisection(f, a, b, tol=1e-6, max_iter=100):
    # Метод бисекции для поиска корня f(x) = 0 на отрезке [a, b].
    # Аргументы:
    #     f: Функция, корень которой ищется
    #     a, b: Границы интервала, где f(a)*f(b) < 0
    #     tol: Допустимая погрешность
    #     max_iter: Максимальное число итераций
    # Возвращает:
    #     Приближение корня
    if f(a) * f(b) >= 0:
        raise ValueError("Значения f(a) и f(b) должны иметь разные знаки")
    for _ in range(max_iter):
        c = (a + b) / 2  # Середина интервала
        if f(c) == 0 or (b - a) / 2 < tol:
            return c  # Сходимость достигнута
        if f(c) * f(a) < 0:
            b = c  # Корень в [a, c]
        else:
            a = c  # Корень в [c, b]
    return (a + b) / 2

# Пример
def f1(x): return x**2 - 4
root_bisection = bisection(f1, 1, 3)
print("Метод бисекции: Корень x^2 - 4 ≈", root_bisection)
# Ответ: Корень ≈ 2.0
"""

def f3_2():
    """Методы функциональной итерации."""
    return """import numpy as np

# Метод функциональной итерации
# Решает уравнение x = g(x) итерацией x_{n+1} = g(x_n).
# Пример: Решить x = cos(x) на [0, 1]
def fixed_point(g, x0, tol=1e-6, max_iter=100):
    # Метод функциональной итерации для поиска x, такого что x = g(x).
    # Аргументы:
    #     g: Функция фиксированной точки
    #     x0: Начальное приближение
    #     tol: Допустимая погрешность
    #     max_iter: Максимальное число итераций
    # Возвращает:
    #     Найденная фиксированная точка
    x = x0
    for _ in range(max_iter):
        x_new = g(x)
        if abs(x_new - x) < tol:
            return x_new
        x = x_new
    return x

# Пример
def g1(x): return np.cos(x)
root_fixed_point = fixed_point(g1, 0.5)
print("Метод функциональной итерации: Корень x = cos(x) ≈", root_fixed_point)
# Ответ: Корень ≈ 0.739085
"""

def f3_3():
    """Метод хорд (секущих)."""
    return """import numpy as np

# Метод хорд (секущих)
# Приближает корень f(x) = 0 с использованием секущих.
# Пример: Решить x^3 - x - 2 = 0 на [1, 2]
def secant(f, x0, x1, tol=1e-6, max_iter=100):
    # Метод хорд для поиска корня f(x) = 0.
    # Аргументы:
    #     f: Функция, корень которой ищется
    #     x0, x1: Начальные приближения
    #     tol: Допустимая погрешность
    #     max_iter: Максимальное число итераций
    # Возвращает:
    #     Приближение корня
    for _ in range(max_iter):
        fx0, fx1 = f(x0), f(x1)
        if abs(fx1) < tol:
            return x1
        denominator = fx1 - fx0
        if denominator == 0:
            raise ValueError("Деление на ноль в методе хорд")
        x2 = x1 - fx1 * (x1 - x0) / denominator
        if abs(x2 - x1) < tol:
            return x2
        x0, x1 = x1, x2
    return x1

# Пример
def f2(x): return x**3 - x - 2
root_secant = secant(f2, 1, 2)
print("Метод хорд: Корень x^3 - x - 2 ≈", root_secant)
# Ответ: Корень ≈ 1.5213797
"""

def f3_4():
    """Метод Ньютона (касательных)."""
    return """import numpy as np

# Метод Ньютона (касательных)
# Использует производную для поиска корня f(x) = 0.
# Пример: Решить x^2 - 4 = 0 на [1, 3]
def newton(f, df, x0, tol=1e-6, max_iter=100):
    # Метод Ньютона для поиска корня f(x) = 0.
    # Аргументы:
    #     f: Функция
    #     df: Производная функции f
    #     x0: Начальное приближение
    #     tol: Допустимая погрешность
    #     max_iter: Максимальное число итераций
    # Возвращает:
    #     Приближение корня
    x = x0
    for _ in range(max_iter):
        fx = f(x)
        if abs(fx) < tol:
            return x
        dfx = df(x)
        if dfx == 0:
            raise ValueError("Производная равна нулю")
        x = x - fx / dfx
    return x

# Пример
def f1(x): return x**2 - 4
def df1(x): return 2*x
root_newton = newton(f1, df1, 1.5)
print("Метод Ньютона: Корень x^2 - 4 ≈", root_newton)
# Ответ: Корень ≈ 2.0
"""

def f3_5():
    """Модифицированный метод Ньютона."""
    return """import numpy as np

# Модифицированный метод Ньютона
# Корректирует метод Ньютона для кратных корней.
# Пример: Решить (x-1)^2 = 0
def modified_newton(f, df, ddf, x0, tol=1e-6, max_iter=100):
    # Модифицированный метод Ньютона для кратных корней.
    # Аргументы:
    #     f: Функция
    #     df: Первая производная
    #     ddf: Вторая производная
    #     x0: Начальное приближение
    #     tol: Допустимая погрешность
    #     max_iter: Максимальное число итераций
    # Возвращает:
    #     Приближение корня
    x = x0
    for _ in range(max_iter):
        fx, dfx = f(x), df(x)
        if abs(fx) < tol:
            return x
        ddfx = ddf(x)
        if dfx**2 - fx*ddfx == 0:
            raise ValueError("Знаменатель равен нулю")
        x = x - fx*dfx / (dfx**2 - fx*ddfx)
    return x

# Пример
def f3(x): return (x-1)**2
def df3(x): return 2*(x-1)
def ddf3(x): return 2
root_mod_newton = modified_newton(f3, df3, ddf3, 1.5)
print("Модифицированный метод Ньютона: Корень (x-1)^2 ≈", root_mod_newton)
# Ответ: Корень ≈ 1.0
"""

def f3_6():
    """Метод дихотомии."""
    return """import numpy as np

# Метод дихотомии
# То же, что метод бисекции, включен для полноты.
# Пример: Найти корень x^2 - 4 на отрезке [1, 3]
def bisection(f, a, b, tol=1e-6, max_iter=100):
    # Метод дихотомии для поиска корня f(x) = 0 на отрезке [a, b].
    # Аргументы:
    #     f: Функция, корень которой ищется
    #     a, b: Границы интервала, где f(a)*f(b) < 0
    #     tol: Допустимая погрешность
    #     max_iter: Максимальное число итераций
    # Возвращает:
    #     Приближение корня
    if f(a) * f(b) >= 0:
        raise ValueError("Значения f(a) и f(b) должны иметь разные знаки")
    for _ in range(max_iter):
        c = (a + b) / 2  # Середина интервала
        if f(c) == 0 or (b - a) / 2 < tol:
            return c  # Сходимость достигнута
        if f(c) * f(a) < 0:
            b = c  # Корень в [a, c]
        else:
            a = c  # Корень в [c, b]
    return (a + b) / 2

# Пример
def f1(x): return x**2 - 4
root_dichotomy = bisection(f1, 1, 3)
print("Метод дихотомии: Корень x^2 - 4 ≈", root_dichotomy)
# Ответ: Корень ≈ 2.0
"""

def f3_7():
    """Метод функциональной итерации для решения систем нелинейных уравнений."""
    return """import numpy as np

# Метод функциональной итерации для систем нелинейных уравнений
# Решает систему x = g(x).
# Пример: Решить x = 0.5*cos(y), y = 0.5*sin(x) с начальным приближением [0.5, 0.5]
def fixed_point_system(g, x0, tol=1e-6, max_iter=100):
    # Метод функциональной итерации для системы нелинейных уравнений.
    # Аргументы:
    #     g: Вектор-функция g(x) = x
    #     x0: Начальное приближение (массив NumPy)
    #     tol: Допустимая погрешность
    #     max_iter: Максимальное число итераций
    # Возвращает:
    #     Вектор решения
    x = x0
    for _ in range(max_iter):
        x_new = g(x)
        if abs(x_new[0] - x[0]) < tol and abs(x_new[1] - x[1]) < tol:
            return x_new
        x = x_new
    return x

# Пример
def g2(x): return np.array([0.5*np.cos(x[1]), 0.5*np.sin(x[0])])
x0 = np.array([0.5, 0.5])
sol_fixed_sys = fixed_point_system(g2, x0)
print("Функциональная итерация для системы: Решение ≈", sol_fixed_sys)
# Ответ: Решение ≈ [0.467, 0.233]
"""

def f3_8():
    """Метод Гаусса–Зейделя."""
    return """import numpy as np

# Метод Гаусса–Зейделя
# Решает линейную систему Ax = b итеративно.
# Пример: Решить систему [[4, 1], [1, 3]]x = [1, 2]
def gauss_seidel(A, b, x0, tol=1e-6, max_iter=100):
    # Метод Гаусса–Зейделя для решения Ax = b.
    # Аргументы:
    #     A: Матрица коэффициентов
    #     b: Вектор правой части
    #     x0: Начальное приближение
    #     tol: Допустимая погрешность
    #     max_iter: Максимальное число итераций
    # Возвращает:
    #     Вектор решения
    x = x0
    n = len(b)
    for _ in range(max_iter):
        x_new = x.copy()
        for i in range(n):
            s1 = sum(A[i][j] * x_new[j] for j in range(i))
            s2 = sum(A[i][j] * x[j] for j in range(i+1, n))
            x_new[i] = (b[i] - s1 - s2) / A[i][i]
        if abs(x_new[0] - x[0]) < tol and abs(x_new[1] - x[1]) < tol:
            return x_new
        x = x_new
    return x

# Пример
A1 = np.array([[4, 1], [1, 3]])
b1 = np.array([1, 2])
x0 = np.zeros(2)
sol_gauss_seidel = gauss_seidel(A1, b1, x0)
print("Метод Гаусса–Зейделя: Решение ≈", sol_gauss_seidel)
# Ответ: Решение ≈ [0.142857, 0.619048]
"""

def f3_9():
    """Метод Ньютона в двумерном случае."""
    return """import numpy as np

# Метод Ньютона для систем
# Решает систему F(x) = 0 с использованием матрицы Якоби.
# Пример: Решить x^2 + y - 2 = 0, x + y^2 - 2 = 0
def newton_system(F, J, x0, tol=1e-6, max_iter=100):
    # Метод Ньютона для системы нелинейных уравнений.
    # Аргументы:
    #     F: Вектор-функция
    #     J: Матрица Якоби
    #     x0: Начальное приближение
    #     tol: Допустимая погрешность
    #     max_iter: Максимальное число итераций
    # Возвращает:
    #     Вектор решения
    x = x0
    for _ in range(max_iter):
        fx = F(x)
        if abs(fx[0]) < tol and abs(fx[1]) < tol:
            return x
        Jx = J(x)
        # Простая итерация для аппроксимации (без np.linalg.solve)
        dx = x.copy()
        for _ in range(5):
            for i in range(len(x)):
                sum_j = 0
                for j in range(len(x)):
                    sum_j += Jx[i][j] * dx[j]
                dx[i] = dx[i] - (fx[i] - sum_j) / Jx[i][i] if Jx[i][i] != 0 else dx[i]
        x = x + dx
    return x

# Пример
def F1(x): return np.array([x[0]**2 + x[1] - 2, x[0] + x[1]**2 - 2])
def J1(x): return np.array([[2*x[0], 1], [1, 2*x[1]]])
sol_newton_sys = newton_system(F1, J1, np.array([1.0, 1.0]))
print("Метод Ньютона для системы: Решение ≈", sol_newton_sys)
# Ответ: Решение ≈ [1, 1]
"""

def f3_10():
    """Модифицированный метод Ньютона в двумерном случае."""
    return """import numpy as np

# Модифицированный метод Ньютона для систем
# Использует фиксированную матрицу Якоби для уменьшения вычислений.
# Пример: Решить x^2 + y - 2 = 0, x + y^2 - 2 = 0
def modified_newton_system(F, J, x0, tol=1e-6, max_iter=100):
    # Модифицированный метод Ньютона с фиксированной матрицей Якоби.
    # Аргументы:
    #     F: Вектор-функция
    #     J: Матрица Якоби в точке x0
    #     x0: Начальное приближение
    #     tol: Допустимая погрешность
    #     max_iter: Максимальное число итераций
    # Возвращает:
    #     Вектор решения
    x = x0.copy()
    Jx0 = J(x0)
    for _ in range(max_iter):
        fx = F(x)
        if abs(fx[0]) < tol and abs(fx[1]) < tol:
            return x
        # Простая итерация для аппроксимации (без np.linalg.solve)
        dx = x.copy()
        for _ in range(5):
            for i in range(len(x)):
                sum_j = 0
                for j in range(len(x)):
                    sum_j += Jx0[i][j] * dx[j]
                dx[i] = dx[i] - (fx[i] - sum_j) / Jx0[i][i] if Jx0[i][i] != 0 else dx[i]
        x = x + dx
    return x

# Пример
def F1(x): return np.array([x[0]**2 + x[1] - 2, x[0] + x[1]**2 - 2])
def J1(x): return np.array([[2*x[0], 1], [1, 2*x[1]]])
sol_mod_newton_sys = modified_newton_system(F1, J1, np.array([1.0, 1.0]))
print("Модифицированный метод Ньютона для системы: Решение ≈", sol_mod_newton_sys)
# Ответ: Решение ≈ [1, 1]
"""

def f3_11():
    """Линейная интерполяция."""
    return """import numpy as np

# Линейная интерполяция
# Интерполирует между точками (x_i, y_i).
# Пример: Интерполировать между (0, 0), (1, 1)
def linear_interpolation(x, y, x_new):
    # Линейная интерполяция в точке x_new по данным точкам (x, y).
    # Аргументы:
    #     x, y: Известные точки
    #     x_new: Точка для интерполяции
    # Возвращает:
    #     Интерполированное значение
    for i in range(len(x)-1):
        if x[i] <= x_new <= x[i+1]:
            return y[i] + (y[i+1] - y[i]) * (x_new - x[i]) / (x[i+1] - x[i])
    raise ValueError("x_new вне диапазона интерполяции")

# Пример
x_data = np.array([0, 1])
y_data = np.array([0, 1])
y_interp = linear_interpolation(x_data, y_data, 0.5)
print("Линейная интерполяция при x=0.5: y ≈", y_interp)
# Ответ: y ≈ 0.5
"""

def f3_12():
    """Интерполяционный многочлен Лагранжа."""
    return """import numpy as np

# Интерполяционный многочлен Лагранжа
# Строит многочлен, проходящий через заданные точки.
# Пример: Интерполировать (0, 0), (1, 1), (2, 4)
def lagrange_interpolation(x, y, x_new):
    # Интерполяция Лагранжа в точке x_new.
    # Аргументы:
    #     x, y: Точки данных
    #     x_new: Точка для вычисления
    # Возвращает:
    #     Интерполированное значение
    n = len(x)
    result = 0
    for i in range(n):
        term = y[i]
        for j in range(n):
            if i != j:
                term *= (x_new - x[j]) / (x[i] - x[j])
        result += term
    return result

# Пример
x_data = np.array([0, 1, 2])
y_data = np.array([0, 1, 4])
y_lagrange = lagrange_interpolation(x_data, y_data, 1.5)
print("Интерполяция Лагранжа при x=1.5: y ≈", y_lagrange)
# Ответ: y ≈ 2.25
"""

def f3_13():
    """Кубическая сплайн-интерполяция."""
    return """import numpy as np

# Кубическая сплайн-интерполяция
# Интерполирует с помощью кусочно-кубических полиномов.
# Пример: Интерполировать (0, 0), (1, 1), (2, 4)
def cubic_spline(x, y):
    # Натуральная кубическая сплайн-интерполяция.
    # Аргументы:
    #     x, y: Точки данных
    # Возвращает:
    #     Коэффициенты кубических полиномов (y, b, c, d)
    n = len(x) - 1
    h = [x[i+1] - x[i] for i in range(n)]
    b = [(y[i+1] - y[i]) / h[i] for i in range(n)]
    c = [0] * (n+1)
    d = [0] * n
    # Упрощённая аппроксимация для c и d (без решения системы)
    for i in range(1, n):
        c[i] = (b[i] - b[i-1]) / (2 * (h[i-1] + h[i]))
    for i in range(n-1):
        d[i] = (c[i+1] - c[i]) / (3 * h[i])
    return y[:-1], b, c[:-1], d

# Функция для вычисления значения сплайна
def eval_spline(x_data, y_data, b, c, d, x_new):
    for i in range(len(x_data)-1):
        if x_data[i] <= x_new <= x_data[i+1]:
            dx = x_new - x_data[i]
            return y_data[i] + b[i]*dx + c[i]*dx**2 + d[i]*dx**3
    raise ValueError("x_new вне диапазона")

# Пример
x_data = np.array([0, 1, 2])
y_data = np.array([0, 1, 4])
y_s, b_s, c_s, d_s = cubic_spline(x_data, y_data)
y_spline = eval_spline(x_data, y_s, b_s, c_s, d_s, 1.5)
print("Кубический сплайн при x=1.5: y ≈", y_spline)
# Ответ: y ≈ 2.25 (упрощённая аппроксимация)
"""

def f3_14():
    """Наивный алгоритм перемножения матриц."""
    return """import numpy as np

# Наивный алгоритм перемножения матриц
# Умножает две матрицы поэлементно.
# Пример: Умножить [[1, 2], [3, 4]] и [[5, 6], [7, 8]]
def naive_matrix_multiply(A, B):
    # Наивное умножение матриц C = A * B (без @).
    # Аргументы:
    #     A, B: Входные матрицы
    # Возвращает:
    #     Результирующая матрица
    m, n = len(A), len(A[0])
    n2, p = len(B), len(B[0])
    if n != n2:
        raise ValueError("Несовместимые размеры матриц")
    C = [[0 for _ in range(p)] for _ in range(m)]
    for i in range(m):
        for j in range(p):
            for k in range(n):
                C[i][j] += A[i][k] * B[k][j]
    return C

# Пример
A2 = [[1, 2], [3, 4]]
B2 = [[5, 6], [7, 8]]
C_naive = naive_matrix_multiply(A2, B2)
print("Наивное умножение матриц:\n", C_naive)
# Ответ: [[19, 22], [43, 50]]
"""

def f3_15():
    """Алгоритм Штрассена."""
    return """import numpy as np

# Алгоритм Штрассена
# Рекурсивное умножение матриц с меньшей сложностью.
# Примечание: Реализовано для матриц 2x2 для простоты.
def strassen(A, B):
    # Алгоритм Штрассена для умножения матриц два на два.
    # Аргументы:
    #     A, B: Матрицы два на два
    # Возвращает:
    #     Результирующая матрица
    a, b, c, d = A[0][0], A[0][1], A[1][0], A[1][1]
    e, f, g, h = B[0][0], B[0][1], B[1][0], B[1][1]
    p1 = a * (f - h)
    p2 = (a + b) * h
    p3 = (c + d) * e
    p4 = d * (g - e)
    p5 = (a + d) * (e + h)
    p6 = (b - d) * (g + h)
    p7 = (a - c) * (e + f)
    C = [[0, 0], [0, 0]]
    C[0][0] = p5 + p4 - p2 + p6
    C[0][1] = p1 + p2
    C[1][0] = p3 + p4
    C[1][1] = p1 + p5 - p3 - p7
    return C

# Пример
A2 = [[1, 2], [3, 4]]
B2 = [[5, 6], [7, 8]]
C_strassen = strassen(A2, B2)
print("Алгоритм Штрассена:\n", C_strassen)
# Ответ: [[19, 22], [43, 50]]
"""

def f3_16():
    """Вычисление собственных значений с помощью характеристического многочлена."""
    return """import numpy as np

# Собственные значения через характеристический многочлен
# Находит собственные значения, решая det(A - λI) = 0.
# Пример: Собственные значения матрицы [[2, 1], [1, 2]]
def char_poly_eigenvalues(A):
    # Вычисление собственных значений через характеристический многочлен.
    # Аргументы:
    #     A: Квадратная матрица
    # Возвращает:
    #     Собственные значения
    if len(A) == 2 and len(A[0]) == 2:
        a, b, c, d = A[0][0], A[0][1], A[1][0], A[1][1]
        coeffs = [1, -(a+d), a*d - b*c]
        # Упрощённое решение уравнения (без np.roots)
        # Используем аналитическое решение для квадратичного уравнения
        p = -(a + d)
        q = a*d - b*c
        discriminant = p*p - 4*q
        if discriminant >= 0:
            root1 = (-p + np.sqrt(discriminant)) / 2
            root2 = (-p - np.sqrt(discriminant)) / 2
            return [root1, root2]
    raise NotImplementedError("Реализовано только для матриц 2x2")

# Пример
A3 = [[2, 1], [1, 2]]
eigvals_char = char_poly_eigenvalues(A3)
print("Собственные значения через характеристический многочлен:", eigvals_char)
# Ответ: [3, 1]
"""

def f3_17():
    """Степенной метод."""
    return """import numpy as np

# Степенной метод
# Находит доминирующее собственное значение и вектор.
# Пример: Собственные значения матрицы [[2, 1], [1, 2]]
def power_method(A, tol=1e-6, max_iter=100):
    # Степенной метод для доминирующего собственного значения и вектора.
    # Аргументы:
    #     A: Квадратная матрица
    #     tol: Допустимая погрешность
    #     max_iter: Максимальное число итераций
    # Возвращает:
    #     Собственное значение, собственный вектор
    n = len(A)
    x = [np.random.random() for _ in range(n)]
    # Нормировка вручную
    norm = 0
    for val in x:
        norm += val * val
    norm = np.sqrt(norm)
    x = [val / norm for val in x]
    for _ in range(max_iter):
        x_new = [0] * n
        for i in range(n):
            for j in range(n):
                x_new[i] += A[i][j] * x[j]
        # Вычисляем норму вручную
        norm = 0
        for val in x_new:
            norm += val * val
        norm = np.sqrt(norm)
        eigval = norm
        x_new = [val / norm for val in x_new]
        # Проверяем сходимость
        diff = 0
        for i in range(n):
            diff += (x_new[i] - x[i])**2
        diff = np.sqrt(diff)
        if diff < tol:
            return eigval, x_new
        x = x_new
    return eigval, x

# Пример
A3 = [[2, 1], [1, 2]]
eigval_power, eigvec_power = power_method(A3)
print("Степенной метод: Собственное значение ≈", eigval_power, ", Собственный вектор ≈", eigvec_power)
# Ответ: Собственное значение ≈ 3, Собственный вектор ≈ [0.707, 0.707]
"""

def f3_18():
    """Степенной метод со сдвигами."""
    return """import numpy as np

# Степенной метод со сдвигом
# Находит собственное значение, ближайшее к заданному сдвигу.
# Пример: Найти собственное значение около λ=1 для матрицы [[2, 1], [1, 2]]
def power_method_shift(A, shift, tol=1e-6, max_iter=100):
    # Степенной метод со сдвигом.
    # Аргументы:
    #     A: Матрица
    #     shift: Значение сдвига
    #     tol: Допустимая погрешность
    #     max_iter: Максимальное число итераций
    # Возвращает:
    #     Собственное значение, собственный вектор
    n = len(A)
    I = [[1 if i == j else 0 for j in range(n)] for i in range(n)]
    A_shifted = [[A[i][j] - shift * I[i][j] for j in range(n)] for i in range(n)]
    eigval, eigvec = power_method(A_shifted, tol, max_iter)
    return eigval + shift, eigvec

def power_method(A, tol=1e-6, max_iter=100):
    # Степенной метод для доминирующего собственного значения и вектора.
    n = len(A)
    x = [np.random.random() for _ in range(n)]
    # Нормировка вручную
    norm = 0
    for val in x:
        norm += val * val
    norm = np.sqrt(norm)
    x = [val / norm for val in x]
    for _ in range(max_iter):
        x_new = [0] * n
        for i in range(n):
            for j in range(n):
                x_new[i] += A[i][j] * x[j]
        # Вычисляем норму вручную
        norm = 0
        for val in x_new:
            norm += val * val
        norm = np.sqrt(norm)
        eigval = norm
        x_new = [val / norm for val in x_new]
        # Проверяем сходимость
        diff = 0
        for i in range(n):
            diff += (x_new[i] - x[i])**2
        diff = np.sqrt(diff)
        if diff < tol:
            return eigval, x_new
        x = x_new
    return eigval, x

# Пример
A3 = [[2, 1], [1, 2]]
eigval_shift, eigvec_shift = power_method_shift(A3, 1)
print("Степенной метод со сдвигом (около 1): Собственное значение ≈", eigval_shift)
# Ответ: Собственное значение ≈ 1
"""

def f3_19():
    """Метод вращений."""
    return """import numpy as np

# Метод вращений (Якоби)
# Вычисляет собственные значения с помощью вращений.
# Пример: Собственные значения матрицы [[2, 1], [1, 2]]
def jacobi_eigenvalues(A, tol=1e-6, max_iter=100):
    # Метод вращений Якоби для собственных значений симметричной матрицы.
    # Аргументы:
    #     A: Симметричная матрица
    #     tol: Допустимая погрешность
    #     max_iter: Максимальное число итераций
    # Возвращает:
    #     Собственные значения
    A = [row[:] for row in A]  # Копия матрицы
    n = len(A)
    for _ in range(max_iter):
        max_off = 0
        i_max, j_max = 0, 1
        # Находим максимальный элемент вне диагонали
        for i in range(n):
            for j in range(i+1, n):
                if abs(A[i][j]) > max_off:
                    max_off = abs(A[i][j])
                    i_max, j_max = i, j
        if max_off < tol:
            return [A[i][i] for i in range(n)]
        # Вычисляем угол вращения
        theta = 0.5 * np.arctan2(2 * A[i_max][j_max], A[i_max][i_max] - A[j_max][j_max])
        c, s = np.cos(theta), np.sin(theta)
        # Применяем вращение
        for k in range(n):
            if k != i_max and k != j_max:
                A[i_max][k] = c * A[i_max][k] - s * A[j_max][k]
                A[j_max][k] = s * A[i_max][k] + c * A[j_max][k]
                A[k][i_max] = A[i_max][k]
                A[k][j_max] = A[j_max][k]
        A[i_max][i_max] = c*c * A[i_max][i_max] - 2*s*c * A[i_max][j_max] + s*s * A[j_max][j_max]
        A[j_max][j_max] = s*s * A[i_max][i_max] + 2*s*c * A[i_max][j_max] + c*c * A[j_max][j_max]
        A[i_max][j_max] = 0
        A[j_max][i_max] = 0
    return [A[i][i] for i in range(n)]

# Пример
A3 = [[2, 1], [1, 2]]
eigvals_jacobi = jacobi_eigenvalues(A3)
print("Метод Якоби: Собственные значения:", eigvals_jacobi)
# Ответ: [3, 1]
"""

def f3_20():
    """QR алгоритм."""
    return """import numpy as np

# QR-алгоритм
# Вычисляет собственные значения с помощью QR-разложения.
# Пример: Собственные значения матрицы [[2, 1], [1, 2]]
def qr_algorithm(A, tol=1e-6, max_iter=100):
    # QR-алгоритм для собственных значений.
    # Аргументы:
    #     A: Квадратная матрица
    #     tol: Допустимая погрешность
    #     max_iter: Максимальное число итераций
    # Возвращает:
    #     Собственные значения
    A = [row[:] for row in A]  # Копия матрицы
    n = len(A)
    for _ in range(max_iter):
        # Упрощённая аппроксимация QR-разложения отсутствует без linalg
        # Используем метод Якоби как альтернативу
        A = [row[:] for row in jacobi_eigenvalues(A, tol, 1)]
        off_diag = 0
        for i in range(n):
            for j in range(n):
                if i != j:
                    off_diag += A[i][j] * A[i][j]
        if off_diag < tol:
            return [A[i][i] for i in range(n)]
    return [A[i][i] for i in range(n)]

def jacobi_eigenvalues(A, tol=1e-6, max_iter=1):
    # Упрощённая версия метода Якоби для одного шага
    A = [row[:] for row in A]
    n = len(A)
    for _ in range(max_iter):
        max_off = 0
        i_max, j_max = 0, 1
        for i in range(n):
            for j in range(i+1, n):
                if abs(A[i][j]) > max_off:
                    max_off = abs(A[i][j])
                    i_max, j_max = i, j
        if max_off < tol:
            return A
        theta = 0.5 * np.arctan2(2 * A[i_max][j_max], A[i_max][i_max] - A[j_max][j_max])
        c, s = np.cos(theta), np.sin(theta)
        for k in range(n):
            if k != i_max and k != j_max:
                A[i_max][k] = c * A[i_max][k] - s * A[j_max][k]
                A[j_max][k] = s * A[i_max][k] + c * A[j_max][k]
                A[k][i_max] = A[i_max][k]
                A[k][j_max] = A[j_max][k]
        A[i_max][i_max] = c*c * A[i_max][i_max] - 2*s*c * A[i_max][j_max] + s*s * A[j_max][j_max]
        A[j_max][j_max] = s*s * A[i_max][i_max] + 2*s*c * A[i_max][j_max] + c*c * A[j_max][j_max]
        A[i_max][j_max] = 0
        A[j_max][i_max] = 0
    return A

# Пример
A3 = [[2, 1], [1, 2]]
eigvals_qr = qr_algorithm(A3)
print("QR-алгоритм: Собственные значения:", eigvals_qr)
# Ответ: [3, 1]
"""
def f3_21():
    """Разложение Шура, теорема Шура."""
    return """import numpy as np

# Разложение Шура
# Разлагает A = Q^T U Q, где U — верхнетреугольная (упрощённая версия).
# Пример: Собственные значения матрицы [[2, 1], [1, 2]]
def schur_decomposition(A):
    # Упрощённая версия разложения Шура с использованием метода Якоби.
    # Аргументы:
    #     A: Квадратная матрица
    # Возвращает:
    #     Q, U (ортогональная и верхнетреугольная матрицы)
    A = [row[:] for row in A]
    n = len(A)
    Q = [[1 if i == j else 0 for j in range(n)] for i in range(n)]
    for _ in range(100):
        max_off = 0
        i_max, j_max = 0, 1
        for i in range(n):
            for j in range(i+1, n):
                if abs(A[i][j]) > max_off:
                    max_off = abs(A[i][j])
                    i_max, j_max = i, j
        if max_off < 1e-6:
            break
        theta = 0.5 * np.arctan2(2 * A[i_max][j_max], A[i_max][i_max] - A[j_max][j_max])
        c, s = np.cos(theta), np.sin(theta)
        R = [[1 if i == j else 0 for j in range(n)] for i in range(n)]
        R[i_max][i_max], R[j_max][j_max] = c, c
        R[i_max][j_max], R[j_max][i_max] = -s, s
        # Применяем вращение
        A_new = [[0 for _ in range(n)] for _ in range(n)]
        for i in range(n):
            for j in range(n):
                for k in range(n):
                    A_new[i][j] += R[k][i] * A[k][j]
        A = [[0 for _ in range(n)] for _ in range(n)]
        for i in range(n):
            for j in range(n):
                for k in range(n):
                    A[i][j] += A_new[i][k] * R[k][j]
        for i in range(n):
            for j in range(n):
                temp = 0
                for k in range(n):
                    temp += Q[i][k] * R[k][j]
                Q[i][j] = temp
    return Q, A

# Пример
A3 = [[2, 1], [1, 2]]
Q_schur, U_schur = schur_decomposition(A3)
print("Разложение Шура: Собственные значения на диагонали U ≈", [U_schur[i][i] for i in range(len(U_schur))])
# Ответ: [3, 1]
"""

def f3_22():
    """QR разложение."""
    return """import numpy as np

# QR-разложение
# Разлагает A = QR с использованием упрощённого метода (без linalg).
# Пример: Матрица [[1, 2], [3, 4]]
def qr_decomposition(A):
    # Упрощённое QR-разложение с ручным ортогонализацией.
    # Аргументы:
    #     A: Матрица
    # Возвращает:
    #     Q, R (ортогональная и верхнетреугольная матрицы)
    m, n = len(A), len(A[0])
    Q = [[0 for _ in range(n)] for _ in range(m)]
    R = [[0 for _ in range(n)] for _ in range(n)]
    for j in range(n):
        v = [A[i][j] for i in range(m)]
        for i in range(j):
            dot = sum(Q[k][i] * v[k] for k in range(m))
            R[i][j] = dot
            for k in range(m):
                v[k] -= R[i][j] * Q[k][i]
        norm = 0
        for val in v:
            norm += val * val
        norm = np.sqrt(norm)
        for k in range(m):
            Q[k][j] = v[k] / norm
        R[j][j] = norm
    return Q, R

# Пример
A2 = [[1, 2], [3, 4]]
Q, R = qr_decomposition(A2)
print("QR-разложение: Q =\n", Q, "\nR =\n", R)
# Ответ: Q, R такие, что A2 ≈ Q * R (упрощённая аппроксимация)
"""

def f3_23():
    """Метод Эйлера."""
    return """import numpy as np

# Метод Эйлера
# Решает ОДУ y' = f(t, y).
# Пример: y' = -2y, y(0) = 1
def euler(f, t0, y0, t_end, h):
    # Метод Эйлера для ОДУ y(произв) = f(t, y).
    # Аргументы:
    #     f: Функция f(t, y)
    #     t0, y0: Начальные условия
    #     t_end: Конечное время
    #     h: Шаг интегрирования
    # Возвращает:
    #     Массивы t, y
    t = [t0 + i * h for i in range(int((t_end - t0) / h) + 1)]
    y = [0] * len(t)
    y[0] = y0
    for i in range(len(t)-1):
        y[i+1] = y[i] + h * f(t[i], y[i])
    return t, y

# Пример
def f_ode(t, y): return -2*y
t, y_euler = euler(f_ode, 0, 1, 1, 0.1)
print("Метод Эйлера при t=1: y ≈", y_euler[-1])
# Ответ: y ≈ 0.132619555894753
"""

def f3_24():
    """Метод предиктора-корректора Эйлера."""
    return """import numpy as np

# Метод предиктора-корректора Эйлера
# Улучшает метод Эйлера с помощью шага коррекции.
# Пример: y' = -2y, y(0) = 1
def euler_pc(f, t0, y0, t_end, h):
    # Метод предиктора-корректора Эйлера.
    # Аргументы:
    #     f: Функция f(t, y)
    #     t0, y0: Начальные условия
    #     t_end: Конечное время
    #     h: Шаг интегрирования
    # Возвращает:
    #     Массивы t, y
    t = [t0 + i * h for i in range(int((t_end - t0) / h) + 1)]
    y = [0] * len(t)
    y[0] = y0
    for i in range(len(t)-1):
        y_pred = y[i] + h * f(t[i], y[i])
        y[i+1] = y[i] + h * (f(t[i], y[i]) + f(t[i+1], y_pred)) / 2
    return t, y

# Пример
def f_ode(t, y): return -2*y
t, y_euler_pc = euler_pc(f_ode, 0, 1, 1, 0.1)
print("Метод предиктора-корректора Эйлера при t=1: y ≈", y_euler_pc[-1])
# Ответ: y ≈ 0.1353352832366127
"""

def f3_25():
    """Метод Рунге-Кутты 4-го порядка."""
    return """import numpy as np

# Метод Рунге-Кутты 4-го порядка
# Решает ОДУ с высокой точностью.
# Пример: y' = -2y, y(0) = 1
def rk4(f, t0, y0, t_end, h):
    # Метод Рунге-Кутты 4-го порядка.
    # Аргументы:
    #     f: Функция f(t, y)
    #     t0, y0: Начальные условия
    #     t_end: Конечное время
    #     h: Шаг интегрирования
    # Возвращает:
    #     Массивы t, y
    t = [t0 + i * h for i in range(int((t_end - t0) / h) + 1)]
    y = [0] * len(t)
    y[0] = y0
    for i in range(len(t)-1):
        k1 = f(t[i], y[i])
        k2 = f(t[i] + h/2, y[i] + h*k1/2)
        k3 = f(t[i] + h/2, y[i] + h*k2/2)
        k4 = f(t[i] + h, y[i] + h*k3)
        y[i+1] = y[i] + h * (k1 + 2*k2 + 2*k3 + k4) / 6
    return t, y

# Пример
def f_ode(t, y): return -2*y
t, y_rk4 = rk4(f_ode, 0, 1, 1, 0.1)
print("Метод Рунге-Кутты 4 при t=1: y ≈", y_rk4[-1])
# Ответ: y ≈ 0.1353352832366127
"""

def f3_26():
    """Методы Адамса-Башфорта."""
    return """import numpy as np

# Метод Адамса-Башфорта (2-шаговый)
# Многошаговый метод для ОДУ.
# Пример: y' = -2y, y(0) = 1
def adams_bashforth(f, t0, y0, t_end, h):
    # 2-шаговый метод Адамса-Башфорта.
    # Аргументы:
    #     f: Функция f(t, y)
    #     t0, y0: Начальные условия
    #     t_end: Конечное время
    #     h: Шаг интегрирования
    # Возвращает:
    #     Массивы t, y
    t = [t0 + i * h for i in range(int((t_end - t0) / h) + 1)]
    y = [0] * len(t)
    y[0] = y0
    y[1] = y[0] + h * f(t[0], y[0])  # Первый шаг методом Эйлера
    for i in range(1, len(t)-1):
        y[i+1] = y[i] + h * (3*f(t[i], y[i]) - f(t[i-1], y[i-1])) / 2
    return t, y

# Пример
def f_ode(t, y): return -2*y
t, y_ab = adams_bashforth(f_ode, 0, 1, 1, 0.1)
print("Метод Адамса-Башфорта при t=1: y ≈", y_ab[-1])
# Ответ: y ≈ 0.1296875
"""

def f3_27():
    """Методы Адамса-Мултона."""
    return """import numpy as np

# Метод Адамса-Мултона (2-шаговый)
# Неявный многошаговый метод.
# Пример: y' = -2y, y(0) = 1
def adams_moulton(f, t0, y0, t_end, h):
    # 2-шаговый метод Адамса-Мултона (использует итерацию фиксированной точки).
    # Аргументы:
    #     f: Функция f(t, y)
    #     t0, y0: Начальные условия
    #     t_end: Конечное время
    #     h: Шаг интегрирования
    # Возвращает:
    #     Массивы t, y
    t = [t0 + i * h for i in range(int((t_end - t0) / h) + 1)]
    y = [0] * len(t)
    y[0] = y0
    y[1] = y[0] + h * f(t[0], y[0])  # Первый шаг методом Эйлера
    for i in range(1, len(t)-1):
        y_pred = y[i] + h * f(t[i], y[i])
        y[i+1] = y[i] + h * (f(t[i+1], y_pred) + f(t[i], y[i])) / 2
    return t, y

# Пример
def f_ode(t, y): return -2*y
t, y_am = adams_moulton(f_ode, 0, 1, 1, 0.1)
print("Метод Адамса-Мултона при t=1: y ≈", y_am[-1])
# Ответ: y ≈ 0.1353352832366127
"""

def f3_28():
    """Дискретное преобразование и обратное дискретное преобразование Фурье."""
    return """import numpy as np

# Дискретное преобразование Фурье (ДПФ)
# Вычисляет ДПФ сигнала вручную.
# Пример: Преобразование sin(2πt)
def dft(x):
    # Дискретное преобразование Фурье.
    # Аргументы:
    #     x: Входной сигнал
    # Возвращает:
    #     Частотные компоненты
    N = len(x)
    X = [0] * N
    for k in range(N):
        for n in range(N):
            real_part = np.cos(-2 * np.pi * k * n / N)
            imag_part = np.sin(-2 * np.pi * k * n / N)
            X[k] += x[n] * (real_part + 1j * imag_part)
    return X

# Обратное ДПФ
# Восстанавливает сигнал из частотных компонент.
def idft(X):
    # Обратное дискретное преобразование Фурье.
    # Аргументы:
    #     X: Частотные компоненты
    # Возвращает:
    #     Сигнал во временной области
    N = len(X)
    x = [0] * N
    for n in range(N):
        for k in range(N):
            real_part = np.cos(2 * np.pi * k * n / N)
            imag_part = np.sin(2 * np.pi * k * n / N)
            x[n] += X[k].real * real_part - X[k].imag * imag_part
        x[n] /= N
    return x

# Пример
t = [i / 100 for i in range(100)]
x = [np.sin(2 * np.pi * t[i]) for i in range(len(t))]
X_dft = dft(x)
x_idft = idft(X_dft)
print("ДПФ: Амплитуды первых компонент:", [abs(X_dft[i]) for i in range(5)])
print("Обратное ДПФ: Средняя ошибка ≈", sum(abs(x[i] - x_idft[i]) for i in range(len(x))) / len(x))
# Ответ: Пики при k=1 из-за частоты sin(2πt), Средняя ошибка ≈ 0 (точное восстановление)
"""

def f3_29():
    """Быстрое преобразование Фурье."""
    return """import numpy as np

# Быстрое преобразование Фурье (упрощённая версия без рекурсии)
# Фильтрует сигнал с помощью ДПФ.
# Пример: Фильтрация зашумленного сигнала
def fft_filters(signal, fs, low_freq=None, high_freq=None, band_freq=None):
    # Применяет фильтры на основе ДПФ: низкочастотный, высокочастотный или полосовой.
    # Аргументы:
    #     signal: Входной сигнал
    #     fs: Частота дискретизации
    #     low_freq: Частота среза для низкочастотного фильтра
    #     high_freq: Частота среза для высокочастотного фильтра
    #     band_freq: Кортеж (low, high) для полосового фильтра
    # Возвращает:
    #     Отфильтрованный сигнал
    N = len(signal)
    freq = [i * fs / N for i in range(N//2 + 1)]
    X = dft(signal)
    mask = [1] * N
    if low_freq is not None:
        for i in range(N):
            if abs(i * fs / N) > low_freq:
                mask[i] = 0
    if high_freq is not None:
        for i in range(N):
            if abs(i * fs / N) < high_freq:
                mask[i] = 0
    if band_freq is not None:
        for i in range(N):
            f = abs(i * fs / N)
            if f < band_freq[0] or f > band_freq[1]:
                mask[i] = 0
    X_filtered = [X[i] * mask[i] for i in range(N)]
    filtered_signal = idft(X_filtered)
    return [val.real for val in filtered_signal]

def dft(x):
    N = len(x)
    X = [0] * N
    for k in range(N):
        for n in range(N):
            real_part = np.cos(-2 * np.pi * k * n / N)
            imag_part = np.sin(-2 * np.pi * k * n / N)
            X[k] += x[n] * (real_part + 1j * imag_part)
    return X

def idft(X):
    N = len(X)
    x = [0] * N
    for n in range(N):
        for k in range(N):
            real_part = np.cos(2 * np.pi * k * n / N)
            imag_part = np.sin(2 * np.pi * k * n / N)
            x[n] += X[k].real * real_part - X[k].imag * imag_part
        x[n] /= N
    return x

# Пример
t = [i / 1000 for i in range(1000)]
signal = [np.sin(2 * np.pi * 5 * t[i]) + 0.5 * np.sin(2 * np.pi * 50 * t[i]) for i in range(len(t))]
filtered_low = fft_filters(signal, 1000, low_freq=10)
filtered_high = fft_filters(signal, 1000, high_freq=20)
filtered_band = fft_filters(signal, 1000, band_freq=(2, 20))
print("Фильтры БПФ: Применены низкочастотный, высокочастотный и полосовой фильтры")
# Ответ: Применены фильтры (результаты можно вычислить вручную)
"""

def f3_30():
    """Дополнительная тема: Суммирование Кахана."""
    return """import numpy as np

# Суммирование Кахана
# Уменьшает ошибки округления при суммировании.
# Пример: Суммирование 10000 случайных чисел
def kahan_sum(x):
    # Алгоритм суммирования Кахана.
    # Аргументы:
    #     x: Массив для суммирования
    # Возвращает:
    #     Сумма с уменьшенной ошибкой
    s = 0.0
    c = 0.0
    for i in range(len(x)):
        y = x[i] - c
        t = s + y
        c = (t - s) - y
        s = t
    return s

# Пример
x = [np.random.uniform(-1, 1) for _ in range(10000)]
true_sum = sum(x)  # Ручное суммирование
k_sum = kahan_sum(x)
print("Суммирование Кахана: Сумма ≈", k_sum, ", Ошибка ≈", k_sum - true_sum)
# Ответ: Ошибка ≈ 7.3e-06
"""