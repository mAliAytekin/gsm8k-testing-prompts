# 10 soruluk deney — repeat10-warm-v5

K2–K8, K2–K5 one-/two-shot kontrolleri ve tek öğretmen örnekli K9:
16 koşul/model, beş Q8_0 model, toplam 800 üretim.
Sabit 200 soruluk pilot manifestinin ilk 10 kimliği kullanılır.
K9 yalnız train0 açıklamasını, diğer örnekli koşullar A çiftini kullanır.

Koşul seçimi önceki keşifsel gözlemlerden sonra güncellenmiştir; bu tasarım
ilk değerlendirmeden önce kaydedilmiş yeni bir protokol gibi sunulmaz.
Her soruya tek yanıt; otomatik düzeltme, yargıç veya tekrar çözme yoktur.

Yapılandırma configs/repeat10.json; çıktı results/repeat10-warm.sqlite.
Model digestleri ve veri manifest hash'i configs/model-lock.json ile doğrulanır;
eski koşum veritabanı gerekmez. Kod, prompt, örnek ve config hashleri kimliktedir.
Qwen think=false, temperature=0, context4096, output512. Model istekler arasında keep_alive="30m" ile bellekte tutulur. Prompt cache
kullanımı kabul edilir; ölçülen/eksik sayaçlar ayrı kaydedilir. Docker izolasyonu zorunludur.

Koşum sonrası reports/RUN_ID/ altında tablo, grafik, denetim ve süre/token
özetleri oluşur. Payda her hücrede 10; eksikler açık gösterilir. K9−K2_1shot
beş model için eşleştirilmiş soru bootstrap'ı, McNemar ve Holm aile5 ile
keşifsel karşılaştırılır. Aynı soru farklı koşullarda bağımsız örnek sayılmaz.
K9 farkı öğretmen kaynağı ile açıklama içeriğinin birlikte değişimini içerir.

Komutlar README içindedir. Yeni koşum ve tam test temizlik sırasında başlatılmadı.
