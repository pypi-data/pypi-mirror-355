import numpy as np

def saludar():
    print("Hola, te saludo desde saludos.saludar()")

def prueba():
    print("Esto es una prueba de la nueva version")

def generar_array(numeros):
    return np.arange(numeros)

class Saludo:
    def __init__(self):
        print("Hola, te saludo desde Saludo.__init__()")

if __name__ == '__main__':
    print(generar_array(5))#esto evita que se ejecute un codigo de un modulo  desde otro fichero es decir repetido
