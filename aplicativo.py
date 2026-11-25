"""
APLICATIVO SEMIAUTOMATIZADO - INVESTIGACIÓN DE OPERACIONES  (interfaz Tkinter)
=============================================================================
Este archivo es SOLO la interfaz: lee los datos que escribe el usuario, los envía a los
motores de cálculo y muestra los resultados. Los cálculos están en:

    metodo_grafico.py  -> Método Gráfico (Programación Lineal con 2 variables)
    teoria_colas.py    -> Teoría de Colas (M/M/1 y M/M/s)

Ejecutar:  python aplicativo.py      (o doble clic en el .exe si ya se creó)
"""

import tkinter as tk
from tkinter import messagebox, ttk

import matplotlib
matplotlib.use("Agg")   # las figuras se dibujan "en memoria" y luego se incrustan en la ventana
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

import metodo_grafico as mg
import teoria_colas as tc

# Ejemplo precargado del método gráfico: (nombre, a1, a2, signo, b)
EJEMPLO_PL = [("R1", 1, 0, "<=", 4), ("R2", 0, 2, "<=", 12), ("R3", 3, 2, "<=", 18)]


# =============================================================================
# FUNCIONES DE AYUDA (se usan en ambos módulos)
# =============================================================================
def leer_numero(entrada, nombre, entero=False, minimo=None):
    """Convierte el texto de una casilla en número. Si no se puede, avisa cuál casilla está mal."""
    texto = entrada.get().strip().replace(",", ".")
    try:
        valor = int(float(texto)) if entero else float(texto)
    except ValueError:
        raise ValueError(f"'{nombre}' debe ser un número (escribiste: '{texto}').")
    if minimo is not None and valor < minimo:
        raise ValueError(f"'{nombre}' debe ser mayor o igual a {minimo}.")
    return valor


def mostrar_figura(contenedor, fig):
    """Borra la gráfica anterior del contenedor y pone la nueva."""
    for widget in contenedor.winfo_children():
        widget.destroy()
    lienzo = FigureCanvasTkAgg(fig, master=contenedor)
    lienzo.draw()
    lienzo.get_tk_widget().pack(fill="both", expand=True)
    plt.close(fig)   # libera memoria (la imagen ya quedó en la ventana)


def crear_tabla(padre, columnas, alto=6):
    """Crea una tabla (Treeview) con las columnas indicadas."""
    tabla = ttk.Treeview(padre, columns=columnas, show="headings", height=alto)
    for c in columnas:
        tabla.heading(c, text=c)
        tabla.column(c, width=95, anchor="center")
    return tabla


def llenar_tabla(tabla, filas):
    """Borra el contenido de la tabla y escribe las filas nuevas (lista de tuplas)."""
    tabla.delete(*tabla.get_children())
    for fila in filas:
        tabla.insert("", "end", values=fila)


def casilla(padre, valor, ancho=10):
    """Casilla de texto con un valor inicial."""
    e = ttk.Entry(padre, width=ancho, justify="center")
    e.insert(0, str(valor))
    return e


