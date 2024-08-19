from django.test import TestCase

from core.parsers.csv import CSVCommandParser


class TestCSVParser(TestCase):
    def test_parse_header(self):
        parser = CSVCommandParser()
        self.assertEqual(parser.parse_header(["qid","P31","-P31"]),["qid","P31","-P31"])
        self.assertEqual(parser.parse_header(["qid","Lpt"]), ["qid","Lpt"])
        self.assertEqual(parser.parse_header(["qid","Lpt", "#"]), ["qid","Lpt", "#"])
        self.assertEqual(parser.parse_header(["qid","-Lpt", "#"]), ["qid","-Lpt", "#"])
        self.assertEqual(parser.parse_header(["qid","Dpt"]), ["qid","Dpt"])
        self.assertEqual(parser.parse_header(["qid","Dpt", "#"]), ["qid","Dpt", "#"])
        self.assertEqual(parser.parse_header(["qid","-Dpt", "#"]), ["qid","-Dpt", "#"])
        self.assertEqual(parser.parse_header(["qid","Apt"]), ["qid","Apt"])
        self.assertEqual(parser.parse_header(["qid","Apt", "#"]), ["qid","Apt", "#"])
        self.assertEqual(parser.parse_header(["qid","-Apt", "#"]), ["qid","-Apt", "#"])
        self.assertEqual(parser.parse_header(["qid","Swiki"]), ["qid","Swiki"])
        self.assertEqual(parser.parse_header(["qid","Swiki", "#"]), ["qid","Swiki", "#"])
        self.assertEqual(parser.parse_header(["qid","-Swiki", "#"]), ["qid","-Swiki", "#"])

    def test_parse_header_no_qid(self):
        parser = CSVCommandParser()
        with self.assertRaises(Exception) as context:
            parser.parse_header(["", "qid","P31","-P31"])
        self.assertEqual(context.exception.message, "CSV header first element must be qid")

    def test_parse_header_comment_before_property(self):
        parser = CSVCommandParser()
        with self.assertRaises(Exception) as context:
            parser.parse_header(["qid","#","P31"])
        self.assertEqual(context.exception.message, "A valid property must precede a comment")

    def test_parse_item(self):
        parser = CSVCommandParser()

        # ADD / REMOVE
        self.assertEqual(parser.parse_line(["Q4115189","Q5","Q5"], ["qid","P31","-P31"]),
            [
                {
                    'action': 'add',
                    'entity': {'id': 'Q4115189', 'type': 'item'},
                    'property': 'P31',
                    'value': {'type': 'wikibase-entityid',
                             'value': {'entity-type': 'item', 'id': 'Q5'}},
                    'what': 'statement'
                },
                {
                    'action': 'remove',
                    'entity': {'id': 'Q4115189', 'type': 'item'},
                    'property': 'P31',
                    'value': {'type': 'wikibase-entityid',
                         'value': {'entity-type': 'item', 'id': 'Q5'}},
                    'what': 'statement'
                }
            ]
        )

        # ITEM
        self.assertEqual(parser.parse_line(["Q4115189","Q5"], ["qid","P369"]),
            [
                {
                    'action': 'add',
                    'entity': {'id': 'Q4115189', 'type': 'item'},
                    'property': 'P369',
                    'value': {'type': 'wikibase-entityid',
                             'value': {'entity-type': 'item', 'id': 'Q5'}},
                    'what': 'statement'
                },
            ]
        )

        # SOMEVALUE
        self.assertEqual(parser.parse_line(["Q4115189","somevalue"], ["qid","P369"]),
            [
                {
                    'action': 'add',
                    'entity': {'id': 'Q4115189', 'type': 'item'},
                    'property': 'P369',
                    'value': {'type': 'somevalue', 'value': 'somevalue'},
                    'what': 'statement'
                },
            ]
        )

        # NOVALUE
        self.assertEqual(parser.parse_line(["Q4115189","novalue"], ["qid","P369"]),
            [
                {
                    'action': 'add',
                    'entity': {'id': 'Q4115189', 'type': 'item'},
                    'property': 'P369',
                    'value': {'type': 'novalue', 'value': 'novalue'},
                    'what': 'statement'
                },
            ]
        )

        # LEXEME
        self.assertEqual(parser.parse_line(["L123","Q5"], ["qid","P369"]),
            [
                {
                    'action': 'add',
                    'entity': {'id': 'L123', 'type': 'lexeme'},
                    'property': 'P369',
                    'value': {'type': 'wikibase-entityid',
                             'value': {'entity-type': 'item', 'id': 'Q5'}},
                    'what': 'statement'
                },
            ]
        )

        self.assertEqual(parser.parse_line(["L123-S1","Q5"], ["qid","P369"]),
            [
                {
                    'action': 'add',
                    'entity': {'id': 'L123-S1', 'type': 'sense'},
                    'property': 'P369',
                    'value': {'type': 'wikibase-entityid',
                             'value': {'entity-type': 'item', 'id': 'Q5'}},
                    'what': 'statement'
                },
            ]
        )

        self.assertEqual(parser.parse_line(["L123-F1","Q5"], ["qid","P369"]),
            [
                {
                    'action': 'add',
                    'entity': {'id': 'L123-F1', 'type': 'form'},
                    'property': 'P369',
                    'value': {'type': 'wikibase-entityid',
                             'value': {'entity-type': 'item', 'id': 'Q5'}},
                    'what': 'statement'
                },
            ]
        )

    def test_parse_coordinates(self):
        parser = CSVCommandParser()

        self.assertEqual(parser.parse_line(["Q4115189","@43.26193/10.92708"], ["qid","P625"]),
            [
                {
                    'action': 'add',
                    'entity': {'id': 'Q4115189', 'type': 'item'},
                    'property': 'P625',
                    'value': {
                        'type': 'globecoordinate',
                        'value': {
                            'globe': 'http://www.wikidata.org/entity/Q2',
                            'latitude': "43.26193",
                            'longitude': "10.92708",
                            'precision': "0.000001"
                        }
                    },
                    'what': 'statement'
                },
            ]
        )

    def test_parse_datetime(self):
        parser = CSVCommandParser()
        self.assertEqual(parser.parse_line(["Q4115189","+1856-01-01T00:00:00Z/9"], ["qid","P577"]),
            [
                {
                    'action': 'add',
                    'entity': {'id': 'Q4115189', 'type': 'item'},
                    'property': 'P577',
                    'value': {
                        "type": "time",
                        "value": {
                            "time": "+1856-01-01T00:00:00Z",
                            "timezone": 0,
                            "before": 0,
                            "after": 0,
                            "precision": 9,
                            "calendarmodel": "http://www.wikidata.org/entity/Q1985727",
                        },
                    },
                    'what': 'statement'
                },
            ]
        )

    def test_parse_external_identifier(self):
        parser = CSVCommandParser()
        self.assertEqual(parser.parse_line(["Q4115189",'"""Sandbox"""'], ["qid","P370"]),
            [
                {
                    'action': 'add',
                    'entity': {'id': 'Q4115189', 'type': 'item'},
                    'property': 'P370',
                    'value': {
                        "type": "external-id",
                        "value": "Sandbox",
                    },
                    'what': 'statement'
                },
            ]
        )

        self.assertEqual(parser.parse_line(["Q4115189",'"""Patterns, Predictors, and Outcome"""'], ["qid","P370"]),
            [
                {
                    'action': 'add',
                    'entity': {'id': 'Q4115189', 'type': 'item'},
                    'property': 'P370',
                    'value': {
                        "type": "external-id",
                        "value": "Patterns, Predictors, and Outcome",
                    },
                    'what': 'statement'
                },
            ]
        )

        # result = parser.parse_line(["Q4115189",'"""Toys ""R"" Us"""'], ["qid","P370"])
        # self.assertEqual(result,
        #     [
        #         {
        #             'action': 'add',
        #             'entity': {'id': 'Q4115189', 'type': 'item'},
        #             'property': 'P370',
        #             'value': {
        #                 "type": "external-id",
        #                 "value": "Toys ""R"" Us",
        #             },
        #             'what': 'statement'
        #         },
        #     ]
        # )

    def test_parse_url(self):
        parser = CSVCommandParser()
        self.assertEqual(parser.parse_line(["Q4115189",'"""https://wiki.com.br"""'], ["qid","P370"]),
            [
                {
                    'action': 'add',
                    'entity': {'id': 'Q4115189', 'type': 'item'},
                    'property': 'P370',
                    'value': {
                        "type": "url",
                        "value": "https://wiki.com.br",
                    },
                    'what': 'statement'
                },
            ]
        )

        self.assertEqual(parser.parse_line(["Q4115189",'"""http://wiki.com"""'], ["qid","P370"]),
            [
                {
                    'action': 'add',
                    'entity': {'id': 'Q4115189', 'type': 'item'},
                    'property': 'P370',
                    'value': {
                        "type": "url",
                        "value": "http://wiki.com",
                    },
                    'what': 'statement'
                },
            ]
        )

    def test_parse_commons(self):
        parser = CSVCommandParser()
        self.assertEqual(parser.parse_line(["Q4115189",'"""Frans Breydel - A merry company.jpg"""'], ["qid","P370"]),
            [
                {
                    'action': 'add',
                    'entity': {'id': 'Q4115189', 'type': 'item'},
                    'property': 'P370',
                    'value': {
                        "type": "commonsMedia",
                        "value": "Frans Breydel - A merry company.jpg",
                    },
                    'what': 'statement'
                },
            ]
        )

        self.assertEqual(parser.parse_line(["Q4115189",'"""\'Girl Reading\' by Mary Colman Wheeler, El Paso Museum of Art.JPG"""'], ["qid","P370"]),
            [
                {
                    'action': 'add',
                    'entity': {'id': 'Q4115189', 'type': 'item'},
                    'property': 'P370',
                    'value': {
                        "type": "commonsMedia",
                        "value": "'Girl Reading' by Mary Colman Wheeler, El Paso Museum of Art.JPG",
                    },
                    'what': 'statement'
                },
            ]
        )

        # self.assertEqual(parser.parse_line(["Q4115189",'"""Kaubalaeva ""E. Russ"" vrakk.jpg"""'], ["qid","P370"]),
        #     [
        #         {
        #             'action': 'add',
        #             'entity': {'id': 'Q4115189', 'type': 'item'},
        #             'property': 'P370',
        #             'value': {
        #                 "type": "commonsMedia",
        #                 "value": "Kaubalaeva ""E. Russ"" vrakk.jpg",
        #             },
        #             'what': 'statement'
        #         },
        #     ]
        # )

        # self.assertEqual(parser.parse_line(["Q4115189",'"""\'\'L\'empereur Napoleon III\'\' de Franz-Xaver Winterhalter.jpg"""'], ["qid","P370"]),
        #     [
        #         {
        #             'action': 'add',
        #             'entity': {'id': 'Q4115189', 'type': 'item'},
        #             'property': 'P370',
        #             'value': {
        #                 "type": "commonsMedia",
        #                 "value": "'L'empereur Napoleon III' de Franz-Xaver Winterhalter.jpg",
        #             },
        #             'what': 'statement'
        #         },
        #     ]
        # )

    def test_parse_quantity(self):
        parser = CSVCommandParser()

        self.assertEqual(parser.parse_line(["Q4115189","10"], ["qid","P1114"]),
            [
                {
                    'action': 'add',
                    'entity': {'id': 'Q4115189', 'type': 'item'},
                    'property': 'P1114',
                    'value': {'type': 'quantity', 'value': {'amount': '10'}},
                    'what': 'statement'
                },
            ]
        )

        self.assertEqual(parser.parse_line(["Q4115189","+20"], ["qid","P1114"]),
            [
                {
                    'action': 'add',
                    'entity': {'id': 'Q4115189', 'type': 'item'},
                    'property': 'P1114',
                    'value': {'type': 'quantity', 'value': {'amount': '20'}},
                    'what': 'statement'
                },
            ]
        )

        self.assertEqual(parser.parse_line(["Q4115189","+3.1415926"], ["qid","P1114"]),
            [
                {
                    'action': 'add',
                    'entity': {'id': 'Q4115189', 'type': 'item'},
                    'property': 'P1114',
                    'value': {'type': 'quantity', 'value': {'amount': '3.1415926'}},
                    'what': 'statement'
                },
            ]
        )

        self.assertEqual(parser.parse_line(["Q4115189","-40"], ["qid","P1114"]),
            [
                {
                    'action': 'add',
                    'entity': {'id': 'Q4115189', 'type': 'item'},
                    'property': 'P1114',
                    'value': {'type': 'quantity', 'value': {'amount': '-40'}},
                    'what': 'statement'
                },
            ]
        )

        self.assertEqual(parser.parse_line(["Q4115189","-80~1.5"], ["qid","P1114"]),
            [
                {
                    'action': 'add',
                    'entity': {'id': 'Q4115189', 'type': 'item'},
                    'property': 'P1114',
                    'value': {'type': 'quantity', 'value': {'amount': '-80', "lowerBound": '-81.5', "upperBound": '-78.5'}},
                    'what': 'statement'
                },
            ]
        )

        self.assertEqual(parser.parse_line(["Q4115189","2.2~0.3"], ["qid","P1114"]),
            [
                {
                    'action': 'add',
                    'entity': {'id': 'Q4115189', 'type': 'item'},
                    'property': 'P1114',
                    'value': {'type': 'quantity', 'value': {'amount': '2.2', "lowerBound": '1.9', "upperBound": '2.5'}},
                    'what': 'statement'
                },
            ]
        )

        self.assertEqual(parser.parse_line(["Q4115189","+1.2~0.3"], ["qid","P1114"]),
            [
                {
                    'action': 'add',
                    'entity': {'id': 'Q4115189', 'type': 'item'},
                    'property': 'P1114',
                    'value': {'type': 'quantity', 'value': {'amount': '1.2', "lowerBound": '0.9', "upperBound": '1.5'}},
                    'what': 'statement'
                },
            ]
        )

    
    def test_parse_label(self):
        parser = CSVCommandParser()
        result = parser.parse_line(["Q4115189","Regina Phalange"], ["qid","Len"])
        self.assertEqual(result,
            [
                {
                    'action': 'add',
                    'item': 'Q4115189',
                    'value': {'type': 'string', 'value': 'Regina Phalange'},
                    'what': 'label',
                    'language': "en"
                },
            ]
        )

    def test_parse_description(self):
        parser = CSVCommandParser()
        result = parser.parse_line(["Q4115189","Ma maison"], ["qid","Dfr"])
        self.assertEqual(result,
            [
                {
                    'action': 'add',
                    'item': 'Q4115189',
                    'value': {'type': 'string', 'value': 'Ma maison'},
                    'what': 'description',
                    'language': "fr"
                },
            ]
        )

    def test_parse_alias(self):
        parser = CSVCommandParser()
        result = parser.parse_line(["Q4115189","Chacara Santo Antonio"], ["qid","Apt"])
        self.assertEqual(result,
            [
                {
                    'action': 'add',
                    'item': 'Q4115189',
                    'value': {'type': 'string', 'value': 'Chacara Santo Antonio'},
                    'what': 'alias',
                    'language': "pt"
                },
            ]
        )

    def test_parse_sitelink(self):
        parser = CSVCommandParser()
        result = parser.parse_line(["Q4115189","wiki.com.br"], ["qid","Swiki"])
        self.assertEqual(result,
            [
                {
                    'action': 'add',
                    'item': 'Q4115189',
                    'value': {'type': 'string', 'value': 'wiki.com.br'},
                    'what': 'sitelink',
                    'site': "wiki"
                },
            ]
        )

    def test_parse_monolingualtext(self):
        parser = CSVCommandParser()
        result = parser.parse_line(["Q4115189","en:\"Thats an english, text\""], ["qid","P31"])
        self.assertEqual(result,
            [
                {
                    'action': 'add',
                    'entity': {'id': 'Q4115189', 'type': 'item'},
                    'value': {'type': 'monolingualtext', 'value': {'language': 'en', 'text': 'Thats an english, text'}},
                    'what': 'statement',
                    'property': "P31"
                },
            ]
        )

    def test_create(self):
        parser = CSVCommandParser()
        result = parser.parse_line(["","Regina Phalange","fictional character", "Q95074"], ["qid","Len", "Den", "P31"])
        self.assertEqual(result,
            [
                {"action": "create", "type": "item"},
                {"action": "add", "what": "label", "item": "LAST", "language": "en", "value": {'type': 'string', 'value': 'Regina Phalange'}},
                {"action": "add", "what": "description", "item": "LAST", "language": "en", "value": {'type': 'string', 'value': 'fictional character'}},
                {"action": "add", "what": "statement", "entity": {"type": "item", "id": "LAST"}, "property": "P31", "value": {'type': 'wikibase-entityid', 'value': {'entity-type': 'item', 'id': 'Q95074'}}}
            ]
        )


