# 🧬 FoldX Genetik Mutasyon Analiz Raporu

## 1. 📘 Yönetici Özeti
Bu proje, protein mühendisliği çalışmalarında kullanılan **FoldX** yazılımının `.fxout` çıktılarını işlemek üzere geliştirilmiş modern bir otomasyon aracıdır. Manuel Excel iş akışlarını dijitalleştirerek, mutasyonların termodinamik stabilitesini ($\Delta\Delta G$) hesaplar ve **Biomatik Sentezlenebilirlik** kriterlerine göre adayları filtreler.

## 2. ✨ Temel Özellikler
- **Hızlı Batch Analizi:** Klasör bazlı veya çoklu dosya seçimi ile paralel işlem.
- **Gelişmiş İstatistik:** MEAN, STD ve SEM hesaplamaları ile replika bazlı doğrulama.
- **Otomatik Outlier Temizliği:** Sterik çakışma (clash) kaynaklı hatalı verilerin (+50 kcal/mol üstü) elenmesi.
- **Biomatik Filtresi:** Hidrofobiklik, jelleşme riski ve şarj dengesi denetimi.
- **Zengin Görselleştirme:** Matplotlib tabanlı, yayın kalitesinde profil grafiklerinin otomatik oluşturulması.
- **Modern UI:** CustomTkinter ile karanlık mod desteği ve gerçek zamanlı loglama.

## 3. 🏗️ Mimari Analiz
Uygulama, **Modüler Katmanlı Mimari** prensiplerine göre yapılandırılmıştır:

- **UI Layer (`ui/`):** Arayüz bileşenleri, event binding ve thread yönetimi.
- **Core Logic (`core/`):** Parsing, istatistiksel hesaplama, görselleştirme ve dışa aktarma motorları.
- **Utilities (`utils/`):** Merkezi konfigürasyon, regex pattern'leri ve logger.

**Veri Akışı:**
`.fxout` (Raw) ➔ `Parser` ➔ `Statistics` (Cleaning) ➔ `Visualizer` (Plot) ➔ `Exporter` (Excel)

## 4. 📁 Dosya Yapısı
```text
C:\Projects\PycharmProjects\FoldX_Project_Nil\
├── core/
│   ├── exporter.py        # Excel (openpyxl) motoru
│   ├── parser.py          # .fxout (Regex) ayrıştırıcı
│   ├── statistics.py      # ΔΔG ve karar mantığı
│   ├── synthesizability.py# Biomatik kural motoru
│   └── visualizer.py      # Matplotlib çizim motoru
├── ui/
│   ├── main_window.py     # Ana pencere ve thread pool
│   └── widgets.py         # Custom UI komponentleri
├── utils/
│   ├── config.py          # Eşik değerler ve sabitler
│   └── logger.py          # Renkli konsol loglama
├── main.py                # Uygulama giriş noktası (Entry point)
└── output/                # Çıktı klasörleri (Otomatik oluşur)
    ├── excels/
    └── plots/
```

## 5. 🔍 Denetim Bulguları
| Kategori | Durum | Tespit |
| :--- | :---: | :--- |
| **Performans** | ✅ | ThreadPoolExecutor ile UI donması engellenmiş. |
| **Hata Yönetimi** | ⚠️ | Excel dosyası açıkken `PermissionError` yönetiliyor ancak uyarı mesajı iyileştirilebilir. |
| **Encoding** | 🚨 | Buton ikonlarında (`â–¶`) karakter bozulması (Mojibake) mevcut. |
| **Bilimsel Doğruluk**| ✅ | Outlier temizleme ve SEM hesaplama mantığı FoldX standartlarına uygun. |

## 6. 🧬 Biomatik Sentezlenebilirlik Kuralları
Uygulama, laboratuvar sentez başarısını artırmak için şu kuralları uygular:

| Kural | Eşik Değer | Risk |
| :--- | :--- | :--- |
| Hidrofobik Oran | < %50 | Suda çözünmeme riski |
| Şarj Dengesi | 5 AA'da en az 1 yüklü | Agregasyon (kümelenme) |
| Jelleşme | < 4 ardışık Gly (G) | Sentez zorluğu |
| N-Terminal | Q (Glutamin) yasağı | Piroglutamat oluşumu |

## 7. 🚀 Kullanım Kılavuzu
1. **Dosya Seçimi:** `.fxout` dosyalarını sürükleyip bırakın veya "Select Files" butonuyla seçin.
2. **Biomatik Aktivasyonu:** Opsiyonel olarak dizinizi girin ve "Biomatik Filtresi"ni işaretleyin.
3. **Analiz:** "Start Analysis"e basın.
4. **Sonuçlar:** `output/` dizinindeki Excel ve PNG dosyalarını inceleyin.

## 8. 🐛 Tespit Edilen Sorunlar ve Çözüm Önerileri

### 8.1 Encoding Sorunu (Kritik)
**Sorun:** `main_window.py` içindeki UTF-8 karakterler bozulmuş.
**Çözüm:** Dosyalar "UTF-8 without BOM" formatında kaydedilmeli ve stringler Python `u""` veya doğrudan UTF-8 literal olarak tanımlanmalı.

### 8.2 Biomatik Entegrasyon Boşluğu
**Sorun:** Mutasyonun dizideki tam konumu parser tarafından `statistics.py`'ye iletilmediği için kural denetimi tüm dizi üzerinden yapılıyor.
**Çözüm:** `Pdb` ismindeki pozisyon bilgisi (örn: `_1_0.pdb`'deki `1`) dizi indeksi olarak maplenmeli.

### 8.3 Paket Yapısı
**Sorun:** `__init__.py` eksikliği.
**Çözüm:** Tüm alt klasörlere boş `__init__.py` eklenmeli ve `main.py` içindeki `sys.path` manipülasyonu kaldırılmalı.

## 9. 🎯 Gelecek İyileştirmeler
- **PDB Görselleştirme:** PyMol veya NGLView entegrasyonu.
- **Interactive Plots:** Plotly kullanarak web tabanlı interaktif grafikler.
- **CLI Modu:** Sunucu taraflı batch analizler için komut satırı desteği.
- **Database Export:** SQLite veya PostgreSQL desteği.

---
*Hazırlayan: Gemini CLI Senior Architect & Auditor*
*Tarih: 15 Mayıs 2026*
