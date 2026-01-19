
titles = [
    "ON의 EV 및 자동화 피벗에 대한 애널리스트의 새로운 지원으로 ON의 상승세가 바뀔까요? - simplywall.st",
    "Trump Surprised by China’s Electric Vehicle Advancements - filmogaz.com",
    "트럼프, 중국 자동차 브랜드 미국 진출 조건 제시 - SpeedMe.ru"
]

print("=== Character Analysis ===")
for t in titles:
    print(f"\nTitle: {t}")
    # Find the dash
    for char in t:
        if not char.isalnum() and char not in [' ', '.', '’', '?', ',']:
             print(f"Special char: '{char}' (ord: {ord(char)})")

print("\n=== Algorithm Test ===")
BLOCK_LIST = {'simplywall.st', 'filmogaz', 'speedme'}

for t in titles:
    source_name = "UNKNOWN"
    if ' - ' in t:
        source_name = t.rsplit(' - ', 1)[-1].strip().lower()
    
    source_Check = source_name.replace(' ', '')
    
    blocked = False
    for spam in BLOCK_LIST:
        if spam in source_Check:
            blocked = True
            break
            
    print(f"Title: {t[:30]}... | Source: '{source_name}' | Blocked: {blocked}")
