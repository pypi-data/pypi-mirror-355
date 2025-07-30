from setuptools import setup, find_packages  

setup(  
    name='zerogpt',  
    version='1.0.0',  
    packages=find_packages(), 
    install_requires=[ 
        'requests',
        'httpx',
        'httpx[http2]',
        'fake_useragent',
        'pandas',
        'requests_toolbelt',
    ],  
    author='Redpiar',  
    author_email='Regeonwix@gmail.com',  
    description='Python client for interacting with the ZeroGPT API and generating images.',  
    long_description=open('README.md').read(),  
    long_description_content_type='text/markdown',
    url='https://github.com/RedPiarOfficial/ZeroGPT',
    classifiers=[  
        'Programming Language :: Python :: 3',  
        'License :: OSI Approved :: MIT License',  
        'Operating System :: OS Independent',  
    ],
    keywords=[
        'ai',
        'zerogpt',
        'arting',
        'text',
        'to',
        'image',
        'free',
        'api',
        'uncensored',
        'gpt',
        'deepseek',
        'chatgpt'
    ],
    python_requires='>=3.8',  
)  