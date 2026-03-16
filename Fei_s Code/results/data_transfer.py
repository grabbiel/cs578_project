import pandas as pd
import matplotlib.pyplot as plt
import os

# =================配置區=================
OUTPUT_IMAGE = 'all_transfer_comparison_MB.png'
TARGET_FILE = 'bits_transfer.csv'
# ========================================

def plot_total_transferred_mb():
    plt.figure(figsize=(12, 8))
    
    # 獲取當前目錄下所有的資料夾並排序
    # folders = sorted([f for f in os.listdir('.') if os.path.isdir(f)])
    folders = ["baseline_b1", "attack_a1_10ms", "attack_a1_50ms", "attack_a1_100ms", "attack_a1_200ms", "attack_a2_offset100", "attack_a2_offset500", "attack_a2_offset500_frac25", "attack_a3_rate1", "attack_a3_rate5"]
    found_data = False

    for folder in folders:
        file_path = os.path.join(folder, TARGET_FILE)
        
        if os.path.exists(file_path):
            try:
                df = pd.read_csv(file_path)
                
                if 'ElapsedSeconds' in df.columns and 'BytesTransferred' in df.columns:
                    print(f"正在處理: {folder}")
                    
                    # 轉換單位：Bytes -> MB (10^6)
                    df['Total_MB'] = df['BytesTransferred'] / (2**20)
                    
                    # 繪製總量曲線
                    plt.plot(df['ElapsedSeconds'], df['Total_MB'], 
                             label=folder, linewidth=2, alpha=0.9)
                    found_data = True
                else:
                    print(f"跳過 {folder}: 缺少必要欄位")
            except Exception as e:
                print(f"讀取 {folder} 時出錯: {e}")
    
    if not found_data:
        print("錯誤：找不到任何有效的數據進行繪圖。")
        return

    # 圖表美化
    plt.title('Total Data Transferred Comparison (MB)', fontsize=16, fontweight='bold')
    plt.xlabel('Time (seconds)', fontsize=12)
    plt.ylabel('Total Amount Transferred (MB)', fontsize=12)
    
    plt.xlim(0, 50)
    plt.ylim(0, 500)
    plt.grid(True, linestyle='--', alpha=0.5)
    
    # 將圖例放在右側，避免遮擋曲線
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=10)
    
    plt.tight_layout()
    plt.savefig(OUTPUT_IMAGE, dpi=300)
    print(f"\n✅ 總量對照圖（MB）已生成！\n儲存路徑：{OUTPUT_IMAGE}")

if __name__ == "__main__":
    plot_total_transferred_mb()