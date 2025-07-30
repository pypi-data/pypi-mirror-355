import re
import ast
import json
import logging

# to run python -m string2dict.string2dict


logger = logging.getLogger(__name__)

class String2Dict:
    """
    A class to convert strings that represent dictionaries into actual Python dictionaries.
    """

    def __init__(self, debug=False):
        """
        Initializes the String2Dict instance.

        Args:
            debug (bool): If True, enables debug messages within the class. Default is False.
        """
        self.debug = debug
        self.logger = logging.getLogger(__name__)

    def _debug(self, message):

        if self.debug:
            self.logger.debug(message)

    def strip_surrounding_whitespace(self, string: str) -> str:
        """
        Strips leading and trailing whitespace from the string.

        Args:
            string (str): The input string.

        Returns:
            str: The stripped string.
        """
        stripped = string.strip()
        self._debug(f"After stripping whitespace: {repr(stripped)}")
        return stripped

    def remove_embedded_markers(self, string: str) -> str:
        """
        Removes embedded markers like ```json and ``` from the string.

        Args:
            string (str): The input string.

        Returns:
            str: The string with markers removed.
        """
        markers_removed = re.sub(r'```json', '', string)
        markers_removed = re.sub(r'```', '', markers_removed)
        self._debug(f"After removing embedded markers: {repr(markers_removed)}")
        return markers_removed

    def ensure_string_starts_and_ends_with_braces(self, string: str) -> str:
        """
        Ensures the string starts with '{' and ends with '}'.

        Args:
            string (str): The input string.

        Returns:
            str: The string enclosed with braces.
        """
        start = string.find('{')
        end = string.rfind('}') + 1  # Include the closing brace
        if start != -1 and end != -1:
            string = string[start:end]
        self._debug(f"After ensuring braces: {repr(string)}")
        return string

    def parse_as_json(self, string: str) -> dict:
        """
        Attempts to parse the string as JSON.

        Args:
            string (str): The input string.

        Returns:
            dict: The parsed dictionary.

        Raises:
            json.JSONDecodeError: If parsing fails.
        """
        parsed = json.loads(string)
        self._debug("Parsed with json.loads successfully.")
        return parsed

    def parse_with_literal_eval(self, string: str) -> dict:
        """
        Attempts to parse the string using ast.literal_eval.

        Args:
            string (str): The input string.

        Returns:
            dict: The parsed dictionary.

        Raises:
            SyntaxError, ValueError: If parsing fails.
        """
        parsed = ast.literal_eval(string)
        self._debug("Parsed with ast.literal_eval successfully.")
        return parsed

    def run(self, string: str) -> dict:
        """
        Converts a string representation of a dictionary into an actual dictionary.

        Args:
            string (str): The input string.

        Returns:
            dict: The parsed dictionary, or None if parsing fails.
        """
        self._debug(f"Input to s2d: {repr(string)}")

        if not string:
            self._debug("Input string is empty.")
            return None

        # Step 1: Strip surrounding whitespace
        string = self.strip_surrounding_whitespace(string)

        # Step 2: Remove embedded markers
        string = self.remove_embedded_markers(string)

        # Step 3: Ensure the string starts and ends with braces
        string = self.ensure_string_starts_and_ends_with_braces(string)

        # Log the cleaned string for debugging
        self._debug(f"Cleaned string: {repr(string)}")

        # Step 4: Attempt to parse as JSON
        try:
            parsed_dict = self.parse_as_json(string)
            return parsed_dict
        except json.JSONDecodeError as json_err:
            self._debug(f"json.loads failed with error: {json_err}")
            # Step 5: Attempt to parse with ast.literal_eval
            try:
                parsed_dict = self.parse_with_literal_eval(string)
                return parsed_dict
            except (SyntaxError, ValueError) as eval_err:
                self.logger.error(f"Both json.loads and ast.literal_eval failed. Errors: {json_err}, {eval_err}")
                return None

    def string_to_dict_list(self, string: str) -> list:
        """
        Extracts multiple dictionaries from a string and converts each to a Python dictionary.

        Args:
            string (str): The input string containing one or more dictionaries.

        Returns:
            list: A list of parsed dictionaries, or None if parsing fails.
        """
        # Step 1: Strip surrounding whitespace
        string = self.strip_surrounding_whitespace(string)

        # Step 2: Extract dictionary-like substrings
        dict_strings = re.findall(r'\{[^}]*\}', string)
        dict_list = []

        for dict_str in dict_strings:
            # Clean each dictionary-like string using existing methods
            dict_str = self.strip_surrounding_whitespace(dict_str)
            dict_str = self.remove_embedded_markers(dict_str)
            dict_str = self.ensure_string_starts_and_ends_with_braces(dict_str)

            # Attempt to parse each cleaned dictionary string
            try:
                parsed_dict = self.run(dict_str)
                if parsed_dict is not None:
                    dict_list.append(parsed_dict)
            except Exception as e:
                self.logger.error(f"Error parsing dictionary string: {dict_str}\n{e}")
                return None

        return dict_list if dict_list else None


