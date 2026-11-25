# Aplicativo de Investigación de Operaciones (Tkinter)

Módulos: **Método Gráfico** (programación lineal con 2 variables) y **Teoría de Colas** (M/M/1 y M/M/s con análisis de costos).

## ejecutar
```
py -m pip install -r requirements.txt
py aplicativo.py
si sale el error NameError: name 'py' is not defined
remplaza py con python
o simplemente ejecutar el archivo aplicativo.py en vscode y tener instalado las librerias numpy y matplotlib
```

## Archivos
| Archivo | Qué hace |
|---|---|
| `aplicativo.py` | Interfaz (ventanas, casillas, tablas, botones). No calcula nada |
| `metodo_grafico.py` | Motor del método gráfico: vértices, factibilidad, óptimo, gráfica |
| `teoria_colas.py` | Motor de colas: P0, Pw, L, Lq, W, Wq, costos y gráficas |
| `crear_exe.bat` | Genera el ejecutable con PyInstaller |

## Uso
Cambia cualquier dato y presiona **CALCULAR** (o la tecla Enter). En el método gráfico puedes agregar o borrar restricciones con los botones.

## Ejemplos precargados (para validar)
- **Método gráfico:** Max Z = 3x + 5y; x ≤ 4; 2y ≤ 12; 3x + 2y ≤ 18 → óptimo (2, 6), Z = 36.
- **Colas:** λ = 10 clientes/h, μ = 4 clientes/h, s = 3, Cs = $15.000/h, Cw = $20.000/h → ρ = 83,3 %, Lq = 3,51, Wq ≈ 21 min; el costo mínimo se da con s = 4.
