#1
def fchyaks():
    print('''#Используя лямбда-функцию, найдите все числа в заданном списке, которые являются числами Фибоначчи.

is_fibo = (lambda a: lambda v,fib=0,n=1: a(a,v,fib,n))(lambda f,value,fib,n: f(f,value,fib+n,fib) if fib < value else fib==value)

# Заданный список чисел
numbers = list(range(100))

# Использование лямбда-функции для фильтрации чисел Фибоначчи из списка
fibonacci_numbers = list(filter(is_fibo, numbers))

# Вывод результатов
print(fibonacci_numbers)''')
    
def kkemi():
    print('''#Напишите программу для сортировки заданного списка кортежей по разности между максимальным и минимальным элементами каждого кортежа.

# Заданный список кортежей
tuples = [(3, 8, 2), (1, 5, 10), (4, 7, 6), (2, 9, 1)]

# Функция для получения разности между максимальным и минимальным элементами кортежа
get_diff = lambda tuple: max(tuple) - min(tuple)

# Сортировка списка кортежей по разности между максимальным и минимальным элементами
sorted_tuples = sorted(tuples, key=get_diff)

# Вывод отсортированного списка кортежей
print(sorted_tuples)''')
    
def bstsk():
    print('''#Используя лямбда-функцию, найдите все строки в заданном списке строк, которые содержат только согласные буквы.

# Заданный список строк
strings = ['hll', 'wrld', 'bye', 'peace', 'aisd', 'sht']

# Функция для проверки строки на наличие только согласных букв
is_consonant = lambda s: all(letter.lower() not in 'aeiou' for letter in s)

# Фильтрация списка строк с помощью лямбда-функции
consonant_strings = list(filter(is_consonant, strings))

# Вывод результатов
print(consonant_strings)''')
    
def sieui():
    print('''#Реализовать функцию, которая находит максимальный элемент в двусвязном списке и удаляет его из списка. 

#реализация двусвязного списка
class Node:
    def __init__(self, data):
        self.data = data
        self.prev = None
        self.next = None

class DoublyLinkedList:
    def __init__(self):
        self.head = None

    def add_node(self, data):
        new_node = Node(data)
        if self.head is None:
            self.head = new_node
        else:
            current = self.head
            while current.next is not None:
                current = current.next
            current.next = new_node
            new_node.prev = current

    def delete_node(self, data):
        if self.head is None:
            return
        elif self.head.data == data:
            if self.head.next is not None:
                self.head = self.head.next
                self.head.prev = None
            else:
                self.head = None
        else:
            current = self.head
            while current.next is not None and current.next.data != data:
                current = current.next
            if current.next is None:
                return
            else:
                current.next = current.next.next
                if current.next is not None:
                    current.next.prev = current

    def __len__(self):
        count = 0
        current = self.head
        while current:
            count += 1
            current = current.next
        return count

    def __str__(self):
        if self.head == None:
            return f"Двусвязный список пустой"
        current = self.head
        dllist_str = ""
        while current:
            dllist_str += " ⇄ " + str(current.data)
            current = current.next
        return dllist_str.lstrip(" ⇄ ") 
    
#программа

def find_and_remove_max(dllist):
    if dllist.head is None:
        return None

    current = dllist.head
    max_node = current

    # Находим узел с максимальным значением
    while current.next:
        current = current.next
        if current.data > max_node.data:
            max_node = current

    # Удаляем узел с максимальным значением
    if max_node.prev:
        max_node.prev.next = max_node.next
    else:
        dllist.head = max_node.next

    if max_node.next:
        max_node.next.prev = max_node.prev

    return max_node.data

#проверка
dllist = DoublyLinkedList()
dllist.add_node(5)
dllist.add_node(10)
dllist.add_node(8)
dllist.add_node(3)

print("Изначальный список:", dllist)
max_value = find_and_remove_max(dllist)
print("Максимальное значение:", max_value)
print("Список после удаления максимального элемента:", dllist)''')

#2    
def lpschs():
    print('''#Отфильтровать список целых чисел на простые и составные числа с помощью лямбда-функции.

# Заданный список целых чисел
numbers = [2, 3, 4, 5, 6, 7, 8, 9, 10]

# Лямбда-функция для проверки числа на простоту
is_prime = lambda num: all(num % i != 0 for i in range(2, int(num**0.5) + 1)) and num > 1

# Фильтрация списка на простые числа
prime_numbers = list(filter(is_prime, numbers))

# Фильтрация списка на составные числа
composite_numbers = list(filter(lambda num: not is_prime(num), numbers))

prime_numbers, composite_numbers''')
    