if __name__ == "__main__":
    # Configure logging for testing purposes
    import sys

    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=sys.stdout
    )
    
    # Test strings
    a = "{\n    'key': 'SELECT DATE_FORMAT(bills.bill_date, \\'%Y-%m\\') AS month, SUM(bills.total) AS total_spending FROM bills WHERE YEAR(bills.bill_date) = 2023 GROUP BY DATE_FORMAT(bills.bill_date, \\'%Y-%m\\') ORDER BY month;'\n}"
    b = '{\n    "key": "SELECT DATE_FORMAT(bills.bill_date, \'%Y-%m\') AS month, SUM(bills.total) AS total_spending FROM bills WHERE YEAR(bills.bill_date) = 2023 GROUP BY DATE_FORMAT(bills.bill_date, \'%Y-%m\') ORDER BY month;"\n}'
    c = "{\n    'key': 'SELECT DATE_FORMAT(bill_date, \\'%Y-%m\\') AS month, SUM(total) AS total_spendings FROM bills WHERE YEAR(bill_date) = 2023 GROUP BY month ORDER BY month;'\n}"
    d = '{\n    \'key\': "SELECT DATE_FORMAT(bill_date, \'%Y-%m\') AS month, SUM(total) AS total_spendings FROM bills WHERE YEAR(bill_date) = 2023 GROUP BY DATE_FORMAT(bill_date, \'%Y-%m\') ORDER BY DATE_FORMAT(bill_date, \'%Y-%m\');"\n}'
    e = '{   \'key\': "https://dfasdfasfer.vercel.app/"}'
    f = '{\n  "part_number": "B18B-PUDSS-1(LF)(SN)",\n  "type": "Connector Header",\n  "sub_type": "Shrouded Header (4 Sides)",\n  "gender": "Header",\n  "number_of_contacts": 18,\n  "number_of_rows": 2,\n  "mounting_method": "Through Hole",\n  "termination_method": "Solder",\n  "terminal_pitch": "2 mm",\n  "body_orientation": "Straight",\n  "polarization_type": "Center Slot",\n  "row_spacing": "2 mm",\n  "maximum_current_rating": "3 A",\n  "maximum_voltage_rating": "250 VDC / 250 VAC",\n  "insulation_resistance": "1000 MΩ",\n  "maximum_contact_resistance": "20 mΩ",\n  "operating_temperature_range": "-25°C to 85°C",\n  "product_dimensions": {\n    "length": "20 mm",\n    "height": "9.6 mm",\n    "depth": "8.3 mm"\n  },\n  "compliance": "EU RoHS Compliant",\n  "eccn": "EAR99",\n  "packaging": "Box",\n  "manufacturer_lead_time": "0 weeks",\n  "price": 0.5988,\n  "use_cases": [\n    "PCB receptacles",\n    "consumer electronics",\n    "automotive systems",\n    "industrial equipment"\n  ],\n  "datasheet_link": "www.arrow.com/en/datasheets"\n}'
   
    g="```json\n[\n    {\n        \"title\": \"Wireless Keyboard\",\n        \"price\": \"€49.99\"\n    },\n    {\n        \"title\": \"USB-C Hub\",\n        \"price\": \"€29.50\"\n    }\n]\n```"
    
    # Create an instance with debug mode enabled
    s2d = String2Dict(debug=True)

    # Test the run method
    result = s2d.run(g)
    print("Result of parsing 'a':")
    print(result)
    print()

    # # Test the string_to_dict_list method
    # test_string = a + b + c
    # dict_list = s2d.string_to_dict_list(test_string)
    # print("Result of parsing multiple dictionaries:")
    # for idx, d in enumerate(dict_list, 1):
    #     print(f"Dictionary {idx}: {d}")
