import re
import csv
import io

from .base import BaseParser
from .base import ParserException

from core.models import Batch
from core.models import BatchCommand


class CSVCommandParser(BaseParser):
    # def parse_statement(self, elements, first_command):
    #     llen = len(elements)
    #     if llen < 3:
    #         raise ParserException(f"STATEMENT must contain at least entity, property and value")

    #     if first_command[0] == "-":
    #         action = "remove"
    #         entity = first_command[1:]
    #     else:
    #         action = "add"
    #         entity = first_command

    #     entity_type = self.get_entity_type(entity)

    #     if entity_type is None:
    #         raise ParserException(f"Invalid entity {entity}")

    #     vvalue = self.parse_value(elements[2])

    #     if llen == 3 and elements[1][0] in ["L", "A", "D", "S"]:
    #         # We are adding / removing a LABEL, ALIAS, DESCRIPTION or SITELINK to our property
    #         what = self.WHAT[elements[1][0]]
    #         if not vvalue or vvalue["type"] != "string":
    #             raise ParserException(f"{what} must be a string instance")

    #         lang = elements[1][1:]
    #         data = {"action": action, "what": what, "item": entity, "value": vvalue}
    #         if what == "sitelink":
    #             data["site"] = lang
    #         else:
    #             data["language"] = lang

    #     else:
    #         # We are adding / removing values
    #         pproperty = elements[1]
    #         if not self.is_valid_property_id(pproperty):
    #             raise ParserException(f"Invalid property {pproperty}")

    #         data = {
    #             "action": action,
    #             "what": "statement",
    #             "entity": {"type": entity_type, "id": entity},
    #             "property": pproperty,
    #             "value": vvalue,
    #         }

    #         sources = []
    #         qualifiers = []

    #         # ITERATE OVER qualifiers or sources (key, value) pairs
    #         index = 3
    #         while index + 1 < llen:
    #             key = elements[index].strip()
    #             value = self.parse_value(elements[index + 1].strip())
    #             if key[0] == "P":
    #                 if not self.is_valid_property_id(key):
    #                     raise ParserException(f"Invalid qualifier property {key}")
    #                 qualifiers.append({"property": key, "value": value})
    #             else:
    #                 new_source_block = False
    #                 if key.startswith("!S"):
    #                     new_source_block = False
    #                     key = key[1:]
    #                 if not self.is_valid_source_id(key):
    #                     raise ParserException(f"Invalid source {key}")
    #                 sources.append({"source": key, "value": value})
    #             index += 2

    #         if sources:
    #             data["sources"] = sources
    #         if qualifiers:
    #             data["qualifiers"] = qualifiers

    #     return data

    def parse_header(self, header):
        parsed_header = []
        for index, entity in enumerate(header):
            if index == 0:
                if entity != "qid":
                    raise ParserException(f"CSV header first element must be qid")
                parsed_header.append(entity)
            elif entity == "#":
                parsed_header.append(entity) # Adds comment (source) to previous command
            else:
                what = "statement"
                if entity[0] == "-":
                    action = "remove"
                    entity = entity[1:]
                else:
                    action = "add"

                entity_type = self.get_entity_type(entity)

                if entity_type in ["alias", "description", "label", "sitelink"]:
                    what = entity_type
                    lang = entity[1:]
                    data = {"action": action, "what": what, "item": entity}
                    if what == "sitelink":
                        data["site"] = lang
                    else:
                        data["language"] = lang
                else:
                    data = {
                        "action": action,
                        "what": what,
                        "entity": {"type": entity_type, "id": entity},
                    }
                parsed_header.append(data)

        return parsed_header


    def parse(self, batch_name, batch_owner, raw_csv):
        batch = Batch.objects.create(name=batch_name, user=batch_owner)
        
        memory_file = io.StringIO(raw_csv, newline='')
        
        first_line = True
        reader = csv.reader(memory_file, delimiter=',')
        for row in reader:
            if first_line:
                header = self.parse_header(row)
                first_line = False
            else:
                pass

        return batch



    # for row in spamreader:
    #     print(', '.join(row))

    #     elements = raw_command.split("\t")
    #     if len(elements) == 0:
    #         raise ParserException("Empty command statement")

    #     first_command = elements[0].upper().strip()

    #     if first_command == "CREATE":
    #         data = self.parse_create(elements)
    #     elif first_command == "MERGE":
    #         data = self.parse_merge(elements)
    #     else:
    #         data = self.parse_statement(elements, first_command)

    #     if comment:
    #         data["summary"] = comment

    #     return data
