
import re

from decimal import Decimal

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

    def is_valid_entity_id(self, value):
        """
        Returns True if value is a valid entity id

        Item: Q1234
        Commons: M1234
        Properties: P1234
        Lexemes: L1234
        Forms: L1234-F1234
        Senses: L1234-S1234

        """
        return value is not None and (
            re.match(r"^[QMPL]\d+$", value) is not None or re.match(r"^L\d+\-[FS]\d+$", value) is not None
        )

    def is_valid_label(self, value):
        """
        Returns True if value is a valid label
        Len
        Lpt
        """
        return value is not None and re.match("^L[a-z]{2}$", value) is not None

    def is_valid_alias(self, value):
        """
        Returns True if value is a valid alias
        Aen
        Apt
        """
        return value is not None and re.match("^A[a-z]{2}$", value) is not None

    def is_valid_description(self, value):
        """
        Returns True if value is a valid description
        Den
        Dpt
        """
        return value is not None and re.match("^D[a-z]{2}$", value) is not None

    def is_valid_sitelink(self, value):
        """
        Returns True if value is a valid sitelink
        Swiki
        """
        return value is not None and re.match("^S[a-z]+$", value) is not None

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
            if self.is_valid_alias(entity):
                return "alias"
            if self.is_valid_description(entity):
                return "description"
            if self.is_valid_label(entity):
                return "label"
            if self.is_valid_sitelink(entity):
                return "sitelink"
        return None

    def convert_to_utf8(self, s):
        if isinstance(s, str):
            return s.encode("utf-8").decode("utf-8")
        return s

    def parse_value_somevalue_novalue(self, v):
        """
        Returns somevalue data if v matches somevalue or novalue 
        Returns None otherwise
        """
        if v in ["somevalue", "novalue"]:
            return {"value": v, "type": v}
        return None

    def parse_value_entity(self, v):
        """
        Returns ITEM data if v matches a valid entity id,
        being an item, a property, a lexeme, a form or a sense.

        Item: Q1234
        Commons: M1234
        Properties: P1234
        Lexemes: L1234
        Forms: L1234-F1234
        Senses: L1234-S1234

        Returns None otherwise
        """
        if v == "LAST":
            return {"type": "wikibase-entityid", "value": "LAST"}
        if self.is_valid_entity_id(v):
            return {"type": "wikibase-entityid", "value": v.upper()}
        return None

    def parse_value_string(self, v):
        """
        Returns string data if v matches a text value, that must be in double quotes:

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
        Returns monolingualtext data if v matches a monolingual text value:

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

    def parse_value_url(self, v):
        """
        Returns url data if v matches a monolingual text value:

        \"\"\"https://www.google.com\"\"\"
        \"\"\"http://www.google.com\"\"\"

        Returns None otherwise
        """
        url_match = re.match(r'^"""(http(s)?:.*)"""$', v)
        if url_match:
            return {
                # TODO: maybe implement again data_type: url
                "type": "string",
                "value": url_match.group(1)
            }
        return None

    def parse_value_commons_media_file(self, v):
        """
        Returns commons media data if v matches a monolingual text value:

        \"\"\"Some tex.jpg\"\"\"

        Returns None otherwise
        """
        url_match = re.match(r'^"""(.*\.(?:jpg|JPG|jpeg|JPEG|png|PNG))"""$', v)
        if url_match:
            return {
                # TODO: maybe implement again data_type: commonsMedia
                "type": "string",
                "value": url_match.group(1)
            }
        return None

    def parse_value_external_id(self, v):
        """
        Returns external-id data if v matches a monolingual text value:

        \"\"\"myid\"\"\"

        Returns None otherwise
        """
        id_match = re.match(r'^"""(.*)"""$', v)
        if id_match:
            return {
                # TODO: maybe implement again data_type: commonsMedia
                "type": "string",
                "value": id_match.group(1)
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
        Returns geolocation data if v matches @LAT/LON

        @43.26193/10.92708

        Returns None otherwise
        """
        gps_match = re.match(r"^\@\s*([+-]{0,1}[0-9.]+)\s*\/\s*([+-]{0,1}[0-9.]+)$", v)
        if gps_match:
            return {
                "type": "globecoordinate",
                "value": {
                    "latitude": gps_match.group(1),
                    "longitude": gps_match.group(2),
                    "precision": "0.000001",
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
            amount = Decimal(quantity_match.group(1))
            unit = quantity_match.group(4)
            return {
                "type": "quantity",
                "value": {
                    "amount": str(amount),
                    "unit": unit if unit else "1",

                },
            }

        quantity_error_match = re.match(
            r"^([\+\-]{0,1}\d+(\.\d+){0,1})\s*~\s*([\+\-]{0,1}\d+(\.\d+){0,1})(U(\d+)){0,1}$", v
        )
        if quantity_error_match:
            value = Decimal(quantity_error_match.group(1))
            error = Decimal(quantity_error_match.group(3))
            unit = quantity_error_match.group(6)
            return {
                "type": "quantity",
                "value": {
                    "amount": str(value),
                    "upperBound": str(value + error),
                    "lowerBound": str(value - error),
                    "unit": unit if unit else "1",
                },
            }
        return None

    def parse_value(self, v):
        """
        Try to detect if v is a valid entity id, somevalue, novalue, text, monolingual text, time, location or quantity.
        Returns None otherwise
        """
        v = v.strip()
        for fn in [
            self.parse_value_somevalue_novalue, 
            self.parse_value_entity,
            self.parse_value_url,
            self.parse_value_commons_media_file,
            self.parse_value_external_id,
            self.parse_value_monolingualtext,
            self.parse_value_string,
            self.parse_value_time,
            self.parse_value_location,
            self.parser_value_quantity,
        ]:
            ret = fn(v)
            if ret is not None:
                return ret
        return None
