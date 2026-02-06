"""Tests for aws/textract.py"""

# pylint: disable=protected-access

from datetime import date
import pytest

from userdb.aws import textract
from userdb.models.user import ProcessedUserData


class TestHandleResults:
    """Tests for handle_results function"""

    def test_handle_results_missing_blocks(self):
        """Test handle_results returns failure when Blocks key is missing"""
        result = textract.handle_results({})
        assert result.success is False

    def test_handle_results_with_valid_blocks(self):
        """Test handle_results processes valid blocks successfully"""
        textract_results = {
            "Blocks": [
                {
                    "BlockType": "QUERY",
                    "Id": "query-1",
                    "Query": {"Alias": "firstname"},
                    "Relationships": [{"Type": "ANSWER", "Ids": ["answer-1"]}],
                },
                {
                    "BlockType": "QUERY_RESULT",
                    "Id": "answer-1",
                    "Text": "John",
                },
                {
                    "BlockType": "QUERY",
                    "Id": "query-2",
                    "Query": {"Alias": "lastname"},
                    "Relationships": [{"Type": "ANSWER", "Ids": ["answer-2"]}],
                },
                {
                    "BlockType": "QUERY_RESULT",
                    "Id": "answer-2",
                    "Text": "Smith",
                },
                {
                    "BlockType": "KEY_VALUE_SET",
                    "Id": "key-1",
                    "EntityTypes": ["KEY"],
                    "Relationships": [
                        {"Type": "CHILD", "Ids": ["word-1"]},
                        {"Type": "VALUE", "Ids": ["value-1"]},
                    ],
                },
                {
                    "Id": "word-1",
                    "BlockType": "WORD",
                    "Text": "d.o.b.",
                },
                {
                    "Id": "value-1",
                    "BlockType": "KEY_VALUE_SET",
                    "EntityTypes": ["VALUE"],
                    "Relationships": [{"Type": "CHILD", "Ids": ["word-2"]}],
                },
                {
                    "Id": "word-2",
                    "BlockType": "WORD",
                    "Text": "March 15th, 1990",
                },
            ]
        }

        result = textract.handle_results(textract_results)
        assert result.success is True
        assert result.payload
        assert result.payload.firstname == "John"
        assert result.payload.lastname == "Smith"
        assert result.payload.date_of_birth == date(1990, 3, 15)


class TestQueryResults:
    """Tests for query_results function"""

    def test_query_results_extracts_data(self):
        """Test query_results extracts data from query blocks"""
        blocks = [
            {
                "BlockType": "QUERY",
                "Id": "query-1",
                "Query": {"Alias": "firstname"},
                "Relationships": [{"Type": "ANSWER", "Ids": ["answer-1"]}],
            },
            {
                "BlockType": "QUERY_RESULT",
                "Id": "answer-1",
                "Text": "Jane",
            },
            {
                "BlockType": "QUERY",
                "Id": "query-2",
                "Query": {"Alias": "lastname"},
                "Relationships": [{"Type": "ANSWER", "Ids": ["answer-2"]}],
            },
            {
                "BlockType": "QUERY_RESULT",
                "Id": "answer-2",
                "Text": "DOE",
            },
            {
                "BlockType": "QUERY",
                "Id": "query-3",
                "Query": {"Alias": "date_of_birth"},
                "Relationships": [{"Type": "ANSWER", "Ids": ["answer-3"]}],
            },
            {
                "BlockType": "QUERY_RESULT",
                "Id": "answer-3",
                "Text": "15/03/1990",
            },
        ]

        result = textract.query_results(blocks)
        assert result.firstname == "Jane"
        assert result.lastname == "Doe"
        assert result.date_of_birth == date(1990, 3, 15)

    def test_query_results_handles_missing_data(self):
        """Test query_results handles missing data gracefully"""
        blocks = []

        result = textract.query_results(blocks)
        assert isinstance(result, ProcessedUserData)
        assert result.date_of_birth is None


class TestCapitaliseName:
    """Tests for _capitalise_name function"""

    @pytest.mark.parametrize(
        "input_name,expected",
        [
            ("", None),
            ("smith", "Smith"),
            ("JONES", "Jones"),
            ("o'connor", "O'Connor"),
            ("smith-jones", "Smith-Jones"),
            ("SMITH-JONES", "Smith-Jones"),
            ("mc-donald", "Mc-Donald"),
            ("mc-Donald", "mc-Donald"),
            ("Smith", "Smith"),
            ("smIth", "smIth"),
            ("sm3sh", "Sm3sh"),
        ],
    )
    def test_capitalise_name(self, input_name: str, expected: str):
        """Test _capitalise_name handles various name formats"""
        result = textract._capitalise_name(input_name)
        assert result == expected


