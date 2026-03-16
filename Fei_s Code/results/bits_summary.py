import os
import re

# =================配置區=================
BASELINE_NAME = "baseline_b1"
SUMMARY_FILE = "bits_summary.txt"

# 指定要讀取的實驗資料夾（按此順序輸出）
TARGET_EXPERIMENTS = [
    "baseline_b1", 
    "attack_a1_10ms", 
    "attack_a1_50ms", 
    "attack_a1_100ms", 
    "attack_a1_200ms", 
    "attack_a2_offset100", 
    "attack_a2_offset500", 
    "attack_a2_offset500_frac25", 
    "attack_a3_rate1", 
    "attack_a3_rate5"
]
# ========================================

def parse_summary_file(folder_path):
    """解析指定資料夾下的 bits_summary.txt"""
    file_path = os.path.join(folder_path, SUMMARY_FILE)
    if not os.path.exists(file_path):
        return None
        
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # 擷取資訊
            throughput_match = re.search(r"Average Throughput:\s+([\d.]+)\s+Mbps", content)
            duration_match = re.search(r"Duration:\s+([\d.]+)\s+seconds", content)
            
            if throughput_match and duration_match:
                return {
                    'name': folder_path, # 直接使用資料夾名稱
                    'throughput': float(throughput_match.group(1)),
                    'duration': float(duration_match.group(1))
                }
    except Exception as e:
        print(f"讀取 {folder_path} 時出錯: {e}")
    return None

def main():
    data_map = {}
    
    # 只抓取目標清單中的資料
    for exp_dir in TARGET_EXPERIMENTS:
        data = parse_summary_file(exp_dir)
        if data:
            data_map[exp_dir] = data
        else:
            print(f"⚠️ 找不到或無法解析: {exp_dir}/{SUMMARY_FILE}")

    # 取得 Baseline 基準值
    if BASELINE_NAME not in data_map:
        print(f"❌ 錯誤：找不到基準資料夾 '{BASELINE_NAME}'")
        return

    base_tp = data_map[BASELINE_NAME]['throughput']

    print("\n--- LaTeX Table Rows ---")
    for exp_name in TARGET_EXPERIMENTS:
        if exp_name in data_map:
            item = data_map[exp_name]
            # 計算與 baseline 的百分比差異
            percent_diff = ((item['throughput'] - base_tp) / base_tp) * 100
            
            # 替換底線為 LaTeX 可接受的格式 (如需要)
            safe_name = item['name'].replace("_", r"\_")
            
            # 格式：{名稱} & {Average Throughput:.2f} & {Duration:.1f} & {xxx:.2f}%\\
            line = f"{safe_name} & {item['throughput']:.2f} & {item['duration']:.1f} & {percent_diff:+.2f}\\% \\\\"
            print(line)

if __name__ == "__main__":
    main()