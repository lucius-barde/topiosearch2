from django.db import models
from unidecode import unidecode
from bs4 import BeautifulSoup
import requests

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

        return {
            "search_criteria":searchCriteria,
            "url":termNoAccentsLower,
            "name": name,
            "type":"", # not present in topio data
            "definition":definition,
            "example":example,
            "alternative_forms":"", # TODO: can be done in topio with splitting on " - " as in: "Toyet - Toyotse"
            "copyright":"topio.ch",
            "origin":"https://www.topio.ch/dico.php"
        }




'''
Scratchpad - conversion de PHP vers Python - copier coller le code PHP ici.


'''