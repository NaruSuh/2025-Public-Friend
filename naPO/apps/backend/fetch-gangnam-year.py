import requests
import json
import os

api_key = os.environ.get('RONE_API_KEY')
base_url = 'https://www.reb.or.kr/r-one/openapi/SttsApiTblData.do'

# Monthly data for past 12 months
months = ['202411', '202410', '202409', '202408', '202407', '202406',
          '202405', '202404', '202403', '202402', '202401', '202312']

print('\n=== 지난 1년 서울 지역별 아파트 매매지수 ===\n')

all_data = []

for month in months:
    params = {
        'KEY': api_key,
        'Type': 'json',
        'STATBL_ID': 'A_2024_00178',
        'DTACYCLE_CD': 'MM',
        'WRTTIME_IDTFR_ID': month,
        'pSize': '1000'
    }

    response = requests.get(base_url, params=params)
    data = response.json()

    if 'SttsApiTblData' in data:
        rows = data['SttsApiTblData'][1]['row']
        for row in rows:
            if '동남권' in row.get('CLS_NM', ''):  # 강남, 서초, 송파, 강동
                all_data.append({
                    'month': row['WRTTIME_DESC'],
                    'region': row['CLS_FULLNM'],
                    'index': float(row['DTA_VAL'])
                })

# Print results grouped by region
regions = {}
for d in all_data:
    region = d['region']
    if region not in regions:
        regions[region] = []
    regions[region].append((d['month'], d['index']))

for region, values in regions.items():
    print(f'\n{region}:')
    print('=' * 60)
    for month, index in sorted(values, reverse=True):
        print(f'{month}: {index:.2f}')

    if len(values) >= 2:
        first_val = values[-1][1]
        last_val = values[0][1]
        change = last_val - first_val
        change_pct = (change / first_val) * 100
        print(f'\n연간 변화: {change:+.2f} ({change_pct:+.2f}%)')
