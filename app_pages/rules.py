import base64
import os
import streamlit as st

# ── Background image ──────────────────────────────────────────────────────────
_img_path = os.path.join(os.path.dirname(__file__), "..", "assets", "ioag9w7poe8ayrodgmlc.webp")
if os.path.exists(_img_path):
    _b64 = base64.b64encode(open(_img_path, "rb").read()).decode()
    st.markdown(
        f"""
        <style>
        [data-testid="stAppViewContainer"] {{
            background-image: url("data:image/webp;base64,{_b64}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
        [data-testid="stAppViewContainer"]::before {{
            content: "";
            position: fixed;
            inset: 0;
            background: rgba(5, 10, 30, 0.72);
            pointer-events: none;
            z-index: 0;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )

st.title("Säännöt")

st.header("Näin veikkaat")
st.write(
    "Syötä veikkaukset **Omat veikkaukset** -sivulla. "
    "Voit päivittää veikkauksiasi milloin tahansa ennen lukkiutumisaikaa "
    "(11.6.2026 klo 19:00 Suomen aikaa)."
)
st.write(
    "Päivitys korvaa aiemman veikkauksen. "
    "Järjestelmä ei säilytä vanhoja versioita."
)

st.divider()

st.header("Alkulohkon pisteytys")
st.write("Esimerkki: ottelu **Ranska vs Marokko**.")
st.write("Veikkauksesi: Ranska voittaa **3–1**.")
st.markdown(
    """
- Ottelu päättyy **3–1** → saat **5 pistettä** (täysosuma)
- Ottelu päättyy **2–0** → saat **3 pistettä** (sama maaliero ja voittaja)
- Ottelu päättyy **4–2** → saat **1 pisteen** (oikea voittaja)
- Ottelu päättyy **0–0** → saat **0 pistettä** (väärä voittaja)
- Tasapelin tapauksessa **maaliero 0** lasketaan kuten muut maalierot,
  joten 1–1 → 0–0 antaa 3 pistettä ja 1–1 → 1–1 täydet 5.
- Tasatilanteessa aiemmin lähetetty veikkaus voittaa.
"""
)

st.divider()

st.header("Pudotuspelibracket")
st.write(
    "Alkulohkon tulosten lisäksi veikkaat koko pudotuspelibracketin etukäteen: "
    "lohkovoittajat, lohkojen kakkoset, 8 parasta kolmossijaa, R16-jatkajat, "
    "puolivälieräpaikat, välieräpaikat, finalistit ja mestarin. "
    "Lisäksi turnauksen maalikuningas ja oma **mustana hevosena** ennustamasi joukkue."
)
st.markdown(
    """
| Veikkaus | Pisteet | Maksimi |
|---|---|---|
| Lohkovoittaja (per lohko A–L) | 3 p / kpl | 36 p |
| Lohkon kakkonen (per lohko A–L) | 3 p / kpl | 36 p |
| Parhaat kolmoset (8 kpl) | 1 p / kpl | 8 p |
| R16-jatkaja (16 kpl) | 2 p / kpl | 32 p |
| Puolivälieräpaikka (8 kpl) | 3 p / kpl | 24 p |
| Välieräpaikka (4 kpl) | 5 p / kpl | 20 p |
| Finalisti | +10 p / kpl | 20 p |
| Mestari | +20 p | 20 p |
| Maalikuningas | 15 p | 15 p |
| Musta hevonen (etenee puolivälieriin) | 15 p | 15 p |
| **Pudotuspelimaksimi yhteensä** | | **226 p** |
"""
)

st.caption(
    "Finalisti- ja mestaribonus tulevat välieräpaikan pisteiden päälle. "
    "Maalikuningas tarkoittaa turnauksen maalipörssin voittajaa (FIFA Golden Boot)."
)

st.divider()

st.header("Yhteenveto")
st.write(
    "Alkulohkossa pelataan **72 ottelua** ja maksimipistemäärä on **360 p** "
    "(72 × 5). Bracket-osuudesta voi saada enintään **226 p**. "
    "Turnauksen kokonaisennätys on siten teoreettisesti **586 p**."
)
