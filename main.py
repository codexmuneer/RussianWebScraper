from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from flask_cors import CORS
import threading
import os


from scrape import web_scrape

app = Flask(__name__)
CORS(app,  origins="*")  # Enable CORS for all routes

@app.route('/')
def home(): 
    return "Hello, this is the home route!"


# this api will scrape only new links data and concatetenate inside old data 
@app.route("/update", methods=["POST"])
def update_data():
    data = request.json
    url = data['url']
    name = data['name']


    thread = threading.Thread(target=web_scrape.for_updating_data, args=(url,name,))
    thread.start()

    msg=f"Web scraping is being processed on url: {url} it will take 5-10 mins (time is depend upon the website size). Please wait..."


    return jsonify(message=msg)



# this api will scrape all the content of the given url and its sub urls
@app.route("/scrape", methods=["POST"])
def scrape_data():
    data = request.json
    url = data['url']
    name = data['name']
    thread = threading.Thread(target=web_scrape.for_new_data, args=(url,name,))
    thread.start()

    msg=f"Web scraping is being processed on url: {url} it will take 5-10 mins (time is depend upon the website size). Please wait..."


    return jsonify(message=msg)



# this api will load the scraped data and return it if data is found
@app.route("/load_data", methods=["POST"])
def load():
    data = request.json
    name = data['name']
    data_path = f'data/{name}_data.json'


    if os.path.exists(data_path):
        # json_data = web_scrape.load_docs_from_jsonl(data_path)
        json_data = [vars(doc) for doc in web_scrape.load_docs_from_jsonl(data_path)]

    
    else:
        json_data = "data is being scraped wait few minutes..."

    # print( json_data[0][0]['page_content'] )
    

    return jsonify(json_data)








if __name__ == '__main__':

    app.run(host='0.0.0.0' , port=5000)