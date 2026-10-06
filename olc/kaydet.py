"""Bir ölçüm koşusunu olc/sonuclar/<yol>-<n>.json olarak özetler (maliyet, süre, doğruluk)."""
import json
import os
import sys

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(KOK, "betik"))
from ortak import json_ayikla  # noqa: E402
from puanla import puanla  # noqa: E402


def son_json(metin):
    """Metindeki son {"siniflar": ...} bloğunu bulur."""
    yer = metin.rfind('"siniflar"')
    bas = metin.rfind("{", 0, yer) if yer != -1 else -1
    if bas == -1:
        return {}
    try:
        return json.JSONDecoder().raw_decode(metin[bas:])[0]
    except json.JSONDecodeError:
        return json_ayikla(metin) or {}


def naif(ham_yol):
    with open(ham_yol, encoding="utf-8") as f:
        d = json.load(f)
    veri = son_json(d.get("result", ""))
    tahmin = veri.get("siniflar", {}) if isinstance(veri.get("siniflar"), dict) else {}
    dagilim = {m: round(u.get("costUSD", 0), 4) for m, u in d.get("modelUsage", {}).items()}
    return {"usd": d.get("total_cost_usd", 0.0), "tur": d.get("num_turns"),
            "hata": d.get("is_error", False), "modeller": dagilim, "tahmin": tahmin}


def akilli(maliyet_yol):
    with open(maliyet_yol, encoding="utf-8") as f:
        m = json.load(f)
    with open(os.path.join(KOK, "cikti", "siniflar.json"), encoding="utf-8") as f:
        tahmin = {i: s["sinif"] for i, s in json.load(f).items()}
    dagilim = {b.get("model", "-"): round(b["usd"], 4) for b in m["basamaklar"]}
    return {"usd": m["toplam_usd"], "tur": sum(b["cagri"] for b in m["basamaklar"]),
            "hata": False, "modeller": dagilim, "tahmin": tahmin}


if __name__ == "__main__":
    yol, n, kaynak, sure = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
    kayit = naif(kaynak) if yol == "naif" else akilli(kaynak)
    p = puanla(kayit.pop("tahmin"))
    kayit.update({"yol": yol, "kos": int(n), "sure_sn": sure, "dogru": p["dogru"], "toplam": p["toplam"],
                  "supheli": f"{p['supheli_yakalanan']}/{p['supheli_toplam']}"})
    with open(os.path.join(KOK, "olc", "sonuclar", f"{yol}-{n}.json"), "w", encoding="utf-8") as f:
        json.dump(kayit, f, ensure_ascii=False, indent=2)
    print(f"   {yol} {n}: {kayit['usd']:.4f} USD · {sure} sn · doğruluk {p['dogru']}/{p['toplam']}"
          f" · şüpheli {kayit['supheli']}")
