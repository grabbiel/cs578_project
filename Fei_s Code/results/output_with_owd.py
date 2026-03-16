import pandas as pd
import matplotlib.pyplot as plt
import os
import numpy as np

# =================配置區=================
# 1. 取樣時間間隔 (delta t)，主要是為了圖表標示參考
DELTA_T = 1 

# 2. 輸出圖片檔名
OUTPUT_IMAGE = 'baseline_b1_vs_attack_a2_offset100_bits.png'
USE_LOG_SCALE_WND = True

# 3. 排除清單
EXCLUDE_DIRS = ['.venv', '__pycache__', '.ipynb_checkpoints']

# 4. 指定顯示的實驗資料夾
experiment_dirs = ["baseline_b1", "attack_a2_offset100"]
# ========================================

def process_owd_with_resets(df):
    """
    偵測 TCP 重置並分段計算 OWD
    """
    # 1. 偵測連線重置點：當目前的 seq 比前一個小，代表是新連線
    df['session_id'] = (df['tcp.seq'] < df['tcp.seq'].shift(1)).fillna(False).astype(int).cumsum()
    
    # 2. 計算原始 OWD (ms)
    df['owd_raw'] = (df['frame.time_relative'] * 1000) - df['tcp.options.timestamp.tsval']
    
    # 3. 分段歸一化：針對每個 session 獨立減去最小值
    df['owd_norm'] = df.groupby('session_id')['owd_raw'].transform(lambda x: x - x.min())
    df['owd_norm'] = df['owd_norm'].clip(lower=0, upper=100)
    return df

def generate_comparison_plots():
    # 建立圖表畫布 (3個子圖)
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(14, 16), sharex=True)

    for exp_name in experiment_dirs:
        wnd_path = os.path.join(exp_name, 'rcv_wnd.csv')
        ts_path = os.path.join(exp_name, 'timestamps.csv')
        bits_path = os.path.join(exp_name, 'bits_transfer.csv')

        # 檢查該資料夾下是否具備必要的檔案
        if not (os.path.exists(wnd_path) and os.path.exists(ts_path) and os.path.exists(bits_path)):
            print(f"跳過 '{exp_name}': 缺少必要的 CSV 檔案 (rcv_wnd/timestamps/bits_transfer)")
            continue

        print(f"正在處理實驗: {exp_name}...")

        try:
            # --- 1. Window Size (上圖 - 決策) ---
            df_wnd = pd.read_csv(wnd_path)
            y_wnd = df_wnd['tcp.window_size']
            if USE_LOG_SCALE_WND:
                y_wnd = y_wnd.replace(0, 1)
                ax1.set_yscale('log')
            
            ax1.plot(df_wnd['frame.time_relative'], y_wnd, 
                     marker='.', markersize=2, linestyle='None', alpha=0.5, label=exp_name)

            # --- 2. OWD (中圖 - 輸入信號) ---
            df_ts = pd.read_csv(ts_path).dropna(subset=['tcp.options.timestamp.tsval'])
            df_ts = process_owd_with_resets(df_ts)

            ax2.plot(df_ts['frame.time_relative'], df_ts['owd_norm'], 
                     marker='.', markersize=1, linestyle='None', alpha=0.4, label=exp_name)

            # --- 3. Throughput (下圖 - 結果，改用 bits_transfer.csv) ---
            df_bits = pd.read_csv(bits_path)
            
            # 計算兩筆記錄之間的時間差 (dt) 與 位元組差 (db)
            df_bits['dt'] = df_bits['ElapsedSeconds'].diff()
            df_bits['db'] = df_bits['BytesTransferred'].diff()
            
            # Mbps 公式: (Bytes * 8) / (Time * 1,000,000)
            df_bits['Mbps'] = (df_bits['db'] * 8) / (df_bits['dt'] * 1000000)
            
            # 清理第一行的 NaN 以及可能的除以零異常
            df_bits['Mbps'] = df_bits['Mbps'].fillna(0).replace([np.inf, -np.inf], 0)

            # 使用階梯圖 (step) 繪製 Mbps
            ax3.step(df_bits['ElapsedSeconds'], df_bits['Mbps'], 
                     where='post', alpha=0.8, linewidth=2, label=exp_name)

        except Exception as e:
            print(f"處理 '{exp_name}' 時發生錯誤: {e}")

    # --- 圖表格式化 ---
    ax1.set_title('Receiver Window Size (rLEDBAT Decision)', fontsize=14)
    ax1.set_ylabel('Window Size (Bytes)')
    ax1.grid(True, which='both', linestyle='--', alpha=0.5)
    ax1.legend(loc='upper right', fontsize='x-small', ncol=2)

    ax2.set_title('One-Way Delay (OWD - Input Signal)', fontsize=14)
    ax2.set_ylabel('Relative OWD (ms)')
    ax2.set_ylim(-5, 105) # OWD 通常觀察 0-100ms
    ax2.grid(True, linestyle='--', alpha=0.5)

    ax3.set_title('Download Throughput (Calculated from bits_transfer.csv)', fontsize=14)
    ax3.set_ylabel('Throughput (Mbps)')
    ax3.set_xlabel('Time Relative (seconds)')
    ax3.grid(True, linestyle='--', alpha=0.5)
    ax3.legend(loc='upper right', fontsize='x-small', ncol=2)

    plt.tight_layout()
    plt.savefig(OUTPUT_IMAGE, dpi=300)
    print(f"\n=============================================")
    print(f"對比圖表已生成: {OUTPUT_IMAGE}")
    print(f"=============================================")

if __name__ == "__main__":
    generate_comparison_plots()