class TestParseName:
    """Tests for _parse_name function"""

    def test_parse_name_with_firstname_lastname(self):
        """Test parsing when firstname and lastname are provided separately"""
        extracted_data = {
            "firstname": "JOHN",
            "lastname": "SMITH",
        }

        fn, ln = textract._parse_name(extracted_data)
        assert fn == "John"
        assert ln == "Smith"

    def test_parse_name_with_fullname(self):
        """Test parsing when fullname is provided"""
        extracted_data = {
            "fullname": "JANE DOE",
            "firstname": "JANE",
            "lastname": "",
        }

        fn, ln = textract._parse_name(extracted_data)
        assert fn == "Jane"
        assert ln == "Doe"

    def test_parse_name_with_hyphenated_lastname(self):
        """Test parsing hyphenated last names"""
        extracted_data = {
            "firstname": "john",
            "lastname": "smith-jones",
        }

        fn, ln = textract._parse_name(extracted_data)
        assert fn == "John"
        assert ln == "Smith-Jones"

    def test_parse_name_empty_values(self):
        """Test parsing with empty values"""
        extracted_data = {}

        fn, ln = textract._parse_name(extracted_data)
        assert fn is None
        assert ln is None

    def test_parse_name_fullname_same_as_firstname(self):
        """Test when fullname equals firstname"""
        extracted_data = {
            "fullname": "John",
            "firstname": "John",
            "lastname": "Smith",
        }

        fn, ln = textract._parse_name(extracted_data)
        assert fn == "John"
        assert ln == "Smith"


class TestParseDob:
    """Tests for _parse_dob function"""

    @pytest.mark.parametrize(
        "dob_string,expected_date",
        [
            ("15/03/1990", date(1990, 3, 15)),
            ("01-01-2000", date(2000, 1, 1)),
            ("25 December 1985", date(1985, 12, 25)),
            ("1990-03-15", date(1990, 3, 15)),
            ("15.03.1990", date(1990, 3, 15)),
        ],
    )
    def test_parse_dob_valid_dates(self, dob_string: str, expected_date: date):
        """Test _parse_dob with various valid date formats"""
        result = textract._parse_dob(dob_string)
        assert result == expected_date

    def test_parse_dob_empty_string(self):
        """Test _parse_dob with empty string"""
        result = textract._parse_dob("")
        assert result is None

    def test_parse_dob_invalid_date(self):
        """Test _parse_dob with invalid date string"""
        result = textract._parse_dob("not a date")
        assert result is None

    def test_parse_dob_fuzzy_parsing(self):
        """Test _parse_dob with text around date"""
        result = textract._parse_dob("Date of birth: 15/03/1990")
        assert result == date(1990, 3, 15)

    def test_parse_dob_uk_format(self):
        """Test _parse_dob prioritizes UK date format (day first)"""
        # 02/03/1990 should be interpreted as 2nd March, not 3rd February
        result = textract._parse_dob("02/03/1990")
        assert result == date(1990, 3, 2)


class TestKvs:
    """Tests for kvs function"""

    def test_kvs_extracts_key_value_pairs(self):
        """Test kvs extracts key-value pairs from form data"""
        blocks = [
            {
                "Id": "key-1",
                "BlockType": "KEY_VALUE_SET",
                "EntityTypes": ["KEY"],
                "Relationships": [
                    {"Type": "CHILD", "Ids": ["word-1"]},
                    {"Type": "VALUE", "Ids": ["value-1"]},
                ],
            },
            {
                "Id": "word-1",
                "BlockType": "WORD",
                "Text": "Name",
            },
            {
                "Id": "value-1",
                "BlockType": "KEY_VALUE_SET",
                "EntityTypes": ["VALUE"],
                "Relationships": [{"Type": "CHILD", "Ids": ["word-2"]}],
            },
            {
                "Id": "word-2",
                "BlockType": "WORD",
                "Text": "John",
            },
        ]

        result = textract.kvs(blocks)
        assert result == {"Name": "John"}

    def test_kvs_handles_multiword_keys_and_values(self):
        """Test kvs handles multi-word keys and values"""
        blocks = [
            {
                "Id": "key-1",
                "BlockType": "KEY_VALUE_SET",
                "EntityTypes": ["KEY"],
                "Relationships": [
                    {"Type": "CHILD", "Ids": ["word-1", "word-2"]},
                    {"Type": "VALUE", "Ids": ["value-1"]},
                ],
            },
            {
                "Id": "word-1",
                "BlockType": "WORD",
                "Text": "Full",
            },
            {
                "Id": "word-2",
                "BlockType": "WORD",
                "Text": "Name",
            },
            {
                "Id": "value-1",
                "BlockType": "KEY_VALUE_SET",
                "EntityTypes": ["VALUE"],
                "Relationships": [{"Type": "CHILD", "Ids": ["word-3", "word-4"]}],
            },
            {
                "Id": "word-3",
                "BlockType": "WORD",
                "Text": "John",
            },
            {
                "Id": "word-4",
                "BlockType": "WORD",
                "Text": "Smith",
            },
        ]

        result = textract.kvs(blocks)
        assert result == {"Full Name": "John Smith"}

    def test_kvs_handles_empty_values(self):
        """Test kvs handles empty values"""
        blocks = [
            {
                "Id": "key-1",
                "BlockType": "KEY_VALUE_SET",
                "EntityTypes": ["KEY"],
                "Relationships": [
                    {"Type": "CHILD", "Ids": ["word-1"]},
                    {"Type": "VALUE", "Ids": ["value-1"]},
                ],
            },
            {
                "Id": "word-1",
                "BlockType": "WORD",
                "Text": "Email",
            },
            {
                "Id": "value-1",
                "BlockType": "KEY_VALUE_SET",
                "EntityTypes": ["VALUE"],
                "Relationships": [],
            },
        ]

        result = textract.kvs(blocks)
        assert result == {"Email": ""}

    def test_kvs_empty_blocks(self):
        """Test kvs with empty blocks list"""
        result = textract.kvs([])
        assert not result

    def test_kvs_no_key_value_sets(self):
        """Test kvs with blocks that don't contain KEY_VALUE_SET"""
        blocks = [
            {
                "Id": "1",
                "BlockType": "PAGE",
            },
            {
                "Id": "2",
                "BlockType": "LINE",
                "Text": "Some text",
            },
        ]

        result = textract.kvs(blocks)
        assert not result


