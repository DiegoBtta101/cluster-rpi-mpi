# 🛠️ Automatización del Clúster: Ansible Playbooks

Este directorio contiene la suite de automatización (Playbooks) utilizada para transformar 8 placas Raspberry Pi 4 individuales en un supercomputador distribuido unificado. 

Utilizamos **Ansible** por su naturaleza *agente-less* (no requiere instalar software en los nodos esclavos), lo cual ahorra valiosa memoria RAM y ciclos de CPU en nuestro entorno de hardware limitado (Raspberry Pi OS Lite).

## 🗂️ Inventario del Clúster
* **`hosts.ini`**: Es el mapa topológico del clúster. Define quién es el Maestro (`Nodo1`) y quiénes son los Esclavos (`[slaves]`). 
  * *¿Por qué es necesario?* Asocia los nombres de host locales (ej. `Nodo2.local`) con las variables de IPs estáticas, permitiendo que Ansible sepa exactamente a qué dirección física atacar y qué rol tiene cada máquina en la arquitectura.

---

## 🌐 Fase 1: Infraestructura Base (Red y Almacenamiento)

### `configurar_red.yml`
* **Qué hace:** Utiliza `nmcli` (NetworkManager) para forzar IPs estáticas en la interfaz `eth0` de todos los nodos.
* **Por qué es necesario:** MPI requiere que la topología de red sea inmutable. Si un router asigna IPs dinámicas por DHCP y estas cambian después de un reinicio, los procesos MPI se quedarán huérfanos y los trabajos fallarán con errores de *timeout*.

### `configurar_nfs.yml`
* **Qué hace:** Configura el Nodo Maestro como servidor NFS (Network File System) exportando la carpeta `/home`, y configura a los esclavos para que monten este directorio en red.
* **Por qué es necesario:** En computación paralela, todos los nodos deben ver exactamente los mismos archivos ejecutables y códigos fuente. En lugar de copiar los archivos a 8 placas distintas cada vez que un estudiante compila su código en C, el NFS permite que lo que se guarde en el Maestro sea instantáneamente accesible y ejecutable por los esclavos.

---

## 👥 Fase 2: Gestión de Identidades y Seguridad

### `add_user_v1.yml`
* **Qué hace:** Crea cuentas de usuario estandarizadas, establece entornos aislados sin permisos `sudo` y configura la comunicación SSH *Passwordless* (sin contraseña) entre el Maestro y los esclavos.
* **Por qué es necesario:** MPI inicia procesos remotamente a través de SSH. Si SSH pide contraseña en cada salto entre nodos, la ejecución paralela se bloquearía esperando interacción humana. La directiva `StrictHostKeyChecking accept-new` evita los bloqueos silenciosos por confirmaciones de huellas criptográficas.

### `limpiar_cluster.yml`
* **Qué hace:** Un script de "Tabula Rasa". Mata los procesos activos de usuarios específicos y purga de forma recursiva sus directorios y grupos (`mpi_users`).
* **Por qué es necesario:** Crucial para la administración del laboratorio. Permite limpiar las cuentas de prueba (ej. `estudiante1`) antes de aprovisionar a la cohorte real de estudiantes, liberando recursos sin necesidad de formatear las tarjetas SD.

### `cluster_simetrico_pruebas.yml`
* **Qué hace:** Genera llaves SSH en todos los nodos y las cruza entre sí, creando una malla simétrica de confianza.
* **Por qué es necesario:** Mientras que los estudiantes solo necesitan acceso del Maestro hacia los Esclavos (arquitectura en estrella), el administrador puede requerir saltar de un esclavo a otro para depuración sin pasar por el Maestro.

---

## ⚡ Fase 3: Middleware y Entorno MPI

### `verificar_cluster_mpi.yml`
* **Qué hace:** Asegura la instalación base de los compiladores y reporta el estado del *wrapper* `mpicc` en cada nodo.
* **Por qué es necesario:** Actúa como un chequeo de salud (Health Check). Audita que las librerías `libmpich-dev` y los *headers* de C estén donde deben estar antes de iniciar la compilación distribuida.

### `reset_mpi.yml`
* **Qué hace:** Elimina rastros de OpenMPI a nivel de sistema y reinstala/blinda una arquitectura pura basada en **MPICH**. 
* **Por qué es necesario:** En entornos ARM (como Raspberry Pi), hemos detectado que OpenMPI puede generar problemas de segmentación o bloqueos en la red. Este playbook garantiza que el clúster use la implementación MPICH (más estable en este hardware) y previene conflictos de librerías.

### `reparar_mpi4py.yml`
* **Qué hace:** Realiza una desinstalación forzada a nivel de sistema y vuelve a compilar la librería `mpi4py` pasándole explícitamente el compilador `mpicc.mpich` como variable de entorno.
* **Por qué es necesario:** Python suele causar problemas al compilar `mpi4py` si cachea cabeceras antiguas o se confunde de *wrapper*. Este script es la "bala de plata" que fuerza a Python a vincularse estrictamente con las librerías nativas de MPICH recién instaladas.

### `deploy_mpi_jobs.yml`
* **Qué hace:** Copia físicamente códigos de ejemplo (`hello.c` y `hello.py`) a los nodos esclavos (con `gather_facts: false` para extrema velocidad).
* **Por qué es necesario:** Aunque tenemos NFS, este script es vital como plan de contingencia. Si el servidor NFS falla o se satura por I/O excesivo, permite distribuir cargas de trabajo estáticas directamente a la memoria SD de los esclavos para pruebas locales.

---

## 🚀 ¿Cómo ejecutar estos Playbooks?

Para aplicar cualquier configuración, colócate en este directorio desde el Nodo Maestro (o tu máquina local conectada por Tailscale) y ejecuta el siguiente comando:

```bash
ansible-playbook -i hosts.ini nombre_del_playbook.yml
```

> **⚠️ Advertencia de Seguridad:** Playbooks como `limpiar_cluster.yml` o `reset_mpi.yml` son destructivos por diseño. Ejecútalos únicamente durante las ventanas de mantenimiento del laboratorio y nunca mientras los estudiantes tengan trabajos MPI en cola.