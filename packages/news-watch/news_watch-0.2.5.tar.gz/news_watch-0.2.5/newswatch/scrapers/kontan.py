import logging
import re
from urllib.parse import urlencode

from bs4 import BeautifulSoup, Comment

from .basescraper import BaseScraper


class KontanScraper(BaseScraper):
    def __init__(self, keywords, concurrency=12, start_date=None, queue_=None):
        super().__init__(keywords, concurrency, queue_)
        self.base_url = "https://www.kontan.co.id"
        self.start_date = start_date
        self.continue_scraping = True
        self.href_pattern = re.compile(r".*\.kontan\.co\.id/news/.*")

    async def build_search_url(self, keyword, page):
        # https://www.kontan.co.id/search/?search=&per_page=20
        query_params = {
            "search": keyword,
            "per_page": (page - 1) * 20,
        }
        url = f"{self.base_url}/search?{urlencode(query_params)}"
        return await self.fetch(url)

    def parse_article_links(self, response_text):
        soup = BeautifulSoup(response_text, "html.parser")
        articles = soup.select(".list-berita ul li a")
        if not articles:
            return None

        filtered_hrefs = {
            f"http:{a.get('href')}"
            for a in articles
            if a.get("href")
            and self.href_pattern.match(a.get("href"))
            and "insight.kontan.co.id"  # FIX ME: dev pattern for insight.kontan.co.id
            not in a.get("href")
        }
        return filtered_hrefs

    async def get_article(self, link, keyword):
        response_text = await self.fetch(link)
        if not response_text:
            logging.warning(f"No response for {link}")
            return
        soup = BeautifulSoup(response_text, "html.parser")
        try:
            # FIX ME: change to select_one
            category = soup.find("div", {"class": "breadcumb fs18"}).get_text(
                strip=True
            )
            title = soup.find("h1", {"class": "detail-desk"}).get_text(strip=True)
            publish_date_str = soup.find(
                "div", {"class": "fs14 ff-opensans font-gray"}
            ).get_text(strip=True)

            content_div = soup.find(
                "div", {"class": "tmpt-desk-kon", "itemprop": "articleBody"}
            )

            author = content_div.find("p").get_text(strip=True)
            content_div.find("p").extract()

            # loop through paragraphs and remove those with class patterns like "track-*"
            for tag in content_div.find_all(["p", "h2"]):
                a_tag = tag.find("a", class_=True)
                if a_tag and any(
                    cls.startswith("track-") for cls in a_tag.get("class", [])
                ):
                    tag.extract()

            # filter before the comment <!-- pagination end -->
            filtered_content = []
            for element in content_div.children:
                if isinstance(element, Comment) and "pagination end" in element:
                    break
                # append text of all elements except pagination end comments
                if not isinstance(element, Comment):
                    filtered_content.append(str(element))

            # join the accumulated elements and parse again to get cleaned text
            content_part = BeautifulSoup("".join(filtered_content), "html.parser")
            content = content_part.get_text(separator="\n", strip=True)

            publish_date = self.parse_date(publish_date_str)
            if not publish_date:
                logging.error(f"Error parsing date for article {link}")
                return
            if self.start_date and publish_date < self.start_date:
                self.continue_scraping = False
                return

            item = {
                "title": title,
                "publish_date": publish_date,
                "author": author,
                "content": content,
                "keyword": keyword,
                "category": category,
                "source": self.base_url.split("www.")[1],
                "link": link,
            }
            await self.queue_.put(item)
        except Exception as e:
            logging.error(f"Error parsing article {link}: {e}")
