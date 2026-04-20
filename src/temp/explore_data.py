"""
探索NYC餐厅评论数据集
"""

import json
import os
from datetime import datetime
from collections import defaultdict


def explore_json_data(file_path, num_samples=5):
    """
    探索JSONL数据文件
    
    参数:
        file_path: JSON Lines文件路径
        num_samples: 显示的示例数量
    """
    
    print("=" * 80)
    print("📊 NYC Restaurant Reviews Dataset Exploration")
    print("=" * 80)
    
    # 获取文件信息
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    print(f"\n📁 File Information:")
    print(f"   File Path: {file_path}")
    print(f"   File Size: {file_size_mb:.2f} MB")
    
    # 读取数据并统计
    samples = []
    field_counts = defaultdict(int)
    rating_dist = defaultdict(int)
    has_pics_count = 0
    has_resp_count = 0
    total_records = 0
    
    print(f"\n⏳ Reading file...")
    with open(file_path, 'r', encoding='utf-8') as f:
        for idx, line in enumerate(f):
            if idx % 500000 == 0 and idx > 0:
                print(f"   Processed {idx:,} records...")
            
            try:
                record = json.loads(line.strip())
                total_records += 1
                
                # 统计字段
                for field in record.keys():
                    field_counts[field] += 1
                
                # 统计评分分布
                if 'rating' in record:
                    rating_dist[record['rating']] += 1
                
                # 统计图片和回复
                if record.get('pics'):
                    has_pics_count += 1
                if record.get('resp'):
                    has_resp_count += 1
                
                # 保存示例
                if len(samples) < num_samples:
                    samples.append(record)
                    
            except json.JSONDecodeError as e:
                print(f"   ⚠️  Line {idx+1} JSON parsing error: {str(e)[:50]}")
    
    print(f"   ✅ Read completed! Total {total_records:,} records\n")
    
    # 显示数据字段信息
    print("=" * 80)
    print("📋 Field Information")
    print("=" * 80)
    print(f"\n{'Field Name':<15} {'Count':<15} {'Coverage':<10} {'Description':<40}")
    print("-" * 80)
    
    field_descriptions = {
        'user_id': 'Google User ID',
        'name': 'Reviewer Name',
        'time': 'Timestamp (milliseconds)',
        'rating': 'Rating (1-5 stars)',
        'text': 'Review Text',
        'pics': 'Image URL List',
        'resp': 'Business Response',
        'gmap_id': 'Google Maps Business ID'
    }
    
    for field, count in sorted(field_counts.items()):
        coverage = (count / total_records) * 100
        description = field_descriptions.get(field, 'Unknown Field')
        print(f"{field:<15} {count:<15,} {coverage:>6.1f}%    {description:<40}")
    
    # 显示评分分布
    print("\n" + "=" * 80)
    print("⭐ Rating Distribution")
    print("=" * 80)
    print(f"\n{'Stars':<10} {'Count':<15} {'Percentage':<10}")
    print("-" * 35)
    for rating in sorted(rating_dist.keys()):
        count = rating_dist[rating]
        percentage = (count / total_records) * 100
        bar = "█" * int(percentage / 2)
        print(f"{rating}★     {count:<15,} {percentage:>6.2f}%  {bar}")
    
    # 显示其他统计
    print("\n" + "=" * 80)
    print("📈 Additional Statistics")
    print("=" * 80)
    print(f"\nReviews with images:     {has_pics_count:>12,} ({has_pics_count/total_records*100:>5.2f}%)")
    print(f"Reviews with responses:  {has_resp_count:>12,} ({has_resp_count/total_records*100:>5.2f}%)")
    print(f"Total records:           {total_records:>12,}")
    
    # 显示示例记录
    print("\n" + "=" * 80)
    print(f"📝 Sample Data (First {num_samples} Records)")
    print("=" * 80)
    
    for i, record in enumerate(samples, 1):
        print(f"\n【Sample {i}】")
        print("-" * 80)
        print(f"User ID:     {record.get('user_id', 'N/A')}")
        print(f"Name:        {record.get('name', 'N/A')}")
        print(f"Rating:      {'⭐' * record.get('rating', 0)} ({record.get('rating', 'N/A')} stars)")
        print(f"Business ID: {record.get('gmap_id', 'N/A')}")
        print(f"Posted:      {datetime.fromtimestamp(record.get('time', 0)/1000).strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Has images:  {'Yes' if record.get('pics') else 'No'}")
        if record.get('pics'):
            print(f"             ({len(record.get('pics', []))} images)")
        print(f"Has response: {'Yes' if record.get('resp') else 'No'}")
        
        # 显示评论文本（截断显示）
        text = record.get('text', 'N/A')
        if len(text) > 1000:
            print(f"Review:      {text[:100]}...")
        else:
            print(f"Review:      {text}")
        
        # 显示营业者回复（如果有）
        if record.get('resp'):
            resp = record['resp']
            resp_text = resp.get('text', 'N/A')
            if len(resp_text) > 1000:
                print(f"Response:    {resp_text[:100]}...")
            else:
                print(f"Response:    {resp_text}")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    # 定义文件路径
    file_path = "/Users/yiduolu/Documents/NYC_study/machine_learning/00nyc_Restaurant/data/review-New_York_10.json"
    
    # 运行探索
    explore_json_data(file_path, num_samples=5)
