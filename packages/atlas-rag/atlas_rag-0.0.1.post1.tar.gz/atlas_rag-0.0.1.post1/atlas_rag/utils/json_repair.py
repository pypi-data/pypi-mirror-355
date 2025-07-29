"""
This module will parse the JSON file following the BNF definition:

    <json> ::= <primitive> | <container>

    <primitive> ::= <number> | <string> | <boolean>
    ; Where:
    ; <number> is a valid real number expressed in one of a number of given formats
    ; <string> is a string of valid characters enclosed in quotes
    ; <boolean> is one of the literal strings 'true', 'false', or 'null' (unquoted)

    <container> ::= <object> | <array>
    <array> ::= '[' [ <json> *(', ' <json>) ] ']' ; A sequence of JSON values separated by commas
    <object> ::= '{' [ <member> *(', ' <member>) ] '}' ; A sequence of 'members'
    <member> ::= <string> ': ' <json> ; A pair consisting of a name, and a JSON value

If something is wrong (a missing parantheses or quotes for example) it will use a few simple heuristics to fix the JSON string:
- Add the missing parentheses if the parser believes that the array or object should be closed
- Quote strings or add missing single quotes
- Adjust whitespaces and remove line breaks

All supported use cases are in the unit tests
"""

import json
from typing import Any, Dict, List, Union, TextIO, Optional


