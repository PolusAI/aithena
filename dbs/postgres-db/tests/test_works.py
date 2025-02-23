from polus.aithena.common.logger import get_logger

logger = get_logger(__name__)

def test_get_10_first_works(db_connection):
    # Create a cursor object
    cur = db_connection.cursor()

    # Execute the query to get the first 10 records from the openalex.works table
    cur.execute("""
        SELECT *
        FROM openalex.works
        LIMIT 10;
    """)

    # Fetch all results
    records = cur.fetchall()

    # Print the first 10 records
    for record in records:
        logger.info(record)

    # Close the cursor
    cur.close()

    logger.debug(f"Retrieved {len(records)} records from the openalex.works table")

    # Assert that there are 10 records
    assert len(records) == 10, "Did not retrieve 10 records from the openalex.works table"