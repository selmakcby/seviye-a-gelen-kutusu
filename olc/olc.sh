#!/usr/bin/env bash
# Ölçüm: NAİF yol (Opus ajanı, araçlı) vs AKILLI yol (katmanlı hat). Her yol N kez.
# Kullanım: ./olc/olc.sh [N=2]
# Tahmini harcama: naif koşu başına ~0,3-0,8 USD, akıllı koşu başına ~0,05 USD.
set -euo pipefail
cd "$(dirname "$0")/.."
REPO=$(pwd)
N="${1:-2}"
SONUC=olc/sonuclar
mkdir -p "$SONUC"
# Kişisel hook'lar, eklentiler, ses çalan modlar bu koşulara karışmasın:
AYAR='{"disableAllHooks":true}'
unset CLAUDE_CODE_PLUGIN_DIRS

for i in $(seq 1 "$N"); do
  echo "== NAİF $i/$N: Opus'a klasörü ver (ajan, Read/Glob/Grep araçlı)"
  # Ajan cevap anahtarını göremesin diye e-postalar geçici bir klasöre kopyalanır.
  GECICI=$(mktemp -d)
  cp ornek-gelen-kutusu/* "$GECICI/"
  BAS=$(date +%s)
  ( cd "$GECICI" && claude -p "$(cat "$REPO/olc/naif-prompt.txt")" --model opus \
      --tools Read,Glob,Grep --allowedTools Read Glob Grep \
      --output-format json --setting-sources project --settings "$AYAR" \
      --strict-mcp-config --no-session-persistence --max-budget-usd 1.0 ) \
      > "$SONUC/naif-$i.ham.json" || true
  SON=$(date +%s)
  rm -rf "$GECICI"
  python3 olc/kaydet.py naif "$i" "$SONUC/naif-$i.ham.json" $((SON - BAS))

  echo "== AKILLI $i/$N: katmanlı hat (betik -> Haiku -> Sonnet)"
  BAS=$(date +%s)
  ./calistir.sh > /dev/null
  SON=$(date +%s)
  python3 olc/kaydet.py akilli "$i" cikti/maliyet.json $((SON - BAS))
done
python3 olc/tablo.py
echo "Tablo: olc/SONUC.md"