def susdp():
    print('''#Для удаления определённых символов из заданной строки используйте лямбда-функцию. Пример: дана строка 'hello world', удалить символы 'l' и 'o' → 'he wrd'.

string = 'hello world'
characters_to_remove = ['l', 'o']

# Функция для удаления символов из строки
remove_characters = lambda s: ''.join([char for char in s if char not in characters_to_remove])

# Применение лямбда-функции к строке
result = remove_characters(string)

# Вывод результата
print(result)''')
    
def nipsu():
    print('''#Используя лямбда-функцию, проверить, является ли указанный список палиндромом или нет

is_pal = lambda x: (x == (x[::-1]))

lst1 = [1,2,1]
lst2 = [1,2,3]
lst3 = ['a','b','a']
lst4 = ['a','b','c']

is_pal(lst1), is_pal(lst2), is_pal(lst3), is_pal(lst4)''')

def nsitn():
    print('''#Реализовать функцию, которая проверяет, является ли двусвязный список палиндромом (элементы списка читаются одинаково как слева направо, так и справа налево)

class Node:
    def __init__(self, data):
        self.data = data
        self.prev = None
        self.next = None

class DoublyLinkedList:
    def __init__(self):
        self.head = None

    def add_node(self, data):
        new_node = Node(data)
        if self.head is None:
            self.head = new_node
        else:
            current = self.head
            while current.next is not None:
                current = current.next
            current.next = new_node
            new_node.prev = current

    def delete_node(self, data):
        if self.head is None:
            return
        elif self.head.data == data:
            if self.head.next is not None:
                self.head = self.head.next
                self.head.prev = None
            else:
                self.head = None
        else:
            current = self.head
            while current.next is not None and current.next.data != data:
                current = current.next
            if current.next is None:
                return
            else:
                current.next = current.next.next
                if current.next is not None:
                    current.next.prev = current

    def __len__(self):
        count = 0
        current = self.head
        while current:
            count += 1
            current = current.next
        return count

    def __str__(self):
        if self.head == None:
            return f"Двусвязный список пустой"
        current = self.head
        dllist_str = ""
        while current:
            dllist_str += " ⇄ " + str(current.data)
            current = current.next
        return dllist_str.lstrip(" ⇄ ")   
    
#программа

def is_palindrome(dllist):
    if dllist.head is None:
        return True

    # Получаем длину списка
    length = len(dllist)

    # Объявляем два указателя, один идет с начала списка, другой - с конца
    front = dllist.head
    back = dllist.head

    # Перемещаем указатель back к последнему элементу списка
    while back.next:
        back = back.next

    # Проверяем значения элементов, двигая указатели front и back
    while front != back and front.prev != back:
        if front.data != back.data:
            return False
        front = front.next
        back = back.prev

    return True

dllist = DoublyLinkedList()
dllist.add_node(1)
dllist.add_node(2)
dllist.add_node(3)
dllist.add_node(2)
dllist.add_node(1)

print(dllist)
print(is_palindrome(dllist))  # Вывод: True

dllist.add_node(4)
print('\n', dllist)
print(is_palindrome(dllist))  # Вывод: False''')

#3    
def fuvko():
    print('''#Создайте класс «Банк» с атрибутами название, адрес и список клиентов.
Каждый клиент представлен классом «Клиент» с атрибутами имя,
фамилия, номер счета и баланс. Напишите методы для добавления
клиента в банк, удаления клиента из банка и вывода информации
о банке в виде «Банк '{название}', адрес - {адрес}, клиенты - {список
клиентов}». Используйте магический метод __str__ для вывода
информации о клиенте в удобном формате.

class Bank:
    def __init__(self, name, address):
        self.name = name
        self.address = address
        self.clients = []
    
    def add_client(self, client):
        self.clients.append(client)
    
    def remove_client(self, client):
        if client in self.clients:
            self.clients.remove(client)
        else:
            print('Клиента нет в базе')
    
    def __str__(self):
        client_info = '\n'.join(str(client) for client in self.clients)
        return f"Банк '{self.name}', адрес - {self.address}, клиенты:\n{client_info}"  

class Client:
    def __init__(self, name, surname, account, balance):
        self.name = name
        self.surname = surname
        self.account = account
        self.balance = balance 
    def __str__(self):
        return f"Клиент: {self.name} {self.surname}, Номер счета: {self.account}, Баланс: {self.balance}"
    
bank = Bank("MFBank", "123 Ryasansky Avenue")

client1 = Client("Russell", "Westbrook", "8954792453", 10000)
client2 = Client("Busta", "Rhimes", "4472933908", 99999)

bank.add_client(client1)
bank.add_client(client2)

print(bank)''')
    
