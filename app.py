# Import des librairies
import csv
import io
from io import StringIO
from flask import Flask, render_template, request, make_response
from bs4 import BeautifulSoup
import requests
import re

app = Flask(
    __name__, template_folder='./templates/')


@app.route("/")
def home():
    return render_template("index.html")


@app.route('/veille', methods=["GET", "POST"])
def index():
    # Envoie une requête POST sur la page, cherche les liens selon un regex
    if request.method == "POST":
        year = request.form.get('year')
        response = requests.get("https://www.vx-underground.org/malware.html")
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            links = re.findall('"((http)s?://samples.*.*?)"', soup.prettify())
            links = [link[0] for link in links]
            # Ajoute /Paper pour tomber sur les PDFs
            links = [link + '/Paper' if link[-1] !=
                     '/' else link + 'Paper' for link in links]
            # Cherche les liens qui concernent l'année choisie par l'utilisateur
            if year:
                year_links = []
                for url in links:
                    match = re.search(r'/APTs/(\d{4})/', url)
                    if match and int(match.group(1)) == int(year):
                        year_links.append(url)
                links = year_links
            rows = []
            # Cherche les fichiers PDFs dans les liens
            for link in links:
                response = requests.get(link)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    pdf_links = soup.find("a", href=re.compile("\.pdf"))
                    if pdf_links:
                        pdf_name = pdf_links.get("href").split("/")[-1]
                        download_link = link + '/' + pdf_name
                        rows.append((pdf_name, download_link))
                    else:
                        rows.append(('No PDF found', ''))
                else:
                    rows.append(('Request failed with status code {}'.format(
                        response.status_code), ''))
            # Création du CSV
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(['PDF Name', 'Download'])
            for row in rows:
                writer.writerow(row)
            output.seek(0)
            response = make_response(output.getvalue())
            response.headers["Content-Disposition"] = "attachment; filename=veille.csv"
            response.headers["Content-type"] = "text/csv"
            return response
        else:
            return "La requête a échoué avec le code d'erreur : " + str(response.status_code)
    else:
        return render_template("veille.html")


if __name__ == '__main__':
    app.run(debug=True)
