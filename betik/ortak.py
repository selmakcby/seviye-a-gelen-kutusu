"""Ortak parçalar: e-posta okuma, Claude'a yalın çağrı, JSON ayıklama.

Sadece Python standart kütüphanesi kullanılır; kurulacak paket yok.
"""
import json
import os
import re
import subprocess
import time
from email import policy
from email.parser import BytesParser
from email.utils import parseaddr

KOK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GOVDE_SINIRI = 1500  # modele giden e-posta gövdesi en fazla bu kadar karakter


# ---------------------------------------------------------------- e-posta okuma
def eposta_oku(yol):
    """Tek bir .eml (ya da başlıklı .md/.txt) dosyasını sözlüğe çevirir."""
    with open(yol, "rb") as f:
        msg = BytesParser(policy=policy.default).parse(f)
    ad, adres = parseaddr(str(msg.get("From", "")))
    govde = msg.get_body(preferencelist=("plain", "html"))
    metin = govde.get_content() if govde else ""
    return {
        "id": os.path.basename(yol),
        "gonderen_ad": ad,
        "gonderen": adres.lower(),
        "konu": str(msg.get("Subject", "(konu yok)")),
        "tarih": str(msg.get("Date", "")),
        "basliklar": {k.lower(): str(v) for k, v in msg.items()},
        "govde": metin.strip(),
    }


def klasor_oku(klasor):
    """Klasördeki bütün .eml/.md/.txt dosyalarını ada göre sıralı okur."""
    if not os.path.isdir(klasor):
        raise SystemExit(f"Klasör bulunamadı: {klasor}")
    adlar = sorted(a for a in os.listdir(klasor) if a.lower().endswith((".eml", ".md", ".txt")))
    return [eposta_oku(os.path.join(klasor, a)) for a in adlar]


def veri_blogu(e):
    """E-postayı modele VERİ olarak gider: etiket içine sarılır, etiketi kıracak metin temizlenir."""
    govde = e["govde"][:GOVDE_SINIRI]
    temiz = re.sub(r"</?\s*eposta[^>]*>", "[etiket silindi]", govde, flags=re.I)
    return (f'<eposta id="{e["id"]}">\n'
            f'Kimden: {e["gonderen_ad"]} <{e["gonderen"]}>\n'
            f'Konu: {e["konu"]}\nTarih: {e["tarih"]}\n---\n{temiz}\n</eposta>')


# ---------------------------------------------------------------- Claude çağrısı
def yalin_cagri(model, sistem, girdi, butce_usd=0.5):
    """Araçsız, kısa system prompt'lu tek çağrı: `claude -p --model <model>`.

    - --tools ""                : hiçbir araç yok (dosya okuyamaz, komut çalıştıramaz)
    - --system-prompt           : Claude Code'un uzun ajan prompt'u yerine bizimki
    - --setting-sources project : kişisel ayarlar ve hook'lar yüklenmez
    - claudeMdExcludes          : kişisel CLAUDE.md'ler bu çağrıya karışmaz
    - alwaysThinkingEnabled=false: sınıflama için "düşünme" token'ı harcanmaz (ölçtük: 2-3 kat ucuz)
    Dönüş: (metin, maliyet_usd, sure_sn, model_adi)
    """
    ayarlar = {"disableAllHooks": True, "alwaysThinkingEnabled": False,
               "claudeMdExcludes": ["**/CLAUDE.md", "**/.claude/rules/**", "**/CLAUDE.local.md"]}
    komut = ["claude", "-p", "--model", model, "--system-prompt", sistem,
             "--tools", "", "--output-format", "json",
             "--setting-sources", "project", "--settings", json.dumps(ayarlar),
             "--strict-mcp-config", "--disable-slash-commands",
             "--no-session-persistence", "--max-budget-usd", str(butce_usd)]
    ortam = {k: v for k, v in os.environ.items() if k != "CLAUDE_CODE_PLUGIN_DIRS"}
    ortam["CLAUDE_CODE_DISABLE_AUTO_MEMORY"] = "1"
    bas = time.time()
    try:
        sonuc = subprocess.run(komut, input=girdi, capture_output=True, text=True,
                               timeout=300, env=ortam, cwd=KOK)
    except FileNotFoundError:
        raise SystemExit("`claude` komutu bulunamadı. Claude Code kurulu mu? (README > Gereksinimler)")
    except subprocess.TimeoutExpired:
        return "", 0.0, time.time() - bas, model
    sure = time.time() - bas
    try:
        veri = json.loads(sonuc.stdout)
    except json.JSONDecodeError:
        hata = (sonuc.stderr or sonuc.stdout).strip()[:300]
        print(f"  ! Claude çağrısı JSON dönmedi: {hata}")
        return "", 0.0, sure, model
    modeller = list(veri.get("modelUsage", {}).keys())
    return (veri.get("result", ""), float(veri.get("total_cost_usd", 0.0)),
            sure, modeller[0] if modeller else model)


def json_ayikla(metin):
    """Model cevabındaki JSON nesnesini bulur (``` çitleri olsa da). Bulamazsa None."""
    if not metin:
        return None
    metin = re.sub(r"^```(?:json)?\s*|\s*```$", "", metin.strip())
    bas, son = metin.find("{"), metin.rfind("}")
    if bas == -1 or son <= bas:
        return None
    try:
        return json.loads(metin[bas:son + 1])
    except json.JSONDecodeError:
        return None


def oku_metin(goreli_yol):
    with open(os.path.join(KOK, goreli_yol), encoding="utf-8") as f:
        return f.read().strip()