class JSONParser:
    def __init__(self, json_str: str) -> None:
        # The string to parse
        self.json_str = json_str
        # Index is our iterator that will keep track of which character we are looking at right now
        self.index = 0
        # This is used in the object member parsing to manage the special cases of missing quotes in key or value
        self.context = ""

    def parse(self) -> Union[Dict[str, Any], List[Any], str, float, int, bool, None]:
        return self.parse_json()

    def parse_json(
        self,
    ) -> Union[Dict[str, Any], List[Any], str, float, int, bool, None]:
        char = self.get_char_at()
        # False means that we are at the end of the string provided, is the base case for recursion
        if char is False:
            return ""
        # <object> starts with '{'
        elif char == "{":
            self.index += 1
            return self.parse_object()
        # <array> starts with '['
        elif char == "[":
            self.index += 1
            return self.parse_array()
        # there can be an edge case in which a key is empty and at the end of an object
        # like "key": }. We return an empty string here to close the object properly
        elif char == "}" and self.context == "object_value":
            return ""
        # <string> starts with '"'
        elif char == '"':
            return self.parse_string()
        elif char == "'":
            return self.parse_string(string_quotes="'")
        elif char == "“":
            return self.parse_string(string_quotes=["“", "”"])
        # <number> starts with [0-9] or minus
        elif char.isdigit() or char == "-":
            return self.parse_number()
        # <boolean> could be (T)rue or (F)alse or (N)ull
        elif char.lower() in ["t", "f", "n"]:
            return self.parse_boolean_or_null()
        # This might be a <string> that is missing the starting '"'
        elif char.isalpha():
            return self.parse_string()
        # If everything else fails, we just ignore and move on
        else:
            self.index += 1
            return self.parse_json()

    def parse_object(self) -> Dict[str, Any]:
        # <object> ::= '{' [ <member> *(', ' <member>) ] '}' ; A sequence of 'members'
        obj = {}
        # Stop when you either find the closing parentheses or you have iterated over the entire string
        while (self.get_char_at() or "}") != "}":
            # This is what we expect to find:
            # <member> ::= <string> ': ' <json>

            # Skip filler whitespaces
            self.skip_whitespaces_at()

            # Sometimes LLMs do weird things, if we find a ":" so early, we'll change it to "," and move on
            if (self.get_char_at() or "") == ":":
                self.remove_char_at()
                self.insert_char_at(",")
                self.index += 1

            # We are now searching for they string key
            # Context is used in the string parser to manage the lack of quotes
            self.context = "object_key"

            self.skip_whitespaces_at()

            # <member> starts with a <string>
            key = ""
            while key == "" and self.get_char_at():
                key = self.parse_json()

                # This can happen sometimes like { "": "value" }
                if key == "" and self.get_char_at() == ":":
                    key = "empty_placeholder"
                    break

            # We reached the end here
            if (self.get_char_at() or "}") == "}":
                continue

            # An extreme case of missing ":" after a key
            if (self.get_char_at() or "") != ":":
                self.insert_char_at(":")
            self.index += 1
            self.context = "object_value"
            # The value can be any valid json
            value = self.parse_json()

            # Reset context since our job is done
            self.context = ""
            obj[key] = value

            if (self.get_char_at() or "") in [",", "'", '"']:
                self.index += 1

            # Remove trailing spaces
            self.skip_whitespaces_at()

        # Especially at the end of an LLM generated json you might miss the last "}"
        if (self.get_char_at() or "}") != "}":
            self.insert_char_at("}")
        self.index += 1
        return obj

    def parse_array(self) -> List[Any]:
        # <array> ::= '[' [ <json> *(', ' <json>) ] ']' ; A sequence of JSON values separated by commas
        arr = []
        # Stop when you either find the closing parentheses or you have iterated over the entire string
        while (self.get_char_at() or "]") != "]":
            value = self.parse_json()

            # It is possible that parse_json() returns nothing valid, so we stop
            if not value:
                break

            arr.append(value)

            # skip over whitespace after a value but before closing ]
            char = self.get_char_at()
            while char and (char.isspace() or char == ","):
                self.index += 1
                char = self.get_char_at()

        # Especially at the end of an LLM generated json you might miss the last "]"
        char = self.get_char_at()
        if char and char != "]":
            # Sometimes when you fix a missing "]" you'll have a trailing "," there that makes the JSON invalid
            if char == ",":
                # Remove trailing "," before adding the "]"
                self.remove_char_at()
            self.insert_char_at("]")

        self.index += 1
        return arr

    def parse_string(self, string_quotes=False) -> str:
        # <string> is a string of valid characters enclosed in quotes
        # i.e. { name: "John" }
        # Somehow all weird cases in an invalid JSON happen to be resolved in this function, so be careful here

        # Flag to manage corner cases related to missing starting quote
        fixed_quotes = False
        double_delimiter = False
        lstring_delimiter = rstring_delimiter = '"'
        if isinstance(string_quotes, list):
            lstring_delimiter = string_quotes[0]
            rstring_delimiter = string_quotes[1]
        elif isinstance(string_quotes, str):
            lstring_delimiter = rstring_delimiter = string_quotes
        if self.get_char_at(1) == lstring_delimiter:
            double_delimiter = True
            self.index += 1
        char = self.get_char_at()
        if char != lstring_delimiter:
            self.insert_char_at(lstring_delimiter)
            fixed_quotes = True
        else:
            self.index += 1

        # Start position of the string (to use later in the return value)
        start = self.index

        # Here things get a bit hairy because a string missing the final quote can also be a key or a value in an object
        # In that case we need to use the ":|,|}" characters as terminators of the string
        # So this will stop if:
        # * It finds a closing quote
        # * It iterated over the entire sequence
        # * If we are fixing missing quotes in an object, when it finds the special terminators
        char = self.get_char_at()
        fix_broken_markdown_link = False
        while char and char != rstring_delimiter:
            if fixed_quotes:
                if self.context == "object_key" and (char == ":" or char.isspace()):
                    break
                elif self.context == "object_value" and char in [",", "}"]:
                    break
            self.index += 1
            char = self.get_char_at()
            # If the string contains an escaped character we should respect that or remove the escape
            if self.get_char_at(-1) == "\\":
                if char in [rstring_delimiter, "t", "n", "r", "b", "\\"]:
                    self.index += 1
                    char = self.get_char_at()
                else:
                    self.remove_char_at(-1)
                    self.index -= 1
            # ChatGPT sometimes forget to quote links in markdown like: { "content": "[LINK]("https://google.com")" }
            if (
                char == rstring_delimiter
                # Next character is not a comma
                and self.get_char_at(1) != ","
                and (
                    fix_broken_markdown_link
                    or (self.get_char_at(-2) == "]" and self.get_char_at(-1)) == "("
                )
            ):
                fix_broken_markdown_link = not fix_broken_markdown_link
                self.index += 1
                char = self.get_char_at()

        if char and fixed_quotes and self.context == "object_key" and char.isspace():
            self.skip_whitespaces_at()
            if self.get_char_at() not in [":", ","]:
                return ""

        end = self.index

        # A fallout of the previous special case in the while loop, we need to update the index only if we had a closing quote
        if char != rstring_delimiter:
            self.insert_char_at(rstring_delimiter)
        else:
            self.index += 1
            if double_delimiter and self.get_char_at() == rstring_delimiter:
                self.index += 1

        return self.json_str[start:end]

    def parse_number(self) -> Union[float, int, str]:
        # <number> is a valid real number expressed in one of a number of given formats
        number_str = ""
        number_chars = set("0123456789-.eE")
        char = self.get_char_at()
        while char and char in number_chars:
            number_str += char
            self.index += 1
            char = self.get_char_at()
        if number_str:
            try:
                if "." in number_str or "e" in number_str or "E" in number_str:
                    return float(number_str)
                elif number_str == "-":
                    # If there is a stray "-" this will throw an exception, throw away this character
                    return self.parse_json()
                else:
                    return int(number_str)
            except ValueError:
                return number_str
        else:
            # This is a string then
            return self.parse_string()

    def parse_boolean_or_null(self) -> Union[bool, str, None]:
        # <boolean> is one of the literal strings 'true', 'false', or 'null' (unquoted)
        boolean_map = {"true": (True, 4), "false": (False, 5), "null": (None, 4)}
        for key, (value, length) in boolean_map.items():
            if self.json_str.lower().startswith(key, self.index):
                self.index += length
                return value

        # This is a string then
        return self.parse_string()

    def insert_char_at(self, char: str) -> None:
        self.json_str = self.json_str[: self.index] + char + self.json_str[self.index :]
        self.index += 1

    def get_char_at(self, count: int = 0) -> Union[str, bool]:
        # Why not use something simpler? Because we might be out of bounds and doing this check all the time is annoying
        try:
            return self.json_str[self.index + count]
        except IndexError:
            return False

    def remove_char_at(self, count: int = 0) -> None:
        self.json_str = (
            self.json_str[: self.index + count]
            + self.json_str[self.index + count + 1 :]
        )

    def skip_whitespaces_at(self) -> None:
        # Remove trailing spaces
        # I'd rather not do this BUT this method is called so many times that it makes sense to expand get_char_at
        # At least this is what the profiler said and I believe in our lord and savior the profiler
        try:
            char = self.json_str[self.index]
        except IndexError:
            return
        while char and char.isspace():
            self.index += 1
            try:
                char = self.json_str[self.index]
            except IndexError:
                return


