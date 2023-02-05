import scrapy
from urllib.parse import urljoin
import json



class HltbSpider(scrapy.Spider):
    name = 'hltb'
    headers = {
                "content-type":"application/json",
                "user-agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.67 Mobile Safari/537.36", 
                "referer": "https://howlongtobeat.com/"
            }
    
    def start_requests(self):
        for page in range(1, 3049):                
            url = 'https://howlongtobeat.com/api/search'
            payload = f'{{"searchType":"games","searchTerms":[""],"searchPage":{page},"size":20,"searchOptions":{{"games":{{"userId":0,"platform":"","sortCategory":"popular","rangeCategory":"main","rangeTime":{{"min":null,"max":null}},"gameplay":{{"perspective":"","flow":"","genre":""}},"rangeYear":{{"min":"","max":""}},"modifier":""}},"users":{{"sortCategory":"postcount"}},"filter":"","sort":0,"randomizer":0}}}}'
            
            yield scrapy.Request(url=url, method='POST', 
                                 body=payload, headers= self.headers, callback=self.parse_urls)

    def parse_urls(self, response):        
        json_data = json.loads(response.text)
        games = json_data['data']
        for game in games: 
            #if not game['game_name'] in Names:
            game_id = game['game_id']
            game_url =  f'https://howlongtobeat.com/game/{game_id}' # for scraping game info
            #reviews_url = urljoin(game_url,"&s=reviews") # for scraping reviews
            
            yield scrapy.Request(url=game_url, method = 'GET', headers= self.headers, callback=self.parse_info)
            #yield scrapy.Request(url=self.reviews_url, headers= headers, callback=self.parse_reviews)

    async def parse_info(self, response):
        #This parses all the the tables and stats and extracts all the info from them
        Name = response.css('div[class="GameHeader_profile_header__g1fEv shadow_text"]::text').get()
        info_dict = {"Name": Name}
        info_dict['Stats'] = {}
        
        tables =  response.css('table')
        for table in tables:
            columns = table.css('thead>tr>td::text').getall()
            dict_ = {columns[0]:{}}
            rows =  table.css('tbody> tr')
            for row in rows:
                row_name = row.css('::text').get()
                td = row.css('td::text').getall()
                dict_[columns[0]].update({row_name: dict(zip(columns[1:], td[1:]))})
            info_dict['Stats'].update(dict_)
            
        info_list = response.css('div[class="GameHeader_profile_details__QMxb9"] >ul>li::text').getall()
        try: 
            Rating_index = info_list.index('Rating') - 1
            info_dict.update({"Rating": info_list[Rating_index]})
        except: pass
        try:
            Retirement_index= info_list.index('Retirement')- 1
            info_dict.update({"Retirement_Rate": info_list[Retirement_index]})
        except: pass
         
        
        steam_url = response.css('div[class="GameSummary_profile_info__e935c"] >strong> a::attr(href)').get()
        if steam_url:
            steam_app_id = ''.join([i for i in steam_url if i.isdigit()])
            info_dict['steam_app_id'] = steam_app_id
        
        #Access additional data using json response
        game_id = response.url.split('/')[-1]
        json_url = f'https://howlongtobeat.com/_next/data/OHESedIkyECBpw22i81kS/game/{game_id}.json?gameId={game_id}'
        json_payload = f'.json?gameId={game_id}'
        json_headers =   {
            'user-agent':"Mozilla/5.0 (iPad; CPU OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148", 
            'X-Requested-With': 'XMLHttpRequest', 
            'Content-Type': 'application/json'
            }
        req =  scrapy.Request(json_url , method = 'GET', body= json_payload, headers = json_headers, callback= self.parse_additional_info)
        res =  await self.crawler.engine.download(req, self)       
        info_dict.update(self.parse_additional_info(res)) 
        
        yield info_dict      
    
        ##Additional game info##
        #game_name = response.css('div[class= "profile_header shadow_text"]::text').get().strip()
        #retirement = response.css('h5[style ="margin-top: -86px;"]::text').getall()
        #retirement = [i.strip() for i in retirement]
        #genres = response.xpath('//div/strong[contains(text(), "Genres:")]/following-sibling::text()').getall()
        #genres = [i.strip() for i in genres]
        #genres = [i for i in genres if i != '']
        #platforms = response.xpath('//div/strong[contains(text(), "Platforms:")]/following-sibling::text()').getall()
        #platforms = [i.strip() for i in platforms]
        #developer = response.xpath('//div/strong[contains(text(), "Developer:")]/following-sibling::text()').getall()
        #developer = "".join( [i.strip() for i in developer])
        #publisher = response.xpath('//div/strong[contains(text(), "Publisher:")]/following-sibling::text()').getall()
        #publisher = "".join( [i.strip() for i in publisher])
        #stats = response.css('div[class ="global_padding back_form"] div[style= "padding: 5px 0;height: 26px;line-height:16px;vertical-align:middle;"] ::text').getall()
        #stats = [i.strip() for i in stats]
        #stats= [i for i in stats if i != ''] 
        #self.game_dict["genres"]= genres
        #self.game_dict["stats"] = stats

    def parse_additional_info(self, response):
        try:
            json_data = json.loads(response.text)   
        except json.JSONDecodeError:
            return None
        Release_date = json_data['pageProps']['game']['data']['game'][0].get('release_world','')
        Genres = json_data['pageProps']['game']['data']['game'][0].get('profile_genre','')
        Review_score = json_data['pageProps']['game']['data']['game'][0].get('review_score','')
        additional_info = {"Release_date": Release_date, "Genres": Genres, 
                           "Review_score": Review_score}
        return additional_info
        
    def parse_reviews(self, response):
        reviews_dict = {}
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
                reviews_dict["reviews"].append( [{"console":consoles}, {"rating":ratings}, {"text": text} ] )
                #consoles_total.append(consoles)
                #ratings_total.append(ratings)
                #texts_total.append(texts)
            
        #for console, rating, text in list(zip(consoles_total, ratings_total, texts_total)):
        #   temp= {}
        #  temp[console] = {rating: text}
           

#process = CrawlerProcess()
#process.crawl(HltbSpider)
#process.start() # the script will block here until the crawling is finished

