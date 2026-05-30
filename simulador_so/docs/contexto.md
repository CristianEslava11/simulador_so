# Simulador de Sistema Operativo
## Contexto

Proyecto académico para la materia de Sistemas Operativos.

### Objetivo

Construir un simulador visual que integre:
* Planificación de procesos
* Gestión de memoria
* Paginación por demanda
* Reemplazo de páginas
* Gestión de archivos
* Concurrencia mediante mutex
* Registro de métricas

Todo dentro de una única simulación.

### Restricciones

* Este NO es un producto empresarial.
* Este NO es un sistema de producción.
* Se debe evitar sobreingeniería.

La prioridad es:
1. Cumplir la rúbrica.
2. Facilitar la sustentación.
3. Mantener una arquitectura limpia.

### Descripción del proyecto

Los estudiantes deben construir un simulador en Python que: 
* Cree múltiples procesos simulados con características distintas (prioridad, duración, uso de CPU, acceso a archivos). 
* Implemente una planificación de procesos (Round Robin, SJF, Prioridad). 
* Simule la asignación de memoria (paginación por demanda, reemplazo de páginas). 
* Gestione archivos simulando lectura/escritura concurrente con bloqueo.

Debe tener lo siguiente:

#### Fase 2: Implementación de planificación de procesos 
* Simulación de cola de procesos. 
* Implementación de al menos dos algoritmos de planificación. 
* Registro de métricas: tiempo de espera, tiempo de ejecución. 

#### Fase 3: Gestión de memoria 
* Simulación de paginación por demanda. 
* Implementación de algoritmo de reemplazo (FIFO, LRU). 
* Visualización del uso de marcos de página. 

#### Fase 4: Gestión de archivos 
* Simulación de acceso concurrente a archivos. 
* Implementación de bloqueo mutuo (mutex o semáforo). 
* Registro de conflictos y resolución. 

### Rúbrica de evaluación

Se debe tener en cuenta la siguiente rúbrica de evaluación:

1. **Diseño técnico del simulador:** El estudiante presenta una arquitectura clara, modular y bien argumentada. Se evidencia comprensión profunda de los componentes del sistema operativo.
2. **Implementación de algoritmos:** Los algoritmos de planificación, memoria y archivos están correctamente implementados, optimizados y bien documentados.
3. **Informe técnico:** El informe está bien estructurado, incluye análisis crítico, justificación de decisiones y reflexiones sobre el proceso.
4. **Pruebas y resultados:** Se presentan casos de prueba variados, con evidencia clara (capturas, métricas) y análisis de resultados.
5. **Presentación final:** El equipo demuestra dominio del tema, explica con claridad y responde preguntas con seguridad.
