#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <time.h>
#include <mpi.h>

int main(int argc, char* argv[]) {
    int rank, size;
    long long int iteraciones = 1000000000; // 1,000 millones
    long long int iteraciones_locales;
    long long int puntos_dentro_local = 0;
    long long int puntos_dentro_total = 0;
    double pi_estimado, tiempo_inicio, tiempo_fin;

    MPI_Init(&argc, &argv);
    MPI_Comm_rank(MPI_COMM_WORLD, &rank);
    MPI_Comm_size(MPI_COMM_WORLD, &size);

    // Dividir el trabajo equitativamente
    iteraciones_locales = iteraciones / size;

    // Semilla aleatoria única para cada nodo
    srand(time(NULL) + rank);

    MPI_Barrier(MPI_COMM_WORLD); // Sincronizar antes de medir el tiempo
    tiempo_inicio = MPI_Wtime();

    // Cálculo intensivo de CPU
    for (long long int i = 0; i < iteraciones_locales; i++) {
        double x = (double)rand() / RAND_MAX;
        double y = (double)rand() / RAND_MAX;
        if (x*x + y*y <= 1.0) {
            puntos_dentro_local++;
        }
    }

    // Reducir (sumar) los resultados parciales en el Maestro (rank 0)
    MPI_Reduce(&puntos_dentro_local, &puntos_dentro_total, 1, MPI_LONG_LONG_INT, MPI_SUM, 0, MPI_COMM_WORLD);

    tiempo_fin = MPI_Wtime();

    if (rank == 0) {
        pi_estimado = 4.0 * ((double)puntos_dentro_total / (double)iteraciones);
        printf("Nodos usados: %d\n", size);
        printf("Valor estimado de Pi: %f\n", pi_estimado);
        printf("Tiempo de ejecución: %f segundos\n", tiempo_fin - tiempo_inicio);
    }

    MPI_Finalize();
    return 0;
}