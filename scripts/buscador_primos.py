from mpi4py import MPI
import time
import math

def es_primo(n):
    if n <= 1: return False
    if n <= 3: return True
    if n % 2 == 0 or n % 3 == 0: return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True

def contar_primos_en_rango(rango):
    inicio, fin = rango
    conteo = 0
    for n in range(inicio, fin):
        if es_primo(n):
            conteo += 1
    return conteo

comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

limite_superior = 2000000 # 2 Millones
tamano_chunk = 50000      # Lotes de 50,000 números

if rank == 0:
    # --- NODO MAESTRO ---
    tiempo_inicio = time.time()
    
    # Crear la lista de tareas (rangos)
    tareas = [(i, min(i + tamano_chunk, limite_superior)) for i in range(0, limite_superior, tamano_chunk)]
    total_primos = 0
    trabajadores_activos = size - 1

    # Enviar primera tarea a cada trabajador
    for i in range(1, size):
        if tareas:
            comm.send(tareas.pop(0), dest=i, tag=1)
        else:
            comm.send(None, dest=i, tag=0) # Señal de apagado (Poison pill)
            trabajadores_activos -= 1

    # Escuchar resultados y enviar más trabajo dinámicamente
    while trabajadores_activos > 0:
        status = MPI.Status()
        resultado = comm.recv(source=MPI.ANY_SOURCE, tag=MPI.ANY_TAG, status=status)
        trabajador = status.Get_source()
        total_primos += resultado
        
        if tareas:
            comm.send(tareas.pop(0), dest=trabajador, tag=1)
        else:
            comm.send(None, dest=trabajador, tag=0) # Ya no hay más tareas
            trabajadores_activos -= 1

    tiempo_fin = time.time()
    print(f"Nodos trabajadores: {size - 1}")
    print(f"Total de números primos encontrados: {total_primos}")
    print(f"Tiempo de ejecución: {tiempo_fin - tiempo_inicio:.2f} segundos")

else:
    # --- NODOS TRABAJADORES (ESCLAVOS) ---
    while True:
        status = MPI.Status()
        tarea = comm.recv(source=0, tag=MPI.ANY_TAG, status=status)
        
        if status.Get_tag() == 0:
            break # Señal de fin recibida, salir del bucle
        
        # Procesar tarea y devolver el conteo al maestro
        conteo_parcial = contar_primos_en_rango(tarea)
        comm.send(conteo_parcial, dest=0)