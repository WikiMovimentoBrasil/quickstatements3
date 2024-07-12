
from .exceptions import ParserException


class V1CommandParser(object):

    def is_valid_property_id(self, value):
        return re.match("^P\\d+$", value) is not None

    def is_valid_lexeme_id(self, value):
        return re.match("^L\\d+$", value) is not None

    def is_valid_form_id(self, value):
        return re.match("^L\\d+\\-F\\d+", value) is not None

    def is_valid_sense_id(self, value):
        return re.match("^L\\d+\\-S\\d+", value) is not None

    def is_valid_item_id(self, value):
        return re.match("^Q\\d+$", value) is not None or re.match("^M\\d+$", value) is not None

    def get_entity_type(self, entity):
        if entity == "LAST" or self.is_item_id(entity):
            return "item"
        if self.is_property_id(entity):
            return "property"
        if self.is_lexeme_id(entity):
            return "lexeme"
        if self.is_form_id(entity):
            return "form"
        if self.is_sense_id(entity):
            return "sense"
        return None

    def convert_to_utf8(self, s):
        if isinstance(s, str):
            return s.encode('utf-8').decode('utf-8')
        return s

    def parse_value(self, v):
        v = v.strip()

        if v in ['somevalue', 'novalue']:
            return {"value": v, "type": v}

        if v == 'LAST':
            return {"type": "wikibase-entityid", "value": {"entity-type": "item", "id": "LAST"}}
            
        if self.is_valid_item_id(v):
            return {"type": "wikibase-entityid", "value": {"entity-type": self.get_entity_type(v), "id": v.upper()}}
            
        string_match = re.match(r'^"(.*)"$', v)
        if string_match:
            return {"type": "string", "value": self.convert_to_utf8(string_match.group(1)).strip()}
            
        monolingualtext_match = re.match(r'^([a-z_-]+):"(.*)"$', v)
        if monolingualtext_match:
            return {"type": "monolingualtext", "value": {"language": monolingualtext_match.group(1), "text": self.enforce_string_encoding(monolingualtext_match.group(2)).strip()}}
            
        time_match = re.match(r'^([+-]{0,1})(\d+)-(\d\d)-(\d\d)T(\d\d):(\d\d):(\d\d)Z\/{0,1}(\d*)(\/J){0,1}$', v)
        if time_match:
            prec = 9
            if time_match.group(8):
                prec = int(time_match.group(8))
            is_julian = time_match.group(9) is not None
            if is_julian:
                v = re.sub(r'/J$', '', v)
            return {
                "type": "time",
                "value": {
                    'time': re.sub(r'/\d+$', '', v),
                    'timezone': 0,
                    'before': 0,
                    'after': 0,
                    'precision': prec,
                    'calendarmodel': 'http://www.wikidata.org/entity/Q1985786' if is_julian else 'http://www.wikidata.org/entity/Q1985727'
                }
            }

        gps_match = re.match(r'^\@\s*([+-]{0,1}[0-9.]+)\s*\/\s*([+-]{0,1}[0-9.]+)$', v)
        if gps_match:
            return {
                "type": "globecoordinate",
                "value": {
                    'latitude': float(gps_match.group(1)),
                    'longitude': float(gps_match.group(2)),
                    'precision': 0.000001,
                    'globe': 'http://www.wikidata.org/entity/Q2'
                }
            }
            return True

        quantity_match = re.match(r'^([\+\-]{0,1}\d+(\.\d+){0,1})(U(\d+)){0,1}$', v)
        if quantity_match:
            return {
                "type": "quantity",
                "value": {
                    "amount": quantity_match.group(1),
                }
            }
            return True

        quantity_error_match = re.match(r'^([\+\-]{0,1}\d+(\.\d+){0,1})\s*~\s*([\+\-]{0,1}\d+(\.\d+){0,1})(U(\d+)){0,1}$', v)
        if quantity_error_match:
            value = float(quantity_error_match.group(1))
            error = float(quantity_error_match.group(3))
            return {
                "type": "quantity",
                "value": {
                    "amount": quantity_error_match.group(1),
                    "upperBound": value + error,
                    "lowerBound": value - error,
                }
            }

        return None

    def parse(self, raw_command):
        # comment = ''
        # if ( re.find ( '/^(.*?) *\/\* *(.*?) *\*\/ *$/' , $row , $m ) ) { // Extract comment as summary
        #     comment = $m[2] ;
        #     raw_command = $m[1] ;
        # }
        elements = raw_command.split("\t")
        if len(elements) == 0:
            raise ParserException("Empty command statement")

        llen = len(elements)
        first_command = elements[0].upper().strip()

        if first_command == "CREATE":
            if llen != 1:
                raise ParserException("CREATE command can have only 1 column")
                
            else:
                return {"action": "create", "type": "item"}

        if first_command == "MERGE":
            if llen != 3:
                raise ParserException("MERGE command must have 3 columns")
            else:
                item1 = elements[1].strip()
                item2 = elements[2].strip()
                try:
                    item1_id = int(item1[1:])
                    item2_id = int(item2[1:])
                    if item1_id > item2_id:
                        # Always merge into older item
                        item1, item2 = item2, item1
                    return {"action": "merge", "type": "item", "item1": item1, "item2": item2}
                except ValueError:
                    raise ParserException(f"MERGE items wrong format item1=[{item1}] item2=[{item2}]")

        if llen < 3:
            raise ParserException(f"STATEMENT must contain at least entity, property and value")

        if first_command[0] == "-":
            action = "remove"
            entity = first_command[1:]
        else:
            action = "create"
            entity = first_command

        entity_type = self.get_entity_type(entity)

        if entity_type is None:
            raise ParserException(f"Invalid entity {entity}")

        pproperty = elements[1]
        if not self.is_property_id(pproperty):
            raise ParserException(f"Invalid property {pproperty}")

        vvalue = self.parse_value(elements[2])

        return {
            "action": action, 
            "entity": {
                "type": entity_type, 
                "value": entity
            }, 
            "property": pproperty, 
            "value": vvalue
        }

