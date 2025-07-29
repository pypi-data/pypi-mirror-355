from setuptools import setup, find_packages

setup(
    name='textminer-pro-InjinSung',
    version='0.1.1',  # NLTK 의존성 문제 해결
    packages=find_packages(),
    install_requires=[
        'nltk>=3.8.1',
        'scikit-learn>=1.3.2',
        'langdetect>=1.0.9'
    ],
    author='InjinSung',
    author_email='2242716@donga.ac.kr',
    description='Advanced text mining tools for preprocessing, keyword extraction, summarization, and language detection.',
    long_description=open('README.md', encoding='utf-8').read(),
    long_description_content_type='text/markdown',
    url='https://github.com/jagari/textminer-pro',
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Topic :: Text Processing :: Linguistic',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.11',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.7',
    license='MIT',
)