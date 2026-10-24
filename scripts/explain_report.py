"""Add self-contained condition definitions to a completed report; no inference calls."""
import argparse
import json
import pathlib
import sqlite3
import sys
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]))
from gsm8k_lab.common import ROOT

DEFINITIONS={
 'K2':('CoT — adım adım doğal dil çözümü',0,'Yürütme yok; son satır FINAL: <sayı>.'),
 'K3':('Aritmetik ifade',0,'Model tek ifade üretir; izin listeli AST hesaplayıcı hesaplar.'),
 'K4':('Python/PAL — serbest çözüm temsili',0,'Model program üretir; Python kodu Docker izolasyonunda çalıştırılır.'),
 'K5':('Python — deterministik durum güncelleme',0,'Miktarlar olay sırasına göre güncellenir; rastgelelik/Monte Carlo yok. Kod Docker’da yürütülür.'),
 'K6':('SymPy — zero-shot',0,'Model SymPy kodu üretir; Python/SymPy Docker’da yürütülür.'),
 'K7':('SymPy — one-shot',1,'K6 ile aynı talimat; bir doğru SymPy örneği eklenir.'),
 'K8':('SymPy — two-shot',2,'K6 ile aynı talimat; iki doğru örnek, ilki K7 ile aynı.'),
 'K9':('Öğretmen CoT — Gemma örneği',1,'gemma4:26b-mlx tarafından önceden üretilmiş tek açıklama; öğrenci K2 ile aynı talimat/parser kullanır. Gemma yargıç değildir.')}
for arm in ['K2','K3','K4','K5']:
 for shots in [1,2]:
  DEFINITIONS[f'{arm}_{shots}shot']=(DEFINITIONS[arm][0],shots,f'{arm} ile aynı talimat ve çıktı sözleşmesi; {shots} çözülmüş örnek eklenir.')


