from news_api_utils import loop_news_api
from llm_utils import insert_report

current_topic = "problem OR issue NOT (no problem OR no issue)"

loop_news_api(current_topic, 1, 5)
insert_report()