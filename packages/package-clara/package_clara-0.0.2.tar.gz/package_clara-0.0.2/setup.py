from setuptools import setup, find_packages

    
with open("README.md", "r") as f:
    long_description = f.read()

        
with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
name = "package_clara",
version = "0.0.2",
author= "Anna_Clara",
author_email= "claramoitinho67@gmail.com",
description= "Estou iniciando esse desafio com muito foco e atenção em relação ao desafio de processamento de imagens",
long_description ="processamento_de_dados_com_imagens" ,
long_description_content_type = 'text/markdown',
packages=find_packages(),
install_requires = requirements,
python_requires ='>=3.8',

)


