"""sabah-ozeti.md üretir: acil üstte, taslaklar altta, şüpheliler ayrı kutuda, maliyet en altta."""
from datetime import datetime

BASLIKLAR = {"acil": "Acil: bugün dönmen gerekenler", "bilgi": "Bilgi: okuman yeter",
             "insan": "İnsana bırakılanlar: model emin olamadı, sen bak"}


def _satir(e, s):
    return f"- **{e['konu']}** · {e['gonderen_ad'] or e['gonderen']} · `{e['id']}`\n  {s['ozet']}"


def _bolum(baslik, kalemler):
    if not kalemler:
        return []
    return [f"## {baslik} ({len(kalemler)})", ""] + kalemler + [""]


def _taslaklar(epostalar, sonuclar, taslaklar):
    kalemler = []
    for e in epostalar:
        if sonuclar[e["id"]]["sinif"] != "cevap-gerekli":
            continue
        metin = taslaklar.get(e["id"], "[Taslak üretilemedi, elle yaz.]")
        alintili = "\n".join("> " + s for s in metin.splitlines())
        kalemler.append(f"### {e['konu']}\n*{e['gonderen_ad']} · `{e['id']}`*\n\n{alintili}\n")
    return _bolum("Cevap bekleyenler ve taslaklar (gönderilmedi, sen gönder)", kalemler)


def _supheliler(epostalar, sonuclar):
    satirlar = [f"> - **{e['konu']}** · `{e['gonderen']}` · `{e['id']}`\n>   {sonuclar[e['id']]['ozet']}"
                f" *({sonuclar[e['id']]['kaynak']})*"
                for e in epostalar if sonuclar[e["id"]]["sinif"] == "supheli"]
    if not satirlar:
        return []
    return ["## Şüpheli: açma, tıklama, iletme", "",
            "> [!warning] Bu e-postalarda yapay zekaya talimat vermeye çalışan metin var.",
            "> Hiçbirine taslak yazılmadı. Gerekirse BT ekibine bildir.", ">"] + satirlar + [""]


def _usd(x):
    return f"{x:.4f}".replace(".", ",")


def _maliyet(maliyetler, elenen_sayisi):
    toplam = sum(m["usd"] for m in maliyetler)
    sure = sum(m["sure_sn"] for m in maliyetler)
    satirlar = ["## Bu koşunun maliyeti", "",
                "| Basamak | Model | E-posta | Çağrı | USD | Süre (sn) |", "|---|---|---|---|---|---|",
                f"| 0 · Betik (kural) | yok | {elenen_sayisi} | 0 | 0,0000 | 0 |"]
    satirlar += [f"| {m['basamak']} | {m.get('model', '-')} | {m.get('eposta', 0)} | {m['cagri']} "
                 f"| {_usd(m['usd'])} | {str(m['sure_sn']).replace('.', ',')} |" for m in maliyetler]
    satirlar.append(f"| **Toplam** | | | | **{_usd(toplam)}** | {str(round(sure, 1)).replace('.', ',')} |")
    satirlar += ["", "*Kaynak: her çağrının `claude -p --output-format json` çıktısındaki `total_cost_usd` alanı.*"]
    return satirlar


def ozet_yaz(yol, epostalar, sonuclar, taslaklar, maliyetler):
    def grup(sinif):
        return [_satir(e, sonuclar[e["id"]]) for e in epostalar if sonuclar[e["id"]]["sinif"] == sinif]

    sayac = {}
    for s in sonuclar.values():
        sayac[s["sinif"]] = sayac.get(s["sinif"], 0) + 1
    elenen = sum(1 for s in sonuclar.values() if s["kaynak"] == "kural")
    satirlar = [f"# Sabah özeti · {datetime.now():%d.%m.%Y %H:%M}", "",
                f"{len(epostalar)} e-posta okundu. " + " · ".join(f"{k}: {v}" for k, v in sorted(sayac.items())),
                ""]
    satirlar += _bolum(BASLIKLAR["acil"], grup("acil"))
    satirlar += _taslaklar(epostalar, sonuclar, taslaklar)
    satirlar += _bolum(BASLIKLAR["insan"], grup("insan"))
    satirlar += _bolum(BASLIKLAR["bilgi"], grup("bilgi"))
    satirlar += _supheliler(epostalar, sonuclar)
    satirlar += [f"## Ayıklananlar: bülten {sayac.get('bulten', 0)}, bildirim {sayac.get('bildirim', 0)}",
                 "", "Bunları açmana gerek yok. Liste `cikti/siniflar.json` dosyasında.", ""]
    satirlar += _maliyet(maliyetler, elenen)
    with open(yol, "w", encoding="utf-8") as f:
        f.write("\n".join(satirlar) + "\n")
