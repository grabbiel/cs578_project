import pandas as pd
import matplotlib.pyplot as plt
import os
import glob
import numpy as np

def calculate_middle_rate_raw(csv_path):
    """
    從 bits_transfer.csv 計算 100MB 到 400MB 區間的原始平均速率 (Mbps)
    """
    try:
        df = pd.read_csv(csv_path)
        
        # 定義閾值 (Bytes)
        START_BYTES = 100 * 1024 * 1024
        END_BYTES = 400 * 1024 * 1024
        
        # 檢查資料總量是否足夠
        if df['BytesTransferred'].max() < END_BYTES:
            max_mb = df['BytesTransferred'].max() / (1024 * 1024)
            print(f"  [跳過] {os.path.basename(os.path.dirname(csv_path))}: 總量僅 {max_mb:.2f} MB，不足 400MB")
            return None
            
        # 找到第一個超過 100MB 的時間點
        start_row = df[df['BytesTransferred'] >= START_BYTES].iloc[0]
        # 找到第一個超過 400MB 的時間點
        end_row = df[df['BytesTransferred'] >= END_BYTES].iloc[0]
        
        # 計算時間差與資料量差
        duration = end_row['ElapsedSeconds'] - start_row['ElapsedSeconds']
        bytes_diff = end_row['BytesTransferred'] - start_row['BytesTransferred']
        
        if duration <= 0:
            return None
            
        # 算出 Mbps: (Bytes * 8) / (seconds * 1,000,000)
        rate_mbps = (bytes_diff * 8) / (duration * 1000000)
        return rate_mbps
    except Exception as e:
        return None

def main():
    root_dir = "."
    results = {}
    
    # 要排除的資料夾清單
    EXCLUDE_LIST = ['baseline_b1', 'baseline_b2', 'attack_a1_50ms_cubic', '.venv', '__pycache__', '.ipynb_checkpoints']

    # 1. 搜尋所有子目錄
    subdirs = [d for d in os.listdir(root_dir) if os.path.isdir(os.path.join(root_dir, d))]
    
    print(f"開始分析實驗資料夾 (排除 baseline_b1/b2)...")

    for exp_name in subdirs:
        # 跳過排除清單中的資料夾
        if exp_name in EXCLUDE_LIST or exp_name.startswith('.'):
            continue
            
        csv_path = os.path.join(root_dir, exp_name, "bits_transfer.csv")
        if os.path.exists(csv_path):
            rate = calculate_middle_rate_raw(csv_path)
            if rate is not None:
                results[exp_name] = rate
                print(f"實驗 {exp_name:30}: 平均速率 = {rate:6.2f} Mbps")

    if not results:
        print("\n[錯誤] 找不到符合 400MB 資料量要求的實驗資料。")
        return

    # 2. 準備繪圖數據
    # 依照速率從高到低排序
    sorted_items = sorted(results.items(), key=lambda x: x[1], reverse=True)
    names = [x[0] for x in sorted_items]
    rates = [x[1] for x in sorted_items]

    # 3. 繪圖
    plt.figure(figsize=(14, 8))
    # 使用漸層色或特定顏色區分
    colors = plt.cm.viridis(np.linspace(0.3, 0.7, len(names)))
    bars = plt.bar(names, rates, color=colors, edgecolor='black', alpha=0.8)

    # 在柱狀圖上方加上 Mbps 數值
    for bar in bars:
        yval = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2, yval + 1, f'{yval:.1f}', 
                 ha='center', va='bottom', fontsize=10, fontweight='bold')

    plt.title("Steady-State Throughput Comparison (Middle 300MB Phase)", fontsize=16)
    plt.xlabel("Experiment Patterns", fontsize=12)
    plt.ylabel("Average Throughput (Mbps)", fontsize=12)
    plt.xticks(rotation=45, ha='right')
    plt.grid(axis='y', linestyle='--', alpha=0.5)
    
    # 設定 Y 軸範圍，留一點空間給標籤
    plt.ylim(0, max(rates) * 1.15)
    
    plt.tight_layout()
    
    # 4. 儲存圖片
    save_path = "experiment_throughput_300MB.png"
    plt.savefig(save_path, dpi=300)
    print(f"\n[成功] 原始數值柱狀圖已儲存至: {save_path}")

if __name__ == "__main__":
    main()