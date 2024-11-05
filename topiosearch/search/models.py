from django.db import models
from unidecode import unidecode
from bs4 import BeautifulSoup
import requests
import sqlite3
import re


# Create your models here.
class Search(models.Model):
    pass
    # create topiosearch functions here

    def inputFilter(term):
        # TODO - filter unsafe input
        return term

    # Gets everything in a tag except children. Gets "foobar" in <td>foo<i>baz</i>bar<i>qux</i></td>
    def getContentBeforeFirstChildTag(html_tag):
        direct_text = ''
        for element in html_tag.contents:
            if isinstance(element, str):
                direct_text = element.strip()  # Get the first text node and strip any surrounding whitespace
                break
        return direct_text

    # Gets text in a tag before first child. Gets "foo" in <td>foo<i>bar</i>baz<i>qux</i></td>
    def getContentWithoutChildrenTags(html_tag,separator):
        direct_text = separator.join([str(element) for element in html_tag.contents if isinstance(element, str)])
        return direct_text

    def onLocalDatabase(termUnsafeInput):


        term = Search.inputFilter(termUnsafeInput)
        termLower = term.lower() # sqlite is able to find case-insensitive apparently.
        termNoAccents = unidecode(term)
        termNoAccentsLower = termNoAccents.lower()
        searchCriteria = (term, termNoAccents, termLower, termNoAccentsLower)

        if(not(term) or term == ""):
            return {"error": "empty_search_term"}

        def format_rows_to_dict(cursor, row):
            d = {}
            for idx, col in enumerate(cursor.description):
                d[col[0]] = row[idx]
            return d


        connection = sqlite3.connect('db.sqlite3')
        connection.row_factory = format_rows_to_dict #has to be done manually with sqlite
        cursor = connection.cursor()

        result = cursor.execute('''SELECT * FROM term_term 
        WHERE name LIKE "%'''+term+'''%"
        OR name LIKE "%'''+termLower+'''%"
        OR name LIKE "%'''+termNoAccents+'''%"
        OR name LIKE "%'''+termNoAccentsLower+'''%"
        OR alternative_forms LIKE "%'''+term+'''%"
        OR alternative_forms LIKE "%'''+termLower+'''%"
        OR alternative_forms LIKE "%'''+termNoAccents+'''%"
        OR alternative_forms LIKE "%'''+termNoAccentsLower+'''%"
        ; ''')
        rows = result.fetchall()
        connection.commit()
        connection.close()

        if(len(rows) == 0):
            return {"error":"no_term_found"}

        # TODO: format the response exactly as the remote.

        response = rows

        return response

    def onTopio(termUnsafeInput):

        term = Search.inputFilter(termUnsafeInput)
        termNoAccents = unidecode(term)
        termLower = term.lower()
        termNoAccentsLower = termNoAccents.lower()
        termCap = term.capitalize()
        termNoAccentsCap = termNoAccents.capitalize()
        termUpper = term.upper()
        termNoAccentsUpper = termNoAccents.upper()
        searchCriteria = (term,termNoAccents,termLower,termNoAccentsLower,termCap,termNoAccentsCap,termUpper,termNoAccentsUpper)

        # generate needed variables
        name = ""
        definition = ""
        example = ""

        # Crawl topio database
        url = 'https://www.topio.ch/dico.php'
        htmlrequest = requests.get(url) # TODO - show debug data
        htmldata = htmlrequest.text

        html = BeautifulSoup(htmldata, "html.parser")
        content = html.find('div', id = 'contenu')
        table = html.find('table')
        rows = table.find_all('tr')

        topioterms = []
        for index, row in enumerate(rows):
            if index > 2: # the 3 first lines of the topio table don't contain words
                first_td = row.find('td')
                if first_td:
                    topioterm = first_td.get_text()
                    topioterms.append(topioterm)
                    if(topioterm in searchCriteria):
                        # Found the entry with the corresponding term, let's get the definition:
                        # TODO - many words have several definitions: defs and examples should be stored as tuples
                        name = topioterm
                        definition_td = first_td.find_next_sibling('td')
                        definition = Search.getContentBeforeFirstChildTag(definition_td)

                        # Get the examples
                        # TODO - examples also should be stored as tuples
                        example_i_elements = definition_td.find_all('i')
                        examples_separator = ""
                        for example_i_element in example_i_elements:

                            if(example != ""):
                                examples_separator = " / "

                            example = example + examples_separator + example_i_element.get_text().capitalize()


        # save in database if not exists

        connection = sqlite3.connect('db.sqlite3')
        cursor = connection.cursor()

        topioSearchQuery = '''SELECT COUNT(id) AS count FROM term_term WHERE url = ? ;'''
        result = cursor.execute(topioSearchQuery, (termNoAccentsLower+"--t",))
        topioAlreadyExists = result.fetchone()[0]


        if(topioAlreadyExists == 0 and name != ""):
            topioInsertQuery = '''INSERT INTO term_term (id,name,type,definition,example,alternative_forms,copyright,origin,date_added,date_edited,key,url)
            VALUES ( NULL, ?, "", ?,  ?, "", "topio.ch", "https://topio.ch/dico.php", DATETIME('now'), DATETIME('now'), 0, ?);'''
            cursor.execute(topioInsertQuery, (name, definition, example, termNoAccentsLower+"--t"))
            connection.commit()
            connection.close()
        else:
            pass


        response = {
            "debug":"",
            "localExists": topioAlreadyExists,
            "search_criteria":searchCriteria,
            "url":termNoAccentsLower + "--t",
            "name": name,
            "type":"", # not present in topio data
            "definition":definition,
            "example":example,
            "alternative_forms":"", # TODO: can be done in topio with splitting on " - " as in: "Toyet - Toyotse"
            "copyright":"topio.ch",
            "origin":"https://www.topio.ch/dico.php"
        }

        return response


    def onHSuter(termUnsafeInput):

        # copy pasted from onTopio()
        term = Search.inputFilter(termUnsafeInput)
        termNoAccents = unidecode(term)
        termLower = term.lower()
        termNoAccentsLower = termNoAccents.lower()
        termCap = term.capitalize()
        termNoAccentsCap = termNoAccents.capitalize()
        termUpper = term.upper()
        termNoAccentsUpper = termNoAccents.upper()
        searchCriteria = (term, termNoAccents, termLower, termNoAccentsLower, termCap, termNoAccentsCap, termUpper, termNoAccentsUpper)


        firstLetter = term[0].upper()
        hSuterPage = ""
        hSuterTermTag = False # will contain the title (<a>) tag

        if(firstLetter == "E"):
            hSuterPage = "D"
        elif(firstLetter == "G"):
            hSuterPage = "F"
        elif(firstLetter in ["I","J","K","L","M"]):
            hSuterPage = "H"
        elif(firstLetter in ["O","P"]):
            hSuterPage = "N"
        elif(firstLetter in ["R","S"]):
            hSuterPage = "Q"
        elif(firstLetter in ["U","V","W","X","Y","Z"]):
            hSuterPage = "T"
        else:
            hSuterPage = firstLetter

        # fetch data from website
        url = 'http://henrysuter.ch/glossaires/patois' + hSuterPage + '0.html'

        htmlrequest = requests.get(url)  # TODO - show debug data
        htmldata = htmlrequest.text
        html = BeautifulSoup(htmldata, "html.parser")
        hSuterTermTag = ""

        # search for the term
        all_a =  html.find_all('a')
        for a in all_a:
            if a.string == termCap:
                hSuterTermTag = a
                # TODO: sometimes there are several <a>'s (like: Niolu, Niolue)

                hSuterTermDt = hSuterTermTag.parent
                hSuterTermDd = hSuterTermDt.find_next_sibling('dd')
                # TODO: extract all the things from the <dd> and populate the response fields
                hSuterTermContents = hSuterTermDd.decode_contents()
                hSuterTermContentsArray = re.split(r'<br\s*/?>', hSuterTermContents)

                hSuterTermDefinition = hSuterTermContentsArray[0]
                hSuterTermExampleParser = BeautifulSoup("[br]".join(hSuterTermContentsArray[1:]), "html.parser")
                hSuterTermExample = hSuterTermExampleParser.get_text()

                # save in database if not exists

                connection = sqlite3.connect('db.sqlite3')
                cursor = connection.cursor()

                hSuterSearchQuery = '''SELECT COUNT(id) AS count FROM term_term WHERE url = ? ;'''
                result = cursor.execute(hSuterSearchQuery, (termNoAccentsLower+'--h',))
                hSuterAlreadyExists = result.fetchone()[0]

                if (hSuterAlreadyExists == 0 and termCap != ""):
                    topioInsertQuery = '''INSERT INTO term_term (id,name,type,definition,example,alternative_forms,copyright,origin,date_added,date_edited,key,url)
                          VALUES ( NULL, ?, "", ?,  ?, ?, "henrysuter.ch", ?, DATETIME('now'), DATETIME('now'), 0, ?);'''
                    cursor.execute(topioInsertQuery, (termCap, hSuterTermDefinition, hSuterTermExample, hSuterTermTag.string, url, termNoAccentsLower + "--h"))
                    connection.commit()
                    connection.close()
                else:
                    pass

                response = {
                    "debug": "",
                    "localExists": hSuterAlreadyExists,
                    "url": termNoAccentsLower + "--h",
                    "name": termCap,
                    "type": "",
                    "definition": hSuterTermDefinition,
                    "example": hSuterTermExample,
                    "alternative_forms": hSuterTermTag.string,
                    "copyright": "henrysuter.ch",
                    "origin": url
                }

                return response

        return False

    def onHSuterNames(termUnsafeInput):

        # copy pasted from onTopio()
        term = Search.inputFilter(termUnsafeInput)
        termNoAccents = unidecode(term)
        termLower = term.lower()
        termNoAccentsLower = termNoAccents.lower()
        termCap = term.capitalize()
        termNoAccentsCap = termNoAccents.capitalize()
        termUpper = term.upper()
        termNoAccentsUpper = termNoAccents.upper()
        searchCriteria = (term, termNoAccents, termLower, termNoAccentsLower, termCap, termNoAccentsCap, termUpper, termNoAccentsUpper)

        # TODO 1. get the correct url according to first letter

        secondLetter = term[1].upper()
        firstLetter = term[0].upper()
        firstLetters = term[0].upper() + term[1].lower()

        hsnPage = ""
        hsnTermTag = False  # will contain the title (<a>) tag

        if( firstLetters in ['Aa','Ab','Ac','Ad','Ae','Af','Ag'] ):
            hsnPage = 'A0'
        elif( firstLetters in ['Ai','Aj','Al','Am','An','Ao','Ap'] ):
            hsnPage = 'A1'
        elif (firstLetters in ['Ar','As']):
            hsnPage = 'A2'
        elif (firstLetters in ['At','Au','Av','Ay','Az']):
            hsnPage = 'A3'
        elif (firstLetters in ['Ba']):
            hsnPage = 'B0'
        elif (firstLetters in ['Be']):
            hsnPage = 'B1'
        elif (firstLetters in ['Bi','Bl']):
            hsnPage = 'B2'
        elif (firstLetters in ['Bo']):
            hsnPage = 'B3'
        elif (firstLetters in ['Br','Bu']):
            hsnPage = 'B4'
        elif (firstLetters in ['Ca','Ce']):
            hsnPage = 'C0'
        elif (firstLetters in ['Ch']):
            hsnPage = 'C1'
        elif (firstLetters in ['Ci','Cl']):
            hsnPage = 'C2'
        elif (firstLetters in ['Co']):
            hsnPage = 'C3'
        elif (firstLetters in ['Cp','Cr','Cu','Cy']):
            hsnPage = 'C4'
        elif (firstLetters in ['Da','De']):
            hsnPage = 'D0'
        elif (firstLetters in ['Dg','Di','Dj','Do','Dr','Du','Dy','Dz']):
            hsnPage = 'D1'
        elif (firstLetters in ['Ea','Eb','Ec','Ed']):
            hsnPage = 'E0'
        elif (firstLetters in ['Ef','Eg','Eh','Ei','El','Em','En','Eo','Ep','Eq','Er']):
            hsnPage = 'E1'
        elif (firstLetters in ['Es','Et','Eu','Ev','Ex','Ey','Ez']):
            hsnPage = 'E2'
        elif (firstLetters in ['Fa','Fe','Fi']):
            hsnPage = 'F0'
        elif (firstLetters in ['Fl','Fo','Fr','Fu']):
            hsnPage = 'F1'
        elif (firstLetters in ['Ga','Ge','Gi']):
            hsnPage = 'G0'
        elif (firstLetters in ['Gl','Go','Gr','Gu','Gy']):
            hsnPage = 'G1'
        elif (firstLetter in ['H']):
            hsnPage = 'H0'
        elif (firstLetter in ['I']):
            hsnPage = 'I0'
        elif (firstLetter in ['J']):
            hsnPage = 'J0'
        elif (firstLetter in ['K']):
            hsnPage = 'K0'
        elif (firstLetters in ['La']):
            hsnPage = 'L0'
        elif (firstLetters in ['Le','Lh','Li','Lo','Lu','Ly']):
            hsnPage = 'L1'
        elif (firstLetters in ['Ma']):
            hsnPage = 'M0'
        elif (firstLetters in ['Me','Mi']):
            hsnPage = 'M1'
        elif (firstLetters in ['Mo','Mu','My']):
            hsnPage = 'M2'
        elif (firstLetter in ['N']):
            hsnPage = 'N0'
        elif (firstLetter in ['O']):
            hsnPage = 'O0'
        elif (firstLetters in ['Pa']):
            hsnPage = 'P0'
        elif (firstLetters in ['Pe','Pf','Ph']):
            hsnPage = 'P1'
        elif (firstLetters in ['Pi','Pl']):
            hsnPage = 'P2'
        elif (firstLetters in ['Po','Pr','Pu','Py']):
            hsnPage = 'P3'
        elif (firstLetter in ['Q']):
            hsnPage = 'Q0'
        elif (firstLetters in ['Ra','Rb','Re','Rh']):
            hsnPage = 'R0'
        elif (firstLetters in ['Ri','Ro','Ru']):
            hsnPage = 'R1'
        elif (firstLetters in ['Sa']):
            hsnPage = 'S0'
        elif (firstLetters in ['Sc','Se','Si','So','Sp','St','Su','Sy']):
            hsnPage = 'S1'
        elif (firstLetters in ['Ta','Tc','Te']):
            hsnPage = 'T0'
        elif (firstLetters in ['Th','Ti','To']):
            hsnPage = 'T1'
        elif (firstLetters in ['Tr','Ts','Tu','Ty','Tz']):
            hsnPage = 'T2'
        elif (firstLetter in ['U']):
            hsnPage = 'U0'
        elif (firstLetters in ['Va']):
            hsnPage = 'V0'
        elif (firstLetters in ['Ve']):
            hsnPage = 'V1'
        elif (firstLetters in ['Vi','Vo','Vu','Vy']):
            hsnPage = 'V2'
        elif (firstLetter in ['W']):
            hsnPage = 'W0'
        elif (firstLetter in ['X']):
            hsnPage = 'X0'
        elif (firstLetter in ['Y']):
            hsnPage = 'Y0'
        elif (firstLetter in ['Z']):
            hsnPage = 'Z0'

        url = 'http://henrysuter.ch/glossaires/topo' + hsnPage + '.html'


        htmlrequest = requests.get(url)  # TODO - show debug data
        htmldata = htmlrequest.text
        html = BeautifulSoup(htmldata, "html.parser")
        hsnTermTag = ""

        # search for the term
        all_a = html.find_all('a')
        for a in all_a:
            if a.string == termCap:
                hsnTermTag = a
                # TODO: sometimes there are several <a>'s (like: Niolu, Niolue)

                hsnTermDt = hsnTermTag.parent
                hsnTermDd = hsnTermDt.find_next_sibling('dd')
                # TODO: extract all the things from the <dd> and populate the response fields
                hsnTermContents = hsnTermDd.decode_contents()
                hsnTermContentsArray = re.split(r'<br\s*/?>', hsnTermContents)

                hsnTermDefinition = hsnTermContentsArray[0]
                hsnTermExampleParser = BeautifulSoup("[br]".join(hsnTermContentsArray[1:]), "html.parser")
                hsnTermExample = hsnTermExampleParser.get_text()

                # save in database if not exists

                connection = sqlite3.connect('db.sqlite3')
                cursor = connection.cursor()

                hsnSearchQuery = '''SELECT COUNT(id) AS count FROM term_term WHERE url = ? ;'''
                result = cursor.execute(hsnSearchQuery, (termNoAccentsLower + '--n',))
                hsnAlreadyExists = result.fetchone()[0]

                if (hsnAlreadyExists == 0 and termCap != ""):
                    topioInsertQuery = '''INSERT INTO term_term (id,name,type,definition,example,alternative_forms,copyright,origin,date_added,date_edited,key,url)
                                  VALUES ( NULL, ?, "", ?,  ?, ?, "henrysuter.ch", ?, DATETIME('now'), DATETIME('now'), 0, ?);'''
                    cursor.execute(topioInsertQuery, (
                    termCap, hsnTermDefinition, hsnTermExample, hsnTermTag.string, url,
                    termNoAccentsLower + "--n"))
                    connection.commit()
                    connection.close()
                else:
                    pass

                response = {
                    "debug": "",
                    "localExists": hsnAlreadyExists,
                    "url": termNoAccentsLower + "--n",
                    "name": termCap,
                    "type": "",
                    "definition": hsnTermDefinition,
                    "example": hsnTermExample,
                    "alternative_forms": hsnTermTag.string,
                    "copyright": "henrysuter.ch",
                    "origin": url
                }

                return response

        return False


