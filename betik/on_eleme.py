"""Basamak 0 · Betik: kuralla çözülen e-postaları ayırır. 0 token, 0 dolar.

Kurallar (yukarıdan aşağı, ilk tutan kazanır):
  1. List-Unsubscribe başlığı var          -> bulten   (pazarlama/haber bülteni)
  2. Auto-Submitted başlığı var            -> bildirim (sistem kendisi gönderdi)
  3. Gönderen no-reply / bildirim / ...    -> bildirim
  4. Gövdede "otomatik olarak gönderilmiştir", "lütfen yanıtlamayınız" -> bildirim
Kalanlar Basamak 1'e (Haiku) gider.

Tek başına çalıştır:  python3 betik/on_eleme.py ornek-gelen-kutusu
"""
import re
import sys

from ortak import klasor_oku

OTOMATIK_GONDEREN = re.compile(r"(no-?reply|do-?not-?reply|bildirim|notification|mailer-daemon)", re.I)
OTOMATIK_GOVDE = re.compile(r"(otomatik olarak gönderil|otomatik bir bildirim|lütfen yanıtlamayınız"
                            r"|bu e-postayı .* bildirim ayarlarınız)", re.I)


def kural(e):
    """E-postayı kuralla sınıflayabiliyorsa (sinif, neden), yoksa None döner."""
    b = e["basliklar"]
    if "list-unsubscribe" in b:
        return "bulten", "List-Unsubscribe başlığı var"
    if b.get("auto-submitted", "no").lower() != "no":
        return "bildirim", "Auto-Submitted başlığı var"
    yerel = e["gonderen"].split("@")[0]
    if OTOMATIK_GONDEREN.search(yerel):
        return "bildirim", f"gönderen adresi otomatik ({yerel}@...)"
    if OTOMATIK_GOVDE.search(e["govde"]):
        return "bildirim", "gövdede otomatik gönderim kalıbı var"
    return None


def on_eleme(epostalar):
    """(elenenler, kalanlar) döner. elenenler: id -> {sinif, ozet, kaynak}"""
    elenenler, kalanlar = {}, []
    for e in epostalar:
        sonuc = kural(e)
        if sonuc:
            elenenler[e["id"]] = {"sinif": sonuc[0], "ozet": f"{e['konu']} ({sonuc[1]})", "kaynak": "kural"}
        else:
            kalanlar.append(e)
    return elenenler, kalanlar


if __name__ == "__main__":
    klasor = sys.argv[1] if len(sys.argv) > 1 else "ornek-gelen-kutusu"
    epostalar = klasor_oku(klasor)
    elenenler, kalanlar = on_eleme(epostalar)
    for e in epostalar:
        s = elenenler.get(e["id"])
        etiket = s["sinif"] if s else "-> Haiku"
        print(f"{e['id']:<10} {etiket:<10} {e['konu'][:60]}")
    print(f"\nToplam {len(epostalar)} e-posta: {len(elenenler)} tanesi kuralla ayrıldı (0 token), "
          f"{len(kalanlar)} tanesi Basamak 1'e gidiyor.")
