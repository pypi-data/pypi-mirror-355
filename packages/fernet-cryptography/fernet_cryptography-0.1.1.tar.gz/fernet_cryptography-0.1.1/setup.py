from setuptools import setup, find_packages

setup(
    name='fernet-cryptography',          # уникальное имя вашей библиотеки
    version='0.1.1',
    description='My asyncio-like library',
    author='Ваше имя',
    author_email='email@example.com',
    packages=find_packages(),             # найдёт все пакеты, включая 'S', если есть __init__.py
    include_package_data=True,            # позволяет включить файлы из MANIFEST.in
    python_requires='>=3.6',
)
