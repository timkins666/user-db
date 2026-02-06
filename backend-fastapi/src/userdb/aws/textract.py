"""Helper methods for working with AWS Textract."""

from datetime import date
from typing import Iterable
import dateutil

from userdb.responses import SuccessResult
from userdb.utils import log
from userdb.models.user import ProcessedUserData

_logger = log.get_logger(__name__)


def handle_results(textract_results: dict) -> SuccessResult[ProcessedUserData]:
    """Handle the results from Textract."""

    if "Blocks" not in textract_results:
        _logger.error("Textract results missing 'Blocks' key")
        return SuccessResult(success=False)

    blocks = textract_results["Blocks"]

    return SuccessResult(success=True, payload=query_results(blocks))


def query_results(blocks: list) -> ProcessedUserData:
    """Get user data from query results in textract output."""

    extracted_data = {}
    query_blocks = [
        block for block in blocks if block.get("BlockType") in ["QUERY", "QUERY_RESULT"]
    ]

    for block in query_blocks:
        if block.get("BlockType") == "QUERY_RESULT":
            continue

        alias = block["Query"]["Alias"]
        answer_block_id = block["Relationships"][0]["Ids"][0]
        answer_block = next((b for b in blocks if b["Id"] == answer_block_id), {})
        extracted_data[alias] = answer_block.get("Text", "")

    dob = _parse_dob(extracted_data.get("date_of_birth", ""))
    fn, ln = _parse_name(extracted_data)

    return ProcessedUserData(
        firstname=fn,
        lastname=ln,
        date_of_birth=dob,
    )


# TODOs:
# Try going hardcore on k/v usage and queries as fallback,
# ideally remove queries.
#
# Only capitalise if all upper or lowercase
#
# look for singlechar' like D'Silva, O'Connor
#


def _capitalise_name(*names: str) -> Iterable[str]:
    """
    Capitalise a name, handling hyphens
    e.g. "SMITH-JONES" -> "Smith-Jones".
    """

    def cap(part: str) -> str:
        if "-" in part:
            return "-".join(cap(part) for part in part.split("-"))
        return (part or "").capitalize()

    return (cap(name) for name in names)


def _parse_name(extracted_data: dict) -> Iterable[str]:
    """
    Attempt to pick correct values for firstname and lastname from Textract results
    """
    _logger.info("Extracting name from Textract results: %s", extracted_data)

    fullname: str = extracted_data.get("fullname", "")
    firstname: str = extracted_data.get("firstname", "")
    lastname: str = extracted_data.get("lastname", "")

    if not fullname or fullname == firstname or fullname == lastname:
        return _capitalise_name(firstname, lastname)

    split = fullname.split(" ")
    fullname, lastname = split[0], split[-1]
    return _capitalise_name(firstname, lastname)


def _parse_dob(dob: str) -> date | None:
    """
    Attempt to parse a date of birth from a string.
    Assumes UK date format.
    """

    if not dob:
        _logger.info("No date of birth detected in Textract results")
        return None

    try:
        parsed_date = dateutil.parser.parse(dob, dayfirst=True, fuzzy=True)
        _logger.info(
            "Parsed date of birth %s from Textract input: %s", parsed_date, dob
        )
        return parsed_date.date()
    except (ValueError, IndexError):
        _logger.warning("Failed to parse date of birth: %s", dob)
    return None


def kvs(blocks: list) -> dict:
    """Get form data key value pairs from Textract results."""

    # Build a map of block IDs to blocks for quick lookup
    block_map = {block["Id"]: block for block in blocks}

    # Find all KEY_VALUE_SET blocks
    key_value_sets = [
        block for block in blocks if block.get("BlockType") == "KEY_VALUE_SET"
    ]

    # Separate keys and values
    key_blocks = [
        block for block in key_value_sets if "KEY" in block.get("EntityTypes", [])
    ]

    def get_text_from_block(block: dict, block_map: dict) -> str:
        """Extract text from a block by following CHILD relationships."""
        text_parts = []
        relationships = block.get("Relationships", [])

        for relationship in relationships:
            if relationship.get("Type") == "CHILD":
                for child_id in relationship.get("Ids", []):
                    child_block = block_map.get(child_id)
                    if child_block and child_block.get("BlockType") == "WORD":
                        text_parts.append(child_block.get("Text", ""))

        return " ".join(text_parts)

    key_value_pairs = {}

    for key_block in key_blocks:
        key_text = get_text_from_block(key_block, block_map)

        # Find the corresponding VALUE block
        value_text = ""
        relationships = key_block.get("Relationships", [])

        for relationship in relationships:
            if relationship.get("Type") == "VALUE":
                value_ids = relationship.get("Ids", [])
                if value_ids:
                    value_block = block_map.get(value_ids[0])
                    if value_block:
                        value_text = get_text_from_block(value_block, block_map)
                break

        if key_text:
            key_value_pairs[key_text] = value_text

    _logger.debug(
        "Extracted %d key-value pairs from Textract results", len(key_value_pairs)
    )

    return key_value_pairs
