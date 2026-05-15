# 🧬 FoldX Genetik Mutasyon Analizörü ve Görselleştirici

Protein mühendisliği ve genetik araştırmalar için **FoldX** yazılımının çıktılarını (PSSM - `.fxout` dosyaları) analiz eden, termodinamik stabiliteyi hesaplayan ve Biomatik sentezlenebilirlik kurallarını otomatik uygulayan masaüstü otomasyon aracı.

---

## ✨ Temel Özellikler

- 🚀 **Hızlı Batch Analizi:** Tek bir dosya, birden fazla dosya veya tüm klasörü tek tıkla işleme imkanı. (Çok izlekli/multi-threaded mimari ile arayüz donmaz.)
- 📊 **Gelişmiş İstatistikler:** Mutasyonların 5 replikası üzerinden ortalama (MEAN), standart sapma (STD) ve standart hata (SEM) hesaplamaları.
- 🧹 **Otomatik Gürültü Temizliği:** Fiziksel olarak anlamsız sterik çakışmaları (clash) $\Delta\Delta G \ge 50$ kcal/mol eşiğiyle otomatik temizleme.
- 🧪 **Biomatik Filtresi:** Mutasyonların laboratuvar ortamında sentezlenebilirlik riskini (Hidrofobiklik, Şarj dengesi, Jelleşme, N-Terminal riskleri) denetleme.
- 📈 **Zengin Görselleştirme:** Yayın kalitesinde, eşik çizgileri ve hata paylarını (error bars) içeren mutasyon profil grafiklerinin (Matplotlib) otomatik üretilmesi.
- 🎨 **Modern Kullanıcı Arayüzü:** CustomTkinter tabanlı, karanlık/aydınlık (dark/light) mod destekli, sürükle-bırak yeteneğine sahip şık GUI.

---

## 🖼️ Ekran Görüntüleri

![Uygulama Arayüzü](ekran_goruntusu.png "FoldX Analyzer UI") *(Buraya uygulamanın ekran görüntüsünü ekleyebilirsiniz)*

---

## 🚀 Hızlı Başlangıç

### Gereksinimler
- Python 3.9 veya daha güncel bir sürüm.

### Kurulum Adımları

1. Projeyi bilgisayarınıza klonlayın:
   ```bash
   git clone https://github.com/KULLANICI_ADINIZ/FoldX_Project_Nil.git
   cd FoldX_Project_Nil
   ```

2. Sanal bir Python ortamı (virtual environment) oluşturun (Önerilir):
   ```bash
   python -m venv venv
   # Windows için aktivasyon:
   venv\Scripts\activate
   # macOS/Linux için aktivasyon:
   source venv/bin/activate
   ```

3. Gerekli bağımlılıkları yükleyin:
   ```bash
   pip install -r requirements.txt
   ```

4. Uygulamayı çalıştırın:
   ```bash
   python main.py
   ```

---

## 🖥️ Kullanım Kılavuzu

1. **Dosya Yükleme:** Arayüz açıldığında `.fxout` uzantılı dosyalarınızı doğrudan "Sürükle-Bırak" alanına bırakabilir veya "Select Files" / "Select Folder" butonlarını kullanabilirsiniz.
2. **Biomatik Aktivasyonu (Opsiyonel):** Eğer laboratuvar sentez risklerini denetlemek isterseniz, "Biomatik Sentezlenebilirlik Filtresi" kutucuğunu işaretleyip orijinal peptid dizisini girin.
3. **Analizi Başlatma:** Seçimlerin ardından `▶ Start Analysis` butonuna tıklayın. İşlem ilerlemesini Progress Bar ve Activity Log üzerinden gerçek zamanlı takip edebilirsiniz.
4. **Sonuçları Görüntüleme:** İşlem bittiğinde tablo üzerinde oluşan satırlara **çift tıklayarak** o analizin profil grafiğini anında açabilirsiniz.

---

## 📂 Çıktı Dizini (`output/`)

Analizler tamamlandığında proje kök dizininde otomatik olarak bir `output/` klasörü oluşur.
- `output/excels/`: İçerisinde iki sayfa barındıran (Özet ve Detaylı Hesaplamalar) analiz sonuç dosyalarını (`_Analiz.xlsx`) tutar.
- `output/plots/`: Üretilen bar grafiklerini yüksek çözünürlüklü (`.png`) formatta tutar.

---

## 🧪 Bilimsel Arka Plan ve Kurallar

Uygulamanın karar mekanizması aşağıdaki temel kurallara dayanır:

**Termodinamik Eşikler:**
- **Hesaplama:** $\Delta\Delta G$ = $Enerji_{Mutant}$ - $Enerji_{WT}$
- **İdeal Aday Eşiği:** Ortalama $\Delta\Delta G < -0.5$ kcal/mol ise mutasyon yapıyı stabilize eder.
- **Sterik Çakışma Filtresi:** Eşik değeri $50.0$ kcal/mol üzerindekiler outlier kabul edilir.

**Biomatik Sentezlenebilirlik Kuralları:**
| Kural | Risk Durumu |
| :--- | :--- |
| **Hidrofobiklik Oranı** | Hidrofobik AA oranı > %50 ise çözünürlük düşer. |
| **Şarj Dengesi** | Her 5 AA'lık blokta en az 1 yüklü AA yoksa agregasyon riski. |
| **Jelleşme (Gel Risk)** | $\ge 4$ ardışık Glycine (G) bulunması sentezi zorlaştırır. |
| **N-Terminal Riski** | Dizinin başında Glutamine (Q) olması piroglutamat riski yaratır. |

---

## 🏗️ Mimari & Katkıda Bulunma

Proje, genişletilebilir modüler bir yapıya sahiptir:
- `core/`: Regex tabanlı parser, istatistik hesaplamaları, Biomatik kuralları, export ve Matplotlib motoru.
- `ui/`: CustomTkinter arayüzü, Thread-pool yönetimi, özel widget'lar.
- `utils/`: Log yönetimi ve merkezi konfigürasyon değişkenleri.

**Katkıda Bulunmak İçin:**
1. Projeyi fork'layın.
2. Yeni bir dal oluşturun (`git checkout -b feature/yeni-ozellik`).
3. Değişikliklerinizi yapıp commit'leyin (`git commit -m 'Yeni özellik eklendi'`).
4. Dalınıza push yapın (`git push origin feature/yeni-ozellik`).
5. Bir Pull Request (PR) açın.

---

## 🐛 Sorun Giderme

- **`PermissionError: Excel dosyası açık`**: Eğer oluşturulan `_Analiz.xlsx` dosyası arka planda açıksa uygulama üzerine yazamaz. Excel'i kapatıp arayüzden çıkan uyarıdaki "Tekrar Dene" butonuna basmanız yeterlidir.
- **`ParseException` Hatası**: Bu hata giderilmiştir. Grafik çizim backend'i artık thread-safe olarak `Agg` şeklinde tanımlı olup LaTeX sözdizimi Unicode ile değiştirilmiştir.
- **UTF-8 Encoding Hataları**: Terminalinizde Türkçe karakterlerin bozulmaması için uygulamanın `UTF-8` kodlama formatıyla çalıştırıldığına dikkat edin.

---

## 📜 Lisans & İletişim

Bu proje **MIT Lisansı** ile lisanslanmıştır. Akademik ve araştırma amaçlı serbestçe kullanılabilir, değiştirilebilir ve dağıtılabilir. 

Projeyle ilgili sorularınız veya hata bildirimleri için **Issues** sekmesini kullanabilirsiniz.
