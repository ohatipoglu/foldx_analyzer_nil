# FoldX Genetik Mutasyon Analizörü ve Otomasyon Projesi Dokümantasyonu

Bu doküman, FoldX yazılımı kullanılarak gerçekleştirilen protein mutasyon analizlerinin manuel süreçten tam otomatik bir sistem haline getirilme sürecini, analiz mantığını ve geliştirilen yazılımın teknik detaylarını kapsamaktadır.

---

## 1. Proje Özeti ve Kapsam
Bu çalışma, protein mühendisliği süreçlerinde kullanılan **FoldX** yazılımının çıktılarını anlamlandırmak, bir genetik mühendisinin manuel iş akışını (Excel tabanlı hesaplamalar) dijitalleştirmek ve laboratuvar sentezlenebilirlik kriterlerini (Biomatik Rehberi) analiz sürecine dahil etmek amacıyla yürütülmüştür.

**Temel Hedef:** FoldX'in `Pssm` komutuyla ürettiği ham verileri okuyarak, termodinamik olarak stabil ve laboratuvar koşullarında sentezlenebilir "İdeal Mutasyon Adaylarını" otomatik olarak tespit etmektir.

---

## 2. Sorun Analizi: Manuel İş Akışı vs. Otomasyon Sapmaları
Projenin başında, mevcut otomasyon araçları ile mühendisin manuel Excel çalışmaları arasında grafiksel ve sayısal farklar olduğu tespit edilmiştir. Bu farkların nedenleri şunlardır:

1.  **Metrik Farklılığı:** Uygulama ham "Interaction Energy" değerlerini çizerken, mühendisin mutasyon etkisini anlamak için $\Delta\Delta G$ (Mutant - Wild Type) farkını kullandığı anlaşıldı.
2.  **Sterik Çakışmalar (Clashes):** FoldX simülasyonlarında bazen atomların üst üste binmesi sonucu +1000 kcal/mol gibi fiziksel olarak anlamsız enerji değerleri oluşmaktadır. Mühendis bunları manuel olarak temizlerken, ilk yazılımlar bu "gürültüyü" ortalamaya dahil ediyordu.
3.  **Filtreleme Mantığı:** Yazılımın başarısız adayları silerek grafikten çıkarması, mühendisin ise tüm 20 amino asitlik "profili" bir bütün olarak görüp karşılaştırma yapma ihtiyacı arasındaki fark giderildi.

---

## 3. Mühendisin İş Akış Mantığı (Analiz Algoritması)
Mühendisin bir protein pozisyonu (örneğin AH58) için izlediği laboratuvar-analiz adımları şöyledir:

* **Veri Üretimi:** FoldX terminalinde `command=Pssm` komutuyla 5 replika (`numberOfRuns=5`) üzerinden analiz başlatılır.
* **Eşleştirme:** Her bir mutasyon iterasyonu (Run 0, 1, 2, 3, 4) için üretilen **Mutant** yapısı ile **Wild Type (WT)** yapısı dosyada isimlerine göre eşleştirilir.
* **Enerji Farkı Hesaplama:** $$\Delta\Delta G = 	ext{Enerji}_{Mutant} - 	ext{Enerji}_{WT}$$
    hesaplaması her 5 run için ayrı ayrı yapılır.
* **İstatistiksel Doğrulama:** 5 adet $\Delta\Delta G$ değerinin ortalaması (MEAN) alınır. Standart Hata (SEM) ile hesaplamanın güvenilirliği kontrol edilir.
* **Karar Eşiği:** Ortalama $\Delta\Delta G < -0.5$ kcal/mol ise o mutasyon yapıyı stabilize ediyor kabul edilir ve "başarılı aday" olarak işaretlenir.

---

## 4. Sentezlenebilirlik ve Kimyasal Kurallar (Biomatik Entegrasyonu)
Sadece termodinamik olarak stabil olan bir mutasyon, laboratuvarda üretilemiyorsa değersizdir. **Biomatik Peptide Design Guideline** uyarınca sisteme şu filtreler eklenmiştir:

