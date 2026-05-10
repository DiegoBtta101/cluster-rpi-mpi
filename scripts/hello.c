#include <mpi.h>
#include <stdio.h>
#include <unistd.h>

int main(int argc, char** argv) {
    MPI_Init(NULL, NULL);
    int world_size, world_rank;
    char hostname[256];
    
    MPI_Comm_size(MPI_COMM_WORLD, &world_size);
    MPI_Comm_rank(MPI_COMM_WORLD, &world_rank);
    gethostname(hostname, 256);

    printf("Hola desde %s, rango %d de %d procesadores\n", hostname, world_rank, world_size);

    MPI_Finalize();
    return 0;
}