# =============================================================================
# MÓDULO 1: MÉTODO GRÁFICO
# =============================================================================
class PestanaMetodoGrafico(ttk.Frame):
    def __init__(self, padre):
        super().__init__(padre, padding=10)
        izq = ttk.Frame(self)
        izq.pack(side="left", fill="y", padx=(0, 10))
        self.zona_grafica = ttk.Frame(self)
        self.zona_grafica.pack(side="right", fill="both", expand=True)

        # ---------- ENTRADA: función objetivo ----------
        fo = ttk.LabelFrame(izq, text="1. Función objetivo   Z = c1·x + c2·y", padding=8)
        fo.pack(fill="x")
        self.tipo = ttk.Combobox(fo, values=["Maximizar", "Minimizar"], state="readonly", width=11)
        self.tipo.set("Maximizar")
        self.tipo.grid(row=0, column=0, padx=4)
        ttk.Label(fo, text="c1 (coef. x):").grid(row=0, column=1)
        self.c1 = casilla(fo, 3, 7)
        self.c1.grid(row=0, column=2, padx=4)
        ttk.Label(fo, text="c2 (coef. y):").grid(row=0, column=3)
        self.c2 = casilla(fo, 5, 7)
        self.c2.grid(row=0, column=4, padx=4)

        # ---------- ENTRADA: restricciones (filas dinámicas) ----------
        marco_r = ttk.LabelFrame(izq, text="2. Restricciones   a1·x + a2·y (signo) b", padding=8)
        marco_r.pack(fill="x", pady=8)
        self.zona_filas = ttk.Frame(marco_r)
        self.zona_filas.pack(fill="x")
        for col, titulo in enumerate(["Nombre", "a1 (x)", "a2 (y)", "Signo", "b", ""]):
            ttk.Label(self.zona_filas, text=titulo, font=("Segoe UI", 9, "bold")).grid(row=0, column=col)
        self.filas = []   # cada fila es un diccionario con sus casillas
        ttk.Label(marco_r, text="x ≥ 0 y y ≥ 0 se incluyen automáticamente.",
                  foreground="gray").pack(anchor="w", pady=(4, 0))

        botones = ttk.Frame(izq)
        botones.pack(fill="x")
        ttk.Button(botones, text="+ Agregar restricción", command=self.agregar_fila).pack(side="left")
        ttk.Button(botones, text="Restaurar ejemplo", command=self.cargar_ejemplo).pack(side="left", padx=5)
        ttk.Button(botones, text="CALCULAR", command=self.calcular).pack(side="right")

        # ---------- SALIDA: mensaje y tablas ----------
        self.mensaje = ttk.Label(izq, text="", wraplength=470, font=("Segoe UI", 10, "bold"))
        self.mensaje.pack(fill="x", pady=8)
        ttk.Label(izq, text="Vértices de la región factible").pack(anchor="w")
        self.tabla_vertices = crear_tabla(izq, ("x", "y", "Z", "¿Óptimo?"))
        self.tabla_vertices.pack(fill="x")
        ttk.Label(izq, text="Holguras en el óptimo").pack(anchor="w", pady=(8, 0))
        self.tabla_holguras = crear_tabla(izq, ("Restricción", "Usado", "b", "Holgura", "¿Activa?"), 5)
        self.tabla_holguras.pack(fill="x")

        self.cargar_ejemplo()

    def agregar_fila(self, nombre="", a1=0, a2=0, signo="<=", b=0):
        """Agrega una fila de casillas para una restricción nueva."""
        r = len(self.filas) + 1
        fila = {"nombre": casilla(self.zona_filas, nombre or f"R{r}", 6),
                "a1": casilla(self.zona_filas, a1, 7),
                "a2": casilla(self.zona_filas, a2, 7),
                "signo": ttk.Combobox(self.zona_filas, values=["<=", ">=", "="], state="readonly", width=4),
                "b": casilla(self.zona_filas, b, 8)}
        fila["signo"].set(signo)
        fila["borrar"] = ttk.Button(self.zona_filas, text="✕", width=3, command=lambda: self.borrar_fila(fila))
        self.filas.append(fila)
        self.reacomodar_filas()

    def borrar_fila(self, fila):
        for w in fila.values():
            w.destroy()
        self.filas.remove(fila)
        self.reacomodar_filas()

    def reacomodar_filas(self):
        """Vuelve a ubicar las filas en la cuadrícula después de agregar o borrar."""
        for i, fila in enumerate(self.filas, start=1):
            for col, clave in enumerate(["nombre", "a1", "a2", "signo", "b", "borrar"]):
                fila[clave].grid(row=i, column=col, padx=2, pady=2)

    def cargar_ejemplo(self):
        for fila in list(self.filas):
            self.borrar_fila(fila)
        for datos in EJEMPLO_PL:
            self.agregar_fila(*datos)
        self.calcular()

    def calcular(self):
        # 1. Leer y validar los datos de la pantalla
        try:
            c1 = leer_numero(self.c1, "c1")
            c2 = leer_numero(self.c2, "c2")
            restricciones = []
            for f in self.filas:
                n = f["nombre"].get()
                r = mg.Restriccion(leer_numero(f["a1"], f"a1 de {n}"), leer_numero(f["a2"], f"a2 de {n}"),
                                   f["signo"].get(), leer_numero(f["b"], f"b de {n}"), n)
                if r.a1 == 0 and r.a2 == 0:
                    raise ValueError(f"En {n}, a1 y a2 no pueden ser ambos cero.")
                restricciones.append(r)
            if not restricciones:
                raise ValueError("Agrega al menos una restricción.")
        except ValueError as error:
            messagebox.showerror("Dato inválido", str(error))
            return

        # 2. Enviar al motor de cálculo
        tipo = "max" if self.tipo.get() == "Maximizar" else "min"
        res = mg.resolver(c1, c2, restricciones, tipo)

        # 3. Mostrar resultados
        self.mensaje.config(text=res["mensaje"], foreground="darkgreen" if res["optimo"] else "red")
        reales = [v for v in res["vertices"] if not v["artificial"]]
        ganadores = res.get("ganadores", [])
        llenar_tabla(self.tabla_vertices, [(f"{v['x']:.4g}", f"{v['y']:.4g}", f"{v['Z']:.4g}",
                                            "★" if v in ganadores else "") for v in reales])
        if res["optimo"]:
            h = mg.holguras(restricciones, res["optimo"]["x"], res["optimo"]["y"])
            llenar_tabla(self.tabla_holguras, [(f["Restricción"], f["Lado izq. en el óptimo"], f["Lado der. (b)"],
                                                f["Holgura / excedente"], f["¿Activa?"]) for f in h])
        else:
            llenar_tabla(self.tabla_holguras, [])
        if res["vertices"]:
            mostrar_figura(self.zona_grafica, mg.graficar(c1, c2, restricciones, res, tipo))
        else:
            mostrar_figura(self.zona_grafica, plt.figure())


