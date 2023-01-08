
from asyncio.log import logger
from platform import platform
from urllib.parse import urlencode
from wsgiref import headers
import scrapy
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from scrapy.selector import Selector
import undetected_chromedriver as uc
from scrapy.crawler import CrawlerProcess




headers= {
                "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 Mobile Safari/537.36", 
                "referer": "https://howlongtobeat.com/"
            }

class HltbSpider(scrapy.Spider):
    name = 'hltb'
    def start_requests(self):

        for i in list(range(1,2)):                
            url = f'https://howlongtobeat.com/search_results?page={i}'
            payload = "queryString=&t=games&sorthead=popular&sortd=0&plat=&length_type=main&length_min=&length_max=&v=&f=&g=&detail=&randomize=0"
            headers_ = {
                "content-type":"application/x-www-form-urlencoded",
                "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 Mobile Safari/537.36", 
                "referer": "https://howlongtobeat.com/"
            }
        yield scrapy.Request(url=url, method='POST', body=payload, headers=headers_, callback=self.parse)

    def parse(self, response):
        cards = response.css('div[class="search_list_details"]')

        for card in cards: 
            game_name = card.css('a[class=text_white]::attr(title)').get()
            completion_type = card.css('div[class="search_list_tidbit text_white shadow_text"]::text').getall()
            completion_hours = card.css('div[class="search_list_tidbit center time_100"]::text').getall()
            url = response.css('a::attr(href)').get()
            
            self.game_dict = {"Game_name": game_name, "reviews":[]}

            if completion_type and completion_hours: 
                info = list(zip(completion_type, completion_hours))

            for i,g in info:
                self.game_dict[i] = g 
            #print(self.game_dict)

            self.game_url =  "https://howlongtobeat.com/"+url # for scraping game info
            self.reviews_url = self.game_url + "&s=reviews" # for scraping reviews
        
            yield scrapy.Request(url=self.game_url, headers=headers, callback=self.parse_info)
            yield scrapy.Request(url=self.reviews_url, headers= headers, callback=self.parse_reviews)

    def parse_info(self, response):
        #game_name = response.css('div[class= "profile_header shadow_text"]::text').get().strip()
        retirement = response.css('h5[style ="margin-top: -86px;"]::text').getall()
        retirement = [i.strip() for i in retirement]
        genres = response.xpath('//div/strong[contains(text(), "Genres:")]/following-sibling::text()').getall()
        genres = [i.strip() for i in genres]
        genres = [i for i in genres if i != '']
        platforms = response.xpath('//div/strong[contains(text(), "Platforms:")]/following-sibling::text()').getall()
        platforms = [i.strip() for i in platforms]
        developer = response.xpath('//div/strong[contains(text(), "Developer:")]/following-sibling::text()').getall()
        developer = "".join( [i.strip() for i in developer])
        publisher = response.xpath('//div/strong[contains(text(), "Publisher:")]/following-sibling::text()').getall()
        publisher = "".join( [i.strip() for i in publisher])
        stats = response.css('div[class ="global_padding back_form"] div[style= "padding: 5px 0;height: 26px;line-height:16px;vertical-align:middle;"] ::text').getall()
        stats = [i.strip() for i in stats]
        stats= [i for i in stats if i != ''] 

        self.game_dict["genres"]= genres
        self.game_dict["stats"] = stats

    def parse_reviews(self, response ):
        reviews = response.css('div[class ="in back_primary shadow_box"] ')

        
        consoles_total = []
        ratings_total = []
        texts_total = []
        if reviews != None:
            for review in reviews:
                consoles = review.css('h5 span::text').get()
                ratings = review.css('h5 strong::text').get()
                texts = review.css('div::text').getall()
                texts = [i.strip() for i in texts]
                texts = [i for i in texts if i != '']
                text = "".join(texts)
                self.game_dict["reviews"].append( [{"console":consoles}, {"rating":ratings}, {"text": text} ] )
                #consoles_total.append(consoles)
                #ratings_total.append(ratings)
                #texts_total.append(texts)
            
        #for console, rating, text in list(zip(consoles_total, ratings_total, texts_total)):
        #   temp= {}
        #  temp[console] = {rating: text}
        yield self.game_dict   

process = CrawlerProcess()

process.crawl(HltbSpider)
process.start() # the script will block here until the crawling is finished

