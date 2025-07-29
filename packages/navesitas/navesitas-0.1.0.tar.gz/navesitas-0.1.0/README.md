# Navesitas de tu taita !

videitos cortitos que son de tu padre!

## Videos disponibles:

- Toyota Supra [15 Segundos]
- Nissan GT-R R35 [10 Segundos]
- Lamboghinni Aventador SVJ [5 Segundos]

## Instalacion

Instala el paquete usando `pip3`:

```python3
pip3 install navesitas
```

## Uso Basico

### Listar todas las naves!

```python
from navesitas import list_naves():

from nave in list_naves():
    print(nave)
```

### Obtener una nave por nombre

```python
from navesitas import search_nave_by_brand():

nave = search_nave_by_brand("Toyota")
print(nave)
```

### Calcular la duracion total de los videos

```python3
from navesitas.utils import total_duration

print(f"Duracion total: {total_duration()} segundos")
