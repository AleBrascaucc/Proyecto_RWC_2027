# =============== CELDA 2: MODELO DEL MARCADOR (corre después de la celda 1) ===============
from scipy.stats import norm

# ---- modelo de probabilidad final, entrenado con todos los datos ----
# Se promedian dos modelos: uno completo y otro SIN la forma reciente en victorias
# (esa variable mejora la validación pero tiene un signo contraintuitivo; el promedio es un punto medio).
VARS_SIN = [v for v in VARS if v != "dif_forma_gan"]
def _ajustar(cols):
    m = make_pipeline(StandardScaler(), LogisticRegression(max_iter=1000))
    m.fit(datos[cols], datos.ganó_local, logisticregression__sample_weight=datos.peso.values)
    return m
_mod_a, _mod_b = _ajustar(VARS), _ajustar(VARS_SIN)

class Promedio:
    """Se usa igual que un modelo de sklearn: predict_proba(DataFrame con todas las variables)."""
    def predict_proba(self, X):
        p = (_mod_a.predict_proba(X[VARS])[:, 1] + _mod_b.predict_proba(X[VARS_SIN])[:, 1]) / 2
        return np.column_stack([1 - p, p])
mod = Promedio()

# ---- historial desde 2015 (incluye empates) en "perspectiva del favorito" ----
hist = res[res.date >= "2015-01-01"].copy()
hist["home_tries"] = d.loc[hist.index, "home_tries"]; hist["away_tries"] = d.loc[hist.index, "away_tries"]
hist["p"] = mod.predict_proba(hist[VARS])[:, 1]          # P(gana el local), sin contar empates
hist["fav_local"] = hist.p >= 0.5
hist["p_fav"] = np.where(hist.fav_local, hist.p, 1 - hist.p)
hist["fz"] = norm.ppf(hist.p_fav.clip(0.5, 0.999))       # qué tan desparejo es el partido
hist["pts_fav"] = np.where(hist.fav_local, hist.home_score, hist.away_score)
hist["pts_dog"] = np.where(hist.fav_local, hist.away_score, hist.home_score)
hist["tries_fav"] = np.where(hist.fav_local, hist.home_tries, hist.away_tries)
hist["tries_dog"] = np.where(hist.fav_local, hist.away_tries, hist.home_tries)
hist["empate"] = hist.pts_fav == hist.pts_dog
hist["fav_gano"] = hist.pts_fav > hist.pts_dog

K_TRIES = 1.15     # ajuste de ensayos, calibrado con 2025 (1.0 = sin ajuste)
VIDA_MEDIA = 1.0   # años: un partido de hace 1 año pesa la mitad que uno de hoy (el rugby anota cada vez más)
def recientes(h, fecha_ref, vida_media=VIDA_MEDIA, n=6000, seed=0):
    """Remuestrea el historial dando más peso a los partidos recientes."""
    edad = (pd.Timestamp(fecha_ref) - h.date).dt.days / 365.25
    w = 0.5 ** (edad / vida_media); w = w / w.sum()
    return h.loc[np.random.default_rng(seed).choice(h.index, n, p=w)]

class Marcador:
    """Simula puntos y tries de un partido a partir de la probabilidad de que gane el favorito."""
    def __init__(self, h, rng, k=K_TRIES):
        self.rng = rng
        self.k = k   # ajuste de ensayos: sortea con el historial de equipos de P*k puntos
        self.p_empate = h.empate.mean()
        nd = h[~h.empate]
        # margen del ganador: lognormal cuya media depende de lo desparejo del partido y de si ganó el favorito
        W = (nd.pts_fav - nd.pts_dog).abs()
        X = np.column_stack([np.ones(len(nd)), nd.fz, nd.fav_gano.astype(float)])
        self.beta, *_ = np.linalg.lstsq(X, np.log(W), rcond=None)
        self.sd_w = (np.log(W) - X @ self.beta).std()
        # puntos del perdedor dado el margen (muestreo empírico con margen parecido)
        perd = np.minimum(nd.pts_fav, nd.pts_dog).values
        self.W_hist, self.L_hist = W.values, perd
        self.L_por_W = {w: perd[np.abs(W.values - w) <= (2 if w < 40 else 8)] for w in range(1, 111)}
        self.puntos_empate = h[h.empate].pts_fav.values
        # tries dado los puntos (muestreo empírico)
        ht = h.dropna(subset=["tries_fav", "tries_dog"])
        self.pts_all = np.concatenate([ht.pts_fav, ht.pts_dog]); self.tr_all = np.concatenate([ht.tries_fav, ht.tries_dog])
        self.tr_por_p = {}
        for x in range(0, 141):
            v = 2
            while True:
                s = self.tr_all[np.abs(self.pts_all - x) <= v]
                if len(s) >= 20 or v > 25: break
                v += 1
            self.tr_por_p[x] = s

    def tries(self, pts):
        return self.rng.choice(self.tr_por_p[int(min(round(pts * self.k), 140))])

    def simular(self, p_fav):
        """Devuelve (pts_fav, pts_dog, tries_fav, tries_dog)."""
        r = self.rng
        u = r.random()
        if u < self.p_empate:
            x = int(r.choice(self.puntos_empate)); return x, x, self.tries(x), self.tries(x)
        fav_gana = (r.random() < p_fav)
        fz = norm.ppf(min(max(p_fav, 0.5), 0.999))
        mu = self.beta[0] + self.beta[1] * fz + self.beta[2] * float(fav_gana)
        W = int(max(1, round(np.exp(mu + self.sd_w * r.standard_normal()))))
        L = int(r.choice(self.L_por_W[min(W, 110)]))
        G = L + W
        pf, pd_ = (G, L) if fav_gana else (L, G)
        return pf, pd_, self.tries(pf), self.tries(pd_)

