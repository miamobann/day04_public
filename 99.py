# day04/99.py
while True:
    for i in range(2, 10):
        print(f"--- {i}단 ---")
        for j in range(1, 10):
            print(f"{i} x {j} = {i * j}")
        print()
    
    cont = input("계속하시겠습니까? (y/n): ")
    if cont.lower() != 'y':
        break
