"""Basamak 1 · Yalın ucuz çağrı: kalan e-postaları tek Haiku çağrısıyla sınıflar.

- Araç yok, kısa system prompt, e-postalar stdin'den veri olarak gider.
- Çıktı betik/sema/siniflar.schema.json ile doğrulanır.
- Bozuksa bir kez tekrar; yine bozuksa ya da bir e-posta eksikse -> "insan".
- Güvenlik ağı: bilinen enjeksiyon kalıbı içeren e-posta, Haiku ne derse desin "supheli" olur.
"""
import re

from dogrula import hatalar, sema_yukle
from ortak import json_ayikla, oku_metin, veri_blogu, yalin_cagri

MODEL = "haiku"
ENJEKSIYON = re.compile(
    r"(talimatlar\w* (yok say|unut)|önceki talimat|sistem talimat|sistem notu"
    r"|ignore (all |any )?(previous|prior) instructions|yapay zeka asistan\w* (için|:)|asistan\w*:)", re.I)


def _cagir(sistem, girdi, sema):
    metin, usd, sure, model = yalin_cagri(MODEL, sistem, girdi)
    veri = json_ayikla(metin)
    sorunlar = ["JSON bulunamadı"] if veri is None else hatalar(veri, sema)
    return veri, sorunlar, usd, sure, model


def siniflandir(kalanlar):
    """Döner: (sonuclar: id -> {sinif, ozet, kaynak}, maliyet_kaydi)"""
    if not kalanlar:
        return {}, {"basamak": "1 · Haiku sınıflama", "usd": 0.0, "sure_sn": 0.0, "cagri": 0}
    sistem = oku_metin("betik/promptlar/siniflandirici.txt")
    sema = sema_yukle("siniflar.schema.json")
    girdi = "Aşağıdaki e-postaları sınıfla.\n\n" + "\n\n".join(veri_blogu(e) for e in kalanlar)

    veri, sorunlar, usd, sure, model = _cagir(sistem, girdi, sema)
    cagri = 1
    if sorunlar:  # bir kez tekrar dene
        print(f"  ! Haiku çıktısı şemaya uymadı ({sorunlar[0]}), bir kez tekrar deniyorum.")
        ek = "\n\nÖNCEKİ ÇIKTIN GEÇERSİZDİ. Sadece istenen JSON'u yaz."
        veri, sorunlar, usd2, sure2, model = _cagir(sistem, girdi + ek, sema)
        usd, sure, cagri = usd + usd2, sure + sure2, 2

    gelen = {} if sorunlar else {s["id"]: s for s in veri["siniflar"]}
    sonuclar = {}
    for e in kalanlar:
        s = gelen.get(e["id"])
        if s is None:
            sonuclar[e["id"]] = {"sinif": "insan", "ozet": e["konu"], "kaynak": "insan (model cevap vermedi)"}
            continue
        kayit = {"sinif": s["sinif"], "ozet": s["ozet"], "kaynak": "haiku"}
        if s["sinif"] != "supheli" and ENJEKSIYON.search(e["govde"]):
            kayit = {**kayit, "sinif": "supheli", "kaynak": "kural ağı (Haiku kaçırdı)",
                     "ozet": f"Talimat enjeksiyonu kalıbı var. Haiku '{s['sinif']}' demişti."}
        sonuclar[e["id"]] = kayit
    maliyet = {"basamak": "1 · Haiku sınıflama", "model": model, "usd": usd,
               "sure_sn": round(sure, 1), "cagri": cagri, "eposta": len(kalanlar)}
    return sonuclar, maliyet
