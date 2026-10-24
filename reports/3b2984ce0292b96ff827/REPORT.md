# GSM8K: 10 soruluk temsil ve örnek karşılaştırması

[Türkçe](REPORT.md) · [English](REPORT.en.md)

Koşum: `3b2984ce0292b96ff827`. Tamamlanan: **800/800**.
Araştırma sorusu: Harici hesaplamanın faydası temsil biçimine, model büyüklüğüne ve verilen çözüm/API örneklerine göre nasıl değişiyor?
Bu rapor önceki sohbetten bağımsız okunabilir. Mevcut yöntemlerin kontrollü, keşifsel karşılaştırmasıdır; yeni yöntem/öncelik iddiası yoktur.

## Deney koşulları

**Zero-shot:** çözülmüş örnek yok. **One-shot / 1shot:** bir örnek. **Two-shot / 2shot:** iki örnek. Shot sayısı deneme/yeniden üretim sayısı değildir; her hedef soru için tek üretim yapılır.
**CoT (Chain of Thought):** doğal dilde adım adım çözüm. **PAL:** programla temsil edilen çözüm. **SymPy:** Python sembolik matematik kütüphanesi.

| Kod | Açıklama | Örnek sayısı | Üretim ve yürütme |
|---|---|---:|---|
| K2 | CoT — adım adım doğal dil çözümü | 0 | Yürütme yok; son satır FINAL: <sayı>. |
| K3 | Aritmetik ifade | 0 | Model tek ifade üretir; izin listeli AST hesaplayıcı hesaplar. |
| K4 | Python/PAL — serbest çözüm temsili | 0 | Model program üretir; Python kodu Docker izolasyonunda çalıştırılır. |
| K5 | Python — deterministik durum güncelleme | 0 | Miktarlar olay sırasına göre güncellenir; rastgelelik/Monte Carlo yok. Kod Docker’da yürütülür. |
| K6 | SymPy — zero-shot | 0 | Model SymPy kodu üretir; Python/SymPy Docker’da yürütülür. |
| K7 | SymPy — one-shot | 1 | K6 ile aynı talimat; bir doğru SymPy örneği eklenir. |
| K8 | SymPy — two-shot | 2 | K6 ile aynı talimat; iki doğru örnek, ilki K7 ile aynı. |
| K2_1shot | CoT — adım adım doğal dil çözümü | 1 | K2 ile aynı talimat ve çıktı sözleşmesi; 1 çözülmüş örnek eklenir. |
| K2_2shot | CoT — adım adım doğal dil çözümü | 2 | K2 ile aynı talimat ve çıktı sözleşmesi; 2 çözülmüş örnek eklenir. |
| K3_1shot | Aritmetik ifade | 1 | K3 ile aynı talimat ve çıktı sözleşmesi; 1 çözülmüş örnek eklenir. |
| K3_2shot | Aritmetik ifade | 2 | K3 ile aynı talimat ve çıktı sözleşmesi; 2 çözülmüş örnek eklenir. |
| K4_1shot | Python/PAL — serbest çözüm temsili | 1 | K4 ile aynı talimat ve çıktı sözleşmesi; 1 çözülmüş örnek eklenir. |
| K4_2shot | Python/PAL — serbest çözüm temsili | 2 | K4 ile aynı talimat ve çıktı sözleşmesi; 2 çözülmüş örnek eklenir. |
| K5_1shot | Python — deterministik durum güncelleme | 1 | K5 ile aynı talimat ve çıktı sözleşmesi; 1 çözülmüş örnek eklenir. |
| K5_2shot | Python — deterministik durum güncelleme | 2 | K5 ile aynı talimat ve çıktı sözleşmesi; 2 çözülmüş örnek eklenir. |
| K9 | Öğretmen CoT — Gemma örneği | 1 | gemma4:26b-mlx tarafından önceden üretilmiş tek açıklama; öğrenci K2 ile aynı talimat/parser kullanır. Gemma yargıç değildir. |

