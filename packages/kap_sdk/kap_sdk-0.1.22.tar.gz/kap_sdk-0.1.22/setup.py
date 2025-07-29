from setuptools import setup, find_packages
import tomli

# pyproject.toml dosyasından bağımlılıkları oku
with open("pyproject.toml", "rb") as f:
    pyproject_data = tomli.load(f)
    dependencies = pyproject_data["project"]["dependencies"]

setup(
    name='kap_sdk',
    version='0.1.22',
    description='KAP (Kamuyu Aydınlatma Platformu) üzerinden veri çekmek için bir Python SDK',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Mustafa Kilic',
    author_email='mustafa@example.com',
    url='https://github.com/mustafakilic/kap_sdk',
    packages=find_packages(),
    install_requires=dependencies,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Libraries :: Python Modules',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
    ],
    keywords='kap, public disclosure platform, data scraping, financial data',
    python_requires='>=3.8',
)
