import re

from .base import BaseParser
from .base import ParserException


class V1CommandParser(BaseParser):

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
            "entity": {"type": entity_type, "id": entity},
            "property": pproperty,
            "value": vvalue,
        }