K2–K8 örnekli kollarında aynı örnek sorular, kola uygun çözüm gösterimleriyle kullanılır: GSM8K train 0 ve 2; one-shot yalnız ilkini kullanır. K9 da train 0 sorusunu kullanır, fakat açıklaması Gemma tarafından üretilmiştir. Aynı koldaki bütün modeller/hedef sorular aynı sabit örnekleri görür. API öğretimi, genel few-shot faydası, içerik ve prompt uzunluğu nedensel olarak tamamen ayrıştırılamaz.
K4 genel Python çözümüdür ve SymPy kullanabilir; K5 durum güncelleme talimatıdır. K5’in gerçekten stratejiye uyduğu insan incelemesiyle henüz doğrulanmamıştır. K6/K7/K8 aynı SymPy talimatını paylaşır.

## Veri ve üretim ayarları

Resmî Hugging Face `openai/gsm8k`, `main`, revision `740312add88f781978c0658806c59bc2815b9866`. Train 7.473, test 1.319 soru. Train’den seed 20261021 ile ayrılan sabit 200 soruluk pilotun ilk 10 kimliği kullanılmıştır. Test bölümü bu koşumda kullanılmadı. Örnekler pilot dışında; hedef sorular özgün İngilizce; gold yalnız değerlendirme katmanındadır.
Soru kimlikleri: `gsm8k:train:00001`, `gsm8k:train:00035`, `gsm8k:train:00044`, `gsm8k:train:00088`, `gsm8k:train:00104`, `gsm8k:train:00123`, `gsm8k:train:00148`, `gsm8k:train:00246`, `gsm8k:train:00370`, `gsm8k:train:00381`.
Beş modelin tamamı Q8_0; kesin ağırlık sürümleri/model digestleri koşum SQLite meta verisinde kayıtlıdır. Qwen `think=false`; LFM2 ayrı thinking modu sunmaz. CoT adımları normal yanıt metnindedir.
Gönderilen ortak üretim ayarları: `{"min_p": 0.0, "num_batch": 512, "num_ctx": 4096, "num_predict": 512, "num_thread": 8, "repeat_last_n": 64, "repeat_penalty": 1.0, "seed": 20261021, "temperature": 0, "top_k": 1, "top_p": 1.0}`.
Her üretim öncesi model boşaltılır, `keep_alive=0`; bütün 800 üretimde cache sayacı sıfır, beklenmeyen thinking/altyapı eksiği yoktur. Tek üretim; self-consistency, otomatik onarım, yeniden çözme veya güçlü modele yönlendirme yoktur.

## Puanlama: uçtan uca başarı

Tablodaki her hücre **doğru/10**; grafikte aynı ölçüm yüzde olarak gösterilir. Her doğru yanıt 10 yüzde puandır. Kesin normalize sayısal eşitlik kullanılır; eşdeğer tam sayı/ondalık/kesir ve geçerli para/binlik biçimleri normalize edilir. Geniş tolerans veya son görülen sayıyı seçme yoktur.
- K2 ve K9: tek nihai alan son satırda `FINAL: <sayı>` olmalıdır.
- K3: yanıtın tamamı izinli bir aritmetik ifade olmalıdır; AST hesaplayıcı sonucu değerlendirir.
- Kod kolları: Python 3.12.8 / SymPy 1.13.3 ile izole yürütme; stdout yalnız tek `FINAL: <sayı>` satırı olmalıdır. Kod içinde bulunan bir sayı cevap sayılmaz.
- Format/sözdizimi/API/kaynak/kesilme hataları uçtan uca başarıda başarısızdır. Altyapı eksikleri ayrı tutulur; bu koşumda yoktur.
**Bu ölçüm saf matematiksel doğruluk değildir.** Matematiksel olarak doğru bir yanıt format/çıktı aktarımı yüzünden başarısız sayılabilir. Semantik doğruluk için LLM yargıcı kullanılmadı. Semantik modelleme ve aritmetik hata ayrımı bu rapordan otomatik çıkarılamaz.

## Sonuç tablosu

