# =============== CELDA 3: FASE DE GRUPOS (corre después de las celdas 1 y 2) ===============
import time
from collections import Counter

POOLS = {"A": ["AUS","NZL","CHI","HKG"], "B": ["RSA","ITA","GEO","ROU"],
         "C": ["FIJ","ESP","ARG","CAN"], "D": ["SCO","URU","IRE","POR"],
         "E": ["FRA","USA","JPN","SAM"], "F": ["ENG","WAL","TON","ZIM"]}
POOL_DE = {t: p for p, ts in POOLS.items() for t in ts}

# ---- 1) los 36 partidos de grupo con sus variables (foto de hoy) ----
fx = df[(df.comp == "rwc") & df.home_score.isna() & (df.date >= "2027-01-01")].sort_values("date").reset_index(drop=True)
assert len(fx) == 36 and all(POOL_DE[a] == POOL_DE[b] for a, b in zip(fx.home, fx.away)), "revisar fixtures/grupos"

ult = largo.groupby("eq").tail(N).groupby("eq").agg(forma_gan=("gano", "mean"), forma_margen=("margen", "mean"))
fx["elo_h"], fx["elo_a"] = fx.home.map(elo), fx.away.map(elo)
fx["ventaja"] = HFA * fx.venue_country
fx["elo_diff"] = fx.elo_h + fx.ventaja - fx.elo_a
fx["neutral"] = (fx.venue_country == 0).astype(int)
fx["dif_forma_gan"] = fx.home.map(ult.forma_gan) - fx.away.map(ult.forma_gan)
fx["dif_forma_margen"] = fx.home.map(ult.forma_margen) - fx.away.map(ult.forma_margen)
# descanso: antes de su primer partido, 180 (el Mundial queda lejos del último partido registrado);
# después, los días desde su partido anterior del Mundial
prev = {}; desc_h, desc_a = [], []
for r_ in fx.itertuples():
    desc_h.append(min((r_.date - prev[r_.home]).days, 180) if r_.home in prev else 180)
    desc_a.append(min((r_.date - prev[r_.away]).days, 180) if r_.away in prev else 180)
    prev[r_.home] = prev[r_.away] = r_.date
fx["dif_descanso"] = np.array(desc_h) - np.array(desc_a)
for c in ["rwc", "rwc_qual", "six_nations", "rugby_championship", "tier2_comp", "warmup"]:
    fx[f"comp_{c}"] = int(c == "rwc")
fx["p_local"] = mod.predict_proba(fx[VARS])[:, 1]       # P(gana el local), sin contar empates

# ---- 2) simulador de marcador ajustado con todo el historial (con más peso a lo reciente) ----
rng = np.random.default_rng(2027)
marc = Marcador(recientes(hist, hist.date.max()), rng)

# ---- 3) una fase de grupos completa ----
ELO_RANK = {t: elo[t] for t in elo}      # aproxima el ranking mundial para el último desempate
def fase_de_grupos():
    st = {t: dict(pts=0, dif=0, pf=0, tr=0) for t in POOL_DE}
    gano = {}                                            # gano[(a,b)] = True si a le ganó a b
    for r_ in fx.itertuples():
        p = r_.p_local; fav_local = p >= 0.5
        pf, pd_, tf, td = marc.simular(p if fav_local else 1 - p)
        ph, pa, th, ta = (pf, pd_, tf, td) if fav_local else (pd_, pf, td, tf)
        for eq, a_fav, en_c, tr in ((r_.home, ph, pa, th), (r_.away, pa, ph, ta)):
            s = st[eq]
            s["pts"] += (4 if a_fav > en_c else 2 if a_fav == en_c else 0) + int(tr >= 4) + int(a_fav < en_c and en_c - a_fav < 8)
            s["dif"] += a_fav - en_c; s["pf"] += a_fav; s["tr"] += tr
        gano[(r_.home, r_.away)] = ph > pa; gano[(r_.away, r_.home)] = pa > ph
    orden, terceros = {}, []
    for pool, eqs in POOLS.items():
        res_pool = []
        for pts in sorted({st[t]["pts"] for t in eqs}, reverse=True):
            g = [t for t in eqs if st[t]["pts"] == pts]
            if len(g) == 2 and (gano[(g[0], g[1])] or gano[(g[1], g[0])]):   # empate de 2: gana el que ganó el cruce
                g = g if gano[(g[0], g[1])] else g[::-1]
            else:
                g = sorted(g, key=lambda t: (st[t]["dif"], st[t]["pf"], st[t]["tr"], ELO_RANK[t]), reverse=True)
            res_pool += g
        orden[pool] = res_pool
        terceros.append(res_pool[2])
    # mejores 4 terceros: puntos, diferencia de puntos, puntos a favor, tries a favor, ranking
    terceros.sort(key=lambda t: (st[t]["pts"], st[t]["dif"], st[t]["pf"], st[t]["tr"], ELO_RANK[t]), reverse=True)
    return orden, terceros[:4], st

# ---- 4) 10.000 fases de grupos: ¿quién avanza? ----
N_TORNEOS = 10_000
pos = {t: np.zeros(4) for t in POOL_DE}; como_3ro = Counter(); combos = Counter(); pts_tot = Counter()
t0 = time.time()
for _ in range(N_TORNEOS):
    orden, mejores3, st = fase_de_grupos()
    for pool, lst in orden.items():
        for i, t in enumerate(lst): pos[t][i] += 1
    for t in mejores3: como_3ro[t] += 1
    combos["".join(sorted(POOL_DE[t] for t in mejores3))] += 1
    for t in POOL_DE: pts_tot[t] += st[t]["pts"]

out = pd.DataFrame([{"grupo": POOL_DE[t], "equipo": t, "1º": pos[t][0] / N_TORNEOS, "2º": pos[t][1] / N_TORNEOS,
                     "3º": pos[t][2] / N_TORNEOS, "4º": pos[t][3] / N_TORNEOS,
                     "avanza como 3º": como_3ro[t] / N_TORNEOS,
                     "avanza (total)": (pos[t][0] + pos[t][1]) / N_TORNEOS + como_3ro[t] / N_TORNEOS,
                     "pts medios": pts_tot[t] / N_TORNEOS} for t in POOL_DE]).sort_values(["grupo", "1º"], ascending=[True, False])
print(f"{N_TORNEOS:,} fases de grupos en {time.time()-t0:.0f}s\n")
print(out.round(3).to_string(index=False))
print("\nCombinaciones de grupos de los 4 mejores terceros (las más frecuentes):")
print(pd.Series(combos).sort_values(ascending=False).head(8).div(N_TORNEOS).round(3).to_string())
print(f"Combinaciones distintas vistas: {len(combos)} de 15")
print("\nControl: suma de 'avanza (total)' (debe dar 16):", round(out["avanza (total)"].sum(), 2))

# ---- exportar para el dashboard ----
out.to_csv("resultados_grupos.csv", index=False)
fx_exp = fx[["date", "home", "away", "venue_country", "p_local"]].copy()
fx_exp["grupo"] = fx.home.map(POOL_DE); fx_exp.to_csv("resultados_partidos.csv", index=False)
pd.Series(combos).div(N_TORNEOS).rename("prob").to_csv("resultados_terceros.csv", index_label="grupos")
