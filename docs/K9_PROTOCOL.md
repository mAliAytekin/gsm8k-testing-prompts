# K9 — tek öğretmen örneği

K9, K2 ile aynı ortak talimatı, CoT çıktı sözleşmesini ve parser'ı kullanır.
Tek fark prompttaki sabit örnek açıklamasıdır. Öğretmen tam adı gemma4:26b-mlx;
üretim sırasında öğrenci modelin yerine kullanılmaz ve cevapları değerlendirmez.

Mevcut demonstrations/k9/teacher.json bankasında train 0/2/3/4 için geçmişte
üretilmiş dört açıklama bulunur. Güncel runner yalnız ilkini (train0) seçer.
Bankanın kalan açıklamaları kaynak bütünlüğünü korumak için saklanır; yeni
öğrenci promptuna eklenmez. Banka üretim ayarları configs/k9.json içindedir.

`python scripts/k9.py verify` soruları, split ayrımını, nihai sayıları, çözüm
inceleme hash'ini ve ham öğretmen yanıtlarını doğrular. `prepare` mevcut bankayı
korur; banka yoksa üretim aracıdır. K9 dört örnekli eski öğrenci runner'ı kaldırıldı.
Güncel öğrenci deneyi scripts/repeat10.py üzerinden yürütülür.

Kaynak yanıtlara artifacts/k9-teacher altından erişilir. Adım incelemesi ajan
incelemesidir; bağımsız insan doğrulaması olarak sunulmaz. Örnekler pilot/testle
çakışmaz. Güçlü öğretmen örneğinin avantajı varsayılmaz; K2_1shot ile aynı soru
ve örnek sayısında karşılaştırılır. Bu karşılaştırma içerik farklarını ortadan kaldırmaz.
