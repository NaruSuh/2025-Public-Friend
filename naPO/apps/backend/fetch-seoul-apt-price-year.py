import requests
import json
import os
from collections import defaultdict

api_key = os.environ.get('RONE_API_KEY')
base_url = 'https://www.reb.or.kr/r-one/openapi/SttsApiTblData.do'

# Monthly data for past 13 months
months = ['202411', '202410', '202409', '202408', '202407', '202406',
          '202405', '202404', '202403', '202402', '202401', '202312', '202311']

print('\n=== 지난 1년 서울 권역별 아파트 매매 중위가격 ===\n')

all_data = []

for month in months:
    params = {
        'KEY': api_key,
        'Type': 'json',
        'STATBL_ID': 'A_2024_00189',  # (월) 지역별 매매 중위가격_아파트
        'DTACYCLE_CD': 'MM',
        'WRTTIME_IDTFR_ID': month,
        'pSize': '1000'
    }

    response = requests.get(base_url, params=params)
    data = response.json()

    if 'SttsApiTblData' in data:
        rows = data['SttsApiTblData'][1]['row']
        for row in rows:
            # Filter for Seoul regions (서울 in CLS_FULLNM)
            if '서울' in row.get('CLS_FULLNM', ''):
                all_data.append({
                    'month': row['WRTTIME_DESC'],
                    'month_id': month,
                    'region': row['CLS_FULLNM'],
                    'price_per_sqm': float(row['DTA_VAL']),
                    'unit': row['UI_NM']
                })

# Group by region
regions = defaultdict(list)
for d in all_data:
    regions[d['region']].append((d['month_id'], d['month'], d['price_per_sqm']))

# Print results
for region, values in sorted(regions.items()):
    print(f'\n{region}:')
    print('=' * 80)

    # Sort by month ID (newest first)
    values_sorted = sorted(values, key=lambda x: x[0], reverse=True)

    for month_id, month, price in values_sorted:
        # Convert to price per pyeong (1 pyeong = 3.3058 sqm)
        price_per_pyeong = price * 3.3058
        print(f'{month}: {price:>8.2f} 만원/㎡ = {price_per_pyeong:>9.2f} 만원/평')

    if len(values_sorted) >= 2:
        oldest_price = values_sorted[-1][2]
        newest_price = values_sorted[0][2]
        change = newest_price - oldest_price
        change_pct = (change / oldest_price) * 100
        print(f'\n연간 변화: {change:+.2f} 만원/㎡ ({change_pct:+.2f}%)')
