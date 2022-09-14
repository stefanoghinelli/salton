# Thematic search engine

## Goals

Project: development of a vertical search engine on a specific topic
of your interest that is based on a corpus of documents from multiple
sources.

Collection: builting from at least 2 separate document sources dealing with the chosen topic. 
The data sources could be websites, collections of pdf documents,  ... 
Each real-world entity in the collection may be represented in more than one source.

Access: users will have the ability to formulate requests based on a defined query language, the results should be presented in a list sorted in descending order of relevance.


## Document collection: web scraping with python
- lxml (https://lxml.de) 

## Preparing the environment

```shell
pip3 install -r requirements.txt

python3
>>import nltk
>>nltk.download('punkt')
>>nltk.download('stopwords')
>>nltk.download('omw-1.4')
>>nltk.download('wordnet')
>>exit()

sh prepare_environment.sh 


```

## Store first

```shell
cd src
python3 scraping.py
python3 preprocessing.py
python3 indexing.py

```

## Query later

```shell
cd src
python3 queryprocessing.py

```

## Do Benchmark

```shell
cd src
python3 queryprocessing.py

```