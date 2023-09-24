import asyncio
import logging
import os
import time

import aiohttp
import bs4

OUTPUT_DIR = 'down'
ARTICLES_LIMIT = 30
MAXIMUM_GET_TRIES = 3
TOP_ARTICLES_URL = "https://hacker-news.firebaseio.com/v0/topstories.json"
URL_TEMPLATE = "https://hacker-news.firebaseio.com/v0/item/{}.json"

logging.basicConfig(format='%(asctime)s %(message)s', datefmt='[%H:%M:%S]')
log = logging.getLogger()
log.setLevel(logging.INFO)


def prepare_env():
    if not os.path.exists(OUTPUT_DIR):
        os.mkdir(OUTPUT_DIR)


async def get_url(session: aiohttp.ClientSession, url: str):
    tries = 0
    while tries < MAXIMUM_GET_TRIES:
        try:
            tries += 1
            logging.info(f'[GET]: {url}')
            response = await session.get(url)
            return response
        except (aiohttp.client_exceptions.ClientConnectorError, aiohttp.client_exceptions.ServerDisconnectedError) as ex:
            logging.error(f'{url}: {ex}')
            await asyncio.sleep(3)
    logging.error('Too many tries')
    return None


async def download_page(session: aiohttp.ClientSession, url: str, article_id: int):
    path = f'{OUTPUT_DIR}/{article_id}'
    if not os.path.exists(path):
        os.mkdir(path)
    page = await get_url(session, url)
    if page:
        name = str(len(list(os.scandir(path)))).zfill(3)
        with open(f'{path}/{name}.html', 'wb') as f:
            f.write(await page.read())


async def download_children(session: aiohttp.ClientSession, url: str, article_id: int):
    page = await get_url(session, url)
    page_json = await page.json()
    children = page_json.get('kids', [])
    for child_id in children:
        await download_children(session, URL_TEMPLATE.format(child_id), article_id)
    soup = bs4.BeautifulSoup(page_json.get('text', ''), features="html.parser")
    for link in soup.find_all('a'):
        await download_page(session, link['href'], article_id)


async def download_article(session: aiohttp.ClientSession, article_id: int):
    article_json_url = URL_TEMPLATE.format(article_id)
    article_page = await session.get(article_json_url)
    article = await article_page.json()
    await download_page(session, article['url'], article_id)
    await download_children(session, article_json_url, article_id)


def get_processed_articles() -> list:
    return list(os.scandir(OUTPUT_DIR))


async def get_new_articles(url: str):
    processed_articles = get_processed_articles()
    async with aiohttp.ClientSession() as session:
        articles_page = await session.get(url)
        articles_ids = await articles_page.json()
        tasks = []
        for articles_id in articles_ids[:ARTICLES_LIMIT]:
            if str(articles_id) not in processed_articles:
                tasks.append(download_article(session, articles_id))
        await asyncio.gather(*tasks)


async def parse_site(url):
    while True:
        await get_new_articles(url)
        time.sleep(60)  # there is no use of using async sleep here


if __name__ == '__main__':
    prepare_env()
    asyncio.run(parse_site(TOP_ARTICLES_URL))