def sedkya():
    print('''# Дан стек. Необходимо проверить, содержит ли он хотя бы один элемент,
# который является квадратом другого элемента стека.

class Node:
    def __init__(self, data):
        self.data = data
        self.next = None

class Stack:
    def __init__(self):
        self.head = None

    def is_empty(self):
        return self.head is None

    def push(self, item):
        new_node = Node(item)
        new_node.next = self.head
        self.head = new_node

    def pop(self):
        if self.is_empty():
            return None
        else:
            popped_item = self.head.data
            self.head = self.head.next
            return popped_item

    def peek(self):
        if self.is_empty():
            return None
        else:
            return self.head.data

    def __str__(self):
        current = self.head
        stack_str = ""
        while current:
            stack_str += str(current.data) + " → "
            current = current.next
        return stack_str.rstrip(" → ")

#программа

def square(stack):
    if stack.is_empty():
        return False

    # Создаем множество для хранения уникальных элементов стека
    unique_elements = set()

    # Проходим по всем элементам стека
    current = stack.head
    while current:
        # Проверяем, является ли текущий элемент квадратом другого элемента
        if current.data ** 2 in unique_elements:
            return True

        # Добавляем текущий элемент в множество уникальных элементов
        unique_elements.add(current.data)

        current = current.next

    return False

lst1 = [1,2,3,5,9,25]
lst2 = [1,3,5,7,11,13,17]

stack1 = Stack()
stack2 = Stack()

for item in lst1:
    stack1.push(item)

for item in lst2:
    stack2.push(item)

print(f'Стек 1: {stack1}, {square(stack1)}')
print(f'Стек 2: {stack2}, {square(stack2)}')''')

#4    
def hzsap():
    print('''# Создайте класс АВТОМОБИЛЬ с методами, позволяющими вывести на
# экран информацию об автомобиле, а также определить, подходит ли
# данный автомобиль для заданных условий. Создайте дочерние классы
# ЛЕГКОВОЙ (марка, модель, год выпуска, объем двигателя, тип
# топлива), ГРУЗОВОЙ (марка, модель, год выпуска, грузоподъемность),
# ПАССАЖИРСКИЙ (марка, модель, год выпуска, количество мест) со
# своими методами вывода информации на экран и определения
# соответствия заданным условиям. Создайте список автомобилей,
# выведите полную информацию из базы на экран, а также организуйте
# поиск автомобилей с заданными характеристиками.

class Car:
    def __init__(self, brand, model, year, engine_capacity):
        self.brand = brand
        self.model = model
        self.year = year
        self.engine_capacity = engine_capacity

    def display_info(self):
        print(f"Марка: {self.brand}")
        print(f"Модель: {self.model}")
        print(f"Год выпуска: {self.year}")
        print(f"Объем двигателя: {self.engine_capacity} л")

    def is_matching(self, conditions):
        for key, value in conditions.items():
            if getattr(self, key) != value:
                return False
        return True


class PassengerCar(Car):
    def __init__(self, brand, model, year, engine_capacity, fuel_type, seats):
        super().__init__(brand, model, year, engine_capacity)
        self.fuel_type = fuel_type
        self.seats = seats

    def display_info(self):
        super().display_info()
        print(f"Тип топлива: {self.fuel_type}")
        print(f"Количество мест: {self.seats}")

    def is_matching(self, conditions):
        if not super().is_matching(conditions):
            return False
        if 'fuel_type' in conditions and self.fuel_type != conditions['fuel_type']:
            return False
        if 'seats' in conditions and self.seats < conditions['seats']:
            return False
        return True


class FreightCar(Car):
    def __init__(self, brand, model, year, engine_capacity, load_capacity):
        super().__init__(brand, model, year, engine_capacity)
        self.load_capacity = load_capacity

    def display_info(self):
        super().display_info()
        print(f"Грузоподъемность: {self.load_capacity} т")

    def is_matching(self, conditions):
        if not super().is_matching(conditions):
            return False
        if 'load_capacity' in conditions and self.load_capacity < conditions['load_capacity']:
            return False
        return True


class PassengerVan(Car):
    def __init__(self, brand, model, year, engine_capacity, seats):
        super().__init__(brand, model, year, engine_capacity)
        self.seats = seats

    def display_info(self):
        super().display_info()
        print(f"Количество мест: {self.seats}")

    def is_matching(self, conditions):
        if not super().is_matching(conditions):
            return False
        if 'seats' in conditions and self.seats < conditions['seats']:
            return False
        return True
    
cars = [
    PassengerCar("Toyota", "Camry", 2020, 2.5, "бензин", 5),
    FreightCar("Volvo", "FH16", 2018, 13.0, 30),
    PassengerVan("Mercedes-Benz", "Sprinter", 2019, 2.2, 9)
]

# Вывод полной информации о всех автомобилях
for car in cars:
    car.display_info()
    print()

# Поиск автомобилей по заданным характеристикам
search_conditions = {
    'brand': "Toyota",
    'engine_capacity': 2.5
}

matching_cars = [car for car in cars if car.is_matching(search_conditions)]

if matching_cars:
    print("Результаты поиска:")
    for car in matching_cars:
        car.display_info()
else:
    print("Нет автомобилей, удовлетворяющих заданным характеристикам.")
''')


