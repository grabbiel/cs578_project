import pandas as pd
import matplotlib.pyplot as plt
import os
import glob
import numpy as np

def plot_wifi_throughput_analysis():
    # 1. 設定實驗資料夾
    experiment_dirs = ["baseline_b1", "attack_a2_offset100"]
    
    WIFI_CSV = "wifi_signal_log.csv" 
    BITS_CSV = "bits_transfer.csv"
    
    num_exps = len(experiment_dirs)
    fig, axes = plt.subplots(num_exps, 1, figsize=(15, 6 * num_exps), squeeze=False)

    for i, exp_dir in enumerate(experiment_dirs):
        exp_name = os.path.basename(exp_dir)
        wifi_path = os.path.join(exp_dir, WIFI_CSV)
        bits_path = os.path.join(exp_dir, BITS_CSV)
        
        ax1 = axes[i, 0]
        
        if os.path.exists(wifi_path) and os.path.exists(bits_path):
            try:
                # --- 讀取資料 ---
                df_wifi = pd.read_csv(wifi_path)
                df_bits = pd.read_csv(bits_path)
                
                # --- 網速計算 ---
                df_bits['dt'] = df_bits['ElapsedSeconds'].diff()
                df_bits['db'] = df_bits['BytesTransferred'].diff()
                df_bits['Mbps'] = (df_bits['db'] * 8) / (df_bits['dt'] * 1000000)
                df_bits['Mbps'] = df_bits['Mbps'].fillna(0).replace([np.inf, -np.inf], 0)

                # --- 繪圖：左軸 Wi-Fi Signal ---
                color_signal = 'tab:orange'
                lns1 = ax1.plot(df_wifi['ElapsedSeconds'], df_wifi['Signal'], 
                                color=color_signal, alpha=0.7, label='Wi-Fi Signal', linewidth=2)
                ax1.set_ylabel('Wi-Fi Signal (Quality/Strength)', color=color_signal, fontsize=12)
                ax1.tick_params(axis='y', labelcolor=color_signal)
                ax1.set_ylim(0, 105)
                
                # 限制 X 軸範圍：0 到 50 秒
                ax1.set_xlim(0, 50) 
                
                ax1.set_title(f"Experiment: {exp_name}", fontsize=14, fontweight='bold')
                ax1.grid(True, alpha=0.3, linestyle='--')

                # --- 繪圖：右軸 Throughput ---
                ax2 = ax1.twinx()
                color_tp = 'tab:blue'
                lns2 = ax2.plot(df_bits['ElapsedSeconds'], df_bits['Mbps'], 
                                color=color_tp, label='Throughput (Mbps)', linewidth=2)
                ax2.set_ylabel('Throughput (Mbps)', color=color_tp, fontsize=12)
                ax2.tick_params(axis='y', labelcolor=color_tp)
                ax2.set_ylim(0, 500)

                # 合併圖例：修正 alpha -> framealpha
                lns = lns1 + lns2
                labs = [l.get_label() for l in lns]
                ax1.legend(lns, labs, loc='upper left', frameon=True, framealpha=0.8)

            except Exception as e:
                print(f"處理 {exp_name} 時發生錯誤: {e}")
                ax1.text(0.5, 0.5, f"Error processing {exp_name}", ha='center')
        else:
            ax1.text(0.5, 0.5, f"Missing CSV files", ha='center')

    plt.xlabel("Elapsed Time (seconds)", fontsize=12)
    plt.tight_layout()
    
    save_path = "wifi_throughput.png"
    plt.savefig(save_path, dpi=300)
    print(f"分析圖表已儲存至: {save_path} (已截斷至 50s)")

if __name__ == "__main__":
    plot_wifi_throughput_analysis()