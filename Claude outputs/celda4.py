# =============== CELDA 4: CUADRO ELIMINATORIO Y CAMPEÓN (corre después de las celdas 1, 2 y 3) ===============
# Fuente de llaves y tabla de terceros: página del Mundial 2027 en Wikipedia (consistente con el artículo de World Rugby).
# Por cada combinación de 4 grupos con tercero clasificado: qué tercero enfrenta a A1, B1, C1, D1
TERCEROS = {
 "ABCD": "CDAB", "ABCE": "CEAB", "ABCF": "CFAB", "ABDE": "EDAB", "ABDF": "FDAB",
 "ABEF": "EFAB", "ACDE": "CDAE", "ACDF": "CDAF", "ACEF": "CEAF", "ADEF": "EDAF",
 "BCDE": "CDEB", "BCDF": "CDFB", "BCEF": "CEFB", "BDEF": "EDFB", "CDEF": "CDEF"}

# ---- probabilidad de que A le gane a B en un partido de eliminación (sin empates) ----
EQUIPOS = sorted(POOL_DE)
def p_gana(a, b):
    """Mundial, cancha neutral (Australia, de local), descanso igual. Se promedia en ambos sentidos para que sea simétrico."""
    def una(h, v):
        ventaja = HFA * (1 if h == "AUS" else -1 if v == "AUS" else 0)
        x = {"elo_diff": elo[h] + ventaja - elo[v], "neutral": int(ventaja == 0),
             "dif_forma_gan": ult.forma_gan[h] - ult.forma_gan[v], "dif_forma_margen": ult.forma_margen[h] - ult.forma_margen[v],
             "dif_descanso": 0, "comp_rwc": 1, "comp_rwc_qual": 0, "comp_six_nations": 0,
             "comp_rugby_championship": 0, "comp_tier2_comp": 0, "comp_warmup": 0}
        return x
    filas = pd.DataFrame([una(a, b), una(b, a)])[VARS]
    p = mod.predict_proba(filas)[:, 1]
    return (p[0] + 1 - p[1]) / 2
P = {(a, b): p_gana(a, b) for a in EQUIPOS for b in EQUIPOS if a != b}

def juega(a, b):
    return a if rng.random() < P[(a, b)] else b

def torneo():
    orden, mejores3, _ = fase_de_grupos()
    g1 = {p: l[0] for p, l in orden.items()}; g2 = {p: l[1] for p, l in orden.items()}
    clave = "".join(sorted(POOL_DE[t] for t in mejores3))
    t3 = {p: orden[p][2] for p in orden}
    vs_A, vs_B, vs_C, vs_D = (t3[g] for g in TERCEROS[clave])
    # octavos (numeración oficial)
    o = {1: juega(g2["C"], g2["F"]), 2: juega(g1["A"], vs_A), 3: juega(g1["E"], g2["D"]), 4: juega(g1["B"], vs_B),
         5: juega(g1["C"], vs_C),    6: juega(g1["D"], vs_D),  7: juega(g2["A"], g2["E"]), 8: juega(g1["F"], g2["B"])}
    octavos = set(g1.values()) | set(g2.values()) | set(t3[g] for g in "ABCDEF" if t3[g] in mejores3)
    cuartos = [o[i] for i in range(1, 9)]
    c = {1: juega(o[2], o[4]), 2: juega(o[1], o[3]), 3: juega(o[5], o[6]), 4: juega(o[7], o[8])}
    s1, s2 = juega(c[1], c[2]), juega(c[3], c[4])
    campeon = juega(s1, s2)
    return octavos, set(cuartos), set(c.values()), {s1, s2}, campeon

N_SIM = 10_000
cont = {t: np.zeros(5) for t in EQUIPOS}      # octavos, cuartos, semis, final, campeón
t0 = time.time()
for _ in range(N_SIM):
    octavos, cuartos, semis, final, campeon = torneo()
    for i, conj in enumerate((octavos, cuartos, semis, final)):
        for t in conj: cont[t][i] += 1
    cont[campeon][4] += 1

tabla_final = pd.DataFrame({t: v / N_SIM for t, v in cont.items()}, index=["octavos", "cuartos", "semis", "final", "campeón"]).T
tabla_final.insert(0, "grupo", [POOL_DE[t] for t in tabla_final.index])
tabla_final = tabla_final.sort_values("campeón", ascending=False)
print(f"{N_SIM:,} Mundiales simulados en {time.time()-t0:.0f}s\n")
print((tabla_final.assign(**{c: tabla_final[c].map("{:.1%}".format) for c in ["octavos", "cuartos", "semis", "final", "campeón"]})).to_string())
print("\nControl: suma de campeón =", round(tabla_final["campeón"].sum(), 3), "| suma de finalistas =", round(tabla_final["final"].sum(), 3))

# ---- exportar para el dashboard ----
tabla_final.to_csv("resultados_torneo.csv", index_label="equipo")
pd.DataFrame([{"a": a, "b": b, "p_a_gana": p} for (a, b), p in P.items()]).to_csv("resultados_cruces.csv", index=False)
pd.DataFrame([{"ultimo_partido": str(hist.date.max().date()), "n_simulaciones": N_SIM}]).to_csv("resultados_meta.csv", index=False)
print("\nArchivos guardados: resultados_torneo, resultados_grupos, resultados_partidos, resultados_cruces y resultados_meta (.csv)")
