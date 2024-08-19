
import re


class ParserException(Exception):
    def __init__(self, message):
        super(ParserException, self).__init__(message)
        self.message = message


class BaseParser(object):
    """
    Base parser. Can parse basic data ids for wikidata
    """
    def is_valid_property_id(self, value):
        """
        Returns True if value is a valid PROPERTY ID
        PXXXX
        """
        return value is not None and re.match("^P\\d+$", value) is not None

    def is_valid_source_id(self, value):
        """
        Returns True if value is a valid SOURCE ID
        SXXXX
        """
        return value is not None and re.match("^S\\d+$", value) is not None

    def is_valid_lexeme_id(self, value):
        """
        Returns True if value is a valid LEXEME ID
        LXXXX
        """
        return value is not None and re.match("^L\\d+$", value) is not None

    def is_valid_form_id(self, value):
        """
        Returns True if value is a valid FORM ID
        LXXXX-FXXXX
        """
        return value is not None and re.match("^L\\d+\\-F\\d+", value) is not None

    def is_valid_sense_id(self, value):
        """
        Returns True if value is a valid SENSE ID
        LXXXX-SXXXX
        """
        return value is not None and re.match("^L\\d+\\-S\\d+", value) is not None

    def is_valid_item_id(self, value):
        """
        Returns True if value is a valid ITEM ID
        QXXXXX
        MXXXXX
        """
        return value is not None and (
            re.match("^Q\\d+$", value) is not None or re.match("^M\\d+$", value) is not None
        )

    def get_entity_type(self, entity):
        """
        Detects the entity type based on the pattern. 
        Returns item, property, lexeme, form, sense if its a valid pattern.
        Returns None otherwise
        """
        if entity is not None:
            if entity == "LAST" or self.is_valid_item_id(entity):
                return "item"
            if self.is_valid_property_id(entity):
                return "property"
            if self.is_valid_lexeme_id(entity):
                return "lexeme"
            if self.is_valid_form_id(entity):
                return "form"
            if self.is_valid_sense_id(entity):
                return "sense"
        return None

    def convert_to_utf8(self, s):
        if isinstance(s, str):
            return s.encode("utf-8").decode("utf-8")
        return s

    def parse_value_somevalue_novalue(self, v):
        """
        Returns quantity data if v matches somevalue or novalue 
        Returns None otherwise
        """
        if v in ["somevalue", "novalue"]:
            return {"value": v, "type": v}
        return None

    def parse_value_item(self, v): 
        """
        Returns quantity data if v matches a valid item id:

        Q1234
        M1234

        Returns None otherwise
        """
        if v == "LAST":
            return {"type": "wikibase-entityid", "value": {"entity-type": "item", "id": "LAST"}}
        if self.is_valid_item_id(v):
            return {"type": "wikibase-entityid", "value": {"entity-type": self.get_entity_type(v), "id": v.upper()}}
        return None

    def parse_value_string(self, v):
        """
        Returns quantity data if v matches a text value, that must be in double quotes:

        "Some text"
        "Algum texto"

        Returns None otherwise
        """
        string_match = re.match(r'^"(.*)"$', v)
        if string_match:
            return {"type": "string", "value": self.convert_to_utf8(string_match.group(1)).strip()}
        return None

    def parse_value_monolingualtext(self, v):
        """
        Returns quantity data if v matches a monolingual text value:

        en:"Some text"
        pt:"Algum texto"

        Returns None otherwise
        """
        monolingualtext_match = re.match(r'^([a-z_-]+):"(.*)"$', v)
        if monolingualtext_match:
            return {
                "type": "monolingualtext",
                "value": {
                    "language": monolingualtext_match.group(1),
                    "text": self.convert_to_utf8(monolingualtext_match.group(2)).strip(),
                },
            }
        return None

    def parse_value_time(self, v):
        """
        Returns quantity data if v matches a time value

        +1967-01-17T00:00:00Z/11

        Returns None otherwise
        """
        time_match = re.match(r"^([+-]{0,1})(\d+)-(\d\d)-(\d\d)T(\d\d):(\d\d):(\d\d)Z\/{0,1}(\d*)(\/J){0,1}$", v)
        if time_match:
            prec = 9
            if time_match.group(8):
                prec = int(time_match.group(8))
            is_julian = time_match.group(9) is not None
            if is_julian:
                v = re.sub(r"/J$", "", v)
            return {
                "type": "time",
                "value": {
                    "time": re.sub(r"/\d+$", "", v),
                    "timezone": 0,
                    "before": 0,
                    "after": 0,
                    "precision": prec,
                    "calendarmodel": "http://www.wikidata.org/entity/Q1985786"
                    if is_julian
                    else "http://www.wikidata.org/entity/Q1985727",
                },
            }
        return None

    def parse_value_location(self, v):
        """
        Returns quantity data if v matches @LAT/LON

        @43.26193/10.92708

        Returns None otherwise
        """
        gps_match = re.match(r"^\@\s*([+-]{0,1}[0-9.]+)\s*\/\s*([+-]{0,1}[0-9.]+)$", v)
        if gps_match:
            return {
                "type": "globecoordinate",
                "value": {
                    "latitude": float(gps_match.group(1)),
                    "longitude": float(gps_match.group(2)),
                    "precision": 0.000001,
                    "globe": "http://www.wikidata.org/entity/Q2",
                },
            }
        return None

    def parser_value_quantity(self, v):
        """
        Returns quantity data if v matches one of the following format:

        10, 10U11573, 1.2~0.3

        Returns None otherwise
        """
        quantity_match = re.match(r"^([\+\-]{0,1}\d+(\.\d+){0,1})(U(\d+)){0,1}$", v)
        if quantity_match:
            unit = quantity_match.group(4)
            return {
                "type": "quantity",
                "value": {
                    "amount": quantity_match.group(1),
                    "unit": unit if unit else "1",
                },
            }

        quantity_error_match = re.match(
            r"^([\+\-]{0,1}\d+(\.\d+){0,1})\s*~\s*([\+\-]{0,1}\d+(\.\d+){0,1})(U(\d+)){0,1}$", v
        )
        if quantity_error_match:
            value = float(quantity_error_match.group(1))
            error = float(quantity_error_match.group(3))
            unit = quantity_error_match.group(6)
            return {
                "type": "quantity",
                "value": {
                    "amount": quantity_error_match.group(1),
                    "upperBound": value + error,
                    "lowerBound": value - error,
                    "unit": unit if unit else "1",
                },
            }
        return None

    def parse_value(self, v):
        """
        Try to detect if v is a valid item id, somevalue, novalue, text, monolingual text, time, location or quantity.
        Returns None otherwise
        """
        v = v.strip()
        for fn in [
            self.parse_value_somevalue_novalue, 
            self.parse_value_item, 
            self.parse_value_string,
            self.parse_value_monolingualtext,
            self.parse_value_time,
            self.parse_value_location,
            self.parser_value_quantity,
        ]:
            ret = fn(v)
            if ret is not None:
                return ret
        return None
