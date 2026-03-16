import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np

# =================配置區=================
OUTPUT_IMAGE = 'baseline_b1_with_25s_line.png'
USE_LOG_SCALE_WND = True
exp_name = "baseline_b1"
MARK_TIME = 25
# ========================================

def generate_baseline_plots():
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10), sharex=True)

    wnd_path = os.path.join(exp_name, 'rcv_wnd.csv')
    bits_path = os.path.join(exp_name, 'bits_transfer.csv')

    if not (os.path.exists(wnd_path) and os.path.exists(bits_path)):
        print(f"錯誤：資料夾 '{exp_name}' 缺少 csv 檔案")
        return

    try:
        # --- 1. Window Size (上圖) ---
        df_wnd = pd.read_csv(wnd_path)
        y_wnd = df_wnd['tcp.window_size']
        
        ax1.plot(df_wnd['frame.time_relative'], y_wnd, 
                 marker='.', markersize=2, linestyle='None', color='tab:blue', alpha=0.5)
        
        ax1.axvline(x=MARK_TIME, color='red', linestyle='--', linewidth=2)
        ax1.set_xlim(left=0) 
        
        ax1.set_title(f'Receiver Window Size - {exp_name}', fontsize=16, fontweight='bold')
        ax1.set_ylabel('Window Size (Bytes)', fontsize=12)
        ax1.grid(True, which='both', linestyle='--', alpha=0.5)

        if USE_LOG_SCALE_WND:
            y_wnd = y_wnd.replace(0, 1)
            ax1.set_yscale('log')
            ax1.set_ylim(bottom=1)
        else:
            ax1.set_ylim(bottom=0)

        # --- 2. Throughput (下圖) ---
        df_bits = pd.read_csv(bits_path)
        df_bits['dt'] = df_bits['ElapsedSeconds'].diff()
        df_bits['db'] = df_bits['BytesTransferred'].diff()
        df_bits['Mbps'] = (df_bits['db'] * 8) / (df_bits['dt'] * 1000000)
        df_bits['Mbps'] = df_bits['Mbps'].fillna(0).replace([np.inf, -np.inf], 0)

        ax2.plot(df_bits['ElapsedSeconds'], df_bits['Mbps'], color='tab:green', linewidth=2)
        # ax2.step(df_bits['ElapsedSeconds'], df_bits['Mbps'], where='post', color='tab:green', linewidth=2)

        ax2.axvline(x=MARK_TIME, color='red', linestyle='--', linewidth=2)
        ax2.set_xlim(left=0)   
        ax2.set_ylim(bottom=0) 

        ax2.set_title(f'Download Throughput - {exp_name}', fontsize=16, fontweight='bold')
        ax2.set_ylabel('Throughput (Mbps)', fontsize=12)
        ax2.set_xlabel('Time (seconds)', fontsize=12)
        ax2.grid(True, linestyle='--', alpha=0.5)

        # --- 強制讓 X 軸顯示 25 ---
        # 取得目前的刻度
        plt.draw() # 先強制繪圖一次以計算自動刻度
        xticks = list(ax2.get_xticks())
        # 加入 25 並排序，同時過濾掉負數
        xticks = sorted(list(set([t for t in xticks if t >= 0] + [MARK_TIME])))
        ax2.set_xticks(xticks)

        plt.tight_layout()
        plt.savefig(OUTPUT_IMAGE, dpi=300)
        print(f"分析完成！X 軸已顯示 {MARK_TIME}。圖片：{OUTPUT_IMAGE}")

    except Exception as e:
        print(f"處理數據時發生錯誤: {e}")

if __name__ == "__main__":
    generate_baseline_plots()