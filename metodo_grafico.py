"""
MOTOR DE CÁLCULO: MÉTODO GRÁFICO (Programación Lineal con 2 variables)
=====================================================================

Problema que resuelve:
    Maximizar o Minimizar   Z = c1·x + c2·y
    sujeto a                a1·x + a2·y  (<=, >= o =)  b     (una por restricción)
                            x >= 0 , y >= 0

Idea del método gráfico (la que programamos aquí):
    1. Cada restricción es una recta en el plano x-y.
    2. Los VÉRTICES de la región factible siempre son cruces entre dos rectas.
    3. Calculamos TODOS los cruces posibles entre pares de rectas.
    4. Nos quedamos solo con los cruces que cumplen TODAS las restricciones (factibles).
    5. Evaluamos Z en cada vértice factible: el mejor es el óptimo
       (Teorema fundamental de la PL: si hay óptimo, está en un vértice).

Casos especiales que detecta:
    - Infactible: no hay ningún punto que cumpla todas las restricciones.
    - No acotado: Z puede crecer (o bajar) sin límite.
    - Óptimos alternativos: dos vértices empatan en el mejor valor de Z.
"""

from dataclasses import dataclass
from itertools import combinations

import matplotlib.pyplot as plt
import numpy as np

TOL = 1e-7  # tolerancia numérica para comparar números decimales


@dataclass
class Restriccion:
    a1: float      # coeficiente de x
    a2: float      # coeficiente de y
    signo: str     # "<=", ">=" o "="
    b: float       # lado derecho
    nombre: str = ""

    def se_cumple(self, x, y):
        """¿El punto (x, y) cumple esta restricción?"""
        lado_izq = self.a1 * x + self.a2 * y
        if self.signo == "<=":
            return lado_izq <= self.b + TOL
        if self.signo == ">=":
            return lado_izq >= self.b - TOL
        return abs(lado_izq - self.b) <= TOL  # "="

    def texto(self):
        return f"{self.a1:g}x + {self.a2:g}y {self.signo} {self.b:g}"


def cruce(r1, r2):
    """Punto donde se cruzan las rectas de dos restricciones (o None si son paralelas)."""
    A = np.array([[r1.a1, r1.a2], [r2.a1, r2.a2]], dtype=float)
    B = np.array([r1.b, r2.b], dtype=float)
    if abs(np.linalg.det(A)) < TOL:          # rectas paralelas: no se cruzan
        return None
    x, y = np.linalg.solve(A, B)
    return float(x), float(y)


def resolver(c1, c2, restricciones, tipo="max"):
    """
    Resuelve el problema por enumeración de vértices.
    Devuelve un diccionario con: estado, vértices, óptimo y mensaje.
    """
    # Paso 1: agregar la no negatividad (x >= 0, y >= 0)
    no_neg = [Restriccion(1, 0, ">=", 0, "x ≥ 0"), Restriccion(0, 1, ">=", 0, "y ≥ 0")]
    todas = restricciones + no_neg

    # Paso 2: una "caja" muy grande (x <= M, y <= M). Sirve para dos cosas:
    #   - poder sombrear regiones infinitas en la gráfica
    #   - detectar problemas NO ACOTADOS (si el óptimo cae en la caja, no hay límite real)
    escala = max([abs(r.b) for r in restricciones] + [1])
    M = 1000 * escala
    caja = [Restriccion(1, 0, "<=", M, "caja"), Restriccion(0, 1, "<=", M, "caja")]

    # Paso 3: cruces entre todos los pares de rectas
    candidatos = []
    for r1, r2 in combinations(todas + caja, 2):
        p = cruce(r1, r2)
        if p is not None:
            artificial = r1 in caja or r2 in caja   # vértice creado por la caja
            candidatos.append((p, artificial))

    # Paso 4: quedarnos con los factibles (cumplen todo, incluida la caja), sin repetidos
    vertices, vistos = [], set()
    for (x, y), artificial in candidatos:
        if all(r.se_cumple(x, y) for r in todas + caja):
            clave = (round(x, 6), round(y, 6))
            if clave not in vistos:
                vistos.add(clave)
                vertices.append({"x": x, "y": y, "Z": c1 * x + c2 * y, "artificial": artificial})

    if not vertices:
        return {"estado": "infactible", "vertices": [], "optimo": None,
                "mensaje": "No existe ningún punto que cumpla todas las restricciones (problema infactible)."}

    # Paso 5: evaluar Z y elegir el mejor vértice
    mejor = max if tipo == "max" else min
    z_opt = mejor(v["Z"] for v in vertices)
    ganadores = [v for v in vertices if abs(v["Z"] - z_opt) <= TOL * max(1, abs(z_opt))]

    if any(v["artificial"] for v in ganadores):
        return {"estado": "no acotado", "vertices": vertices, "optimo": None,
                "mensaje": "La región factible es abierta en la dirección que mejora Z: "
                           "el problema es NO ACOTADO (Z puede mejorar sin límite)."}

    optimo = ganadores[0]
    if len(ganadores) > 1:
        puntos = " y ".join(f"({v['x']:.2f}, {v['y']:.2f})" for v in ganadores)
        mensaje = (f"Óptimos alternativos: Z = {z_opt:.4g} en todo el segmento entre {puntos}.")
        estado = "óptimos alternativos"
    else:
        mensaje = f"Solución óptima única: x = {optimo['x']:.4g}, y = {optimo['y']:.4g}, Z = {z_opt:.4g}."
        estado = "óptimo"

    return {"estado": estado, "vertices": vertices, "optimo": optimo,
            "ganadores": ganadores, "mensaje": mensaje}