def repair_json(
    json_str: str, return_objects: bool = False, skip_json_loads: bool = False
) -> Union[Dict[str, Any], List[Any], str, float, int, bool, None]:
    """
    Given a json formatted string, it will try to decode it and, if it fails, it will try to fix it.
    It will return the fixed string by default.
    When `return_objects=True` is passed, it will return the decoded data structure instead.
    """
    json_str = json_str.strip().lstrip("```json")
    parser = JSONParser(json_str)
    if skip_json_loads:
        parsed_json = parser.parse()
    else:
        try:
            parsed_json = json.loads(json_str)
        except json.JSONDecodeError:
            parsed_json = parser.parse()
    # It's useful to return the actual object instead of the json string, it allows this lib to be a replacement of the json library
    if return_objects:
        return parsed_json
    return json.dumps(parsed_json)


def loads(
    json_str: str,
) -> Union[Dict[str, Any], List[Any], str, float, int, bool, None]:
    """
    This function works like `json.loads()` except that it will fix your JSON in the process.
    It is a wrapper around the `repair_json()` function with `return_objects=True`.
    """
    return repair_json(json_str, True)


def load(fp: TextIO) -> Union[Dict[str, Any], List[Any], str, float, int, bool, None]:
    return loads(fp.read())


def from_file(
    filename: str,
) -> Union[Dict[str, Any], List[Any], str, float, int, bool, None]:
    fd = open(filename)
    jsonobj = load(fd)
    fd.close()

    return jsonobj