class TestFormResults:
    """Tests for form_results function"""

    def test_form_results_with_exact_dob_key(self):
        """Test form_results with exact 'dateofbirth' key"""
        kv_pairs = {
            "DateOfBirth": "15/03/1990",
            "FirstName": "John",
            "LastName": "SMITH",
        }

        result = textract.form_results(kv_pairs)
        assert result.firstname == "John"
        assert result.lastname == "Smith"
        assert result.date_of_birth == date(1990, 3, 15)

    def test_form_results_with_dob_key(self):
        """Test form_results with 'dob' key"""
        kv_pairs = {
            "D.O.B.": "01/01/2000",
            "GivenName": "jane",
            "Surname": "doe",
        }

        result = textract.form_results(kv_pairs)
        assert result.firstname == "Jane"
        assert result.lastname == "Doe"
        assert result.date_of_birth == date(2000, 1, 1)

    def test_form_results_with_fuzzy_keys(self):
        """Test form_results with less exact key matches"""
        kv_pairs = {
            "Birth Date": "25/12/1985",
            "Name": "Alice",
        }

        result = textract.form_results(kv_pairs)
        assert result.firstname == "Alice"
        assert result.date_of_birth == date(1985, 12, 25)

    def test_form_results_empty_dict(self):
        """Test form_results with empty dictionary"""
        kv_pairs = {}

        result = textract.form_results(kv_pairs)
        assert result.firstname is None
        assert result.lastname is None
        assert result.date_of_birth is None

    def test_form_results_with_hyphenated_lastname(self):
        """Test form_results with hyphenated last name"""
        kv_pairs = {
            "DateOfBirth": "10/05/1995",
            "FirstName": "mary",
            "FamilyName": "smith-jones",
        }

        result = textract.form_results(kv_pairs)
        assert result.firstname == "Mary"
        assert result.lastname == "Smith-Jones"
        assert result.date_of_birth == date(1995, 5, 10)

    def test_form_results_invalid_dob(self):
        """Test form_results with invalid date of birth"""
        kv_pairs = {
            "DateOfBirth": "invalid date",
            "FirstName": "Bob",
        }

        result = textract.form_results(kv_pairs)
        assert result.firstname == "Bob"
        assert result.date_of_birth is None

    def test_form_results_prioritizes_better_key_matches(self):
        """Test form_results chooses better-ranked keys when multiple exist"""
        kv_pairs = {
            "BirthDate": "20/08/1988",
            "DOB": "15/03/1990",
        }

        result = textract.form_results(kv_pairs)
        # Should pick DOB over BirthDate
        assert result.date_of_birth == date(1990, 3, 15)

    def test_form_results_ignores_poor_name_matches(self):
        """Test form_results ignores keys that don't match name patterns"""
        kv_pairs = {
            "DOB": "15/03/1990",
            "Address": "123 Main St",
        }

        result = textract.form_results(kv_pairs)
        assert result.firstname is None
        assert result.lastname is None
        assert result.date_of_birth == date(1990, 3, 15)

    def test_form_results_with_forename_key(self):
        """Test form_results with 'forename' key variant"""
        kv_pairs = {
            "DOB": "05/11/1992",
            "Forename": "Alice",
            "FamilyName": "Johnson",
        }

        result = textract.form_results(kv_pairs)
        assert result.firstname == "Alice"
        assert result.lastname == "Johnson"
        assert result.date_of_birth == date(1992, 11, 5)

    def test_form_results_mixed_case_keys(self):
        """Test form_results handles mixed case in keys"""
        kv_pairs = {
            "date of BIRTH": "12/06/1988",
            "FIRSTNAME": "MIKE",
            "lastname": "BROWN",
        }

        result = textract.form_results(kv_pairs)
        assert result.firstname == "Mike"
        assert result.lastname == "Brown"
        assert result.date_of_birth == date(1988, 6, 12)
