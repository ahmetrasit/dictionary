# Ayet Bazlı İkincil Rezonans Raporları

Bu dizinde kesin su hedef listesindeki her kök için bir rapor bulunur. Her rapor,
o kökün su anlamıyla hedeflenen ayetlerinin tamamını tek tek işler.

Her ayet bölümü şu ayrımı korur:

- **Birincil anlam:** Hedef kelimenin odak ayette yaptığı doğrudan iş.
- **Beş ayetlik sürpriz:** İki önceki ve iki sonraki ayetin hedef ayete eklediği
  ilişki, karşıtlık, tersine dönüş veya çağrışım.
- **İkincil rezonans hükmü:** Sürprizin gerçekten aynı kökün başka bir dalını
  etkinleştirip etkinleştirmediği. `A` ve `B` desteklenen, `C` araştırmaya açık,
  `Reject` reddedilen adaydır; `none` dal aktivasyonu bulunmadığını gösterir.

Hiçbir aday sonuç tablosundan çıkarılmaz. `C — keşifsel/zayıf` ve
`REJECT — reddedildi` adayları da raporda görünür; bu bölümler hem adayı doğuran
çağrışımı hem de hedef kelimeye neden yeterince bağlanmadığını açıklar. Her aday
şu üç soruya ayrı cevap verir: şaşırtıcı unsur nedir, birincil okumayı nasıl
değiştirir ve beş ayetlik penceredeki hangi unsur bu okumayı doğurur?

Bir pencerede şaşırtıcı anlatısal ilişki bulunması, otomatik olarak ikincil kök
anlamı bulunduğu demek değildir. Raporların amacı bu iki düzeyi görünür biçimde
ayırmaktır.

Kapsam, 197 farklı odak ayetini içerir. Bir ayet birden fazla su köküne ait
olabildiği için kök raporlarındaki ayet bölümlerinin toplamı 238'dir. Aynı ayette
aynı kökün birden fazla hedef biçimi varsa tek ayet bölümünde birlikte korunur.

Her Markdown raporunun aynı adlı PDF sürümü `pdf/` dizinindedir. PDF'ler şu
komutla yeniden üretilebilir:

```bash
python3 scripts/render_water_root_reports.py \
  --report-dir data/output/water_secondary_resonance/secondary_reports \
  --stylesheet data/output/water_secondary_resonance/root_reports/report.css
```
