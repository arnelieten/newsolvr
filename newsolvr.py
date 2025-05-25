from newsapi_utils import insert_news_api, transform_news_api
import pandas as pd
from datetime import datetime, timedelta

current_topic = "problem NOT no problem"
from_date = datetime.now() - timedelta(minutes=1620)
to_date = datetime.now() - timedelta(minutes=1560)

df = transform_news_api(current_topic, from_date, to_date)
insert_news_api(df)