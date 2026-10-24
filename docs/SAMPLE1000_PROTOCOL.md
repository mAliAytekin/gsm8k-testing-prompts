# Sabit 1000 soruluk keşifsel deney

1000 kayıt = 1000 farklı GSM8K sorusu olarak yorumlanır. Beş model ve 16 koşul
ile toplam 80.000 öğrenci üretimi yapılır. K9 tek örnekli; yargıç, yeniden çözme
veya otomatik onarım yoktur. 10 soruluk koşumun diğer parametreleri korunur.

Havuz resmî main train+test birleşimi (8792 soru), aktif A örnekleri train0/train2
hariç 8790 sorudur. Model çıktısı/gold görülmeden seed20261021 ile 1000 soru
seçilir; ID/hash listesi data/sample1000-manifest.json ile sabitlenir. K9 train0
kullanır. Aynı manifest bütün modeller ve koşullarda kullanılır. Önceki pilotla
örtüşen kimlikler ayrıca işaretlenir. Train/test kaynak sayıları kaydedilir;
bağımsız held-out test iddiası yoktur. Eski soruların sonuçları yeniden kullanılmaz.

Warm politika: keep_alive30m, model blokları, cache kullanımına izin; gerçek
sayaçlar ve süreler kaydedilir. Q8_0, temperature0, Qwen think=false, context4096,
output512. Veri/model kilitleri ve sandbox değişirse koşum reddedilir. Konservatif
bağlam preflight'ı tüm örneklerde geçmelidir; koşullar uysun diye soru elenmez.

Ayrı config configs/sample1000.json ve results/sample1000-warm.sqlite kullanılır.
Kesinti sonrası aynı kaynak/config ile resume kayıtları korur; belirsiz inflight
istek altyapı hatası sayılır, yeniden üretilmez. Tamamlanma durumu açık raporlanır.
10 soruluk hızdan ilk süre tahmini yaklaşık 11 saattir, garanti değildir.

Komutlar:
```
.venv/bin/python scripts/sample_run.py prepare
.venv/bin/python scripts/sample_run.py run
.venv/bin/python scripts/sample_run.py status
.venv/bin/python scripts/sample_run.py resume RUN_ID
.venv/bin/python scripts/sample_run.py analyze RUN_ID
```
Tamamlandığında açıklamalı rapor/grafik ve ZIP otomatik üretilir. Aynı soruya ait
koşullar bağımsız örnek sayılmaz. Mevcut eşleştirilmiş K9−K2_1shot karşılaştırması
soru bootstrap'ı, McNemar ve Holm aile5 ile keşifseldir.
