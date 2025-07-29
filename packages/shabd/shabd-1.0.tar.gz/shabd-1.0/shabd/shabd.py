import requests
from bs4 import BeautifulSoup
import sys
import sqlite3
import os
import argparse
from pathlib import Path

def get_db_path():
    """Get the path to the database file in the user's home directory."""
    return os.path.join(Path.home(), ".shabd.db")

def init_db():
    """Initialize the database if it doesn't exist."""
    db_path = get_db_path()
    exists = os.path.isfile(db_path)
    
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    if not exists:
        c.execute('''CREATE TABLE dictionary(word TEXT, meaning TEXT)''')
        conn.commit()
    
    return conn, c

def cambridge(word, conn, c):
    """Fetch word meaning from Cambridge Dictionary."""
    headers = {
        "Sec-Ch-Ua-Platform": "Android",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
        "Priority": "u=0, i",
        "Sec-Ch-Ua": "\"Google Chrome\";v=\"137\", \"Chromium\";v=\"137\", \"Not/A)Brand\";v=\"24\"",
        "User-Agent": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Mobile Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Dest": "document",
        "Sec-Ch-Ua-Mobile": "?1"
    }
    
    url = "https://dictionary.cambridge.org/dictionary/english/" + word
    response = requests.get(url, headers=headers)
    remove = ["A1", "A2", "B1", "B2", "C1"]
    soup = BeautifulSoup(response.text, "html.parser")
    
    word_title = soup.find(class_="ti fs fs12 lmb-0 hw superentry").get_text()
    print(f'{word_title}:')
    
    num = 0
    meaning_ = ""
    for item in soup.select(".ddef_h"):
        num += 1
        a = item.get_text().lstrip(" ").rstrip(": ").split()
        a_list = [word for word in a if word not in remove]
        actual = ' '.join(a_list)
        meaning_ = meaning_ + f'{num}. {actual}\n'
    
    print(meaning_)
    c.execute('''INSERT INTO dictionary VALUES(?,?)''', (word, meaning_))
    conn.commit()
    return meaning_

def lookup_word(word):
    """Look up a word in the database or fetch it from Cambridge Dictionary."""
    conn, c = init_db()
    try:
        # Check if word is in database
        c.execute('''SELECT * FROM dictionary WHERE word = ?''', (word,))
        entry = c.fetchone()
        
        if entry:
            print(f"Meaning of {entry[0]} in English: ")
            print(entry[1])
        else:
            cambridge(word, conn, c)
    except Exception as e:
        print("Something went wrong!")
        print("Possibly the word you entered is not in the dictionary or there's a connection issue")
        print(f"Error details: {str(e)}")
    finally:
        conn.close()

def main():
    """Main entry point for the shabd command."""
    parser = argparse.ArgumentParser(
        description="Shabd - A command-line English dictionary tool"
    )
    parser.add_argument(
        "word", 
        nargs="*", 
        help="The word to look up in the dictionary"
    )
    parser.add_argument(
        "-v", "--version",
        action="version",
        version="shabd 1.0"
    )
    
    args = parser.parse_args()
    
    if not args.word:
        parser.print_help()
        sys.exit(1)
    
    word = " ".join(args.word)
    lookup_word(word)

if __name__ == "__main__":
    main()