def sdvev():
    print('''# Реализовать функцию, которая находит произведение квадратов всех
# элементов в двусвязном списке.

class Node:
    def __init__(self, data):
        self.data = data
        self.prev = None
        self.next = None

class DoublyLinkedList:
    def __init__(self):
        self.head = None

    def add_node(self, data):
        new_node = Node(data)
        if self.head is None:
            self.head = new_node
        else:
            current = self.head
            while current.next is not None:
                current = current.next
            current.next = new_node
            new_node.prev = current

    def delete_node(self, data):
        if self.head is None:
            return
        elif self.head.data == data:
            if self.head.next is not None:
                self.head = self.head.next
                self.head.prev = None
            else:
                self.head = None
        else:
            current = self.head
            while current.next is not None and current.next.data != data:
                current = current.next
            if current.next is None:
                return
            else:
                current.next = current.next.next
                if current.next is not None:
                    current.next.prev = current

    def __len__(self):
        count = 0
        current = self.head
        while current:
            count += 1
            current = current.next
        return count
    
    def calculate_square_product(self):
        if self.head is None:
            return 1  # Если список пустой, возвращаем 1

        product = 1
        current = self.head
        while current:
            product *= current.data ** 2
            current = current.next

        return product
    
    def __str__(self):
        if self.head == None:
            return f"Двусвязный список пустой"
        current = self.head
        dllist_str = ""
        while current:
            dllist_str += " ⇄ " + str(current.data)
            current = current.next
        return dllist_str.lstrip(" ⇄ ")  
    
dllist = DoublyLinkedList()
dllist.add_node(2)
dllist.add_node(3)
dllist.add_node(4)
dllist.add_node(5)

square_product = dllist.calculate_square_product()
print(dllist)
print("Произведение квадратов элементов в списке:", square_product)''')

#5    
def rivgz():
    print('''# Создайте класс ФИЛЬМ с методами, позволяющими вывести на экран
# информацию о фильме, а также определить, подходит ли данный фильм
# для заданных условий. Создайте дочерние классы КОМЕДИЯ
# (название, год выпуска, режиссер, актеры), ДРАМА (название, год
# выпуска, режиссер, актеры), ФАНТАСТИКА (название, год выпуска,
# режиссер, актеры) со своими методами вывода информации на экран и
# определения соответствия заданным условиям. Создайте список
# фильмов, выведите полную информацию из базы на экран, а также
# организуйте поиск фильмов с заданным годом выпуска или режиссером.

class Film:
    def __init__(self, title, year, director, actors):
        self.title = title
        self.year = year
        self.director = director
        self.actors = actors

    def display_info(self):
        print("Фильм:", self.title)
        print("Год выпуска:", self.year)
        print("Режиссер:", self.director)
        print("Актеры:", ', '.join(self.actors))

    def matches_condition(self, year=None, director=None):
        if year and self.year != year:
            return False
        if director and self.director != director:
            return False
        return True


class Comedy(Film):
    def display_info(self):
        print("Комедия:")
        super().display_info()


class Drama(Film):
    def display_info(self):
        print("Драма:")
        super().display_info()


class Fantasy(Film):
    def display_info(self):
        print("Фантастика:")
        super().display_info()


# Создание списка фильмов
films = [
    Comedy("Комедия 1", 2000, "Режиссер 1", ["Актер 1", "Актер 2"]),
    Drama("Драма 1", 2005, "Режиссер 2", ["Актер 3", "Актер 4"]),
    Fantasy("Фантастика 1", 2010, "Режиссер 3", ["Актер 5", "Актер 6"]),
    Comedy("Комедия 2", 2000, "Режиссер 1", ["Актер 7", "Актер 8"]),
]

# Вывод полной информации о фильмах
for film in films:
    film.display_info()
    print()

# Поиск фильмов по заданным условиям
print("Фильмы, выпущенные в 2000 году:")
for film in films:
    if film.matches_condition(year=2000):
        film.display_info()
        print()

print("Фильмы режиссера 'Режиссер 1':")
for film in films:
    if film.matches_condition(director="Режиссер 1"):
        film.display_info()
        print()
''')
    
