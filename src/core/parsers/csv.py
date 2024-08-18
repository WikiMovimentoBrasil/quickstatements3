import re
import csv
import io

from .base import BaseParser
from .base import ParserException

from core.models import Batch
from core.models import BatchCommand


class CSVCommandParser(BaseParser):


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

    def parse_line(self, row, header):
        commands = []
        current_property = None
        current_action = None
        current_what = None
        qid = None
        entity_type = None

        for index, cell in enumerate(row):
            cell = cell.strip()
            if index == 0: # That is the QID, alway in the firs column
                if not cell:
                    # Our qid is empty, so it means we are creating a new item
                    commands.append({"action": "create", "type": "item"})
                    qid = "LAST"
                    entity_type = self.get_entity_type(qid)
                else:
                    # Just modifying and existing one
                    qid = cell
                    entity_type = self.get_entity_type(qid)

            elif not cell:
                continue # Empty, does nothing

            elif header[index] == "#":
                # Our header indicates that this column represents comments
                # We add the cell value to the last command created
                commands[-1]["summary"] = cell
                continue

            else:
                _header = header[index]

                # Checking action
                if _header[0] == "-":
                    action = "remove"
                    _header = _header[1:]
                else:
                    action = "add"
                    _header = _header

                current_value = self.parse_value(cell)
                if current_value is None:
                    current_value = {"type": "string", "value": cell}

                # Is it a new property
                if self.is_valid_property_id(_header):
                    current_property = _header
                    current_action = action
                    current_what = "statement"

                    data = {
                        "action": current_action,
                        "what": current_what,
                        "entity": {"type": entity_type, "id": qid},
                        "property": current_property,
                        "value": current_value,
                    }
                else:
                    _type = self.get_entity_type(_header)
                    if _type in ["alias", "description", "label", "sitelink"]:
                        current_action = action
                        current_what = _type
                        lang = _header[1:]
                        data = {"action": action, "what": current_what, "item": qid, "value": current_value}
                        if current_what == "sitelink":
                            data["site"] = lang
                        else:
                            data["language"] = lang
            
                commands.append(data)
        return commands

    def parse_header(self, header):
        """
        Validates header
        """
        has_property_alias_description_label_sitelink = False
        parsed_header = []
        for index, cell in enumerate(header):
            if index == 0:
                if cell != "qid":
                    raise ParserException(f"CSV header first element must be qid")
            elif cell == "#":
                if not has_property_alias_description_label_sitelink:
                    raise ParserException(f"A valid property must precede a comment")
            else:
                clean_cell = cell[1:] if cell[0] == "-" else cell
                _type = self.get_entity_type(clean_cell)
                if not has_property_alias_description_label_sitelink:
                    has_property_alias_description_label_sitelink = _type in ["alias", "description", "label", "sitelink", "property"]
            parsed_header.append(cell)
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
                commands = self.parse_line(row, header)
                
        return batch
