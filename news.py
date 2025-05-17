from api_utils import api_call
import pandas as pd
from db_utils import connect_to_db, run_query, close_query

topic = "problem"
news_data = api_call(topic)

df = pd.json_normalize(news_data, 'articles')
df = df[['title', 'description', 'content', 'publishedAt', 'url']]
df = df.dropna(subset=['title', 'description', 'content'])
df = df.drop_duplicates(subset='title')

dcb = connect_to_db()
for row in df.itertuples(index=False):
    run_query(dcb, 
        """INSERT INTO public.problems 
           (title_article, description_article, content_article, link_article, published_date) 
           VALUES (%s, %s, %s, %s, %s)
           ON CONFLICT (link_article) DO NOTHING""", 
        (row.title, row.description, row.content, row.url, row.publishedAt))

close_query(dcb)