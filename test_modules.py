import sys
sys.path.insert(0, '.')

print('Testing db_manager...')
from db_manager import DBManager
db = DBManager()
print('db_manager OK')

print('\nTesting machine_code...')
from machine_code import get_machine_code
mc = get_machine_code()
print(f'Machine code: {mc}')
print('machine_code OK')

print('\nTesting license_manager...')
from license_manager import LicenseManager
lm = LicenseManager()
print('license_manager OK')

print('\nAll modules imported successfully!')