def validate_response(response: str, prompt_type: str, event_list: Optional[List[str]] = None):
    """Validate JSON response based on the prompt type"""
    try:
        json_start_token = response.find("[")
        json_end_token = response.rfind("]") + 1
        if json_end_token ==  0 or json_end_token < json_start_token:
            json_end_token = len(response)
        json_text = response[json_start_token: json_end_token]
        
        # print("JSON entity text: ", json_text)

        # fixed_json_text = repair_json(json_text)
            
        json_text = json_text.strip()

        json_text = json_text.replace("\n", "")
        json_text = json_text.replace("\r", "")
        json_text = json_text.replace("\t", "")
        

        response = repair_json(json_text)
        data = json.loads(response)
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON format")

    if not isinstance(data, list):
        raise TypeError("Response must be a JSON array")

    required_keys = {
        "entity_relation": {"Head", "Relation", "Tail"},
        "event_entity": {"Event", "Entity"},
        "event_relation": {"Head", "Relation", "Tail"}
    }

    for idx, item in enumerate(data):
        # Basic structure validation
        if not isinstance(item, dict):
            raise TypeError(f"Item {idx} must be a JSON object")

        # Check required keys
        missing = required_keys[prompt_type] - item.keys()
        if missing:
            raise KeyError(f"Item {idx} missing required keys: {missing}")

        # Type checking
        if prompt_type == "entity_relation":
            for key in ["Head", "Relation", "Tail"]:
                if not isinstance(item[key], str) or not item[key].strip():
                    raise TypeError(f"Item {idx} {key} must be a non-empty string")

        elif prompt_type == "event_entity":
            if not isinstance(item["Event"], str) or not item["Event"].strip():
                raise TypeError(f"Item {idx} Event must be a non-empty string")
            if not isinstance(item["Entity"], list) or not item["Entity"]:
                raise TypeError(f"Item {idx} Entity must be a non-empty array")
            for ent in item["Entity"]:
                if not isinstance(ent, str) or not ent.strip():
                    raise TypeError(f"Item {idx} Entity list contains invalid entry: {ent}")

        elif prompt_type == "event_relation":
            # Check exact wording for event_relation_2
            if event_list:
                if item["Head"] not in event_list:
                    raise ValueError(f"Item {idx} Head not in event list: {item['Head']}")
                if item["Tail"] not in event_list:
                    raise ValueError(f"Item {idx} Tail not in event list: {item['Tail']}")

            # Sentence validation
            for key in ["Head", "Tail"]:
                if not isinstance(item[key], str) or not item[key].strip():
                    raise TypeError(f"Item {idx} {key} must be a non-empty sentence")

    return True

def normalize_key(key):
    return key.strip().lower()

def split_json_objects(content: str) -> list[str]:
    """Split a comma-separated string of JSON objects into individual object strings."""
    objects = []
    start = None
    depth = 0
    
    for i, char in enumerate(content):
        if char == '{':
            if depth == 0:
                start = i  # Start of a new object
            depth += 1
        elif char == '}':
            depth -= 1
            if depth == 0 and start is not None:
                # End of an object
                objects.append(content[start:i + 1].strip())
                start = None
        # Ignore commas and other characters unless depth is 0 (top-level separator)
    
    return objects

