import requests
from bs4 import BeautifulSoup
import re
from flask import Flask, render_template, request

app = Flask(__name__)

# Function to clean text by removing unwanted characters
def clean_text(text):
    cleaned_text = re.sub(r'\(\d+\)', '', text)  # Removes (1), (2), (3), etc.
    cleaned_text = re.sub(r'^\d+\.', '', cleaned_text)  # Removes numbers followed by a period (16.)
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text)  # Remove extra spaces
    return cleaned_text.strip()

# Function to fetch the full document from the case page
def get_full_case_document(case_url, headers):
    response = requests.get(case_url, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        case_title = soup.find('h2', class_='doc_title')
        case_title = clean_text(case_title.text.strip()) if case_title else "No title found"
        article_title = soup.find('h3')
        article_title = clean_text(article_title.text.strip()) if article_title else "No article title found"
        paragraphs = soup.find_all('span', class_='akn-p')
        case_content = "\n".join([clean_text(p.text.strip()) for p in paragraphs])
        return case_title, article_title, case_content
    else:
        print(f"Failed to load case page: {case_url}")
        return None, None, None

# Route to handle the search request and display results
@app.route('/', methods=['GET', 'POST'])
def search_cases_and_scrape_data():
    search_term = None
    results = []

    if request.method == 'POST':
        search_term = request.form['search_term']
        url = f'https://indiankanoon.org/search/?formInput={search_term}'

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            case_titles = soup.find_all('div', class_='result_title')

            if case_titles:
                for title in case_titles:
                    case_title = clean_text(title.find('a').text.strip())
                    case_url = 'https://indiankanoon.org' + title.find('a')['href']
                    full_case_title, article_title, full_case_content = get_full_case_document(case_url, headers)
                    
                    results.append({
                        'case_title': case_title,
                        'case_url': case_url,
                        'full_case_title': full_case_title,
                        'article_title': article_title,
                        'full_case_content': full_case_content
                    })

    return render_template('index.html', search_term=search_term, results=results)

if __name__ == '__main__':
    app.run(debug=True)
