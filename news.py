from api_utils import api_call
import json
import pandas as pd
from db_utils import connect_to_db, run_query, get_query

news_data = api_call("Problem")

df = pd.json_normalize(news_data,'articles')
df = df[['title', 'description', 'content', 'publishedAt', 'url']]
df = df.dropna(subset=['title', 'description', 'content'])
df = df.drop_duplicates(subset='title')
print(df)