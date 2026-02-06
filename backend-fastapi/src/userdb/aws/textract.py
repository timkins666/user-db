"""Helper methods for working with AWS Textract."""

from datetime import date
import re
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

    f_results = form_results(kvs(blocks))
    q_results = query_results(blocks)

    _logger.info("Form results: %s", f_results.model_dump())
    _logger.info("Query results: %s", q_results.model_dump())

    merged_results = ProcessedUserData(
        firstname=f_results.firstname or q_results.firstname,
        lastname=f_results.lastname or q_results.lastname,
        date_of_birth=f_results.date_of_birth or q_results.date_of_birth,
    )

    return SuccessResult(success=True, payload=merged_results)


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


def form_results(kv_pairs: dict[str, str]) -> ProcessedUserData:
    """Get user data from form key-value pairs in textract output."""

    if not kv_pairs:
        _logger.info("No key-value pairs found in Textract results")
        return ProcessedUserData.empty()

    unrelated_key_rank = 999

    def _rank_date_key(key: str) -> int:
        key_ = re.sub(r"[^a-z]", "", key.lower())

        exact_ranks = {
            "dateofbirth": 0,
            "dob": 1,
            "birthdate": 2,
        }

        if key_ in exact_ranks:
            return exact_ranks[key_]
        if "birth" in key_ and "date" in key_:
            return 11
        if "birth" in key_ or "date" in key_:
            return 12
        return unrelated_key_rank

    def _rank_first_name_key(key: str) -> int:
        key_ = re.sub(r"[^a-z]", "", key.lower())

        exact_ranks = {
            "firstname": 0,
            "givenname": 1,
            "forename": 2,
        }

        if key_ in exact_ranks:
            return exact_ranks[key_]
        if "name" in key_:
            return 11
        return unrelated_key_rank

    def _rank_last_name_key(key: str) -> int:
        key_ = re.sub(r"[^a-z]", "", key.lower())

        exact_ranks = {
            "lastname": 0,
            "surname": 1,
            "familyname": 2,
        }

        if key_ in exact_ranks:
            return exact_ranks[key_]
        if "name" in key_:
            return 11
        return unrelated_key_rank

    best_dob_key = sorted(kv_pairs, key=_rank_date_key)[0]
    best_fn_key = sorted(kv_pairs, key=_rank_first_name_key)[0]
    best_ln_key = sorted(kv_pairs, key=_rank_last_name_key)[0]

    _logger.info(
        "using form data keys '%s' for dob, '%s' for firstname, '%s' for lastname",
        best_dob_key,
        best_fn_key,
        best_ln_key,
    )

    dob = _parse_dob(kv_pairs[best_dob_key])
    fn = None
    if _rank_first_name_key(best_fn_key) < unrelated_key_rank:
        fn = kv_pairs[best_fn_key]
    ln = None
    if _rank_last_name_key(best_ln_key) < unrelated_key_rank:
        ln = kv_pairs[best_ln_key]

    if fn and fn == ln:
        # assume fullname
        if " " in fn:
            split = fn.split(" ")
            fn, ln = split[0], split[-1]
        else:
            ln = None

    return ProcessedUserData(
        firstname=_capitalise_name(fn),
        lastname=_capitalise_name(ln),
        date_of_birth=dob,
    )


def _capitalise_name(name: str | None) -> str | None:
    """
    If name is all lowercase or all uppercase, capitalise it, otherwise assumme
    it's correctly capitalised already and return as is.

    Handles hyphens and apostrophes, e.g.
        "SMITH-JONES" -> "Smith-Jones"
        "o'connor" -> "O'Connor"
    """

    if not name or not (name.isupper() or name.islower()):
        return name or None

    def cap(part: str) -> str:
        for char in ["-", "'"]:
            if char in part:
                return char.join(cap(p) for p in part.split(char))
        return part.capitalize()

    return cap(name)


def _parse_name(extracted_data: dict) -> Iterable[str | None]:
    """
    Attempt to pick correct values for firstname and lastname from Textract results
    """
    _logger.info("Extracting name from Textract results: %s", extracted_data)

    fullname: str = extracted_data.get("fullname", "")
    firstname: str = extracted_data.get("firstname", "")
    lastname: str = extracted_data.get("lastname", "")

    if not fullname or fullname == firstname or fullname == lastname:
        return _capitalise_name(firstname), _capitalise_name(lastname)

    split = fullname.split(" ")
    fullname, lastname = split[0], split[-1]
    return _capitalise_name(firstname), _capitalise_name(lastname)


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


def kvs(blocks: list) -> dict[str, str]:
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
