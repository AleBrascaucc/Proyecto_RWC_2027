"""Regenera datos.js a partir de los CSV que exporta el notebook (celdas 3 y 4).

Uso (desde la carpeta del proyecto):
    python actualizar_datos.py                 # lee los resultados_*.csv de esta carpeta
    python actualizar_datos.py otra_carpeta    # los lee de otra carpeta

La página (index.html, estilos.css, app.js) no se toca: solo cambian los datos.
"""
import csv, io, json, sys
from pathlib import Path

carpeta = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent
ARCHIVOS = {
    "torneo":   "resultados_torneo.csv",    # probabilidad de llegar a cada ronda (celda 4)
    "grupos":   "resultados_grupos.csv",    # posiciones en el grupo (celda 3)
    "partidos": "resultados_partidos.csv",  # los 36 partidos de grupo (celda 3)
    "cruces":   "resultados_cruces.csv",    # quién gana cada cruce posible (celda 4)
}
faltan = [f for f in ARCHIVOS.values() if not (carpeta / f).exists()]
if faltan or not (carpeta / "resultados_meta.csv").exists():
    if not (carpeta / "resultados_meta.csv").exists():
        faltan.append("resultados_meta.csv")
    sys.exit("Faltan archivos en " + str(carpeta.resolve()) + ": " + ", ".join(faltan))

datos = {k: (carpeta / f).read_text(encoding="utf-8").replace("\r\n", "\n") for k, f in ARCHIVOS.items()}

# resultados_meta.csv puede venir con encabezado (ultimo_partido,n_simulaciones) o como pares clave,valor
filas = list(csv.reader(io.StringIO((carpeta / "resultados_meta.csv").read_text(encoding="utf-8"))))
if filas and filas[0] == ["ultimo_partido", "n_simulaciones"]:
    meta = dict(zip(filas[0], filas[1]))
else:
    meta = {f[0]: f[1] for f in filas if len(f) >= 2}
datos["corrida"] = f"ultimo_partido,n_simulaciones\n{meta['ultimo_partido']},{meta['n_simulaciones']}\n"

salida = Path(__file__).parent / "datos.js"   # siempre junto a la página
salida.write_text("// Datos del dashboard. Se regenera con actualizar_datos.py a partir de los resultados_*.csv del notebook. No editar a mano.\n"
                  "const CSV = " + json.dumps(datos, ensure_ascii=False) + ";\n", encoding="utf-8")
print(f"Listo: {salida.name} actualizado ({meta['n_simulaciones']} simulaciones, datos hasta {meta['ultimo_partido']}).")
