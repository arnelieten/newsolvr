from api_utils import api_call
from db_utils import connect_to_db, run_query, get_query

data = api_call("Sweco")
if data:
    total_results = data.get("totalResults")
    print(total_results)