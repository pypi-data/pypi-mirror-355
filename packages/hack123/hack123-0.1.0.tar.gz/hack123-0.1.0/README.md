# hack4u academy courses library

una biblioteca python para consultar cursos de hack4u

## Cursos disponibles
-a
-b
-c

## instalacion
Instala el paquete usando pip3:

```python3
pip3 install hack4u
```

## uso basico

### listar todos los cursos

```python
from hack4u import list_courses

for course in list_courses():
    print(course)
```

### Obtener un curso por nombre

```python
from hack4u import get_course_by_name

course = get_course_by_name("Introduccion a linux")
print(course)
```

### Calcular duracion total de todos los cursos

```python
from hack4u.utils import total_duration
print(f"Duracion total: {total_duration()} horas")
```
