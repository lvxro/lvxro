#!/usr/bin/env python3
"""Genera dark_mode.svg y light_mode.svg: una tarjeta estilo neofetch para el
README del perfil de GitHub.

Lee los datos personales de perfil.json, el dibujo de ascii.txt y las stats de
la API de GitHub. Solo usa la libreria estandar de Python.

Uso:
    GITHUB_TOKEN=xxx GH_USER=tu_usuario python3 generar.py
    python3 generar.py --demo     # numeros de ejemplo, sin llamar a la API
"""
import datetime
import json
import os
import sys
import urllib.request
from xml.sax.saxutils import escape

RAIZ = os.path.dirname(os.path.abspath(__file__))

# --- medidas -----------------------------------------------------------------
FS = 14            # tamano de fuente
CW = FS * 0.602    # ancho de un caracter monoespaciado
LH = 20            # alto de linea
PAD = 26           # margen interno
BARRA = 34         # alto de la barra de titulo
SEP = 40           # espacio entre el dibujo y el texto
COLS = 57          # ancho en caracteres de la columna de texto

FUENTE = "ui-monospace,SFMono-Regular,'SF Mono',Menlo,Consolas,'Liberation Mono','DejaVu Sans Mono',monospace"

TEMAS = {
    "dark_mode.svg": {
        "fondo": "#0d1117", "borde": "#30363d", "barra": "#161b22",
        "texto": "#c9d1d9", "tenue": "#484f58", "clave": "#3fb950",
        "titulo": "#58a6ff",
        "verdes": ["#1a5c33", "#1f8a41", "#2fb350", "#56e06f"],
    },
    "light_mode.svg": {
        "fondo": "#ffffff", "borde": "#d0d7de", "barra": "#f6f8fa",
        "texto": "#24292f", "tenue": "#c4ccd4", "clave": "#1a7f37",
        "titulo": "#0969da",
        "verdes": ["#8bdc98", "#40c463", "#30a14e", "#216e39"],
    },
}

# de menos a mas "tinta": se pinta con los 4 verdes de la grilla de contribuciones
RAMPA = ".,-~:;=!*#$@"

# --- API de GitHub -----------------------------------------------------------
Q_USUARIO = """
query($login: String!, $cursor: String) {
  user(login: $login) {
    createdAt
    followers { totalCount }
    pullRequests { totalCount }
    contributionsCollection {
      contributionYears
      contributionCalendar { totalContributions }
    }
    repositories(first: 100, after: $cursor, ownerAffiliations: OWNER,
                 isFork: false, privacy: PUBLIC) {
      totalCount
      pageInfo { hasNextPage endCursor }
      nodes {
        stargazerCount
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges { size node { name } }
        }
      }
    }
  }
}
"""

Q_ANIO = """
query($login: String!, $desde: DateTime!, $hasta: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $desde, to: $hasta) {
      totalCommitContributions
    }
  }
}
"""


