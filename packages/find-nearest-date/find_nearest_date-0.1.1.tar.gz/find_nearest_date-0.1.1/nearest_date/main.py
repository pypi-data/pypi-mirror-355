from datetime import datetime

def parse_target_date(date_str=None):
    """
    Parses a date string into a datetime object set to 23:59:59 of the given day.

    If no date string is provided, defaults to today's date at 23:59:59.
    If the input date string is invalid, returns None.

    Args:
        date_str (str, optional): A date string in the format "YYYY-MM-DD".

    Returns:
        datetime or None: A datetime object at 23:59:59 of the specified date,
        or None if the input is invalid.
    """
    if not date_str:
        today = datetime.today()
        return datetime(today.year, today.month, today.day, 23, 59, 59)
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return datetime(dt.year, dt.month, dt.day, 23, 59, 59)
    except ValueError:
        return None

def get_nearest_extraction_date(filters: dict, target_dt, db):
    """
    Finds the most recent extraction date in the db that is less than or equal to the target date.

    Args:
        filters (dict): A dictionary of additional filter criteria.
        target_dt (datetime): The upper bound datetime for extraction date filtering.
        db: The database interface with a 'perform_aggregation' method.

    Returns:
        datetime or None: The nearest extraction date if found, otherwise None.
    """
    query_filter = filters.copy()
    query_filter["extraction_date"] = {"$lte": target_dt}

    pipeline = [
        {"$match": query_filter},
        {"$sort": {"extraction_date": -1}},
        {"$limit": 1}
    ]
    result = db.perform_aggregation(pipeline=pipeline)
    return result[0]["extraction_date"] if result else None

def get_entries_by_extraction_date(filters: dict, extraction_date, db):
    """
    Retrieves all entries from the database matching a specific extraction date.

    Args:
        filters (dict): A dictionary of filter criteria.
        extraction_date (datetime): The extraction date to match.
        db: The database interface with a `perform_aggregation` method.

    Returns:
        list: A list of matching entries.
    """
    query_filter = filters
    query_filter["extraction_date"] = extraction_date

    pipeline = [{"$match": query_filter}]
    return db.perform_aggregation(pipeline=pipeline)


def retrieve_data_by_nearest_date(filters: dict, target_date: str = None, db=None):
    """
    Fetches entries for the nearest extraction date on or before the target date.

    Args:
        filters (dict): Query filters.
        target_date (str, optional): Date in "YYYY-MM-DD" format. Defaults to today.
        db: Database with `perform_aggregation` method.

    Returns:
        list: Entries matching the nearest extraction date or an empty list.
    """

    target_dt = parse_target_date(target_date)
    if not target_dt:
        return []

    nearest_date = get_nearest_extraction_date(filters, target_dt, db)
    if not nearest_date:
        return []

    return get_entries_by_extraction_date(filters, nearest_date, db)
