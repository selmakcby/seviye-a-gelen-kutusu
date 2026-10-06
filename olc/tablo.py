"""olc/sonuclar/*.json -> olc/SONUC.md tablosu (ortalama + her koşu)."""
import glob
import json
import os
from datetime import datetime

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ADLAR = {"naif": "NAİF: Opus ajanına klasörü ver", "akilli": "AKILLI: betik + Haiku + Sonnet"}


def virgul(x, b=4):
    return f"{x:.{b}f}".replace(".", ",")


def oku():
    kayitlar = []
    for yol in sorted(glob.glob(os.path.join(KOK, "olc", "sonuclar", "*.json"))):
        if not yol.endswith(".ham.json"):
            with open(yol, encoding="utf-8") as f:
                kayitlar.append(json.load(f))
    return kayitlar


def tablo(kayitlar):
    satir = ["| Yol | Koşu | USD | Süre (sn) | Doğruluk | Şüpheli | Model dağılımı |", "|---|---|---|---|---|---|---|"]
    ozet = {}
    for yol in ("naif", "akilli"):
        grup = sorted((k for k in kayitlar if k["yol"] == yol), key=lambda k: k["kos"])
        if not grup:
            continue
        for k in grup:
            dag = ", ".join(f"{m} {virgul(u)}" for m, u in k["modeller"].items())
            satir.append(f"| {ADLAR[yol]} | {k['kos']} | {virgul(k['usd'])} | {k['sure_sn']} "
                         f"| {k['dogru']}/{k['toplam']} | {k['supheli']} | {dag} |")
        ort = {a: sum(k[a] for k in grup) / len(grup) for a in ("usd", "sure_sn", "dogru")}
        ozet[yol] = ort
        satir.append(f"| **{ADLAR[yol]}** | **ortalama** | **{virgul(ort['usd'])}** | **{ort['sure_sn']:.0f}** "
                     f"| **{virgul(ort['dogru'], 1)}/{grup[0]['toplam']}** | | |")
    return satir, ozet


if __name__ == "__main__":
    satirlar, ozet = tablo(oku())
    metin = [f"# Ölçüm sonucu · {datetime.now():%d.%m.%Y}", "",
             "60 e-postalık örnek gelen kutusu, her yol ayrı koşuldu. Maliyet: `claude -p --output-format json`"
             " çıktısındaki `total_cost_usd`. Süre: duvar saati. Doğruluk: `cevap-anahtari.json`.", ""] + satirlar
    if "naif" in ozet and "akilli" in ozet and ozet["akilli"]["usd"] > 0:
        oran = ozet["naif"]["usd"] / ozet["akilli"]["usd"]
        metin += ["", f"**Ortalama maliyet oranı: naif yol akıllı yolun {virgul(oran, 1)} katı.**"]
    notlar = os.path.join(KOK, "olc", "notlar.md")
    if os.path.exists(notlar):
        with open(notlar, encoding="utf-8") as f:
            metin += ["", f.read().strip()]
    with open(os.path.join(KOK, "olc", "SONUC.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(metin) + "\n")
    print("\n".join(metin))
