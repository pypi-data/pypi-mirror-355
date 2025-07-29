import os
import xml.etree.ElementTree as ET
from Orange.data import Table, Domain, StringVariable
from Orange.data.io import FileFormat
from Orange.data.io_base import DataTableMixin

class TEIXMLReader(FileFormat, DataTableMixin):
    EXTENSIONS = ('.xml', '.teixml')
    DESCRIPTION = 'TEI XML'
    PRIORITY = 20

    def read(self):
        tree = ET.parse(self.filename)
        root = tree.getroot()

        def strip_ns(tag):
            return tag.split('}', 1)[-1] if '}' in tag else tag

        def find_text(root, path):
            for tag in path:
                root = next((el for el in root if strip_ns(el.tag) == tag), None)
                if root is None:
                    return ""
            return (root.text or "").strip()

        def extract_tokens(div):
            tokens = []
            processed_set = set()
            speaker = False

            for elem in div.iter():
                tag = strip_ns(elem.tag)
                if tag in {"speaker", "w", "c", "pc", "l"}:
                    text = None
                    if tag == "speaker":
                        speaker = True
                    elif speaker:
                        speaker = False
                        text = ("\n" + elem.text+": " or "")#.lstrip()
                    elif tag == "l":
                        text = "\n"
                    else:
                        text = (elem.text or "")#.lstrip()
                    if text:
                        tokens.append(text)

                    lemma = elem.attrib.get("lemma")
                    ana = elem.attrib.get("ana")
                    if lemma or ana:
                        d = {}
                        if lemma:
                            d["lemma"] = lemma
                        if ana:
                            d["ana"] = ana
                        processed_set.add(frozenset(d.items()))

            text = "".join(tokens)
            processed = [dict(items) for items in processed_set]
            return tokens, processed

        header = root.find(".//{*}teiHeader/{*}fileDesc")
        get = lambda *tags: find_text(header, list(tags)) if header is not None else ""

        attributes = {
            "title": get("titleStmt", "title"),
            "author": get("titleStmt", "author"),
            "publisher": get("publicationStmt", "publisher"),
            "pub_id": get("publicationStmt", "idno"),
            "address": get("publicationStmt", "address", "addrLine"),
            "license": get("publicationStmt", "availability", "license"),
            "date": get("publicationStmt", "date")
        }
        
        body = root.find(".//{*}text/{*}body")
        fields = []
        rows = []
        counters = {}
        if body is not None:
            for div in body.findall(".//{*}div"):
                div_type = div.attrib.get("type", "")
                if div_type not in counters:
                    counters[div_type] = 0
                counters[div_type] += 1

                div_num = div.attrib.get("n", counters[div_type])
                if div_type not in fields:
                    fields.append(div_type)

                subdivs = div.findall(".//{*}div")
                if len(subdivs) == 0:
                    tokens, processed = extract_tokens(div)
                    text = "".join(tokens)
                    row_metas = [f"{div_type}: {div_num}", text, str(processed)]
                else:
                    subcounters = {}
                    for subdiv in subdivs:
                        subdiv_type = subdiv.attrib.get("type", "")
                        if subdiv_type not in subcounters:
                            subcounters[subdiv_type] = 0
                        subcounters[subdiv_type] += 1
                        subdiv_num = subdiv.attrib.get("n", subcounters[subdiv_type])
                        tokens, processed = extract_tokens(subdiv)
                        text = "".join(tokens)
                        if subdiv_type not in fields:
                            fields.append(subdiv_type)
                    row_metas = [f"{div_type}: {div_num}, {subdiv_type}: {subdiv_num}", text, str(processed)]
                rows.append(row_metas)

        metas_vars = [ 
            StringVariable("section"),
            StringVariable("text"),
            StringVariable("processed"),
        ]

        domain = Domain([], metas=metas_vars)
        t = Table.from_list(domain, rows)
        t.attributes = attributes

        return t

if __name__ == "__main__":
    from Orange.data import Table

    file_path = "/home/chris/Downloads/A74980.xml"
    file_path = "/home/chris/Downloads/shakespeares-works_TEIsimple_FolgerShakespeare/hamlet_TEIsimple_FolgerShakespeare.xml"
    reader = TEIXMLReader(file_path)
    table = reader.read()

    print(f"Loaded {len(table)} rows.")
    print(table[0]['text'])