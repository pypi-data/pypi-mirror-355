from setuptools import setup, find_packages

setup(
    name="textminer-pro001",  
    version="0.2.5",
    author="최수한",
    author_email="wagkster@naver.com",
    description="불용어 제거, 키워드 추출, 요약, 언어 감지를 제공하는 텍스트 분석 도구",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/project/Hansupace/textminer-pro",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Topic :: Text Processing :: Linguistic",
    ],
    python_requires='>=3.8',
    install_requires=[
        "nltk>=3.8.1",
        "scikit-learn>=1.3.0",
        "langdetect>=1.0.9",
        "sumy>=0.11.0",
    ]
)
