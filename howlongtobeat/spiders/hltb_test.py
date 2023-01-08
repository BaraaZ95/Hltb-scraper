from email import header
import scrapy
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from scrapy.selector import Selector
import undetected_chromedriver as uc





headers= {
        "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 Mobile Safari/537.36", 
        "referer": "https://howlongtobeat.com/"
        }

class HltbSpider(scrapy.Spider):
    name = 'hltb'
    start_urls = [(f'https://howlongtobeat.com/search_results?page={i}') for i in range(1,2)]
    def start_requests(self):

        for i in list(range(1,3)):                
            url = f'https://howlongtobeat.com/search_results?page={i}'
            payload = "queryString=&t=games&sorthead=popular&sortd=0&plat=&length_type=main&length_min=&length_max=&v=&f=&g=&detail=&randomize=0"
            headers_ = {
                "content-type":"application/x-www-form-urlencoded",
                "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 Mobile Safari/537.36", 
                "referer": "https://howlongtobeat.com/"
            }

            yield scrapy.Request(url=url, method='POST', body=payload, headers=headers_, callback= self.parse_info)

    def parse_info(self, response):
        cards = response.css('div[class="search_list_details"]')

        for card in cards: 
            
            game_name = card.css('a[class=text_white]::attr(title)').get()
            completion_type = card.css('div[class="search_list_tidbit text_white shadow_text"]::text').getall()
            completion_hours = card.css('div[class="search_list_tidbit center time_100"]::text').getall()
            url = card.css('a::attr(href)').get()
            
            game_dict = {"Game_name": game_name, "reviews":[]}

            if completion_type and completion_hours: 
                info = list(zip(completion_type, completion_hours))

            for i,g in info:
                game_dict[i] = g 
            #print(self.game_dict)

            game_url =  "https://howlongtobeat.com/"+url # for scraping game info
            reviews_url = game_url + "&s=reviews" # for scraping reviews
            #game_name = response.css('div[class= "profile_header shadow_text"]::text').get().strip()
            genres = response.xpath('//div/strong[contains(text(), "Genres:")]/following-sibling::text()').getall()
            genres = [i.strip() for i in genres]
            genres = [i for i in genres if i != '']
            stats = response.css('div[class ="global_padding back_form"] div[style= "padding: 5px 0;height: 26px;line-height:16px;vertical-align:middle;"] ::text').getall()
            stats = [i.strip() for i in stats]
            stats= [i for i in stats if i != ''] 

            #game_dict["genres"]= genres
            #game_dict["stats"] = stats
            #yield scrapy.Request(url=self.game_url, headers=headers, callback= self.parse_info)
            #yield game_dict   
            
            
            yield response.follow(reviews_url, self.parse_reviews, headers = headers, cb_kwargs=dict(game_dict = game_dict))

    def parse_reviews(self, response, game_dict ):

        reviews = response.css('div[class ="in back_primary shadow_box"]')

        if reviews != None:
            for review in reviews:
                consoles = review.css('h5 span::text').get()
                ratings = review.css('h5 strong::text').get()
                game_dict["reviews"].append([{"console":consoles}, {"rating":ratings}])
                game_dict["reviews"] = game_dict["reviews"][:2]

        yield game_dict   


process = CrawlerProcess()
process.crawl(HltbSpider)
process.start() # the script will block here until the crawling is finished
