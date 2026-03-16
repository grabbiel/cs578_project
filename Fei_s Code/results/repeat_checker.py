import pandas as pd
import matplotlib.pyplot as plt
import os

# =================配置區=================
DELTA_T = 0.1  # 統計重複 ACK 的時間單位（秒）
EXP_DIR = 'baseline_b1'  # 你想分析的資料夾名稱
# ========================================

def analyze_and_plot_with_dupacks(folder_path):
    wnd_path = os.path.join(folder_path, 'rcv_wnd.csv')
    
    if not os.path.exists(wnd_path):
        print(f"錯誤：找不到 {wnd_path}")
        return

    # 1. 讀取數據
    df = pd.read_csv(wnd_path)
    
    # 2. 識別重複 ACK (Duplicate ACKs)
    # 定義：目前的 ACK 號碼與上一個完全相同
    df['is_dup'] = (df['tcp.ack'] == df['tcp.ack'].shift(1))
    
    # 3. 統計每秒出現幾次重複 ACK
    df['time_bin'] = (df['frame.time_relative'] // DELTA_T) * DELTA_T
    dup_stats = df[df['is_dup'] == True].groupby('time_bin').size().reset_index(name='dup_count')

    # 4. 繪圖
    fig, ax1 = plt.subplots(figsize=(12, 6))

    # 繪製 Window Size (左 Y 軸)
    ax1.plot(df['frame.time_relative'], df['tcp.window_size'], 
             marker='.', markersize=2, linestyle='None', color='blue', alpha=0.4, label='Window Size')
    ax1.set_xlabel('Time (s)')
    ax1.set_ylabel('Window Size (Bytes)', color='blue')
    ax1.set_yscale('log') # 通常 Window Size 用 Log 比較好看
    ax1.tick_params(axis='y', labelcolor='blue')

    # 建立右 Y 軸來繪製重複 ACK 數量
    ax2 = ax1.twinx()
    ax2.bar(dup_stats['time_bin'], dup_stats['dup_count'], 
            width=DELTA_T, alpha=0.3, color='red', label='Duplicate ACK Count', align='edge')
    ax2.set_ylabel('Duplicate ACK Count (per sec)', color='red')
    ax2.tick_params(axis='y', labelcolor='red')

    plt.title(f'Window Size vs Duplicate ACKs ({folder_path})')
    fig.tight_layout()
    
    output_name = f'verify_loss_{folder_path}.png'
    plt.savefig(output_name, dpi=300)
    print(f"分析完成！結果圖片：{output_name}")
    print(f"總重複 ACK 次數：{df['is_dup'].sum()}")

if __name__ == "__main__":
    analyze_and_plot_with_dupacks(EXP_DIR)