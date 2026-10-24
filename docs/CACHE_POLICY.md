# Model belleği ve prompt cache politikası

Güncel ayar `keep_alive: "30m"`. Proje istemcisi üretim öncesinde veya sonrasında
modeli boşaltmaz. Runner model bazında çalışır; aynı modelin soruları art arda
üretilir. İlk model yüklemesi ve model değişimi maliyeti devam eder. Ollama bellek
baskısında modeli çıkarabilir; bellekte kalma ayarı yeniden yüklemeyi mutlak olarak
engellemez. `/api/ps` ile gerçek warm/cold durumu kaydedilir.

Prompt/KV cache kullanımına izin verilir. `prompt_eval_cached_count` mevcutsa
olduğu gibi saklanır, pozitif olması hata sayılmaz. Eksik sayaç sıfır varsayılmaz;
denetimde eksik ölçüm olarak raporlanır. Bu, tamamlanmış cevabı dosyadan döndürmek
değildir; her soru için yeni üretim isteği yapılır. Önceki konuşma geçmişi eklenmez.
Qwen think=false ve diğer üretim parametreleri korunur. Model yanıtı başarısızsa
cache kullanımı gerekçesiyle yeniden üretilmez.

İstek keep_alive ayarı sunucunun global varsayılanını geçersiz kılar. Daha önceki
macOS OLLAMA_KEEP_ALIVE=0 oturum ayarı bu proje isteklerini etkilemez; global
sunucu ayarını değiştirmek veya Ollama'yı yeniden başlatmak gerekmez.

Yeni koşumlar ayrı kimlik ve veritabanlarına yazılır: repeat10-warm.sqlite ve
base-warm.sqlite. Önceki cache-kapalı ölçümler warm ölçümü olarak yeniden etiketlenmez.
Cache'in doğruluğa etkisinin sıfır olduğu varsayılmaz; doğruluk/token/süreler gerçek
koşumda ölçülür. Cache tekrar kullanımı ve bellek yerleşimi süre karşılaştırmasının
bir parçasıdır. İstemci duvar süresi yüklemeyi içerir; load_seconds tekrar eklenmez.

Gerçek teknik kontrol: artifacts/warm-model-validation.json. Aynı küçük tanısal
isteğin iki üretiminde ikinci istek modeli bellekte buldu ve cache kullandı. Bu
iki istek araştırma doğruluğu veya tam deney hız tahmini değildir.