def bonus_puntos(pts_a, pts_b, tries_a, tries_b):
    """Bonus de A: +1 por 4+ tries, +1 si pierde por menos de 8."""
    return int(tries_a >= 4) + int(pts_a < pts_b and pts_b - pts_a < 8)

# =============== VALIDACIÓN: ajustar con partidos hasta 2024 y probar en 2025-2026 ===============
rng = np.random.default_rng(123)
m_fit = Marcador(recientes(hist[hist.date < "2025-01-01"], "2025-01-01"), rng)
test2 = hist[hist.date >= "2025-01-01"]
N_SIM = 100

filas = []
for r_ in test2.itertuples():
    for _ in range(N_SIM):
        pf, pd_, tf, td = m_fit.simular(r_.p_fav)
        filas.append((r_.Index, r_.fz, pf, pd_, tf, td))
sim = pd.DataFrame(filas, columns=["idx", "fz", "pts_fav", "pts_dog", "tries_fav", "tries_dog"])
sim["M"] = (sim.pts_fav - sim.pts_dog).abs()

def resumen(x, tries_ok=True):
    M = (x.pts_fav - x.pts_dog).abs()
    out = {
        "empates": (M == 0).mean(),
        "margen < 8": (M < 8).mean(),
        "margen >= 30": (M >= 30).mean(),
        "puntos totales (media)": (x.pts_fav + x.pts_dog).mean(),
        "favorito gana": (x.pts_fav > x.pts_dog).mean(),
    }
    if tries_ok:
        t4 = np.concatenate([(x.tries_fav >= 4), (x.tries_dog >= 4)]).mean()
        lb = np.concatenate([(x.pts_fav < x.pts_dog) & (x.pts_dog - x.pts_fav < 8), (x.pts_dog < x.pts_fav) & (x.pts_fav - x.pts_dog < 8)])
        perdio = np.concatenate([x.pts_fav < x.pts_dog, x.pts_dog < x.pts_fav])
        out["P(4+ tries) por equipo"] = t4
        out["P(4+ tries) favorito"] = (x.tries_fav >= 4).mean()
        out["P(4+ tries) no favorito"] = (x.tries_dog >= 4).mean()
        out["P(bonus perdedor | perdió)"] = lb.sum() / perdio.sum()
        out["bonus por equipo y partido"] = t4 + lb.mean()
    return out

real_t = test2.dropna(subset=["tries_fav", "tries_dog"])
sim_t = sim[sim.idx.isin(real_t.index)]
comp = pd.DataFrame({"real": resumen(real_t), "simulado": resumen(sim_t)})
print(f"Partidos de prueba: {len(test2)} ({len(real_t)} con tries) | {N_SIM} simulaciones por partido\n")
print(comp.round(3).to_string())

# por nivel de desequilibrio del partido
print("\nMargen medio del ganador, real vs simulado, según qué tan desparejo es el partido:")
test2 = test2.assign(M=(test2.pts_fav - test2.pts_dog).abs(), gb=pd.cut(test2.fz, [-0.01, .5, 1, 1.5, 3]))
sim["gb"] = sim.idx.map(test2.gb)
t = pd.DataFrame({"real": test2[test2.M > 0].groupby("gb", observed=True).M.mean(),
                  "simulado": sim[sim.M > 0].groupby("gb", observed=True).M.mean(),
                  "n_real": test2.groupby("gb", observed=True).size()})
print(t.round(1).to_string())
