from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
import requests
from requests.exceptions import RequestException
from typing import List
from dataclasses import dataclass
import csv
import argparse

"""Ce script permet d'extraire l'ensemble des données utilisées pour le projet.
Les données ont été extraites du site "audio-lingua.versailles.fr de l'académie
de Versailles regroupant des milliers d'enregistrements audios pouvant être utilisés 
pour l'apprentissage de langues.""" 


@dataclass
class Audio:
    audio_language: str
    author: str
    title: str
    description: str
    date: str
    level: str
    gender: str
    age: str
    duration: str
    themes: List[str]
    file_name: str

@dataclass
class Language:
    audios: List[Audio]


base_url = "https://audio-lingua.ac-versailles.fr/"


def get_base_page(base_url):
    homepage = requests.get(base_url)
    home_data = BeautifulSoup(homepage.content, 'lxml')
    return home_data


def choose_language(home_page, base_url):
    language_adresses = []

    div_container = home_page.find_all("div", class_="fr-col-12 fr-col-sm-6 fr-col-lg-2")
    for child in div_container:
        if child:
            a_elem = child.find("a")
            link = a_elem.get("href")
            language_adress = base_url + link
            language_adresses.append(language_adress)

    return language_adresses


def get_accordion(driver):
   
    accordion_buttons = driver.find_elements(By.CSS_SELECTOR, ".fr-accordion__btn")

    for button in accordion_buttons:
        driver.execute_script("arguments[0].scrollIntoView(true);", button)
        time.sleep(0.5)
        try:
            button.click()
        except:
            driver.execute_script("arguments[0].click();", button)
        time.sleep(1)

    return driver.page_source


def get_language_page(language_page):
    language_page_data = BeautifulSoup(language_page, "html.parser")
    return language_page_data


def extract_infos(language_page_data, args):

    page_audios = []

    language = language_page_data.find("h1")
    language = language.text

    audios_sections = language_page_data.find_all("div", class_="fr-alert fr-alert--info mp3")
    for section in audios_sections:
        header = section.find("h3", class_ = "fr-alert__title")
        title = ''.join([str(content).strip() for content in header.contents if isinstance(content, str)])
        header_date_author = section.find("p", class_ = "fr-text--sm")
        for span in header_date_author.find_all("span"):
            if len(span["class"]) == 2:
                if "fr-icon-calendar-event-fill" in span["class"]:
                    date = (span.text).strip()
                elif "fr-icon-account-circle-fill" in span["class"]:
                    author = (span.text).strip()
            
        themes = []
        level, gender, age, duration = None, None, None, None
        tags = section.find("div", class_ = "fr-pt-2w")
        for tag in tags.find_all("a"):
            i = tag.find("i")
            class_i = i.get("class")
            if "icon-tag2" in class_i:
                level = (tag.text).strip()
            elif "icon-tag3" in class_i:
                gender = (tag.text).strip()
            elif "icon-tag4" in class_i:
                age = (tag.text).strip()
            elif "icon-tag5" in class_i:
                duration = (tag.text).strip()
            elif "icon-tag" in class_i:
                themes.append((tag.text).strip())

        quote = section.find("figure", class_ = "fr-quote")
        if quote:
            blockquote = quote.find("blockquote")
            if blockquote:
                description = (blockquote.text).strip()
        else:
            description = ""

        accordion = section.find("section")
        if accordion and level:
            download_section = accordion.find("p", class_ = "fr-text--sm fr-mt-2w")
            download_section = (download_section.text).split(":")
            download_link = download_section[1].strip() + ":" + download_section[2].strip()
            if " " in language:
               language = "_".join(language.split())
            if "/" in title:
                title = title.replace("/", "_")
            file_name = language + "_" + level + "_" + "_".join(title.split())   
            if not download_audio(download_link, file_name, args):
                continue
        else:
            continue

        # print("Pour cet audio : ")
        # print(title)
        # print(date)
        # print(author)
        # print(level, gender, age, duration, themes)
        # print(description)
        # print(download_link)
        # print(file_name)

        audio = Audio(audio_language=language, author=author, title=title, description=description, date=date, 
                      level=level, gender=gender, age=age, duration=duration, themes=themes, file_name=file_name)
        
        page_audios.append(audio)

    return page_audios
    

def download_audio(download_link, file_name, language):

    max_retries = 5 
    retry_delay = 5  

    for attempt in range(max_retries):
        try:
            file_response = requests.get(download_link, timeout=10)  
            file_response.raise_for_status()  
            
            with open(f"../data/audios/{language}/{file_name}.mp3", "wb") as file:
                file.write(file_response.content)
            
            return True

        except RequestException as e:
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
            else:
                return False

def get_next_page_source(driver):

    try:
        next_button = driver.find_element(By.CSS_SELECTOR, "a[aria-label='Aller à la page suivante']")

        if not next_button.get_attribute("href"):
            return None
        
        driver.execute_script("arguments[0].scrollIntoView(true);", next_button)
        time.sleep(0.5)
        next_button.click()
        time.sleep(2)
        return driver.page_source
    except:
        return None

def build_csv(all_data, language):

    with open(f"../data/tables/{language}.csv", "w") as file:
        structure = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        structure.writerow(["Language", "FileName", "Author", "Title", "Description", "Date", "Level", "Gender", "Age", "Duration", "Themes"])
        for language in all_data:
            for audio in language.audios:
                structure.writerow([audio.audio_language, audio.file_name, audio.author, audio.title, audio.description, audio.date, audio.level, audio.gender, audio.age, audio.duration, audio.themes])
                print(f"{audio.audio_language}\t{audio.file_name}\t{audio.author}\t{audio.title}\t{audio.description}\t{audio.date}\t{audio.level}\t{audio.gender}\t{audio.age}\t{audio.duration}\t{audio.themes}")

def main():

    languages = ["Fr", "En", "De", "Es", "It", "Ru", "Po", "Ch", "Oc", "Ar", "Ca", "Co", "Cr", "He"]
    parser = argparse.ArgumentParser(description='Scrap la langue désirée.')
    parser.add_argument("-L", "--Langue", required=True, choices=languages, 
                        help= """Fr = Français, En = Anglais, De = Allemand, Es = Espagnol, It = Italien, Ru = Russe, Po = Portugais, Ch = Chinois,
                        Oc = Occitan, Ar = Arabe, Ca = Catalan, Co = Corse, Cr = Créole, He = Hébreu.""")
    args = parser.parse_args()

    all_data = []

    homepage = get_base_page(base_url)
    language_adresses = choose_language(homepage, base_url)
    driver = webdriver.Chrome()

    
    languages_index = {language : indx for indx, language in enumerate(languages)}

    for language_adress in language_adresses[languages_index[args.Langue]:languages_index[args.Langue] + 1]:
        page = 1
        print(f"Processing Language : {args.Langue}...")
        print(f"Processing page {page}...")
        language = Language(audios=[])

        driver.get(language_adress)
        time.sleep(2)  
        language_page = get_accordion(driver)
        language_page_data = get_language_page(language_page)

        audios = extract_infos(language_page_data, args.Langue)
        language.audios.extend(audios)

        while True:
            next_page_source = get_next_page_source(driver)
            if not next_page_source:
                break
            page += 1
            print(f"Processing page {page}...")
            next_language_page = get_accordion(driver)
            next_language_page_data = get_language_page(next_language_page)
            language_page_data = next_language_page_data 
            audios = extract_infos(language_page_data, args.Langue)
            language.audios.extend(audios)

        all_data.append(language)

    driver.quit()

    build_csv(all_data, args.Langue)

if __name__ == "__main__":
    main()
