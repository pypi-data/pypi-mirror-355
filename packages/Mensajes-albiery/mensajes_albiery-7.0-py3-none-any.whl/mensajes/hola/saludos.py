import numpy as np

def saludar():
    print("Hola, te saludo desde saludos.saludar()")

def prueba():
    print("Esto es una nueva prueba de la nueva version 7.0")

def generar_array(numeros):
    return np.arange(numeros)

class Saludo:
    def __init__(self):
        print("Hola, te saludo desde Saludo.__init__()")

if __name__ == '__main__':
    print(generar_array(5))#esto evita que se ejecute un codigo de un modulo  desde otro fichero es decir repetido
