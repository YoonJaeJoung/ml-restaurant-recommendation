"""
探索NYC餐厅商户元数据集
"""

import json
import os
from collections import defaultdict


def explore_json_data(file_path, num_samples=5):
    """
    探索JSONL数据文件
    
    参数:
        file_path: JSON Lines文件路径
        num_samples: 显示的示例数量
    """
    
    print("=" * 80)
    print("📊 NYC Restaurant Business Metadata Exploration")
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
    price_dist = defaultdict(int)
    has_desc_count = 0
    has_misc_count = 0
    total_records = 0
    categories = defaultdict(int)
    
    print(f"\n⏳ Reading file...")
    with open(file_path, 'r', encoding='utf-8') as f:
        for idx, line in enumerate(f):
            if idx % 50000 == 0 and idx > 0:
                print(f"   Processed {idx:,} records...")
            
            try:
                record = json.loads(line.strip())
                total_records += 1
                
                # 统计字段
                for field in record.keys():
                    field_counts[field] += 1
                
                # 统计评分分布
                if 'avg_rating' in record and record['avg_rating'] is not None:
                    rating_dist[record['avg_rating']] += 1
                
                # 统计价格分布
                if 'price' in record and record['price'] is not None:
                    price_dist[record['price']] += 1
                
                # 统计描述和MISC
                if record.get('description'):
                    has_desc_count += 1
                if record.get('MISC'):
                    has_misc_count += 1
                
                # 统计类别
                if record.get('category'):
                    for cat in record['category']:
                        categories[cat] += 1
                
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
    print(f"\n{'Field Name':<20} {'Count':<15} {'Coverage':<10} {'Description':<40}")
    print("-" * 85)
    
    field_descriptions = {
        'name': 'Business Name',
        'address': 'Business Address',
        'gmap_id': 'Google Maps Business ID',
        'description': 'Business Description',
        'latitude': 'Latitude Coordinate',
        'longitude': 'Longitude Coordinate',
        'category': 'Business Categories',
        'avg_rating': 'Average Rating',
        'num_of_reviews': 'Number of Reviews',
        'price': 'Price Level',
        'hours': 'Operating Hours',
        'MISC': 'Miscellaneous Info',
        'state': 'Current Status',
        'relative_results': 'Related Businesses',
        'url': 'Google Maps URL'
    }
    
    for field, count in sorted(field_counts.items()):
        coverage = (count / total_records) * 100
        description = field_descriptions.get(field, 'Unknown Field')
        print(f"{field:<20} {count:<15,} {coverage:>6.1f}%    {description:<40}")
    
    # 显示评分分布
    print("\n" + "=" * 80)
    print("⭐ Rating Distribution")
    print("=" * 80)
    print(f"\n{'Rating':<10} {'Count':<15} {'Percentage':<10}")
    print("-" * 35)
    for rating in sorted(rating_dist.keys()):
        count = rating_dist[rating]
        percentage = (count / total_records) * 100
        bar = "█" * int(percentage / 3)
        print(f"{rating}★     {count:<15,} {percentage:>6.2f}%  {bar}")
    
    # 显示价格分布
    print("\n" + "=" * 80)
    print("💰 Price Level Distribution")
    print("=" * 80)
    print(f"\n{'Price Level':<15} {'Count':<15} {'Percentage':<10}")
    print("-" * 40)
    for price_level in sorted(price_dist.keys()):
        count = price_dist[price_level]
        percentage = (count / total_records) * 100
        bar = "█" * int(percentage / 2)
        print(f"{price_level:<15} {count:<15,} {percentage:>6.2f}%  {bar}")
    
    # 显示热门类别
    print("\n" + "=" * 80)
    print("📂 Top Categories")
    print("=" * 80)
    print(f"\n{'Category':<40} {'Count':<10}")
    print("-" * 50)
    for category, count in sorted(categories.items(), key=lambda x: x[1], reverse=True)[:15]:
        print(f"{category:<40} {count:<10,}")
    
    # 显示其他统计
    print("\n" + "=" * 80)
    print("📈 Additional Statistics")
    print("=" * 80)
    print(f"\nBusinesses with descriptions:  {has_desc_count:>12,} ({has_desc_count/total_records*100:>5.2f}%)")
    print(f"Businesses with extra info:    {has_misc_count:>12,} ({has_misc_count/total_records*100:>5.2f}%)")
    print(f"Unique categories:             {len(categories):>12,}")
    print(f"Total records:                 {total_records:>12,}")
    
    # 显示示例记录
    print("\n" + "=" * 80)
    print(f"📝 Sample Data (First {num_samples} Records)")
    print("=" * 80)
    
    for i, record in enumerate(samples, 1):
        print(f"\n【Sample {i}】")
        print("-" * 80)
        print(f"Business ID:  {record.get('gmap_id', 'N/A')}")
        print(f"Name:         {record.get('name', 'N/A')}")
        print(f"Address:      {record.get('address', 'N/A')}")
        print(f"Rating:       {record.get('avg_rating', 'N/A')}★ ({record.get('num_of_reviews', 'N/A')} reviews)")
        print(f"Price Level:  {record.get('price', 'N/A')}")
        print(f"Status:       {record.get('state', 'N/A')}")
        
        # 显示类别
        if record.get('category'):
            categories_str = ', '.join(record['category'][:3])
            if len(record['category']) > 3:
                categories_str += f", +{len(record['category']) - 3} more"
            print(f"Categories:   {categories_str}")
        
        # 显示位置
        if record.get('latitude') and record.get('longitude'):
            print(f"Location:     ({record.get('latitude')}, {record.get('longitude')})")
        
        # 显示描述（如果有）
        if record.get('description'):
            desc = record['description']
            if len(desc) > 100:
                print(f"Description:  {desc[:100]}...")
            else:
                print(f"Description:  {desc}")
        
        # 显示营业时间（如果有）
        if record.get('hours'):
            print(f"Hours:        ")
            for day, time in record['hours'][:3]:
                print(f"              {day}: {time}")
            if len(record['hours']) > 3:
                print(f"              ... and {len(record['hours']) - 3} more days")
        
        # 显示杂项信息种类（如果有）
        if record.get('MISC'):
            misc = record['MISC']
            print(f"Extra Info:   {len(misc)} categories of information available")
            for key in list(misc.keys())[:2]:
                print(f"              - {key}")
    
    print("\n" + "=" * 80)


if __name__ == "__main__":
    # 定义文件路径
    file_path = "/Users/yiduolu/Documents/NYC_study/machine_learning/00nyc_Restaurant/data/meta-New_York.json"
    
    # 运行探索
    explore_json_data(file_path, num_samples=5)
