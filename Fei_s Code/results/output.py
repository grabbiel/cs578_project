import pandas as pd
import matplotlib.pyplot as plt
import os

# =================配置區=================
# 1. 取樣時間間隔 (delta t)，單位為秒
DELTA_T = 1

# 2. 輸出圖片檔名
OUTPUT_IMAGE = 'experiment_comparison.png'
USE_LOG_SCALE = True


# 3. 排除清單 (如果不想要掃描某些資料夾，可以放在這裡)
EXCLUDE_DIRS = ['.venv', '__pycache__', '.ipynb_checkpoints']
# ========================================

def generate_comparison_plots():
    # 獲取當前目錄下所有的資料夾
    all_entries = os.listdir('.')
    experiment_dirs = [d for d in all_entries if os.path.isdir(d) and d not in EXCLUDE_DIRS]
    
    if not experiment_dirs:
        print("找不到任何實驗資料夾！")
        return

    # 建立圖表畫布 (2個子圖，上下堆疊)
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 12), sharex=True)

    experiment_dirs = ["baseline_b1", "attack_a2_offset100", "attack_a2_offset500", "attack_a2_offset500_frac25", "attack_a3_rate1", "attack_a3_rate5"]

    # 遍歷每個實驗資料夾
    for exp_name in experiment_dirs:
        wnd_path = os.path.join(exp_name, 'rcv_wnd.csv')
        ts_path = os.path.join(exp_name, 'timestamps.csv')

        # 檢查該資料夾下是否具備必要的檔案
        if not (os.path.exists(wnd_path) and os.path.exists(ts_path)):
            print(f"跳過資料夾 '{exp_name}': 缺少 csv 檔案")
            continue

        print(f"正在處理實驗: {exp_name}...")

        try:
            # --- 處理 Window Size 數據 ---
            df_wnd = pd.read_csv(wnd_path)
            
            y_data = df_wnd['tcp.window_size']
            
            if USE_LOG_SCALE:
                # 處理 0 的方法：將 0 替換為 1，確保 log(1) = 0
                y_data = y_data.replace(0, 1)
                ax1.set_yscale('log') # 直接叫 Matplotlib 使用對數座標
                ax1.set_ylabel('Window Size (Bytes) - Log Scale')
            else:
                ax1.set_ylabel('Window Size (Bytes)')

            ax1.plot(df_wnd['frame.time_relative'], y_data, 
         marker='.', markersize=2, linestyle='None', 
         alpha=0.6, label=exp_name)

            # --- 處理 Throughput 數據 ---
            df_ts = pd.read_csv(ts_path)
            # 計算時間區間 (Bins)
            df_ts['time_bin'] = (df_ts['frame.time_relative'] // DELTA_T) * DELTA_T
            
            # 依時間區間加總 bytes 並轉換成 Mbps
            throughput_df = df_ts.groupby('time_bin')['tcp.len'].sum().reset_index()
            throughput_df['throughput_mbps'] = (throughput_df['tcp.len'] * 8) / (1_000_000 * DELTA_T)

            # 繪製 Throughput 到下方子圖 (使用 step 階梯圖)
            ax2.step(throughput_df['time_bin'], throughput_df['throughput_mbps'], 
                     where='post', alpha=0.8, label=exp_name)

        except Exception as e:
            print(f"處理 '{exp_name}' 時發生錯誤: {e}")

    # --- 圖表格式化 ---
    # 上圖: Window Size
    ax1.set_ylabel('Window Size (Bytes)')
    ax1.set_title(f'rLEDBAT Receiver Window Size Comparison (Multi-Experiment)')
    ax1.grid(True, which='both', linestyle='--', alpha=0.5)
    ax1.legend(loc='upper right', fontsize='small', ncol=2)

    # 下圖: Throughput
    ax2.set_xlabel('Time Relative (seconds)')
    ax2.set_ylabel('Throughput (Mbps)')
    ax2.set_title(f'Download Throughput Comparison ($\Delta t = {DELTA_T}s$)')
    ax2.grid(True, which='both', linestyle='--', alpha=0.5)
    ax2.legend(loc='upper right', fontsize='small', ncol=2)

    # 自動調整佈局
    plt.tight_layout()
    
    # 儲存圖片
    plt.savefig(OUTPUT_IMAGE, dpi=300)
    print(f"\n=============================================")
    print(f"所有實驗比對完成！結果已儲存至: {OUTPUT_IMAGE}")
    print(f"=============================================")

if __name__ == "__main__":
    generate_comparison_plots()