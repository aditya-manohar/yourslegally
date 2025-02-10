# import requests
# from bs4 import BeautifulSoup
# import re
# from flask import Flask, render_template, request
# from flask_cors import CORS
# import numpy as np
# from sentence_transformers import SentenceTransformer
# from scipy.spatial.distance import cosine

# app = Flask(__name__)
# CORS(app)
# model = SentenceTransformer('paraphrase-MiniLM-L6-v2')

# def clean_text(text):
#     cleaned_text = re.sub(r'\(\d+\)', '', text)  # Removes (1), (2), (3), etc.
#     cleaned_text = re.sub(r'^\d+\.', '', cleaned_text)  # Removes numbers followed by a period (16.)
#     cleaned_text = re.sub(r'\s+', ' ', cleaned_text)  # Remove extra spaces
#     return cleaned_text.strip()

# def get_full_case_document(case_url):
#     headers = {
#         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
#     }
#     response = requests.get(case_url, headers=headers)

#     if response.status_code == 200:
#         soup = BeautifulSoup(response.text, 'html.parser')
        
#         # Extracting case title
#         case_title = soup.find('h2', class_='doc_title')
#         case_title = clean_text(case_title.text.strip()) if case_title else "No title found"

#         # Extracting article title (if available)
#         article_title = soup.find('h3')
#         article_title = clean_text(article_title.text.strip()) if article_title else "No article title found"

#         # Extracting case content (paragraphs)
#         paragraphs = soup.find_all('span', class_='akn-p')
#         case_content = "\n".join([clean_text(p.text.strip()) for p in paragraphs]) if paragraphs else "No case content found."

#         # Encoding the case content into a vector (embedding)
#         case_embedding = model.encode(case_content) if case_content != "No case content found." else None
        
#         return case_title, article_title, case_content, case_embedding
#     else:
#         print(f"Failed to load case page: {case_url}")
#         return None, None, None, None


# def find_similar_cases(query_embedding, case_results, threshold=0.5):
#     similar_cases = []
#     for case in case_results:
#         if case['embedding'] is not None:
#             similarity = 1 - cosine(query_embedding, case['embedding'])
#             if similarity > threshold:
#                 case['similarity'] = similarity
#                 similar_cases.append(case)
#     similar_cases.sort(key=lambda x: x['similarity'], reverse=True)
#     return similar_cases

# @app.route('/', methods=['GET', 'POST'])
# def search_cases_and_scrape_data():
#     search_term = None
#     results = []
#     similar_cases = []

#     if request.method == 'POST':
#         search_term = request.form['search_term']
#         query_embedding = model.encode(search_term)
#         url = f'https://indiankanoon.org/search/?formInput={search_term}'
        
#         headers = {
#             'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
#         }
#         response = requests.get(url, headers=headers)

#         if response.status_code == 200:
#             soup = BeautifulSoup(response.text, 'html.parser')
            
#             # Find all the case result titles
#             case_titles = soup.find_all('div', class_='result_title')

#             if case_titles:
#                 for title in case_titles:
#                     case_title = clean_text(title.find('a').text.strip())
#                     case_url = 'https://indiankanoon.org' + title.find('a')['href']
                    
#                     # Scrape full case document
#                     full_case_title, article_title, full_case_content, case_embedding = get_full_case_document(case_url)

#                     results.append({
#                         'case_title': case_title,
#                         'case_url': case_url,
#                         'full_case_title': full_case_title,
#                         'article_title': article_title,
#                         'full_case_content': full_case_content,
#                         'embedding': case_embedding
#                     })
                
#                 # Find similar cases based on the query embedding
#                 similar_cases = find_similar_cases(query_embedding, results)

#     return render_template('index.html', search_term=search_term, results=results, similar_cases=similar_cases)


# if __name__ == '__main__':
#     app.run(debug=True)
import json
from flask import Flask, request, render_template
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

app = Flask(__name__)

# Load the dataset from your JSON file
def load_data():
    with open('yourslegally_data(1).json', 'r', encoding='utf-8') as file:
        return json.load(file)

def preprocess_cases(cases):
    case_contents = [case['full_case_content'] if case['full_case_content'] is not None else "" for case in cases]
    
    vectorizer = TfidfVectorizer(stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(case_contents)
    return tfidf_matrix, vectorizer

def get_similar_cases(user_input, tfidf_matrix, vectorizer, cases):
    user_input_vector = vectorizer.transform([user_input])
    similarities = cosine_similarity(user_input_vector, tfidf_matrix).flatten()
    top_indices = similarities.argsort()[-10:][::-1]  
    similar_cases = []
    
    for index in top_indices:
        case = cases[index]
        similar_cases.append({
            "case_title": case["case_title"],
            "case_url": case["case_url"],
            "article_title":case["article_title"],
            "similarity": similarities[index],
            "full_case_content": case["full_case_content"]
        })
    
    return similar_cases

# Main route to handle user input and return similar cases
@app.route("/", methods=["GET", "POST"])
def search_cases():
    similar_cases = []
    search_term = ""
    
    # Load dataset only when needed
    cases = load_data()
    
    if request.method == "POST":
        search_term = request.form["search_term"]
        tfidf_matrix, vectorizer = preprocess_cases(cases)
        similar_cases = get_similar_cases(search_term, tfidf_matrix, vectorizer, cases)
    
    return render_template("index.html", search_term=search_term, similar_cases=similar_cases)

if __name__ == "__main__":
    app.run(debug=True)

