import sqlite3

conn = sqlite3.connect('fdic_mrm.db')
cursor = conn.cursor()

cursor.execute('SELECT COUNT(*) FROM banks')
total_banks = cursor.fetchone()[0]
print(f'Total banks: {total_banks}')

cursor.execute('SELECT id, bank_name, total_assets FROM banks ORDER BY id')
banks = cursor.fetchall()
print('All banks:')
for bank in banks:
    print(f'ID: {bank[0]}, Name: "{bank[1]}", Assets: {bank[2]}')

conn.close()