def enrich(rid, database=None):
    out=ROOT/'reports'/rid
    summary=json.loads((out/'summary.json').read_text())
    models=['lfm2-350m','lfm2-700m','lfm2-1.2b','qwen3-0.6b','qwen3-1.7b']
    n=len(summary['question_ids'])
    cells=summary['cells'];conditions=list(dict.fromkeys(c['condition'] for c in cells))
    if set(conditions)!=set(DEFINITIONS):raise ValueError('Unexpected condition set')
    before={p.name:p.read_bytes() for p in [out/'summary.json',out/'summary.csv',out/'audit.json']}
    cfg=json.loads((ROOT/'configs/repeat10.json').read_text())
    with sqlite3.connect(f'file:{ROOT/(database or cfg["database"])}?mode=ro',uri=True) as db:
        meta=json.loads(db.execute('SELECT metadata FROM runs WHERE id=?',(rid,)).fetchone()[0])
    effective=meta['identity']['effective_config']
    lines=[f'# GSM8K: {n} soruluk temsil ve örnek karşılaştırması','',
        f'Koşum: `{rid}`. Tamamlanan: **{summary["completed_records"]}/{summary["expected"]}**.',
        'Araştırma sorusu: Harici hesaplamanın faydası temsil biçimine, model büyüklüğüne ve verilen çözüm/API örneklerine göre nasıl değişiyor?',
        'Bu rapor önceki sohbetten bağımsız okunabilir. Mevcut yöntemlerin kontrollü, keşifsel karşılaştırmasıdır; yeni yöntem/öncelik iddiası yoktur.','',
        '## Deney koşulları','',
        '**Zero-shot:** çözülmüş örnek yok. **One-shot / 1shot:** bir örnek. **Two-shot / 2shot:** iki örnek. Shot sayısı deneme/yeniden üretim sayısı değildir; her hedef soru için tek üretim yapılır.',
        '**CoT (Chain of Thought):** doğal dilde adım adım çözüm. **PAL:** programla temsil edilen çözüm. **SymPy:** Python sembolik matematik kütüphanesi.',
        '', '| Kod | Açıklama | Örnek sayısı | Üretim ve yürütme |','|---|---|---:|---|']
    for c in conditions:
        name,shots,description=DEFINITIONS[c]
        lines.append(f'| {c} | {name} | {shots} | {description} |')
    lines+=['',
        'K2–K8 örnekli kollarında aynı örnek sorular, kola uygun çözüm gösterimleriyle kullanılır: GSM8K train 0 ve 2; one-shot yalnız ilkini kullanır. K9 da train 0 sorusunu kullanır, fakat açıklaması Gemma tarafından üretilmiştir. Aynı koldaki bütün modeller/hedef sorular aynı sabit örnekleri görür. API öğretimi, genel few-shot faydası, içerik ve prompt uzunluğu nedensel olarak tamamen ayrıştırılamaz.',
        'K4 genel Python çözümüdür ve SymPy kullanabilir; K5 durum güncelleme talimatıdır. K5’in gerçekten stratejiye uyduğu insan incelemesiyle henüz doğrulanmamıştır. K6/K7/K8 aynı SymPy talimatını paylaşır.',
        '', '## Veri ve üretim ayarları','',
        f'Resmî Hugging Face `openai/gsm8k`, `main`, revision `740312add88f781978c0658806c59bc2815b9866`. Train 7.473, test 1.319 soru. Bu koşum {n} farklı soru içerir; seçim: {meta["identity"]["config"]["question_selection"]}. Hedef sorular özgün İngilizce; gold yalnız değerlendirme katmanındadır. Kullanılan demonstration soruları değerlendirmede yoktur.',
        'Soru kimlikleri: '+', '.join(f'`{q}`' for q in summary['question_ids'])+'.',
        'Beş modelin tamamı Q8_0; kesin ağırlık sürümleri/model digestleri koşum SQLite meta verisinde kayıtlıdır. Qwen `think=false`; LFM2 ayrı thinking modu sunmaz. CoT adımları normal yanıt metnindedir.',
        'Gönderilen ortak üretim ayarları: `'+json.dumps(effective['options'],ensure_ascii=False,sort_keys=True)+'`.',
        f'Koşumun kaydedilmiş cache politikası: {meta["identity"].get("cache_policy", "metadata belirtilmemiş")}. İstek keep_alive: {effective["keep_alive"]}. Gerçek cache ve tamamlanma denetimi audit.json içindedir. Tek üretim; self-consistency, otomatik onarım, yeniden çözme veya güçlü modele yönlendirme yoktur.',
        '', '## Puanlama: uçtan uca başarı','',
        f'Tablodaki her hücre **doğru/{n}**; grafikte aynı ölçüm yüzde olarak gösterilir. Her doğru yanıt {100/n:g} yüzde puandır. Kesin normalize sayısal eşitlik kullanılır; eşdeğer tam sayı/ondalık/kesir ve geçerli para/binlik biçimleri normalize edilir. Geniş tolerans veya son görülen sayıyı seçme yoktur.',
        '- K2 ve K9: tek nihai alan son satırda `FINAL: <sayı>` olmalıdır.',
        '- K3: yanıtın tamamı izinli bir aritmetik ifade olmalıdır; AST hesaplayıcı sonucu değerlendirir.',
        '- Kod kolları: Python 3.12.8 / SymPy 1.13.3 ile izole yürütme; stdout yalnız tek `FINAL: <sayı>` satırı olmalıdır. Kod içinde bulunan bir sayı cevap sayılmaz.',
        '- Format/sözdizimi/API/kaynak/kesilme hataları uçtan uca başarıda başarısızdır. Altyapı eksikleri ayrı tutulur; bu koşumda yoktur.',
        '**Bu ölçüm saf matematiksel doğruluk değildir.** Matematiksel olarak doğru bir yanıt format/çıktı aktarımı yüzünden başarısız sayılabilir. Semantik doğruluk için LLM yargıcı kullanılmadı. Semantik modelleme ve aritmetik hata ayrımı bu rapordan otomatik çıkarılamaz.',
        '', '## Sonuç tablosu','',
        '| Koşul | '+' | '.join(models)+' |','|---|'+'---:|'*len(models)]
    for c in conditions:
        values=[]
        for m in models:
            cell=next(x for x in cells if x['model']==m and x['condition']==c)
            values.append(f'{cell["correct"]}/{n}' if cell['complete'] else 'eksik')
        lines.append('| '+c+' | '+' | '.join(values)+' |')
    errors={}
    for cell in cells:
        for status,error_count in cell['errors'].items():errors[status]=errors.get(status,0)+error_count
    lines+=['','## Tamamlanma, hata ve maliyet','',
        '| Durum | Kayıt sayısı |','|---|---:|']
    for k,v in errors.items():lines.append(f'| {k} | {v} |')
    totals={k:sum(c.get(k,0) or 0 for c in cells) for k in ['input_tokens','output_tokens','generation_wall_seconds','load_seconds','execution_seconds']}
    lines+=['',f'Giriş/çıkış tokenları: **{totals["input_tokens"]:,} / {totals["output_tokens"]:,}**.',
        f'Üretim duvar süresi: **{totals["generation_wall_seconds"]:.1f} s**; bunun içinde model yükleme **{totals["load_seconds"]:.1f} s**. İzole yürütme/yorumlama: **{totals["execution_seconds"]:.1f} s**. Yükleme üretim süresine tekrar eklenmez. Maliyetler bu donanım/cache politikası içindir.',
        '', '## Başka bir değerlendirici için yorumlama sınırları','',
        f'- {n} benzersiz soru vardır. {summary["expected"]} kayıt, {summary["expected"]} bağımsız soru değildir; aynı soru bütün koşul/modellerde tekrar değerlendirilir.',
        '- Koşul seçimi daha önceki keşifsel çalışmalardan sonra güncellenmiştir. Bu tablo bağımsız, ön kayıtlı doğrulayıcı deney olarak sunulmaz.',
        '- Yöntem sıralamaları bu örnekleme ve çıktı sözleşmelerine bağlıdır; evrensel üstünlük olarak yorumlanamaz.',
        f'- Zero-shot başarısızlıkları format, sözdizimi ve API becerisini de içerir. 0/{n} matematiksel yetersizliğin tek başına kanıtı değildir.',
        '- K9 ile K2_1shot aynı örnek sayısı ve örnek sorusunda karşılaştırılabilir; öğretmen/açıklama içeriği birlikte değişir. K9 ile K2_2shot ayrıca örnek sayısında farklıdır.',
        '- Farklı aileler arasındaki farklar mimari, eğitim ve parametre sayısını birlikte içerir; yalnız boyuta veya Liquid mimarisine bağlanamaz.',
        '- Aynı ailede az sayıda boyuttan evrensel yetenek eşiği çıkarılamaz. Ayrı anlamlılık sonuçları etkileşim kanıtı değildir.',
        '- Soru türü anotasyonları ve bağımsız insan hata incelemesi tamamlanmadı; alt grup/semantik hata sonuçları iddia edilmez.',
        '- Eşleştirilmiş K9−K2_1shot bootstrap/McNemar ve beş model için Holm sonuçları summary.json içindedir; keşifseldir. Bu rapor ek anlamlılık iddiası üretmez.',
        '', 'Değerlendirme isteği: Gözlenen sayıları, olası açıklamaları ve bu tasarımla belirlenemeyen nedenleri ayrı belirtin. Format ile matematik hatasını aynı kabul etmeyin; ek inceleme gerektiren iddiaları işaretleyin.',
        '', '## Eşlik eden dosyalar','',
        '- [Açıklamalı grafik](accuracy.png) — her koşulun adı ve örnek sayısı üzerinde yazılıdır.',
        '- [Vektör grafik](accuracy.svg).',
        '- [Makine tarafından okunabilir sonuçlar](summary.json).',
        '- [Hücre bazlı sonuçlar ve maliyetler](summary.csv).',
        '- [Koşum denetimi](audit.json).']
    (out/'REPORT.md').write_text('\n'.join(lines)+'\n')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    matrix=np.array([[100*(next(x['accuracy'] for x in cells if x['model']==m and x['condition']==c) if next(x['accuracy'] for x in cells if x['model']==m and x['condition']==c) is not None else np.nan) for m in models] for c in conditions])
    labels=[f'{c} — {DEFINITIONS[c][0]}\n{DEFINITIONS[c][1]} çözülmüş örnek' for c in conditions]
    fig,ax=plt.subplots(figsize=(14,14))
    im=ax.imshow(matrix,vmin=0,vmax=100,cmap='Blues',aspect='auto')
    for y in range(len(conditions)):
        for x in range(len(models)):
            v=matrix[y,x];ax.text(x,y,'N/A' if np.isnan(v) else f'{v:.1f}%',ha='center',va='center',fontsize=12,color='white' if v>65 else 'black')
    ax.set_yticks(range(len(conditions)),labels,fontsize=10)
    ax.set_xticks(range(len(models)),models,rotation=20,ha='right',fontsize=10)
    ax.set_title(f'GSM8K • {n} soru / hücre • 5 model (Q8_0)\nUçtan uca doğruluk: format + yürütme + sayısal sonuç',fontsize=15,pad=18)
    fig.colorbar(im,ax=ax,label='Doğruluk (%)',fraction=.03,pad=.03)
    fig.text(.02,.018,f'CoT: doğal dilde adımlar | PAL: Python programı | SymPy: sembolik matematik\nK9: Gemma öğretmeninden 1 örnek; yargıç yok. Aynı {n} soru tekrar ölçülür; bulgular keşifseldir.',fontsize=10)
    fig.subplots_adjust(left=.43,right=.92,top=.92,bottom=.10)
    for ext in ['png','svg']:fig.savefig(out/f'accuracy.{ext}',dpi=180)
    plt.close(fig)
    assert all((out/name).read_bytes()==data for name,data in before.items())
    print(out)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('run_id');parser.add_argument('--database',help='Optional source SQLite path for historical runs');args=parser.parse_args();enrich(args.run_id,args.database)
