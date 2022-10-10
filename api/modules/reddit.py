from datetime import datetime, timezone
from os import getenv
from urllib.parse import urljoin
from httpx import AsyncClient

from lxml import etree, html

from api import logger


class Reddit:
    def __init__(
        self,
        base_url: str = "https://libreddit.spike.codes",
        image_cache_url: str = "https://images.weserv.nl",
    ) -> None:
        self.base_url = getenv("REDDIT_URL", base_url)
        self.image_cache_url = urljoin(
            getenv("IMAGE_CACHE_URL", image_cache_url),
            "/?default=https://http.cat/404&url=",
        )
        self.thumbnail_cache_url = urljoin(
            getenv("IMAGE_CACHE_URL", image_cache_url),
            "/?default=https://http.cat/404&w=500&h=500&output=png&url=",
        )
        self.parser = html.HTMLParser(encoding="ISO-8859-1")

        self.client = AsyncClient(
            base_url=self.base_url,
            http2=True,
            timeout=30,
            follow_redirects=True,
            max_redirects=10,
            headers={
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36"
            },        )
        self.cookies = {
            "comment_short": getenv("COMMENT_SHORT", "top"),
            "show_nsfw": getenv("SHOW_NSFW", "on"),
        }
        self.rss: etree._Element = etree.Element(
            "rss", version="2.0", nsmap={"atom": "http://www.w3.org/2005/Atom"}
        )

    # @logger.catch
    def _generate_channel(self, tree: html.HtmlElement) -> etree._Element:
        # channel
        channel: etree._Element = etree.SubElement(self.rss, "channel")

        #
        for el in tree.xpath("//div[@id='subreddit']/div[@id='sub_meta']"):
            el_name: str = el.find("p[@id='sub_name']").text.strip()
            el_title: str = el.find("h1[@id='sub_title']").text.strip()
            el_logo: str = urljoin(self.base_url, el.find("img").get("src")).split(
                "?", maxsplit=1
            )[0]
            el_link: str = urljoin(self.base_url, el_name)
            el_description: str = el.find("p[@id='sub_description']").text.strip()

        # channel.title
        title = etree.SubElement(channel, "title")
        title.text = el_title

        # channel.desciption
        description = etree.SubElement(channel, "description")
        description.text = el_description

        # channel.link
        etree.SubElement(channel, "link").text = el_link

        # channel.logo
        etree.SubElement(channel, "icon").text = self.image_cache_url + el_logo

        gen = etree.SubElement(
            channel,
            "generator",
            uri="https://github.com/iamrony777/reddit-rss",
            version="0.1.0",
        )
        gen.text = "Reddit RSS"

        updated = etree.SubElement(channel, "pubDate")
        updated.text = datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S %z")

        # rss.atom
        etree.SubElement(
            channel,
            etree.QName("http://www.w3.org/2005/Atom", "link"),
            attrib={
                "href": getenv("VERCEL_URL") + el_name.replace("r/", "/r/"),
                "rel": "self",
                "type": "application/rss+xml",
            },
        )

        return channel

    def _generate_entry_description(self, post: html.HtmlElement) -> etree._Element:
        try:
            title = post.find("h2[@class='post_title']/a[2]").text.strip()
        except AttributeError:
            title = post.find("h2[@class='post_title']/a").text.strip()

        if post.find("a/[@class='post_media_image short']") is not None:
            image = urljoin(
                self.base_url,
                post.find("a/[@class='post_media_image short']")
                .get("href")
                .split("?", maxsplit=1)[0],
            )
            thumb = self.thumbnail_cache_url + image
        elif post.find("a/[@class='post_thumbnail ']/svg/desc/img") is not None:
            image = urljoin(
                self.base_url,
                post.find("a/[@class='post_thumbnail ']/svg/desc/img")
                .get("src")
                .split("?", maxsplit=1)[0],
            )
            thumb = self.thumbnail_cache_url + image
        elif post.find("video[@class='post_media_video short']") is not None:
            image = urljoin(
                self.base_url,
                post.find("video/[@class='post_media_video short']")
                .get("src")
                .split("?", maxsplit=1)[0],
            )
            thumb = self.thumbnail_cache_url + image
        else:
            image, thumb = "https://http.cat/404", "https://http.cat/404"

        description_div = etree.Element("div", attrib={"class": "col-md-9"})
        etree.SubElement(
            etree.SubElement(
                description_div,
                "a",
                attrib={"class": "bigImage", "href": self.image_cache_url + image},
            ),
            "img",
            attrib={
                "src": thumb,
                "title": title,
                "referrerpolicy": "no-referrer",
            },
        )
        return description_div

    def _generate_entry(
        self, tree: html.HtmlElement, channel: etree._Element
    ) -> etree._Element:
        for posts in tree.xpath("//div[@id='posts']"):
            for post in posts.xpath("//div[@class='post ']"):
                # item
                item = etree.SubElement(channel, "item")

                # item.title , item.link
                if post.find("h2[@class='post_title']/a[2]") is not None:
                    etree.SubElement(item, "title").text = post.find(
                        "h2[@class='post_title']/a[2]"
                    ).text.strip()

                    etree.SubElement(item, "link").text = urljoin(
                        self.base_url,
                        post.find("h2[@class='post_title']/a[2]").get("href"),
                    )
                else:
                    etree.SubElement(item, "title").text = post.find(
                        "h2[@class='post_title']/a"
                    ).text.strip()

                    etree.SubElement(item, "link").text = urljoin(
                        self.base_url,
                        post.find("h2[@class='post_title']/a").get("href"),
                    )
                # item.description
                etree.SubElement(item, "description").text = etree.CDATA(
                    html.tostring(
                        self._generate_entry_description(post),
                        encoding="unicode",
                        method="xml",
                    )
                )

                # item.guid
                etree.SubElement(item, "guid", isPermaLink="false").text = post.get(
                    "id"
                )

                # item.author
                etree.SubElement(item, "author").text = post.find(
                    "p[@class='post_header']/a[@class='post_author ']"
                ).get("href")

                # item.pubDate
                etree.SubElement(item, "pubDate").text = post.find(
                    "p[@class='post_header']/span[@class='created']"
                ).get("title")

                # item.category
                try:
                    etree.SubElement(item, "category").text = post.find(
                        "h2[@class='post_title']/small"
                    ).text.strip()
                except AttributeError:
                    continue
        return item

    @logger.catch
    async def get_feed(self, subreddit: str):
        resp = await self.client.get(
            url=f"/r/{subreddit}",
            cookies=self.cookies,
        )

        page_content: html.HtmlElement = html.fromstring(
            html=resp.content, base_url=str(resp.url), parser=self.parser
        )

        # rss.channel
        _channel = self._generate_channel(page_content)

        # channel.item[]
        self._generate_entry(page_content, channel=_channel)

        return etree.tostring(
            self.rss,
            pretty_print=True,
            xml_declaration=True,
            encoding="utf-8",
            standalone=True,
        ).decode("utf-8")


if __name__ == "__main__":
    from rich import print
    from asyncio import run

    print(run(Reddit().get_feed(subreddit="ksi")))
