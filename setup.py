from setuptools import setup, find_packages

setup(
    name="Group_Manager",
    version="1.0.0",
    packages=find_packages(),
    python_requires='>=3.7',
    install_requires=[
        'python-telegram-bot==13.7',
        'python-dotenv',
        'psycopg2-binary',
        'google-generativeai',
    ],
) 
