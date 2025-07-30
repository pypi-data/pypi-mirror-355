from setuptools import setup, find_packages

setup(
    name='pureconnection',               # Nama paket
    version='1.0.0',                 # Versi paket
    packages=find_packages(),        # Temukan semua paket Python dalam direktori
    test_suite='tests',              # Menentukan lokasi test
    author='Muhammad Thoyfur',
    author_email='ipungg.id@gmail.com',
    install_requires=[  # Daftar dependensi yang diperlukan
    ],
    description='Lightweight realtime database',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/ipungg-junior/pureconnection',  # URL proyek (misalnya GitHub)
    python_requires='>=3.9',          # Versi Python yang didukung
)
