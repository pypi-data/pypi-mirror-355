from setuptools import setup, find_packages

setup(
    name='TradeSim-Coptee',  # e.g. trading-sim
    version='0.1.0',
    author='Coptee',
    description='Trading simulation using SET50 data with portfolio and order matching features.',
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    packages=find_packages(),
    package_data={
        "TradeSim_package_Coptee": ["Symbol_SET50.csv"],
    },
    install_requires=[
        'pandas',
        'rich',
        'gspread',
        'google-auth',
        'google-api-python-client',
        'google-auth-httplib2',
        'google-auth-oauthlib',
    ],
    license="MIT",
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
        'License :: OSI Approved :: MIT License',
    ],
    python_requires='>=3.9',
)