| Koşul | lfm2-350m | lfm2-700m | lfm2-1.2b | qwen3-0.6b | qwen3-1.7b |
|---|---:|---:|---:|---:|---:|
| K2 | 0/10 | 2/10 | 1/10 | 2/10 | 9/10 |
| K3 | 0/10 | 0/10 | 0/10 | 0/10 | 5/10 |
| K4 | 0/10 | 0/10 | 0/10 | 0/10 | 0/10 |
| K5 | 0/10 | 0/10 | 0/10 | 0/10 | 0/10 |
| K6 | 0/10 | 0/10 | 0/10 | 0/10 | 0/10 |
| K7 | 0/10 | 0/10 | 1/10 | 0/10 | 5/10 |
| K8 | 1/10 | 1/10 | 4/10 | 0/10 | 5/10 |
| K2_1shot | 6/10 | 2/10 | 8/10 | 3/10 | 9/10 |
| K2_2shot | 6/10 | 8/10 | 9/10 | 7/10 | 10/10 |
| K3_1shot | 0/10 | 0/10 | 2/10 | 0/10 | 4/10 |
| K3_2shot | 0/10 | 0/10 | 5/10 | 3/10 | 5/10 |
| K4_1shot | 0/10 | 1/10 | 1/10 | 0/10 | 3/10 |
| K4_2shot | 1/10 | 4/10 | 3/10 | 0/10 | 8/10 |
| K5_1shot | 0/10 | 3/10 | 1/10 | 0/10 | 3/10 |
| K5_2shot | 0/10 | 5/10 | 4/10 | 4/10 | 5/10 |
| K9 | 4/10 | 5/10 | 6/10 | 5/10 | 6/10 |

## Tamamlanma, hata ve maliyet

| Durum | Kayıt sayısı |
|---|---:|
| format_error | 308 |
| correct | 195 |
| syntax_error | 174 |
| runtime_api_error | 14 |
| wrong_answer | 105 |
| generation_truncated | 3 |
| resource_limit | 1 |

Giriş/çıkış tokenları: **218,444 / 64,228**.
Üretim duvar süresi: **674.0 s**; bunun içinde model yükleme **310.6 s**. İzole yürütme/yorumlama: **64.3 s**. Yükleme üretim süresine tekrar eklenmez. Maliyetler bu donanım/cache politikası içindir.

## Başka bir değerlendirici için yorumlama sınırları

- Yalnız 10 benzersiz soru vardır. 800 kayıt, 800 bağımsız soru değildir; aynı soru bütün koşul/modellerde tekrar değerlendirilir.
- Koşul seçimi daha önceki keşifsel çalışmalardan sonra güncellenmiştir. Bu tablo bağımsız, ön kayıtlı doğrulayıcı deney olarak sunulmaz.
- Bütün modellerde en yüksek gözlenen skor K2_2shot’tadır; eşit skorlar olabilir. Bunun genel yöntem üstünlüğü olduğunu 10 sorudan çıkaramayız.
- Zero-shot başarısızlıkları format, sözdizimi ve API becerisini de içerir. 0/10 matematiksel yetersizliğin tek başına kanıtı değildir.
- K9 ile K2_1shot aynı örnek sayısı ve örnek sorusunda karşılaştırılabilir; öğretmen/açıklama içeriği birlikte değişir. K9 ile K2_2shot ayrıca örnek sayısında farklıdır.
- Farklı aileler arasındaki farklar mimari, eğitim ve parametre sayısını birlikte içerir; yalnız boyuta veya Liquid mimarisine bağlanamaz.
- Aynı ailede az sayıda boyuttan evrensel yetenek eşiği çıkarılamaz. Ayrı anlamlılık sonuçları etkileşim kanıtı değildir.
- Soru türü anotasyonları ve bağımsız insan hata incelemesi tamamlanmadı; alt grup/semantik hata sonuçları iddia edilmez.
- Eşleştirilmiş K9−K2_1shot bootstrap/McNemar ve beş model için Holm sonuçları summary.json içindedir; keşifseldir. Bu rapor ek anlamlılık iddiası üretmez.

Değerlendirme isteği: Gözlenen sayıları, olası açıklamaları ve bu tasarımla belirlenemeyen nedenleri ayrı belirtin. Format ile matematik hatasını aynı kabul etmeyin; ek inceleme gerektiren iddiaları işaretleyin.

## Eşlik eden dosyalar

- [Açıklamalı grafik](accuracy.png) — her koşulun adı ve örnek sayısı üzerinde yazılıdır.
- [Vektör grafik](accuracy.svg).
- [Makine tarafından okunabilir sonuçlar](summary.json).
- [Hücre bazlı sonuçlar ve maliyetler](summary.csv).
- [Koşum denetimi](audit.json).