def fix_and_validate_response(response: str, prompt_type: str, event_list: Optional[List[str]] = None):
    """Attempt to fix and validate JSON response based on the prompt type."""
    # Extract the JSON list from the response
    json_start_token = response.find("[")
    if json_start_token == -1:
        print(f"Invalid JSON list format in response: {response}")
        return None, "Response must start with a JSON array"
    
    # Take all content from the opening bracket onward
    json_text = response[json_start_token:].strip()
    
    # Check if it starts with an opening bracket
    if not json_text.startswith('['):
        print(f"Response must start with a JSON array: {json_text}")
        return None, "Response must start with a JSON array"
    
    content = json_text[1:-1].strip()  # Remove outer [ and ]
    
    # Split into individual object strings
    object_strings = split_json_objects(content)
    if not object_strings:
        print(f"No valid JSON objects found in: {json_text}")
        return "[]", None  # Return empty list if no objects
    
    # Parse each object, attempting repair if necessary
    parsed_objects = []
    for obj_str in object_strings:
        try:
            obj = json.loads(obj_str)
            if isinstance(obj, dict):
                parsed_objects.append(obj)
            else:
                print(f"Parsed object is not a dictionary, skipping: {obj_str}")
        except json.JSONDecodeError:
            # Attempt to repair the object
            try:
                repaired = repair_json(obj_str)
                obj = json.loads(repaired)
                if isinstance(obj, dict):
                    parsed_objects.append(obj)
                else:
                    print(f"Repaired object is not a dictionary, skipping: {repaired}")
            except Exception as e:
                print(f"Error repairing JSON: {e}, for string: {obj_str}")
                continue  # Skip this object if repair fails
    
    # Define required keys for each prompt type
    required_keys = {
        "entity_relation": {"Head", "Relation", "Tail"},
        "event_entity": {"Event", "Entity"},
        "event_relation": {"Head", "Relation", "Tail"}
    }
    
    corrected_data = []
    for idx, item in enumerate(parsed_objects):
        if not isinstance(item, dict):
            print(f"Item {idx} must be a JSON object. Problematic item: {item}")
            continue
        
        # Correct the keys
        corrected_item = {}
        for key, value in item.items():
            norm_key = normalize_key(key)
            matching_expected_keys = [exp_key for exp_key in required_keys[prompt_type] if normalize_key(exp_key) in norm_key]
            if len(matching_expected_keys) == 1:
                corrected_key = matching_expected_keys[0]
                corrected_item[corrected_key] = value
            else:
                corrected_item[key] = value
        
        # Check for missing keys in corrected_item
        missing = required_keys[prompt_type] - corrected_item.keys()
        if missing:
            print(f"Item {idx} missing required keys: {missing}. Problematic item: {item}")
            continue
        
        # Validate and correct the values in corrected_item
        if prompt_type == "entity_relation":
            for key in ["Head", "Relation", "Tail"]:
                if not isinstance(corrected_item[key], str) or not corrected_item[key].strip():
                    print(f"Item {idx} {key} must be a non-empty string. Problematic item: {corrected_item}")
                    continue
        
        elif prompt_type == "event_entity":
            if not isinstance(corrected_item["Event"], str) or not corrected_item["Event"].strip():
                print(f"Item {idx} Event must be a non-empty string. Problematic item: {corrected_item}")
                continue
            if not isinstance(corrected_item["Entity"], list) or not corrected_item["Entity"]:
                print(f"Item {idx} Entity must be a non-empty array. Problematic item: {corrected_item}")
                continue
            else:
                corrected_item["Entity"] = [ent.strip() for ent in corrected_item["Entity"] if isinstance(ent, str)]
        
        elif prompt_type == "event_relation":
            for key in ["Head", "Tail"]:
                if not isinstance(corrected_item[key], str) or not corrected_item[key].strip():
                    print(f"Item {idx} {key} must be a non-empty sentence. Problematic item: {corrected_item}")
                    continue
        
        corrected_data.append(corrected_item)
    
    corrected_json_string = json.dumps(corrected_data, ensure_ascii=False)
    return corrected_json_string, None