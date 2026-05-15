import tkinter as tk
from tkinter import filedialog, messagebox
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os

# FoldX'in PSSM taramasında kullandığı standart 20 Amino Asit sırası
AMINO_ACIDS = ['A', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'K', 'L',
               'M', 'N', 'P', 'Q', 'R', 'S', 'T', 'V', 'W', 'Y']


class FoldXAnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("FoldX Genetic Analyzer & Visualizer")
        self.root.geometry("600x450")
        self.root.configure(padx=20, pady=20)

        # UI Elemanları
        self.label = tk.Label(root, text="FoldX .fxout Dosyası Seçin:", font=("Arial", 12, "bold"))
        self.label.pack(pady=10)

        self.btn_file = tk.Button(root, text="Dosya Seç (.fxout)", command=self.select_file, width=30)
        self.btn_file.pack(pady=5)

        self.btn_run = tk.Button(root, text="Analizi Başlat & Excel Oluştur", command=self.run_analysis, bg="green",
                                 fg="black", font=("Arial", 12, "bold"))
        self.btn_run.pack(pady=20)

        self.log_text = tk.Text(root, height=15, width=70, state=tk.DISABLED, bg="#f4f4f4")
        self.log_text.pack(pady=10)

        self.selected_path = None

    def log(self, message):
        """Ekrana anlık log yazdırır"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)
        self.root.update()

    def select_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("FoldX Output", "*.fxout"), ("All Files", "*.*")])
        if file_path:
            self.selected_path = file_path
            self.log(f"Seçilen Dosya: {os.path.basename(file_path)}")

    def run_analysis(self):
        if not self.selected_path:
            messagebox.showwarning("Uyarı", "Lütfen önce bir dosya seçin!")
            return

        self.log("\n--- Analiz Başlıyor ---")
        try:
            # 1. Veriyi Oku ve Eşleştir (Detailed Data)
            detailed_df = self.parse_fxout(self.selected_path)

            # 2. İstatistikleri Hesapla ve Etiketle (Summary Data)
            summary_df = self.calculate_statistics(detailed_df)

            # 3. Dinamik Excel İsimlendirmesi ve Kayıt
            base_filename = os.path.splitext(os.path.basename(self.selected_path))[0]
            export_path = os.path.join(os.path.dirname(self.selected_path), f"{base_filename}_Analiz.xlsx")

            try:
                with pd.ExcelWriter(export_path, engine='openpyxl') as writer:
                    # Birinci Sayfa: Mühendisin Karar Tablosu
                    summary_df.to_excel(writer, sheet_name='Ozet_Analiz', index=False)
                    # İkinci Sayfa: Tüm Hesaplanan Delta Delta G Değerleri (100 Satır)
                    detailed_df.to_excel(writer, sheet_name='Hesaplama_Detaylari', index=False)
                self.log(f"Başarılı! Excel 2 sayfa olarak kaydedildi:\n{export_path}")

            except PermissionError:
                # Dosya açık kalma kontrolü
                messagebox.showerror("Dosya Açık Hatası",
                                     f"Excel dosyası şu an başka bir programda açık!\n\nLütfen kapatıp tekrar deneyin:\n{export_path}")
                self.log("HATA: Excel dosyası açık olduğu için üzerine yazılamadı!")
                return

                # 4. Grafiği Çiz
            self.plot_profile(summary_df, base_filename)

        except Exception as e:
            self.log(f"HATA OLUŞTU: {str(e)}")
            messagebox.showerror("Hata", f"İşlem sırasında bir hata oluştu:\n{str(e)}")

    def parse_fxout(self, filepath):
        """FoldX dosyasını okur, WT ve Mutant'ı ayırır, Delta Delta G'yi hesaplar."""
        self.log("Dosya okunuyor ve eşleştiriliyor...")

        raw_df = pd.read_csv(filepath, sep='\t', skipinitialspace=True)
        raw_df.columns = raw_df.columns.str.strip()

        # Mutant vs WT ayrımı
        raw_df['Is_WT'] = raw_df['Pdb'].str.startswith('./WT_')

        # Dosya isminden Mutasyon Numarası ve Run ID çekme
        extracted = raw_df['Pdb'].str.extract(r'_(\d+)_(\d+)\.pdb')
        raw_df['Mut_Index'] = pd.to_numeric(extracted[0])
        raw_df['Run_ID'] = pd.to_numeric(extracted[1])

        # Amino Asit harfini haritalama
        raw_df['AminoAcid'] = raw_df['Mut_Index'].apply(
            lambda x: AMINO_ACIDS[int(x) - 1] if pd.notnull(x) and 1 <= int(x) <= 20 else 'Unknown'
        )

        wt_df = raw_df[raw_df['Is_WT']][['Mut_Index', 'Run_ID', 'Interaction Energy']]
        wt_df = wt_df.rename(columns={'Interaction Energy': 'WT_Energy'})

        mut_df = raw_df[~raw_df['Is_WT']][['Mut_Index', 'Run_ID', 'AminoAcid', 'Interaction Energy']]
        mut_df = mut_df.rename(columns={'Interaction Energy': 'Mutant_Energy'})

        # Yan yana birleştir
        merged_df = pd.merge(mut_df, wt_df, on=['Mut_Index', 'Run_ID'], how='inner')

        # Delta Delta G Hesaplaması
        merged_df['ddG'] = merged_df['Mutant_Energy'] - merged_df['WT_Energy']

        # Sütun sırasını düzenle
        cols = ['AminoAcid', 'Mut_Index', 'Run_ID', 'Mutant_Energy', 'WT_Energy', 'ddG']
        valid_df = merged_df[cols].copy()

        self.log(f"Eşleştirme tamamlandı. Geçerli iterasyon sayısı: {len(valid_df)}")
        return valid_df

    def calculate_statistics(self, df):
        """MEAN, STDEV, SEM hesaplar ve etiketleme yapar."""
        self.log("İstatistikler ve karar etiketleri hazırlanıyor...")

        # Sterik çakışmaları (FoldX hesaplama hataları) temizle
        clean_df = df[df['ddG'] < 50.0].copy()

        stats = clean_df.groupby('AminoAcid').agg(
            Valid_Runs=('ddG', 'count'),
            MEAN_ddG=('ddG', 'mean'),
            STDEV_ddG=('ddG', 'std'),
            SEM_ddG=('ddG', 'sem')
        ).reset_index()

        # Karar Eşiği Damgası
        stats['Decision_Status'] = stats['MEAN_ddG'].apply(
            lambda x: 'IDEAL CANDIDATE' if x < -0.5 else 'REJECTED'
        )

        # Standart amino asit sırasına göre sırala
        stats['Order'] = stats['AminoAcid'].apply(lambda x: AMINO_ACIDS.index(x) if x in AMINO_ACIDS else 99)
        stats = stats.sort_values('Order').drop(columns=['Order'])

        basarili_sayisi = len(stats[stats['MEAN_ddG'] < -0.5])
        self.log(f"<-0.5 eşiğini geçen İdeal Aday sayısı: {basarili_sayisi}")

        return stats

    def plot_profile(self, summary_df, filename):
        """20 Amino Asitlik profil grafiğini çizer."""
        self.log("Grafik çiziliyor...")

        plt.figure(figsize=(12, 6))

        # Renk ataması
        colors = ['#2ca02c' if val < -0.5 else '#d62728' for val in summary_df['MEAN_ddG']]

        bars = plt.bar(
            summary_df['AminoAcid'],
            summary_df['MEAN_ddG'],
            yerr=summary_df['SEM_ddG'],
            capsize=5,
            color=colors,
            edgecolor='black',
            alpha=0.8
        )

        plt.axhline(y=-0.5, color='black', linestyle='--', linewidth=2, label='Threshold (-0.5 kcal/mol)')
        plt.axhline(y=0.0, color='gray', linestyle='-', linewidth=1)

        plt.title(f"Thermodynamic Mutational Profile\n{filename}", fontsize=14, fontweight='bold')
        plt.xlabel("Mutated Amino Acid", fontsize=12, fontweight='bold')

        # Raw string kullanılarak \D hatası çözüldü
        plt.ylabel(r"$\Delta\Delta G$ (kcal/mol)", fontsize=12, fontweight='bold')

        import matplotlib.patches as mpatches
        green_patch = mpatches.Patch(color='#2ca02c', label='Ideal Candidate (< -0.5)')
        red_patch = mpatches.Patch(color='#d62728', label='Rejected (>= -0.5)')
        plt.legend(handles=[green_patch, red_patch, plt.Line2D([0], [0], color='black', linestyle='--', lw=2)],
                   loc='upper right')

        plt.grid(axis='y', linestyle='--', alpha=0.7)
        plt.tight_layout()
        plt.show()


if __name__ == "__main__":
    root = tk.Tk()
    app = FoldXAnalyzerApp(root)
    root.mainloop()