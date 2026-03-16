import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np

# =================配置區=================
OUTPUT_IMAGE = 'b1 vs a2_offset100.png'
EXP_BASELINE = "baseline_b1"
EXP_OFFSET = "attack_a2_offset100"  # 請確保此資料夾名稱正確
# ========================================

def process_throughput(exp_name):
    """讀取 CSV 並計算 Mbps"""
    path = os.path.join(exp_name, 'bits_transfer.csv')
    if not os.path.exists(path):
        print(f"錯誤：找不到 {path}")
        return None
    
    df = pd.read_csv(path)
    # 計算時間差與位元差
    df['dt'] = df['ElapsedSeconds'].diff()
    df['db'] = df['BytesTransferred'].diff()
    # 計算 Mbps: (Bytes * 8) / (Seconds * 10^6)
    df['Mbps'] = (df['db'] * 8) / (df['dt'] * 1000000)
    df['Mbps'] = df['Mbps'].fillna(0).replace([np.inf, -np.inf], 0)
    return df

def generate_comparison_plot():
    fig, ax = plt.subplots(figsize=(12, 7))

    # --- 1. 讀取與繪製 Baseline ---
    df_base = process_throughput(EXP_BASELINE)
    if df_base is not None:
        ax.step(df_base['ElapsedSeconds'], df_base['Mbps'], 
                where='post', color='tab:gray', linewidth=2, label='Baseline', alpha=0.7)

    # --- 2. 讀取與繪製 Offset 100 ---
    df_offset = process_throughput(EXP_OFFSET)
    if df_offset is not None:
        ax.step(df_offset['ElapsedSeconds'], df_offset['Mbps'], 
                where='post', color='tab:orange', linewidth=2, label='A2: Offset 100')

    # --- 圖表格式設定 ---
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)
    
    ax.set_title('Download Throughput Performance Comparison', fontsize=16, fontweight='bold')
    ax.set_ylabel('Throughput (Mbps)', fontsize=12)
    ax.set_xlabel('Time Relative (seconds)', fontsize=12)
    ax.grid(True, linestyle='--', alpha=0.5)
    
    # 強制 X 軸顯示 MARK_TIME
    plt.draw()

    # 加入圖例
    ax.legend(loc='upper right', fontsize=10)

    plt.tight_layout()
    plt.savefig(OUTPUT_IMAGE, dpi=300)
    print(f"比較圖表已生成：{OUTPUT_IMAGE}")

if __name__ == "__main__":
    generate_comparison_plot()