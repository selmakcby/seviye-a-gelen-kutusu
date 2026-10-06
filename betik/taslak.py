"""Basamak 2 · Sadece "cevap-gerekli" e-postalara Sonnet ile kısa cevap taslağı.

Taslaklar GÖNDERİLMEZ. Gönderme düğmesi her zaman insanda.
Çıktı betik/sema/taslaklar.schema.json ile doğrulanır; bozuksa bir kez tekrar.
Çıkış kontrolü: IBAN, şifre, onay kodu geçen taslak gösterilmez.
"""
import re

from dogrula import hatalar, sema_yukle
from ortak import json_ayikla, oku_metin, veri_blogu, yalin_cagri

MODEL = "sonnet"
YASAK = re.compile(r"(TR\d{2}[\s\d]{10,}|IBAN|şifre|parola|onay kodu)", re.I)


def taslak_yaz(cevaplanacaklar):
    """Döner: (taslaklar: id -> metin, maliyet_kaydi)"""
    if not cevaplanacaklar:
        return {}, {"basamak": "2 · Sonnet taslak", "usd": 0.0, "sure_sn": 0.0, "cagri": 0}
    sistem = oku_metin("betik/promptlar/taslakci.txt")
    sema = sema_yukle("taslaklar.schema.json")
    girdi = "Bu e-postalara cevap taslağı yaz.\n\n" + "\n\n".join(veri_blogu(e) for e in cevaplanacaklar)

    usd_top, sure_top, taslaklar, model = 0.0, 0.0, {}, MODEL
    for deneme in (1, 2):
        ek = "" if deneme == 1 else "\n\nÖNCEKİ ÇIKTIN GEÇERSİZDİ. Sadece istenen JSON'u yaz."
        metin, usd, sure, model = yalin_cagri(MODEL, sistem, girdi + ek)
        usd_top, sure_top = usd_top + usd, sure_top + sure
        veri = json_ayikla(metin)
        if veri is not None and not hatalar(veri, sema):
            taslaklar = {t["id"]: t["taslak"] for t in veri["taslaklar"]}
            break
        print(f"  ! Sonnet çıktısı şemaya uymadı (deneme {deneme}).")

    guvenli = {i: ("[Taslak gizlendi: hassas bilgi içeriyordu, elle yaz.]" if YASAK.search(t) else t)
               for i, t in taslaklar.items()}
    maliyet = {"basamak": "2 · Sonnet taslak", "model": model, "usd": usd_top,
               "sure_sn": round(sure_top, 1), "cagri": deneme, "eposta": len(cevaplanacaklar)}
    return guvenli, maliyet
