import csv
from datetime import datetime

from playwright.sync_api import sync_playwright
from loguru import logger


class RedditJokesParse:
    def __init__(self):
        self.data = [['Ссылка', 'Заголовок', 'Текст', 'Рейтинг', 'Дата публикации']]

    @staticmethod
    def __handle_request(route, request):
        if request.resource_type == "image":
            route.abort()
        else:
            route.continue_()

    def __parse_jokes(self):
        with sync_playwright() as p:
            browser = p.firefox.launch(headless=True)  # headless=False откроет физический браузер
            context = browser.new_context()
            page = context.new_page()

            # Перехват запросов
            page.route("**/*", self.__handle_request)

            page.goto('https://www.reddit.com/r/Jokes/')

            _prev_height = -1
            _max_scrolls = 100
            _scroll_count = 0
            while _scroll_count < _max_scrolls:
                if _scroll_count % 10 == 0:
                    logger.info(f'Scrolling {_scroll_count} page')
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(1000)
                new_height = page.evaluate("document.body.scrollHeight")
                if new_height == _prev_height:
                    break
                _prev_height = new_height
                _scroll_count += 1
            logger.info('Processing data...')
            jokes = page.query_selector_all('article.w-full.m-0')
            for num, joke in enumerate(jokes):
                if num % 100 == 0:
                    logger.info(f'Processed {len(self.data) - 1} jokes')
                title_data = joke.query_selector('a.absolute.inset-0')
                link = f"https://www.reddit.com{title_data.get_attribute('href')}"
                title = title_data.text_content().strip()
                text = joke.query_selector('//div[@data-post-click-location="text-body"]') \
                    .inner_text()
                rating = joke.query_selector('faceplate-number').inner_text()
                public_date = datetime.fromisoformat(joke.query_selector('time').get_attribute('datetime'))
                public_date = public_date.strftime('%Y-%m-%d %H:%M:%S')
                self.data.append([link, title, text, rating, public_date])

            context.close()
            browser.close()

    def __save_to_csv(self):
        with open('jokes.csv', 'w', newline='', encoding='utf-8') as file:
            writer = csv.writer(file, delimiter='\t')
            writer.writerows(self.data)

    def run(self):
        logger.info('Start parsing...')
        self.__parse_jokes()
        logger.info(f'Saving in scv {len(self.data) - 1} jokes')
        self.__save_to_csv()
        logger.info('Parsing finished')


parser = RedditJokesParse()
parser.run()
