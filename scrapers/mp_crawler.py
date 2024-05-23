import httpx
from bs4 import BeautifulSoup
from datetime import datetime
import re


header = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_14_6) AppleWebKit/605.1.15 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/604.1 Edg/112.0.100.0'}


def mp_crawler(url: str, logger) -> (int, dict):
    if not url.startswith('https://mp.weixin.qq.com') and not url.startswith('http://mp.weixin.qq.com'):
        logger.warning(f'{url} is not a mp url, you should not use this function')
        return -5, {}

    if url.startswith('http://mp.weixin.qq.com'):
        url = url.replace("http://", "https://", 1)

    try:
        with httpx.Client() as client:
            response = client.get(url, headers=header, timeout=30)
    except Exception as e:
        logger.warning(f"cannot get content from {url}\n{e}")
        return -7, {}

    soup = BeautifulSoup(response.text, 'html.parser')

    # 先获取原始发布日期
    pattern = r"var createTime = '(\d{4}-\d{2}-\d{2}) \d{2}:\d{2}'"
    match = re.search(pattern, response.text)

    if match:
        # group(1) 用于获取第一个括号内匹配的内容，即日期部分
        date_only = match.group(1)
        publish_time = date_only.replace('-', '')
    else:
        publish_time = datetime.strftime(datetime.today(), "%Y%m%d")

    # 从<meta>标签中获取description内容
    meta_description = soup.find('meta', attrs={'name': 'description'})
    summary = meta_description['content'].strip() if meta_description else ''

    card_info = soup.find('div', id='img-content')

    # 从<div>标签中解析出所需内容
    rich_media_title = soup.find('h1', id='activity-name').text.strip() if soup.find('h1', id='activity-name') else ''
    profile_nickname = card_info.find('strong', class_='profile_nickname').text.strip() if card_info else ''
    # publish_time = card_info.find('em', id='publish_time').text if card_info else ''

    if not rich_media_title:
        logger.warning(f"failed to analysis {url}, no title")
        return -7, {}

    if not profile_nickname:
        logger.warning(f"failed to analysis profile_nickname {url}")
        profile_nickname = '微信公众号'

    # 解析内容区间内的文字和图片链接
    texts = []
    images = set()
    content_area = soup.find('div', id='js_content')
    if content_area:
        # 提取文本
        for section in content_area.find_all(['section', 'p'], recursive=False):  # 遍历顶级section
            text = section.get_text(separator=' ', strip=True)
            if text and text not in texts:
                texts.append(text)

        # 提取图片链接
        for img in content_area.find_all('img', class_='rich_pages wxw-img'):
            img_src = img.get('data-src') or img.get('src')
            if img_src:
                images.add(img_src)
        # 将文本按section分隔，并去除空白行
        cleaned_texts = [t for t in texts if t.strip()]
        content = '\n'.join(cleaned_texts)
    else:
        logger.warning(f"failed to analysis contents {url}")
        return 0, {}
    if content:
        content = f"({profile_nickname} 文章){content}"

    # 获取meta property="og:image"和meta property="twitter:image"中的图片链接
    og_image = soup.find('meta', property='og:image')
    twitter_image = soup.find('meta', property='twitter:image')
    if og_image:
        images.add(og_image['content'])
    if twitter_image:
        images.add(twitter_image['content'])

    # return body format {'url': str, 'title':  str, 'author':  str,  'publish_time':  str, 'content':  str, 'abstract':  str, 'images': [Path]}
    # 微信公众号的abstract很多作者都不认真写，参考价值不大，仅能当副标题用，这里判断是否与title一致，一致的话就舍弃, 不一致的话就与标题拼接作为abstract
    if rich_media_title == summary or not summary:
        abstract = ''
    else:
        abstract = f"({profile_nickname} 文章){rich_media_title}——{summary}"

    return 11, {
        'title': rich_media_title,
        'author': profile_nickname,
        'publish_time': publish_time,
        'abstract': abstract,
        'content': content,
        'images': list(images),  # 转换为列表形式返回
        'url': url,
    }
