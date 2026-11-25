"""
MOTOR DE CÁLCULO: TEORÍA DE COLAS  (modelos M/M/1 y M/M/s)
==========================================================

Notación:
    λ (lam) = tasa de llegadas   (clientes por unidad de tiempo, ej. clientes/hora)
    μ (mu)  = tasa de servicio de UN servidor (clientes que atiende por unidad de tiempo)
    s       = número de servidores en paralelo (s = 1 es el modelo M/M/1)

M/M/s significa: llegadas Poisson (M), tiempos de servicio exponenciales (M), s servidores,
una sola fila, disciplina FIFO y población/capacidad infinitas.

Condición de estabilidad:  ρ = λ / (s·μ) < 1
    Si ρ >= 1 llegan más clientes de los que se pueden atender y la fila crece sin fin.

Medidas de desempeño que calculamos:
    P0  = probabilidad de que el sistema esté vacío
    Pw  = probabilidad de que un cliente que llega tenga que esperar (fórmula de Erlang C)
    Lq  = número promedio de clientes en la FILA
    L   = número promedio de clientes en el SISTEMA (fila + siendo atendidos)
    Wq  = tiempo promedio en la FILA
    W   = tiempo promedio en el SISTEMA
Se relacionan con la Ley de Little:  L = λ·W   y   Lq = λ·Wq
"""

from math import factorial

import matplotlib.pyplot as plt


def medidas_mms(lam, mu, s):
    """Calcula todas las medidas de desempeño de un sistema M/M/s."""
    if lam <= 0 or mu <= 0 or s < 1:
        raise ValueError("λ y μ deben ser positivos y s >= 1.")

    r = lam / mu              # intensidad de tráfico (servidores 'ocupados' en promedio)
    rho = lam / (s * mu)      # utilización de cada servidor
    if rho >= 1:
        return {"estable": False, "rho": rho, "s": s}

    # P0: probabilidad de sistema vacío
    suma = sum(r ** n / factorial(n) for n in range(s))
    P0 = 1 / (suma + r ** s / (factorial(s) * (1 - rho)))

    # Probabilidad de esperar (Erlang C)
    Pw = P0 * r ** s / (factorial(s) * (1 - rho))

    Lq = P0 * r ** s * rho / (factorial(s) * (1 - rho) ** 2)
    L = Lq + r
    Wq = Lq / lam
    W = Wq + 1 / mu

    return {"estable": True, "s": s, "rho": rho, "P0": P0, "Pw": Pw,
            "Lq": Lq, "L": L, "Wq": Wq, "W": W}


def prob_n(lam, mu, s, n, P0):
    """Probabilidad de que haya exactamente n clientes en el sistema (Pn)."""
    r = lam / mu
    if n < s:
        return P0 * r ** n / factorial(n)
    return P0 * r ** n / (factorial(s) * s ** (n - s))


def costo_total(medidas, costo_servidor, costo_espera, base="L"):
    """
    Costo total por unidad de tiempo = costo de servicio + costo de espera
        Costo de servicio = Cs · s     (lo que cuesta tener s servidores)
        Costo de espera   = Cw · L     (o Cw · Lq si solo se cobra el tiempo en fila)
    """
    c_serv = costo_servidor * medidas["s"]
    c_esp = costo_espera * medidas[base]
    return c_serv, c_esp, c_serv + c_esp


def analisis_costos(lam, mu, costo_servidor, costo_espera, base="L", extra=6):
    """
    Compara el costo total para distintos números de servidores, desde el mínimo
    que hace estable el sistema hasta 'extra' servidores más. Devuelve tabla y el s óptimo.
    """
    s_min = int(lam // mu) + 1                 # menor s con ρ < 1
    filas = []
    for s in range(s_min, s_min + extra + 1):
        m = medidas_mms(lam, mu, s)
        c_serv, c_esp, total = costo_total(m, costo_servidor, costo_espera, base)
        filas.append({"Servidores (s)": s, "Utilización ρ": m["rho"], "L": m["L"], "Lq": m["Lq"],
                      "Wq": m["Wq"], "Costo servicio": c_serv, "Costo espera": c_esp,
                      "Costo total": total})
    s_opt = min(filas, key=lambda f: f["Costo total"])["Servidores (s)"]
    return filas, s_opt


def graficar_pn(lam, mu, s, P0, n_max=15):
    """Gráfica de barras de la distribución de probabilidad del número de clientes."""
    ns = list(range(n_max + 1))
    ps = [prob_n(lam, mu, s, n, P0) for n in ns]
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(ns, ps, color="steelblue")
    ax.set_xlabel("n (clientes en el sistema)")
    ax.set_ylabel("Probabilidad Pn")
    ax.set_title(f"Distribución del número de clientes (s = {s})")
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    return fig


def graficar_costos(filas, s_opt):
    """Curvas de costo de servicio, de espera y total vs. número de servidores."""
    s = [f["Servidores (s)"] for f in filas]
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(s, [f["Costo servicio"] for f in filas], "o-", label="Costo de servicio (sube)")
    ax.plot(s, [f["Costo espera"] for f in filas], "o-", label="Costo de espera (baja)")
    ax.plot(s, [f["Costo total"] for f in filas], "o-", lw=3, color="black", label="Costo total")
    opt = next(f for f in filas if f["Servidores (s)"] == s_opt)
    ax.plot(s_opt, opt["Costo total"], "r*", ms=18, label=f"Óptimo: s = {s_opt}")
    ax.set_xlabel("Número de servidores (s)")
    ax.set_ylabel("Costo por unidad de tiempo")
    ax.set_xticks(s)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=8)
    fig.tight_layout()
    return fig
