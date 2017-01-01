from urllib.request import urlopen
from bs4 import BeautifulSoup
import sqlite3 
import json
import re
import time 
import random
import sys

sys.setrecursionlimit(100000) #else we get exception after crawling for too much time

class Crawler:
    def __init__(self, page, timeout=10):
        self.wikipedia = 'https://en.wikipedia.org'
        self.start = time.time()
        self.timeout = timeout
        self.visitedPages = set()
        self.firstPage = page
        
        self.conn = sqlite3.connect('contributers.db')  #init database
        self.cur = self.conn.cursor()
        
    def getAnonEditors(self, page):
        articleName = page[(page.find('/wiki/')+len('/wiki/')):] 
        historyGET = '{0}/w/index.php?title={1}&offset=&limit=250&action=history'.format(self.wikipedia, articleName)
        
        try:
            html = urlopen(historyGET) #go to edit history of the page and search for anon editors' ips
        except Exception as err:
            print(err)
            print(page, historyGET)
            print(self.getStats())
            sys.exit(0)
            
        soup = BeautifulSoup(html, 'html.parser')
        
        anonIPs = set()
        
        for anon in soup.findAll('a', {'class' : re.compile('.*mw-anonuserlink')}):
            ip = anon.attrs['href'].split('/')[-1]
            pattern = re.compile('^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$') #regex for ip address
            if pattern.match(ip):
                anonIPs.add(ip)
                    
        return anonIPs
    
    def getArticleLinks(self, page):
        try:
            html = urlopen(page)
        except Exception as err:
            print(err)
            print(page)
            print(self.getStats())
            sys.exit(0)
            
        soup = BeautifulSoup(html, 'html.parser')
        articles = set()
        
        #search for links to other articles that look like /wiki/<article_name>
        for link in soup.find('div', id='bodyContent').findAll('a', href=re.compile("^(/wiki/)((?!:).)*$")):
            if link.attrs['href'] not in page:
                if link.attrs['href'] not in self.visitedPages:
                    articles.add(link.attrs['href'])
                
        return articles
    
    def getCountryByIp(self, ip):
        GET = "http://freegeoip.net/json/"+ip #I use freegeoip.net to get country by ip address
        
        try:
            response = urlopen(GET).read().decode('utf-8') #get json response
        except Exception as err:
            print(err)
            print(GET)
            print(self.getStats())
            sys.exit(0)
            
        jsonResponse = json.loads(response) 
        
        return jsonResponse['country_name']
    
    def updateDB(self, country):
        #create new column if country not in database or increment count column if country in database
        self.cur.execute("SELECT count FROM countries WHERE country = '{0}';".format(country)) 
        count = self.cur.fetchall()
        
        if count:
            self.cur.execute("UPDATE countries SET count = {0} WHERE country = '{1}';".format(count[0][0]+1, country))
            self.conn.commit()
        else:
            self.cur.execute("INSERT INTO countries (country, count) VALUES ('{0}', {1});".format(country, 1))
            self.conn.commit()
            
    def getResult(self):
        self.cur.execute("SELECT * FROM countries ORDER BY count DESC;") #return results in descending order 
        res = self.cur.fetchall()
        self.cur.close()  #close database
        self.conn.close() #
        return res
                
    def crawl(self, startingPage):
        print('Starting to crawl:', startingPage)
        ips = self.getAnonEditors(startingPage)
        
        for ip in ips:
            country = self.getCountryByIp(ip)
            self.updateDB(country)
                
        if time.time() - self.start >= self.timeout: #timeout check
            print('Time expired.')
            return
        
        if not self.visitedPages: #add the very first page to visitedPages
            self.visitedPages.add(startingPage[startingPage.find('/wiki/'):])
        
        articles = self.getArticleLinks(startingPage)
        
        if len(articles) == 0:
            self.crawl(self.firstPage)
        
        choice = random.choice(tuple(articles)) #choose random article and crawl it 
        self.visitedPages.add(choice)
        page = self.wikipedia + choice
        
        self.crawl(page)
        
  
if __name__ == '__main__':
    page = 'https://en.wikipedia.org/wiki/Wikipedia' #Specify starting article
    crawler = Crawler(page, 100) #Specify time to crawl
    crawler.crawl(page)
    
    for pair in crawler.getResult():
        print(pair[0], ':', pair[1])
    
    
    
        
    
    
