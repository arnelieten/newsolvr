from news_api_utils import loop_news_api
from llm_utils import insert_report

current_topic = "problem NOT no problem"

loop_news_api(current_topic, 1)
insert_report()