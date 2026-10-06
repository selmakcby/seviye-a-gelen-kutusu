"""Katmanlı hat: Basamak 0 (betik) -> 1 (Haiku) -> 2 (Sonnet) -> sabah-ozeti.md

Kullanım: python3 betik/hat.py [gelen-kutusu-klasoru]
"""
import json
import os
import sys
import time

from on_eleme import on_eleme
from ortak import KOK, klasor_oku
from ozet import ozet_yaz
from puanla import puanla
from siniflandir import siniflandir
from taslak import taslak_yaz

ORNEK = os.path.join(KOK, "ornek-gelen-kutusu")


def calistir(klasor):
    bas = time.time()
    epostalar = klasor_oku(klasor)
    print(f"[0] {len(epostalar)} e-posta okundu. Kurallar uygulanıyor (0 token)...")
    elenenler, kalanlar = on_eleme(epostalar)
    print(f"    {len(elenenler)} tanesi kuralla ayrıldı, {len(kalanlar)} tanesi Haiku'ya gidiyor.")

    print("[1] Haiku sınıflıyor (tek yalın çağrı)...")
    siniflar, m1 = siniflandir(kalanlar)
    sonuclar = {**elenenler, **siniflar}
    print(f"    bitti: {m1['usd']:.4f} USD, {m1['sure_sn']} sn")

    cevaplanacak = [e for e in epostalar if sonuclar[e["id"]]["sinif"] == "cevap-gerekli"]
    print(f"[2] Sonnet {len(cevaplanacak)} e-postaya taslak yazıyor (gönderme yok)...")
    taslaklar, m2 = taslak_yaz(cevaplanacak)
    print(f"    bitti: {m2['usd']:.4f} USD, {m2['sure_sn']} sn")

    os.makedirs(os.path.join(KOK, "cikti"), exist_ok=True)
    maliyet = {"basamaklar": [m1, m2], "toplam_usd": m1["usd"] + m2["usd"],
               "sure_sn": round(time.time() - bas, 1), "eposta": len(epostalar)}
    if os.path.abspath(klasor) == ORNEK:
        p = puanla({i: s["sinif"] for i, s in sonuclar.items()})
        maliyet["dogruluk"] = {k: v for k, v in p.items() if k != "yanlislar"}
    with open(os.path.join(KOK, "cikti", "siniflar.json"), "w", encoding="utf-8") as f:
        json.dump(sonuclar, f, ensure_ascii=False, indent=2)
    with open(os.path.join(KOK, "cikti", "maliyet.json"), "w", encoding="utf-8") as f:
        json.dump(maliyet, f, ensure_ascii=False, indent=2)
    ozet_yaz(os.path.join(KOK, "sabah-ozeti.md"), epostalar, sonuclar, taslaklar, [m1, m2])

    print(f"\nHazır: sabah-ozeti.md · toplam {maliyet['toplam_usd']:.4f} USD · {maliyet['sure_sn']} sn")
    if "dogruluk" in maliyet:
        d = maliyet["dogruluk"]
        print(f"Örnek kutuda doğruluk: {d['dogru']}/{d['toplam']} · "
              f"şüpheli yakalanan: {d['supheli_yakalanan']}/{d['supheli_toplam']}")


if __name__ == "__main__":
    calistir(os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else ORNEK)