def pdbvn():
    print('''#Найти высоту бинарного дерева поиска

class Node:
    def __init__(self, data):
        self.data = data
        self.left = None
        self.right = None        

class BinaryTree:
    def __init__(self):
        self.root = None

    def insert(self, data):
        new_node = Node(data)
        if self.root is None:
            self.root = new_node
        else:
            current = self.root
            while True:
                if data < current.data:
                    if current.left is None:
                        current.left = new_node
                        break
                    else:
                        current = current.left
                else:
                    if current.right is None:
                        current.right = new_node
                        break
                    else:
                        current = current.right

    def search(self, data):
        current = self.root
        while current is not None:
            if data == current.data:
                return True
            elif data < current.data:
                current = current.left
            else:
                current = current.right
        return False

    def delete(self, data):
        if self.root is not None:
            self.root = self._delete(data, self.root)

    def _delete(self, data, node):
        if node is None:
            return node

        if data < node.data:
            node.left = self._delete(data, node.left)
        elif data > node.data:
            node.right = self._delete(data, node.right)
        else:
            if node.left is None:
                return node.right
            elif node.right is None:
                return node.left

            temp = self._find_min_node(node.right)
            node.data = temp.data
            node.right = self._delete(temp.data, node.right)

        return node

    def _find_min_node(self, node):
        while node.left is not None:
            node = node.left
        return node

    def __str__(self):
        return '\n'.join(self._display(self.root)[0])

    def height(self):
        return self._height(self.root)

    def _height(self, node):
        if node is None:
            return 0
        else:
            left_height = self._height(node.left)
            right_height = self._height(node.right)
            return max(left_height, right_height) + 1


    def _display(self, node):
        if node.right is None and node.left is None:
            line = str(node.data)
            width = len(line)
            height = 1
            middle = width // 2
            return [line], width, height, middle

        if node.right is None:
            lines, n, p, x = self._display(node.left)
            s = str(node.data)
            u = len(s)
            first_line = (x + 1)*' ' + (n - x - 1)*'_' + s
            second_line = x*' ' + '/' + (n - x - 1 + u)*' '
            shifted_lines = [line + u*' ' for line in lines]
            return [first_line, second_line] + shifted_lines, n + u, p + 2, n + u // 2

        if node.left is None:
            lines, n, p, x = self._display(node.right)
            s = str(node.data)
            u = len(s)
            first_line = s + x*'_' + (n - x)*' '
            second_line = (u + x)*' ' + '\\' + (n - x - 1)*' '
            shifted_lines = [u*' ' + line for line in lines]
            return [first_line, second_line] + shifted_lines, n + u, p + 2, u // 2

        left, n, p, x = self._display(node.left)
        right, m, q, y = self._display(node.right)
        s = str(node.data)
        u = len(s)
        first_line = (x + 1)*' ' + (n - x - 1)*'_' + s + y*'_' + (m - y)*' '
        second_line = x*' ' + '/' + (n - x - 1 + u + y)*' ' + '\\' + (m - y - 1)*' '
        if p < q:
            left += [n*' ']*(q - p)
        elif q < p:
            right += [m*' ']*(p - q)
        zipped_lines = zip(left, right)
        lines = [first_line, second_line] + [a + u*' ' + b for a, b in zipped_lines]
        return lines, n + m + u, max(p, q) + 2, n + u // 2
    
from random import shuffle

# создание объекта класса BinaryTree
tree = BinaryTree()

# создание списка элементов
items = list(range(1,11))
shuffle(items)

# добавление элементов в бинарное дерево
for item in items:
    tree.insert(item)

# вывод бинарного дерева на экран
print(items)
print(tree)
tree.height()''')