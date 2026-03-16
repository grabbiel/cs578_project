import pandas as pd
import matplotlib.pyplot as plt
import os
import glob
import numpy as np

# 1. 設定結果目錄
results_root = r"."
experiment_dirs = [d for d in glob.glob(os.path.join(results_root, "*")) if os.path.isdir(d)]

plt.figure(figsize=(12, 7))

# 2. 遍歷每個實驗資料夾
for exp_dir in experiment_dirs:
    exp_name = os.path.basename(exp_dir)
    bits_csv = os.path.join(exp_dir, "bits_transfer.csv")
    wifi_csv = os.path.join(exp_dir, "wifi_signal_log.csv")
    
    # 確保兩個檔案都存在才進行計算
    if os.path.exists(bits_csv) and os.path.exists(wifi_csv):
        try:
            # 讀取數據
            df_bits = pd.read_csv(bits_csv)
            df_wifi = pd.read_csv(wifi_csv)
            
            # 計算瞬間網速 (Mbps)
            # diff() 算出每秒位元差，乘以 8 轉為 bits，除以 1M 轉為 Mbps
            df_bits['Mbps'] = (df_bits['BytesTransferred'].diff().fillna(0) * 8) / 1000000
            
            # 數據對齊處理：
            # 因為 Wi-Fi Log 是每 5 秒記一次，BITS 是每 1 秒記一次
            # 我們使用 numpy 的 interp 功能，根據時間將 RxRate 補插值到 BITS 的時間點上
            rx_interp = np.interp(
                df_bits['ElapsedSeconds'], 
                df_wifi['ElapsedSeconds'], 
                df_wifi['RxRate']
            )
            
            # 計算利用率 (Mbps / RxRate)
            # 加上 1e-6 避免除以 0
            df_bits['Utilization'] = df_bits['Mbps'] / (rx_interp + 1e-6)
            
            # 3. 畫線 (過濾掉最後完成的幾秒，避免統計誤差)
            mask = df_bits['Utilization'] < 1.2 # 排除異常值
            plt.plot(
                df_bits.loc[mask, 'ElapsedSeconds'], 
                df_bits.loc[mask, 'Utilization'], 
                label=exp_name, 
                linewidth=1.5
            )
            
        except Exception as e:
            print(f"處理 {exp_name} 時出錯: {e}")

# 4. 圖表美化
plt.title("Network Utilization Ratio (Throughput / RxRate)", fontsize=16)
plt.xlabel("Elapsed Time (seconds)", fontsize=12)
plt.ylabel("Utilization Ratio (0.0 - 1.0)", fontsize=12)

# 設定 Y 軸範圍，通常 TCP 利用率最高在 0.8 左右
plt.ylim(0, 1.0)
plt.grid(True, which='both', linestyle='--', alpha=0.5)

# 圖例放在右側
plt.legend(title="Experiments", bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()

# 5. 儲存圖片
save_path = os.path.join(results_root, "all_experiments_utilization.png")
plt.savefig(save_path, dpi=300)
print(f"\n[成功] 鏈路利用率比較圖已儲存至: {save_path}")