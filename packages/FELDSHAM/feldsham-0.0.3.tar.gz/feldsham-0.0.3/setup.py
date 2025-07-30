from setuptools import setup, find_packages
from pathlib import Path

this_directory = Path(__file__).parent
try:
    long_description = (this_directory / "README.md").read_text(encoding='utf-8')
except Exception as e:
    print(f"Error reading README.md: {e}")
    long_description = "My package description"  # fallback
    
setup(
    name='FELDSHAM',
    version='0.0.3',
    packages=find_packages(),
    install_requires=[
        'sympy>=1.7',
    ],  # Add a comma here
    author='Alexander',
    author_email='lloollfox@mail.ru',
    description='Реализация схемы разделения секрета Фельдмана-Шамира',

    long_description=long_description,
    long_description_content_type='text/markdown',
    license='MIT',
     project_urls={
           'Source Repository': 'https://github.com/A-Sharan1/' #replace with your github source
    }
)
