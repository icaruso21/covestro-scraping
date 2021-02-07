# covestro-scraping
A python script to scrape product information and corresponding datasheet pdfs from Covestro

## Installation + Execution
Navigate to this repository and proceed as follows (make sure pip, python3>=3.9, and Google Chrome are installed first):
- Create virtual environment: `python3 -m venv env`
- Activate virtual environment: `source env/bin/activate`
- Install required dependencies: `pip install -r ./requirements.txt`
- Run script: `python ./src/covestro_scraper.py -s -v -d`
	- Optional flags:
		- -s: Scrape Covestro for products
		- -v: Print full information about each product
		- -d: Download pdfs from most recent json