def holguras(restricciones, x, y):
    """Holgura/excedente de cada restricción en el óptimo: indica cuáles son 'activas' (limitantes)."""
    filas = []
    for i, r in enumerate(restricciones, start=1):
        usado = r.a1 * x + r.a2 * y
        dif = r.b - usado if r.signo == "<=" else usado - r.b
        filas.append({"Restricción": r.nombre or f"R{i}", "Ecuación": r.texto(),
                      "Lado izq. en el óptimo": round(usado, 4), "Lado der. (b)": r.b,
                      "Holgura / excedente": round(dif, 4),
                      "¿Activa?": "Sí (limita)" if abs(dif) <= 1e-6 else "No"})
    return filas


def graficar(c1, c2, restricciones, resultado, tipo="max"):
    """Dibuja rectas, región factible sombreada, vértices, óptimo y recta de Z óptima."""
    reales = [v for v in resultado["vertices"] if not v["artificial"]]

    # Límites del dibujo: que se vean los vértices y los cortes de cada recta con los ejes
    puntos = [(v["x"], v["y"]) for v in reales]
    for r in restricciones:
        if abs(r.a1) > TOL and r.b / r.a1 > 0:
            puntos.append((r.b / r.a1, 0))
        if abs(r.a2) > TOL and r.b / r.a2 > 0:
            puntos.append((0, r.b / r.a2))
    xmax = 1.25 * max([p[0] for p in puntos] + [1])
    ymax = 1.25 * max([p[1] for p in puntos] + [1])

    fig, ax = plt.subplots(figsize=(8, 6))
    xs = np.linspace(0, xmax, 400)
    colores = plt.cm.tab10.colors

    # Rectas de cada restricción
    for i, r in enumerate(restricciones):
        etiqueta = f"{r.nombre or 'R' + str(i + 1)}: {r.texto()}"
        if abs(r.a2) > TOL:
            ax.plot(xs, (r.b - r.a1 * xs) / r.a2, color=colores[i % 10], lw=2, label=etiqueta)
        else:                                   # recta vertical (no tiene y)
            ax.axvline(r.b / r.a1, color=colores[i % 10], lw=2, label=etiqueta)

    # Región factible: polígono con los vértices ordenados por ángulo alrededor del centro
    if resultado["vertices"]:
        P = np.array([[v["x"], v["y"]] for v in resultado["vertices"]])
        centro = P.mean(axis=0)
        orden = np.argsort(np.arctan2(P[:, 1] - centro[1], P[:, 0] - centro[0]))
        ax.fill(P[orden, 0], P[orden, 1], color="limegreen", alpha=0.3, label="Región factible")

    # Vértices
    for v in reales:
        ax.plot(v["x"], v["y"], "ko", ms=6)
        ax.annotate(f"({v['x']:.2f}, {v['y']:.2f})", (v["x"], v["y"]),
                    textcoords="offset points", xytext=(6, 6), fontsize=9)

    # Óptimo y recta de nivel de Z que pasa por él
    if resultado["optimo"]:
        o = resultado["optimo"]
        if abs(c2) > TOL:
            ax.plot(xs, (o["Z"] - c1 * xs) / c2, "k--", lw=1.2, label=f"Z óptima = {o['Z']:.4g}")
        for g in resultado["ganadores"]:
            ax.plot(g["x"], g["y"], marker="*", color="red", ms=18, zorder=5)
        ax.plot([], [], "r*", ms=12, label="Óptimo")

    ax.set_xlim(0, xmax)
    ax.set_ylim(0, ymax)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_title(f"{'Maximizar' if tipo == 'max' else 'Minimizar'} Z = {c1:g}x + {c2:g}y")
    ax.grid(alpha=0.3)
    ax.legend(loc="upper right", fontsize=8)
    fig.tight_layout()
    return fig
