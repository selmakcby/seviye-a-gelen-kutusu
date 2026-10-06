"""Doğruluk: cikti/siniflar.json'u cevap-anahtari.json ile karşılaştırır.

Kullanım: python3 betik/puanla.py [cikti/siniflar.json]
"""
import json
import os
import sys

from ortak import KOK


def puanla(tahminler, anahtar_yolu=os.path.join(KOK, "cevap-anahtari.json")):
    """tahminler: id -> sinif. Döner: {dogru, toplam, supheli_yakalanan, supheli_toplam, yanlislar}"""
    with open(anahtar_yolu, encoding="utf-8") as f:
        anahtar = json.load(f)["cevaplar"]
    yanlislar = [(i, tahminler.get(i, "yok"), d) for i, d in sorted(anahtar.items()) if tahminler.get(i) != d]
    supheli = [i for i, d in anahtar.items() if d == "supheli"]
    return {"dogru": len(anahtar) - len(yanlislar), "toplam": len(anahtar),
            "supheli_yakalanan": sum(1 for i in supheli if tahminler.get(i) == "supheli"),
            "supheli_toplam": len(supheli), "yanlislar": yanlislar}


if __name__ == "__main__":
    yol = sys.argv[1] if len(sys.argv) > 1 else os.path.join(KOK, "cikti", "siniflar.json")
    with open(yol, encoding="utf-8") as f:
        tahmin = {i: s["sinif"] for i, s in json.load(f).items()}
    p = puanla(tahmin)
    print(f"Doğruluk: {p['dogru']}/{p['toplam']} · şüpheli yakalanan: {p['supheli_yakalanan']}/{p['supheli_toplam']}")
    for i, t, d in p["yanlislar"]:
        print(f"  {i}: tahmin={t}, doğrusu={d}")
