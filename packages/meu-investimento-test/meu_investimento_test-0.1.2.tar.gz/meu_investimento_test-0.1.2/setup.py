from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
   name='meu_investimento_test',
   version='0.1.2',
   packages=find_packages(),
   install_requires=[],
   author='Vinicius S. de Oliveira',
   author_email='vin.s.oliveira@icloud.com',
   description='Uma biblioteca para cálculos de investimentos.',
   url='https://github.com/tadrianonet/meu_investimento',
   classifiers=[
       'Programming Language :: Python :: 3',
       'License :: OSI Approved :: MIT License',
       'Operating System :: OS Independent',
   ],
   python_requires='>=3.6',
   long_description=long_description,
   long_description_content_type='text/markdown'
)
