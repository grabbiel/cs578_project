import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np

# =================配置區=================
OUTPUT_IMAGE = 'a3.png'
# 定義要比較的實驗資料夾名稱
EXP_DIRS = ["attack_a3_rate1", "attack_a3_rate5"]
# 定義顏色
COLORS = ['tab:blue', 'tab:orange']
USE_LOG_SCALE_WND = True 
DELTA_T = 1  # 採樣時間間隔 (秒)，越小越靈敏，越大越平滑
# ========================================

def process_data(exp_name):
    """讀取並處理 Throughput (取樣法) 與 Window Size 數據"""
    ts_path = os.path.join(exp_name, 'timestamps.csv')
    wnd_path = os.path.join(exp_name, 'rcv_wnd.csv')
    
    # --- 1. 處理 Throughput (改用 Binning 算法) ---
    df_throughput = None
    if os.path.exists(ts_path):
        df_ts = pd.read_csv(ts_path)
        # 建立時間桶
        df_ts['time_bin'] = (df_ts['frame.time_relative'] // DELTA_T) * DELTA_T
        # 加總流量並轉換 Mbps
        df_throughput = df_ts.groupby('time_bin')['tcp.len'].sum().reset_index()
        df_throughput['Mbps'] = (df_throughput['tcp.len'] * 8) / (1_000_000 * DELTA_T)
    
    # --- 2. 處理 Window Size ---
    df_wnd = None
    if os.path.exists(wnd_path):
        df_wnd = pd.read_csv(wnd_path)
    
    return df_throughput, df_wnd

def generate_comparison_plot():
    # 建立 2x1 子圖，共用 X 軸
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 12), sharex=True)

    for exp_name, color in zip(EXP_DIRS, COLORS):
        print(f"正在處理: {exp_name}")
        df_tp, df_wnd = process_data(exp_name)

        # --- 上圖：Window Size ---
        if df_wnd is not None:
            ax1.plot(df_wnd['frame.time_relative'], df_wnd['tcp.window_size'], 
                     marker='.', markersize=1, linestyle='None', 
                     color=color, alpha=0.4, label=f'{exp_name}')

        # --- 下圖：Throughput (使用取樣後的平滑數據) ---
        if df_tp is not None:
            ax2.plot(df_tp['time_bin'], df_tp['Mbps'], 
                     color=color, linewidth=2, label=f'{exp_name}', alpha=0.8)

    # --- 圖表格式美化 ---
    ax1.set_ylabel('Window Size (Bytes)', fontsize=12)
    ax1.set_title('Receiver Window Size - a3', fontsize=16, fontweight='bold')
    ax1.grid(True, which='both', linestyle='--', alpha=0.5)
    if USE_LOG_SCALE_WND:
        ax1.set_yscale('log')
    ax1.legend(loc='upper right', markerscale=5)
    ax1.set_ylim(1, 10**7)

    ax2.set_ylabel('Throughput (Mbps)', fontsize=12)
    ax2.set_xlabel('Time (seconds)', fontsize=12)
    ax2.set_title(f'Download Throughput - a3', fontsize=16, fontweight='bold')
    ax2.grid(True, linestyle='--', alpha=0.5)
    ax2.set_ylim(bottom=0)
    ax2.legend(loc='upper right')

    plt.xlim(left=0)
    plt.tight_layout()
    
    plt.savefig(OUTPUT_IMAGE, dpi=300)
    print(f"✅ 對照圖已完成：{OUTPUT_IMAGE}")

if __name__ == "__main__":
    generate_comparison_plot()