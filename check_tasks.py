import sqlite3

conn = sqlite3.connect('fdic_mrm.db')
cursor = conn.cursor()

# Get sample of pending research tasks
cursor.execute('SELECT id, bank_id, task_type, description, priority, created_at FROM research_tasks WHERE status="pending" LIMIT 10')
tasks = cursor.fetchall()

print('Sample of pending research tasks:')
print('=' * 50)
for task in tasks:
    print(f'Task ID: {task[0]}')
    print(f'Bank ID: {task[1]}')
    print(f'Type: {task[2]}')
    print(f'Priority: {task[4]}')
    print(f'Created: {task[5]}')
    print(f'Description: {task[3]}')
    print('-' * 30)

# Get task status summary
cursor.execute('SELECT status, COUNT(*) FROM research_tasks GROUP BY status')
status_counts = cursor.fetchall()
print('\nTask Status Summary:')
for status, count in status_counts:
    print(f'{status}: {count} tasks')

# Check bank information
print('\nBanks in database:')
print('=' * 50)
cursor.execute('SELECT id, bank_name, total_assets, fdic_cert_id, headquarters_city, headquarters_state FROM banks')
banks = cursor.fetchall()
for bank in banks:
    print(f'ID: {bank[0]}')
    print(f'Name: "{bank[1]}"')
    print(f'Assets: {bank[2]}')
    print(f'FDIC ID: {bank[3]}')
    print(f'Location: {bank[4]}, {bank[5]}')
    print('-' * 30)

conn.close()