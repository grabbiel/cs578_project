import pandas as pd
import matplotlib.pyplot as plt
import os
import glob
import numpy as np

def plot_rtt_analysis():
    # 1. 設定根目錄為目前資料夾
    results_root = "."
    
    # 尋找所有實驗資料夾 (假設實驗資料夾就在目前目錄下)
    experiment_dirs = [d for d in glob.glob(os.path.join(results_root, "*")) if os.path.isdir(d)]
    experiment_dirs = ["baseline_b1", "attack_a2_offset100"]
    if not experiment_dirs:
        print("在目前目錄下找不到任何實驗資料夾。")
        return

    # 設定畫布：每個實驗一個子圖
    num_exps = len(experiment_dirs)
    fig, axes = plt.subplots(num_exps, 1, figsize=(15, 6 * num_exps), squeeze=False)

    for i, exp_dir in enumerate(experiment_dirs):
        exp_name = os.path.basename(exp_dir)
        ts_csv = os.path.join(exp_dir, "timestamps.csv")
        wnd_csv = os.path.join(exp_dir, "rcv_wnd.csv")
        bits_csv = os.path.join(exp_dir, "bits_transfer.csv")
        
        ax1 = axes[i, 0]
        
        # 檢查必要檔案
        if os.path.exists(ts_csv) and os.path.exists(wnd_csv) and os.path.exists(bits_csv):
            try:
                # --- 讀取資料 ---
                df_ts = pd.read_csv(ts_csv)
                df_wnd = pd.read_csv(wnd_csv)
                df_bits = pd.read_csv(bits_csv)

                # --- RTT 計算 ---
                df_ts = df_ts.dropna(subset=['tcp.options.timestamp.tsecr'])
                df_wnd = df_wnd.dropna(subset=['tcp.options.timestamp.tsval'])

                tx_times = df_wnd.groupby('tcp.options.timestamp.tsval')['frame.time_relative'].min()
                df_ts['tx_time'] = df_ts['tcp.options.timestamp.tsecr'].map(tx_times)
                df_ts['rtt_ms'] = (df_ts['frame.time_relative'] - df_ts['tx_time']) * 1000
                
                df_rtt = df_ts[(df_ts['rtt_ms'] > 0) & (df_ts['rtt_ms'] < 2000)].copy()

                # --- 網速計算 (Mbps) ---
                # 這裡使用兩次記錄之間的時間差來計算，會比直接除以 1 更準確
                df_bits['dt'] = df_bits['ElapsedSeconds'].diff()
                df_bits['db'] = df_bits['BytesTransferred'].diff()
                df_bits['Mbps'] = (df_bits['db'] * 8) / (df_bits['dt'] * 1000000)
                df_bits['Mbps'] = df_bits['Mbps'].fillna(0).replace([np.inf, -np.inf], 0)

                # --- 繪圖：左軸 RTT (固定 0-100 ms) ---
                lns1 = ax1.plot(df_rtt['frame.time_relative'], df_rtt['rtt_ms'], 
                                color='tab:red', alpha=0.5, label='RTT (ms)', linewidth=1)
                ax1.set_ylabel('RTT (ms)', color='tab:red', fontsize=12)
                ax1.tick_params(axis='y', labelcolor='tab:red')
                ax1.set_ylim(0, 105) # <--- 固定 RTT 上限
                ax1.set_xlim(0, 50) # <--- 固定 RTT 上限
                
                ax1.set_title(f"Experiment: {exp_name}", fontsize=14, fontweight='bold')
                ax1.grid(True, alpha=0.3)

                # --- 繪圖：右軸 Throughput (固定 0-500 Mbps) ---
                ax2 = ax1.twinx()
                lns2 = ax2.plot(df_bits['ElapsedSeconds'], df_bits['Mbps'], 
                                color='tab:blue', label='Throughput (Mbps)', linewidth=2)
                ax2.set_ylabel('Throughput (Mbps)', color='tab:blue', fontsize=12)
                ax2.tick_params(axis='y', labelcolor='tab:blue')
                ax2.set_ylim(0, 500) # <--- 固定下載速度上限
                ax2.set_xlim(0, 50)

                plt.xlabel("Time (seconds)", fontsize=12)

                # 合併圖例
                lns = lns1 + lns2
                labs = [l.get_label() for l in lns]
                ax1.legend(lns, labs, loc='upper left')

            except Exception as e:
                ax1.text(0.5, 0.5, f"Error processing {exp_name}: {e}", ha='center')
        else:
            ax1.text(0.5, 0.5, f"Missing CSV files in {exp_name}", ha='center')

    plt.xlabel("Elapsed Time (seconds)", fontsize=12)
    plt.tight_layout()
    
    # 儲存到根目錄
    save_path = "rtt_throughput.png"
    plt.savefig(save_path, dpi=300)
    print(f"分析圖表已儲存至: {save_path}")

if __name__ == "__main__":
    plot_rtt_analysis()