# =============================================================================
# MÓDULO 2: TEORÍA DE COLAS
# =============================================================================
class PestanaColas(ttk.Frame):
    def __init__(self, padre):
        super().__init__(padre, padding=10)
        izq = ttk.Frame(self)
        izq.pack(side="left", fill="y", padx=(0, 10))
        der = ttk.Notebook(self)
        der.pack(side="right", fill="both", expand=True)
        self.zona_costos = ttk.Frame(der)
        self.zona_pn = ttk.Frame(der)
        der.add(self.zona_costos, text="Análisis de costos")
        der.add(self.zona_pn, text="Distribución de clientes (Pn)")

        # ---------- ENTRADA: parámetros y costos ----------
        p = ttk.LabelFrame(izq, text="1. Parámetros y costos", padding=8)
        p.pack(fill="x")
        ttk.Label(p, text="Unidad de tiempo:").grid(row=0, column=0, sticky="w")
        self.unidad = ttk.Combobox(p, values=["hora", "minuto", "día"], state="readonly", width=9)
        self.unidad.set("hora")
        self.unidad.grid(row=0, column=1, sticky="w", pady=2)

        campos = [("lam", "λ: llegadas por unidad de tiempo", 10),
                  ("mu", "μ: atendidos por unidad de tiempo (por servidor)", 4),
                  ("s", "s: número de servidores", 3),
                  ("cs", "Cs: costo por servidor por unidad de tiempo", 15000),
                  ("cw", "Cw: costo de espera por cliente por unidad de tiempo", 20000)]
        self.e = {}
        for i, (clave, texto, valor) in enumerate(campos, start=1):
            ttk.Label(p, text=texto).grid(row=i, column=0, sticky="w")
            self.e[clave] = casilla(p, valor, 12)
            self.e[clave].grid(row=i, column=1, sticky="w", pady=2)

        ttk.Label(p, text="Costo de espera sobre:").grid(row=6, column=0, sticky="w")
        self.base = tk.StringVar(value="L")
        rb = ttk.Frame(p)
        rb.grid(row=6, column=1, sticky="w")
        ttk.Radiobutton(rb, text="L (sistema)", variable=self.base, value="L").pack(side="left")
        ttk.Radiobutton(rb, text="Lq (fila)", variable=self.base, value="Lq").pack(side="left")
        ttk.Button(izq, text="CALCULAR", command=self.calcular).pack(anchor="e", pady=6)

        # ---------- SALIDA: medidas de desempeño ----------
        m = ttk.LabelFrame(izq, text="2. Medidas de desempeño", padding=8)
        m.pack(fill="x")
        self.estado = ttk.Label(m, text="", wraplength=480, font=("Segoe UI", 10, "bold"))
        self.estado.grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 4))
        nombres = ["Utilización ρ", "Sistema vacío P0", "Prob. de esperar Pw", "Costo total",
                   "Lq (en fila)", "L (en sistema)", "Wq (espera en fila)", "W (tiempo en sistema)"]
        self.valores = {}
        for i, n in enumerate(nombres):
            fila, col = divmod(i, 2)
            ttk.Label(m, text=n + ":").grid(row=fila + 1, column=col * 2, sticky="w", padx=(0, 4))
            self.valores[n] = ttk.Label(m, text="-", font=("Segoe UI", 10, "bold"), width=18)
            self.valores[n].grid(row=fila + 1, column=col * 2 + 1, sticky="w")
        self.little = ttk.Label(m, text="", foreground="gray")
        self.little.grid(row=6, column=0, columnspan=4, sticky="w", pady=(4, 0))

        # ---------- SALIDA: análisis de costos ----------
        ttk.Label(izq, text="3. ¿Cuántos servidores conviene tener?").pack(anchor="w", pady=(10, 0))
        self.tabla_costos = crear_tabla(izq, ("s", "ρ", "L", "Lq", "C. servicio", "C. espera", "C. total", "Óptimo"), 7)
        for c in ("s", "ρ", "Óptimo"):
            self.tabla_costos.column(c, width=50)
        self.tabla_costos.pack(fill="x")
        self.msg_opt = ttk.Label(izq, text="", foreground="darkgreen", font=("Segoe UI", 10, "bold"))
        self.msg_opt.pack(anchor="w", pady=4)

        self.calcular()

    def calcular(self):
        # 1. Leer y validar
        try:
            lam = leer_numero(self.e["lam"], "λ", minimo=0.0001)
            mu = leer_numero(self.e["mu"], "μ", minimo=0.0001)
            s = leer_numero(self.e["s"], "s", entero=True, minimo=1)
            cs = leer_numero(self.e["cs"], "Cs", minimo=0)
            cw = leer_numero(self.e["cw"], "Cw", minimo=0)
        except ValueError as error:
            messagebox.showerror("Dato inválido", str(error))
            return
        u, base = self.unidad.get(), self.base.get()

        # 2. Motor de cálculo
        m = tc.medidas_mms(lam, mu, s)
        filas, s_opt = tc.analisis_costos(lam, mu, cs, cw, base)

        # 3. Mostrar medidas
        if not m["estable"]:
            self.estado.config(foreground="red",
                               text=f"Sistema INESTABLE: ρ = λ/(s·μ) = {m['rho']:.3f} ≥ 1. La fila crece sin "
                                    f"límite. Se necesitan al menos {int(lam // mu) + 1} servidores.")
            for lbl in self.valores.values():
                lbl.config(text="-")
            self.little.config(text="")
            mostrar_figura(self.zona_pn, plt.figure())
        else:
            modelo = "M/M/1" if s == 1 else f"M/M/{s}"
            self.estado.config(foreground="darkgreen", text=f"Modelo {modelo}: sistema estable.")
            total = tc.costo_total(m, cs, cw, base)[2]
            textos = {"Utilización ρ": f"{m['rho']:.1%}", "Sistema vacío P0": f"{m['P0']:.1%}",
                      "Prob. de esperar Pw": f"{m['Pw']:.1%}", "Costo total": f"${total:,.0f}/{u}",
                      "Lq (en fila)": f"{m['Lq']:.3f} clientes", "L (en sistema)": f"{m['L']:.3f} clientes",
                      "Wq (espera en fila)": f"{m['Wq']:.4f} {u}s", "W (tiempo en sistema)": f"{m['W']:.4f} {u}s"}
            for n, t in textos.items():
                self.valores[n].config(text=t)
            extra = f"   |   En minutos: Wq = {m['Wq'] * 60:.2f}, W = {m['W'] * 60:.2f}" if u == "hora" else ""
            self.little.config(text=f"Ley de Little: λ·W = {lam * m['W']:.4f} = L = {m['L']:.4f}{extra}")
            mostrar_figura(self.zona_pn, tc.graficar_pn(lam, mu, s, m["P0"]))

        # 4. Mostrar análisis de costos
        llenar_tabla(self.tabla_costos, [
            (f["Servidores (s)"], f"{f['Utilización ρ']:.0%}", f"{f['L']:.3f}", f"{f['Lq']:.3f}",
             f"${f['Costo servicio']:,.0f}", f"${f['Costo espera']:,.0f}", f"${f['Costo total']:,.0f}",
             "★" if f["Servidores (s)"] == s_opt else "") for f in filas])
        self.msg_opt.config(text=f"El número de servidores que minimiza el costo total es s = {s_opt}.")
        mostrar_figura(self.zona_costos, tc.graficar_costos(filas, s_opt))


# =============================================================================
# VENTANA PRINCIPAL
# =============================================================================
def main():
    raiz = tk.Tk()
    raiz.title("Aplicativo de Investigación de Operaciones")
    raiz.geometry("1400x820")
    pestanas = ttk.Notebook(raiz)
    pestanas.pack(fill="both", expand=True)
    pg, pc = PestanaMetodoGrafico(pestanas), PestanaColas(pestanas)
    pestanas.add(pg, text="  Método Gráfico (PL)  ")
    pestanas.add(pc, text="  Teoría de Colas (M/M/s)  ")
    # La tecla Enter recalcula la pestaña que esté abierta
    raiz.bind("<Return>", lambda _: (pg if pestanas.index("current") == 0 else pc).calcular())
    raiz.protocol("WM_DELETE_WINDOW", lambda: (raiz.quit(), raiz.destroy()))
    raiz.mainloop()


if __name__ == "__main__":
    main()
