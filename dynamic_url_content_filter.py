import random
import requests
import re
from log import log
from bs4 import BeautifulSoup
from simple_encoder import decode_word

class DynamicURLFilter:
    def __init__(self):
        self.trust_level_map = {}
        self.unverifyable_URLs = set()
        self.banned_phrases = []
        
        # Loads banned phrases from file
        with open('banned_phrases.txt', 'r') as file:
            lines = file.readlines()
        
        for line in lines:
            if line != '' and line != '\n' and not line.startswith('#'):
                self.banned_phrases.append(line.strip().lower())

        # Loads encoded phrases -> essentially just so you dont need to store a bunch of bad words in plaintext 
        with open('banned_phrases_encoded.txt', 'r') as file:
            lines = file.readlines()
        
        for line in lines:
            if line != '' and line != '\n' and not line.startswith('#'):
                self.banned_phrases.append(decode_word(line.strip()).lower())

    def SetTrustLevel(self, request_url, trust_level):
        self.trust_level_map[request_url] = max(-10, min(10, trust_level))

    def VerifyURLContent(self, request_url):
        try:
            headers = {
                'internal-proxy-request': 'true'
            }
            resp = requests.get(request_url, headers=headers, timeout=5, proxies = {"http": "", "https": "",})
            
            if resp.status_code == 200: 
                soup = BeautifulSoup(resp.text, 'html.parser')
                content = soup.get_text()
                
                for phrase in self.banned_phrases:
                    if re.search(phrase, content, re.IGNORECASE):
                        log(3, f"Phrase {phrase} found in content of {request_url}")
                        return False
                return True    
            else:
                # log(3, f"Failed to get content from {request_url}")
                return None
        
        except Exception as e:
            # log(3, f"No response from {request_url}")
            log(-1, f"[ERR IN VALIDATION REQUEST] - {e}")
            return None

    def FilterURL(self, request_url):

        request_url = self.reform_url(request_url)

        if request_url in self.unverifyable_URLs:
            # log(3, f"Item bypassed (unable to verify) - [{request_url}]")
            return False
        
        if request_url not in self.trust_level_map:
            self.trust_level_map[request_url] = 0

        trust_level = self.trust_level_map[request_url]

        if trust_level < -5:
            log(3, f"Trust level {trust_level}: Failed due to low level - [{request_url}]")
            self.SetTrustLevel(request_url, trust_level - 1)
            return True
        
        if trust_level >= 5:
            log(3, f"Trust level {trust_level}: Bypassed due to high level - [{request_url}]")
            self.SetTrustLevel(request_url, trust_level + 1)
            return True

        if trust_level >= 1 and trust_level <= 4:
            skURL_chance = (0.2 * trust_level)
            if random.random() < skURL_chance:
                log(3, f"Trust level {trust_level}: Bypassed with random check ({skURL_chance})  - [{request_url}]")
                return False

        content_verification = self.VerifyURLContent(request_url)

        if content_verification == None:
            self.unverifyable_URLs.add(request_url)
            # log(3, f"Trust level {trust_level}: Unverifiable content - [{request_url}]")
            return False
        
        elif content_verification:
            log(3, f"Trust level {trust_level}: Passed with content check  - [{request_url}]")
            self.SetTrustLevel(request_url, trust_level + 1)
            return False
        
        else:
            log(3, f"Trust level {trust_level}: Failed with content check  - [{request_url}]")
            self.SetTrustLevel(request_url, trust_level - 1)
            return True
        
    def reform_url(self, url):
        if not url.startswith("http://") and not url.startswith("https://"):
            url = "https://" + url
        
        return url