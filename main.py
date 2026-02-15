from utils.llm_utils import insert_report
from utils.news_api_utils import loop_news_api

current_topic = "problem OR issue NOT (no problem OR no issue)"

loop_news_api(current_topic, 4, 1)
insert_report()