def gql(consulta, variables, token):
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": consulta, "variables": variables}).encode(),
        headers={"Authorization": "bearer " + token, "User-Agent": "perfil-readme"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        datos = json.load(r)
    if datos.get("errors"):
        raise RuntimeError(datos["errors"])
    return datos["data"]


def traer_stats(usuario, token, ignorar=()):
    estrellas, lenguajes, cursor = 0, {}, None
    while True:
        u = gql(Q_USUARIO, {"login": usuario, "cursor": cursor}, token)["user"]
        if u is None:
            raise RuntimeError("No existe el usuario " + usuario)
        repos = u["repositories"]
        for r in repos["nodes"]:
            estrellas += r["stargazerCount"]
            for e in r["languages"]["edges"]:
                nombre = e["node"]["name"]
                lenguajes[nombre] = lenguajes.get(nombre, 0) + e["size"]
        if not repos["pageInfo"]["hasNextPage"]:
            break
        cursor = repos["pageInfo"]["endCursor"]

    commits = 0
    for anio in u["contributionsCollection"]["contributionYears"]:
        d = gql(Q_ANIO, {"login": usuario,
                         "desde": "%d-01-01T00:00:00Z" % anio,
                         "hasta": "%d-12-31T23:59:59Z" % anio}, token)
        commits += d["user"]["contributionsCollection"]["totalCommitContributions"]

    ignorar = {i.lower() for i in ignorar}
    top = [n for n, _ in sorted(lenguajes.items(), key=lambda x: -x[1])
           if n.lower() not in ignorar][:4]
    return {
        "repos": repos["totalCount"],
        "estrellas": estrellas,
        "commits": commits,
        "seguidores": u["followers"]["totalCount"],
        "prs": u["pullRequests"]["totalCount"],
        "contribs_anio": u["contributionsCollection"]["contributionCalendar"]["totalContributions"],
        "lenguajes": ", ".join(top) or "-",
        "creado": u["createdAt"][:10],
    }


DEMO = {"repos": 24, "estrellas": 137, "commits": 1842, "seguidores": 58,
        "prs": 96, "contribs_anio": 731, "lenguajes": "Python, TypeScript, Go, Rust",
        "creado": "2019-03-14"}
VACIO = {"repos": "-", "estrellas": "-", "commits": "-", "seguidores": "-",
         "prs": "-", "contribs_anio": "-", "lenguajes": "-", "creado": ""}


# --- armado del texto --------------------------------------------------------
TEXTOS = {
    "es": {"unidades": [("año", "años"), ("mes", "meses"), ("día", "días")],
           "miles": ".", "seguidores": "Seguidores", "contribs": "Contribs (12m)",
           "perfil": "Perfil de GitHub de "},
    "en": {"unidades": [("year", "years"), ("month", "months"), ("day", "days")],
           "miles": ",", "seguidores": "Followers", "contribs": "Contribs (1y)",
           "perfil": "GitHub profile of "},
}


def miles(n, sep="."):
    return "{:,}".format(n).replace(",", sep) if isinstance(n, int) else str(n)


def antiguedad(desde, hoy=None, unidades=TEXTOS["es"]["unidades"]):
    """'2001-05-20' -> '25 años, 4 meses, 16 días'"""
    if not desde:
        return "-"
    d = datetime.date.fromisoformat(desde)
    hoy = hoy or datetime.date.today()
    anios = hoy.year - d.year
    meses = hoy.month - d.month
    dias = hoy.day - d.day
    if dias < 0:
        meses -= 1
        ultimo = hoy.replace(day=1) - datetime.timedelta(days=1)
        dias += ultimo.day
    if meses < 0:
        anios -= 1
        meses += 12
    partes = zip((anios, meses, dias), unidades)
    return ", ".join("%d %s" % (n, s if n == 1 else p) for n, (s, p) in partes if n) or "0 " + unidades[2][1]


def campo(clave, valor, ancho):
    """clave: ........ valor   (ocupa exactamente `ancho` caracteres)"""
    valor = str(valor)
    libre = ancho - len(clave) - len(valor) - 3
    if libre < 2:
        valor = valor[:max(1, len(valor) + libre - 3)] + "…"
        libre = ancho - len(clave) - len(valor) - 3
    return [("k", clave), ("p", ": "), ("d", "." * libre), ("p", " "), ("v", valor)]


def par(k1, v1, k2, v2):
    medio = (COLS - 3) // 2
    return campo(k1, v1, medio) + [("d", " | ")] + campo(k2, v2, COLS - 3 - medio)


def regla(titulo):
    cab = "─ " + titulo + " "
    return [("t", cab), ("d", "─" * (COLS - len(cab)))]


def armar_lineas(cfg, usuario, s):
    tx = TEXTOS.get(cfg.get("idioma", "es"), TEXTOS["es"])
    m = lambda n: miles(n, tx["miles"])
    reemplazos = {
        "{uptime}": antiguedad(cfg.get("nacimiento") or s["creado"], unidades=tx["unidades"]),
        "{lenguajes}": s["lenguajes"],
    }
    cab = usuario + "@github"
    lineas = [[("h", cab), ("p", " "), ("d", "─" * (COLS - len(cab) - 1))]]
    for i, sec in enumerate(cfg.get("secciones", [])):
        if sec.get("titulo"):
            lineas += [[], regla(sec["titulo"])]
        elif i:
            lineas.append([])
        for clave, valor in sec["campos"]:
            lineas.append(campo(clave, reemplazos.get(valor, valor), COLS))
    lineas += [
        [], regla("GitHub"),
        par("Repos", m(s["repos"]), "Stars", m(s["estrellas"])),
        par("Commits", m(s["commits"]), tx["seguidores"], m(s["seguidores"])),
        par("PRs", m(s["prs"]), tx["contribs"], m(s["contribs_anio"])),
    ]
    if cfg.get("minusculas"):
        lineas = [[(c, t.lower()) for c, t in l] for l in lineas]
    return lineas


# --- SVG ---------------------------------------------------------------------
def tramos_ascii(linea, degrade):
    """Agrupa caracteres consecutivos del mismo tono -> [(clase, texto)]"""
    tramos = []
    for ch in linea:
        if degrade and ch in RAMPA:
            cls = "g%d" % (RAMPA.index(ch) * 4 // len(RAMPA))
        else:
            cls = "a"
        if ch == " " and tramos:
            cls = tramos[-1][0]
        if tramos and tramos[-1][0] == cls:
            tramos[-1][1] += ch
        else:
            tramos.append([cls, ch])
    return tramos


def texto_svg(x, y, tramos):
    cuerpo = "".join('<tspan class="%s">%s</tspan>' % (c, escape(t)) for c, t in tramos)
    return '<text x="%.1f" y="%.1f">%s</text>' % (x, y, cuerpo)


def render(tema, usuario, ascii_lineas, lineas, degrade, ascii_fuente=FS, etiqueta="Perfil de GitHub de "):
    # el dibujo se escribe a tamano FS y se achica con scale(): asi se puede usar
    # un dibujo con mucho detalle (letra chica) sin depender del minimo del navegador
    esc = ascii_fuente / FS
    alh = LH if esc == 1 else FS * 1.22          # alto de linea del dibujo (sin escalar)
    ancho_ascii = max((len(l) for l in ascii_lineas), default=0) * CW * esc
    alto_ascii = len(ascii_lineas) * alh * esc
    alto_texto = (len(lineas) + 2) * LH          # +2: linea en blanco y prompt
    cuerpo = max(alto_ascii, alto_texto)
    x_ascii = PAD
    x_texto = PAD + (ancho_ascii + SEP if ancho_ascii else 0)
    ancho = round(x_texto + COLS * CW + PAD)
    alto = round(BARRA + PAD + cuerpo + PAD - 6)
    y0 = BARRA + PAD + FS - 2 + (cuerpo - alto_texto) / 2
    y_ascii = BARRA + PAD + (cuerpo - alto_ascii) / 2

    o = []
    o.append('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" '
             'viewBox="0 0 %d %d" font-family="%s" font-size="%dpx" role="img" '
             'aria-label="%s">' % (ancho, alto, ancho, alto, FUENTE, FS, escape(etiqueta + usuario)))
    v = tema["verdes"]
    o.append("<style>"
             "text{white-space:pre;fill:%s}"
             ".k{fill:%s;font-weight:600}.h{fill:%s;font-weight:700}.t{fill:%s;font-weight:600}"
             ".d{fill:%s}.a{fill:%s}"
             ".g0{fill:%s}.g1{fill:%s}.g2{fill:%s}.g3{fill:%s}"
             ".cur{fill:%s;animation:parpadeo 1.1s steps(1) infinite}"
             "@keyframes parpadeo{50%%{opacity:0}}"
             "@media (prefers-reduced-motion:reduce){.cur{animation:none}}"
             "</style>" % (tema["texto"], tema["clave"], tema["clave"], tema["titulo"],
                           tema["tenue"], tema["texto"], v[0], v[1], v[2], v[3], tema["clave"]))
    # ventana
    o.append('<rect x="0.5" y="0.5" width="%d" height="%d" rx="10" fill="%s" stroke="%s"/>'
             % (ancho - 1, alto - 1, tema["fondo"], tema["borde"]))
    o.append('<path d="M0.5 %d V10.5 a10 10 0 0 1 10 -10 H%.1f a10 10 0 0 1 10 10 V%d Z" fill="%s" stroke="%s"/>'
             % (BARRA, ancho - 10.5, BARRA, tema["barra"], tema["borde"]))
    for i, color in enumerate(("#ff5f57", "#febc2e", "#28c840")):
        o.append('<circle cx="%d" cy="%d" r="5.5" fill="%s"/>' % (20 + i * 18, BARRA // 2 + 1, color))
    o.append('<text x="%d" y="%d" text-anchor="middle" font-size="12px"><tspan class="d" style="fill:%s;opacity:.65">%s</tspan></text>'
             % (ancho // 2, BARRA // 2 + 5, tema["texto"], escape(usuario + "@github: ~")))
    # dibujo
    o.append('<g xml:space="preserve" transform="translate(%.1f %.1f) scale(%.4f)">' % (x_ascii, y_ascii, esc))
    for i, l in enumerate(ascii_lineas):
        if l.strip():
            o.append(texto_svg(0, FS - 2 + i * alh, tramos_ascii(l, degrade)))
    o.append('</g>')
    # texto
    o.append('<g xml:space="preserve">')
    for i, l in enumerate(lineas):
        if l:
            o.append(texto_svg(x_texto, y0 + i * LH, l))
    y_p = y0 + (len(lineas) + 1) * LH
    o.append(texto_svg(x_texto, y_p, [("k", "❯")]))
    o.append('<rect class="cur" x="%.1f" y="%.1f" width="%.1f" height="%d"/>'
             % (x_texto + 2 * CW, y_p - FS + 2, CW, FS + 2))
    o.append("</g></svg>")
    return "\n".join(o) + "\n"


def main():
    demo = "--demo" in sys.argv
    with open(os.path.join(RAIZ, "perfil.json"), encoding="utf-8") as f:
        cfg = json.load(f)
    usuario = cfg.get("usuario") or os.environ.get("GH_USER") or "tu_usuario"
    token = os.environ.get("GITHUB_TOKEN")

    if demo:
        stats = DEMO
    elif token:
        stats = traer_stats(usuario, token, cfg.get("lenguajes_ignorar", []))
    else:
        print("Aviso: sin GITHUB_TOKEN, las stats quedan en '-'.", file=sys.stderr)
        stats = VACIO

    try:
        with open(os.path.join(RAIZ, "ascii.txt"), encoding="utf-8") as f:
            ascii_lineas = f.read().rstrip("\n").split("\n")
    except FileNotFoundError:
        ascii_lineas = []

    lineas = armar_lineas(cfg, usuario, stats)
    for archivo, tema in TEMAS.items():
        with open(os.path.join(RAIZ, archivo), "w", encoding="utf-8") as f:
            f.write(render(tema, usuario, ascii_lineas, lineas, cfg.get("ascii_degrade", True),
                           cfg.get("ascii_fuente", FS),
                           TEXTOS.get(cfg.get("idioma", "es"), TEXTOS["es"])["perfil"]))
        print("ok", archivo)


if __name__ == "__main__":
    main()