* **Hidrofobiklik Oranı:** Mutasyon sonucu oluşan dizideki hidrofobik amino asit oranı %50'yi geçmemelidir.
* **Şarj Dengesi:** Dizideki her 5 amino asitlik blokta en az 1 yüklü (pozitif/negatif) amino asit bulunmalıdır.
* **Jelleşme Riski:** Dizi içerisinde ardışık 4 veya daha fazla Glisin (G) bulunması sentez zorluğu (gel formation) yaratır.
* **N-Terminal Riskleri:** N-terminalinde Glutamin (Q) bulunması piroglutamat oluşumuna neden olabilir; bu durum kalite kontrolünde elenme sebebidir.

---

## 5. Uygulama Mimarisi ve Teknik Detaylar
Geliştirilen Python uygulaması (**FoldX Genetic Analyzer & Visualizer**), mühendisin manuel yaptığı tüm bu işlemleri tek bir tuşla gerçekleştirir.

### Veri İşleme Boru Hattı (Pipeline):
1.  **Parsing:** `.fxout` dosyası RegEx kullanılarak ayrıştırılır. Dosya ismindeki numara amino asit harfine (1->A, 20->Y) çevrilir.
2.  **Pairing:** Mutant ve WT satırları iterasyon ID'lerine göre yan yana getirilir.
3.  **Outlier Cleaning:** Z-Skoru yöntemiyle, sterik çakışma kaynaklı uçuk enerji değerleri otomatik temizlenir.
4.  **Labeling:** Her mutasyona "Ideal Candidate", "Rejected (Weak Stability)" veya "Synthesis Risk" etiketi basılır.
5.  **Multi-Sheet Excel:** Analiz sonuçları hem özet (Summary) hem de tüm hesaplama detaylarını içeren (Detailed) iki ayrı sekme halinde Excel'e aktarılır.

---

## 6. Kod Açıklamaları ve Fonksiyon Rehberi
Yazılımın anlaşılabilirliğini artırmak için temel fonksiyonların görevleri aşağıda açıklanmıştır:

### `parse_fxout(filepath)`
FoldX'ten çıkan ham TXT/FXOUT dosyasını okur. 
* `Pdb` sütunundan dosya isimlerini ayıklar.
* `Mutant` ve `WT` gruplarını oluşturur.
* Replika ID'lerini (0'dan 4'e) eşleştirerek satır bazlı $\Delta\Delta G$ farkını hesaplar.

### `calculate_statistics(df)`
Hesaplanan farkların istatistiksel analizini yapar.
* `groupby('AminoAcid')` ile her amino asit için 5 veriyi gruplar.
* Ortalama (MEAN) ve Standart Hata (SEM) hesaplar.
* `-0.5` eşiğini kontrol ederek karar sütununu oluşturur.

### `plot_profile(summary_df, filename)`
Matplotlib kullanarak mühendisin en çok ihtiyaç duyduğu "Profil Grafiğini" çizer.
* X ekseninde 20 amino asidin tamamını listeler.
* Y ekseninde enerji farkını gösterir.
* **Yeşil Barlar:** Seçilen ideal adayları.
* **Kırmızı Barlar:** Barajı geçemeyenleri temsil eder.
* Kesik çizgi ile **-0.5** eşiğini görsel olarak vurgular.

---

## 7. Kullanım Kılavuzu
1.  Uygulamayı çalıştırın (`python analiz.py`).
2.  "Dosya Seç" butonuyla FoldX'ten çıkan `.fxout` dosyasını seçin.
3.  "Analizi Başlat" butonuna tıklayın.
4.  Sistem aynı klasörde `[Dosya_Adi]_Analiz.xlsx` oluşturacak ve profil grafiğini ekrana getirecektir.

---
*Bu çalışma, genetik mühendisliği ile yazılım otomasyonunun birleştiği, hatasız ve hızlı protein tasarımı için tasarlanmış bir araçtır.*
