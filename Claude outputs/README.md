# Predictor del Mundial de Rugby 2027

Modelo estadístico que estima las probabilidades de cada selección en el Mundial de Rugby 2027 (24 selecciones, 6 grupos de 4, mejores terceros) simulando el torneo completo 10.000 veces.

**Dashboard:** [completar con el link]

## Qué hace

1. Calcula un **Elo** para cada selección con el historial de partidos desde 1995.
2. Estima la probabilidad de cada partido con dos **regresiones logísticas** promediadas.
3. Simula el **marcador** (puntos y tries) para aplicar los puntos de bonus del Mundial.
4. Simula la **fase de grupos**, elige a los cuatro mejores terceros y juega el **cuadro eliminatorio** oficial.
5. Repite todo 10.000 veces y cuenta con qué frecuencia cada selección llega a cada ronda.

## Resultados (datos hasta el 8 de noviembre de 2026)

| Selección | Campeón | Final |
|---|---|---|
| Nueva Zelanda | 38.1% | 48.8% |
| Sudáfrica | 28.5% | 39.7% |
| Irlanda | 12.3% | 36.2% |
| Francia | 6.8% | 14.0% |
| Inglaterra | 6.7% | 24.9% |
| Australia | 4.5% | 20.4% |

Las cifras exactas cambian un poco entre corridas por el azar de las simulaciones.

## Cómo está armado

El notebook tiene cuatro celdas que se corren en orden, en el mismo kernel:

| Celda | Qué hace |
|---|---|
| 1 | Carga los partidos, calcula el Elo, arma las variables y evalúa el modelo en bloques de tiempo |
| 2 | Ajusta el modelo final y el simulador de marcador, y lo valida contra 2025 y 2026 |
| 3 | Simula la fase de grupos con bonus y desempates, y selecciona a los mejores terceros |
| 4 | Simula el cuadro eliminatorio y el campeón, y exporta los resultados a CSV |

Requisitos: Python 3, `pandas`, `numpy`, `scikit-learn` y `scipy`.

## Metodología

- **Elo:** K = 40, ventaja de local de 100 puntos, multiplicador por margen de victoria. Las 10 selecciones tradicionales parten de 1500 y el resto de 900.
- **Modelo de probabilidad:** regresión logística con diferencia de Elo, cancha neutral, forma reciente (últimos 5 partidos), descanso y tipo de competencia. El modelo final promedia una versión completa y otra sin la forma reciente en victorias (esa variable mejora la validación pero tiene un signo contraintuitivo). Se entrena desde 2015, con más peso a los partidos donde juegan selecciones del Mundial.
- **Marcador:** el margen del ganador sigue una distribución lognormal que depende de qué tan desparejo es el partido. Los tries se sortean del historial dado el puntaje, con más peso a los partidos recientes y un factor de ajuste calibrado con 2025.
- **Bonus:** 4 puntos por victoria, 2 por empate, +1 por 4 o más tries y +1 por perder por menos de 8.
- **Desempates de los mejores terceros:** puntos, diferencia de puntos, puntos a favor, tries a favor y, como último recurso, el Elo (aproxima el ranking mundial).
- **Cuadro:** octavos, cuartos y semifinales según el cuadro oficial, con la tabla de asignación de terceros publicada para el torneo.

## Validación

Evaluada con log-loss en cuatro bloques de tiempo (2019-21, 2021-23, 2023-25, 2025-27), entrenando siempre con lo anterior:

| Modelo | Log-loss promedio |
|---|---|
| Solo Elo | 0.4489 |
| Regresión completa | 0.4446 |
| Regresión sin forma en victorias | 0.4541 |
| Promedio de ambas (el que se usa) | 0.4483 |

Es decir, el modelo mejora muy poco sobre el Elo solo. La mayor parte de la información viene del Elo.

## Limitaciones

- **Es una foto de hoy.** El Elo y la forma reciente no se actualizan durante el torneo ni hasta octubre de 2027.
- **Los tries están algo subestimados.** El simulador da menos partidos con 4 o más tries que lo observado en 2025 y 2026 (aproximadamente 44% contra 49%), porque el rugby viene anotando más cada año.
- **Los márgenes de partidos medianamente desparejos salen inflados** respecto del historial.
- **Nueva Zelanda y Sudáfrica quedan muy arriba** porque el Elo los separa varios cientos de puntos del resto. Es un ranking de fuerza actual, no una cuota de apuestas.
- **Los enfrentamientos directos no entran al modelo.** Por ejemplo, Sudáfrica le ganó a Nueva Zelanda 3 de 4 veces en 2026 y el modelo no lo ve de forma explícita.
- **Las eliminatorias no consideran empates** y se supone que Australia juega de local en todo el torneo.
- **Los grupos de Inglaterra, Gales, Tonga y Zimbabue** se infirieron de los fixtures.

## Datos y fuentes

- Partidos: [completar con la fuente de `matches.csv` y su licencia]. Algunos resultados recientes se completaron a mano desde all.rugby y World Rugby.
- Formato del torneo, cuadro y tabla de terceros: [World Rugby](https://www.world.rugby/news/1019814/the-new-mens-rugby-world-cup-draw-format-explained) y [Wikipedia](https://en.wikipedia.org/wiki/2027_Rugby_World_Cup).

## Actualizar los resultados

1. Agregar los partidos nuevos al CSV.
2. Correr las cuatro celdas del notebook.
3. La celda 4 guarda los resultados en archivos `resultados_*.csv`, que son los que alimentan el dashboard.
