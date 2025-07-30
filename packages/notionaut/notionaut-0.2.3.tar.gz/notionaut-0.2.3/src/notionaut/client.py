from typing import Dict, List

import pandas as pd
from notion_client import Client

PARSE_MAP = {
    "rich_text": lambda x: " ".join([y["plain_text"] for y in x["rich_text"]])
    if x["rich_text"]
    else pd.NA,
    "title": lambda x: "".join(p["plain_text"] for p in x["title"]),
    "select": lambda x: x["select"]["name"],
    "multi_select": lambda x: [p["name"] for p in x["multi_select"]],
    "url": lambda x: x["url"],
    "relation": lambda x: [p["id"] for p in x["relation"]],
    "formula": lambda x: x["formula"]["string"],
    "checkbox": lambda x: x["checkbox"],
    "date": lambda x: x["date"]["start"] if x["date"] else pd.NA,
    "number": lambda x: x["number"],
}


def parse_type(to_parse: Dict[str, any]) -> str:
    """
    Parses the type of a property from the Notion API response.

    :param to_parse: The property to parse.

    :return: The type of the property.
    """
    return to_parse["type"]


def parse_property(to_parse: Dict[str, any]) -> str:
    """
    Parses a property value from the Notion API response.

    :param to_parse: The property to parse.

    :return: The parsed property value.
    """
    property_type = parse_type(to_parse)
    try:
        return PARSE_MAP[property_type](to_parse)
    except KeyError:
        raise KeyError(f"Parsing Error: could not parse type {property_type}")


def parse_row(to_parse: Dict[str, any], columns: List[str] = None) -> Dict[str, any]:
    """
    Parses a row from the Notion API response into a dictionary.

    :param to_parse: The row to parse.
    :param columns: List of columns to include, defaults to None.

    :return: The parsed row.
    """
    row = {}
    for name, properties in to_parse.items():
        if not columns or name in columns:
            try:
                row[name] = parse_property(properties)
            except:
                print(f"Failed parsing column {name} in record {to_parse}")
    row["error"] = False
    return row


class NotionautClient:
    def __init__(self, notion_token: str, notion: Client = None):
        """
        Initializes a NotionautClient instance.

        :param notion_token: The Notion authentication token.
        :param notion: Optional parameter to inject the Notion client object.
        """
        if notion is None:
            self.notion = Client(auth=notion_token)
        else:
            self.notion = notion

    def fetch_results(
        self,
        database_id: str,
        query_filter: dict = None,
        query_sort: dict = None,
        page_size: int = 100,
    ) -> dict:
        """
        Fetches all results from a Notion database, handling pagination.

        :param database_id: The Notion database ID.
        :param query_filter: Optional filter for the query.
        :param query_sort: Optional sort for the query.
        :param page_size: Number of results per page (max 100).

        :return: A dict with all results combined.
        """
        all_results = []
        start_cursor = None

        while True:
            response = self.notion.databases.query(
                database_id=database_id,
                filter=query_filter,
                sorts=query_sort,
                start_cursor=start_cursor,
                page_size=page_size,
            )
            all_results.extend(response.get("results", []))
            if not response.get("has_more"):
                break
            start_cursor = response.get("next_cursor")

        return {"results": all_results}

    def process_results(
        self, results: dict, columns: List[str] = None, with_url: bool = False
    ) -> pd.DataFrame:
        df = pd.DataFrame(results["results"])
        if df.empty:
            return pd.DataFrame()
        parsed = pd.DataFrame(
            [parse_row(to_parse=d, columns=columns) for d in df["properties"]]
        )
        parsed = parsed[parsed.error == False].drop("error", axis=1)
        parsed["id"] = df["id"]
        if columns:
            parsed = parsed[columns]
        if with_url:
            parsed["_url"] = df["url"].apply(
                lambda x: x.replace("https://", "notion://")
            )
        return parsed

    def query(
        self,
        database_id: str,
        columns: List[str] = None,
        query_filter: dict = None,
        query_sort: dict = None,
        with_url: bool = False,
    ) -> pd.DataFrame:
        """
        Fetches data from a Notion database and returns it as a pandas DataFrame.

        :param database_id: The ID of the Notion database.
        :param columns: List of columns to include, defaults to None.
        :param filter: Optional database query filter.
        :param sorts: Optional database query sorting.

        :return: The fetched data as a pandas DataFrame.
        """
        results = self.fetch_results(
            database_id=database_id, query_filter=query_filter, query_sort=query_sort
        )
        return self.process_results(results=results, columns=columns, with_url=with_url)
