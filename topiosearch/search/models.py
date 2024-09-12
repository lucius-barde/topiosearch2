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

        topioSearchQuery = '''SELECT COUNT(id) AS count FROM term_term WHERE url = ? AND copyright = "topio.ch";'''
        result = cursor.execute(topioSearchQuery, (termNoAccentsLower,))
        topioAlreadyExists = result.fetchone()[0]

        # TODO: solve the integrity problem when reloading a word that is already in database.
        if(topioAlreadyExists == 0 and name != ""):
            topioInsertQuery = '''INSERT INTO term_term (id,name,type,definition,example,alternative_forms,copyright,origin,date_added,date_edited,key,url)
            VALUES ( NULL, ?, "", ?,  ?, "", "topio.ch", "https://topio.ch/dico.php", DATETIME('now'), DATETIME('now'), 0, ?);'''
            cursor.execute(topioInsertQuery, (name, definition, example, termNoAccentsLower+"--t"))
            connection.commit()
            connection.close()
        else:
            pass


        response = {
            "debugTopioAlreadyExists":topioAlreadyExists,
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
                hSuterTermExampleParser = BeautifulSoup(hSuterTermContentsArray[1], "html.parser")
                hSuterTermExample = hSuterTermExampleParser.get_text()


                response = {
                    "debug": hSuterTermContentsArray,
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
        # TODO 2. crawling html and get all the things
        # TODO 3. dispatch all the things in variables

'''
Scratchpad - conversion de PHP vers Python - copier coller le code PHP ici.

$app->get('/topiosearch/hsuter[/]', function (Request $q, Response $r, array $args) {
	
	$validate = new Validator($this->db);
	$dictionaryModel = new TopioSearch();
    $blobModel = new Blob($this->db);
    
    $keepAccents = true;
	$term = $validate->toFileName($_GET['term'],$keepAccents);
    unset($keepAccents);
    $term = ucfirst($term);

//	$cachefile = ABSDIR.'/cache/topiosearch/'.$term[0].'/topiosearch--hsuter--'.$term.'.json';
  

    $getHsuterWord = $this->db->prepare('SELECT * FROM `api_oppidumweb_public` WHERE url = "topiosearch--hsuter--'.$term.'" AND edited > DATE_SUB(NOW(), INTERVAL 1 MONTH) LIMIT 1;');
    $getHsuterWord->execute();
    $cachefile = $getHsuterWord->fetch();


	if(empty($cachefile)){

        //hsuter remote

        $firstLetter = strtoupper($term[0]);
        
        //firstletter is defined on henrysuter.ch:
        switch($firstLetter){
            case "E": $firstLetter = "D"; break;
            case "G": $firstLetter = "F"; break;
            case "I":
            case "J":
            case "K":
            case "L":
            case "M": $firstLetter = "H"; break;
            case "O":
            case "P": $firstLetter = "N"; break;
            case "R":
            case "S": $firstLetter = "Q"; break;
            case "U":
            case "V":
            case "W":
            case "X":
            case "Y":
            case "Z": $firstLetter = "T"; break;
            
        }
        
        $url = 'http://henrysuter.ch/glossaires/patois'.$firstLetter.'0.html';
            
        //fetch data from website    
        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL, $url);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
        $dictHTML = curl_exec($ch);
        curl_close($ch);     
        $termJSON = $dictionaryModel->parseFileHSuter($dictHTML,$term);

        if(!$termJSON){
            return $r->withStatus(404)->withJson(['status'=>'error', 'term'=>$term, 'url'=>$url,'statusText'=>'This keyword doesn\'t match with any word in the database']);
        }else{


            $urlForApi = 'topiosearch--hsuter--';
            
            $termJSON['params']['copyright'] = '&copy; <a href="http://www.henrysuter.ch">henrysuter.ch</a>';
            $termJSON['params']['origin'] = $url;
            $urlForApi .= $termJSON['params']['term'];
            $termJSON['url'] = $urlForApi;

            /*if(!is_dir(ABSDIR.'/cache/topiosearch/'.$termJSON['params']['term'][0])){
                mkdir(ABSDIR.'/cache/topiosearch/'.$termJSON['params']['term'][0]);
                if(!is_dir(ABSDIR.'/cache/topiosearch/'.$termJSON['params']['term'][0])){
                    return $r->withStatus(500)->withJson(['status'=>'error','statusText'=>'Unable to create the cache folder, please check the permissions on the server', 'term' => $term]);
                }
            }*/

            $termJSON['edited'] = date('Y-m-d H:i:s');
            $termJSON['lang'] = "fr";
            $termJSON['parent'] = 0;
            $termJSON['status'] = 1;

            ksort($termJSON);
            ksort($termJSON['params']);

            
            //Save in topio database - Params
            $termJSON['type'] = "topiosearch";
            $termJSON['name'] = $termJSON['url'];
            $termJSON['content'] = $termJSON['params']['term'];

            $insertEntry = $blobModel->addBlob($termJSON); 
            $termJSON['params']['db_insert_callback'] = $insertEntry;
            $termJSON['params']['source'] = "remote";

            
            return $r->withStatus(200)->withJson($termJSON);

        }


    }else{

        //hsuter local
        $localdata = $cachefile;
        if(!!$localdata){
            $localdata['params'] = json_decode($localdata['params'],true);
            $localdata['params']['source'] = 'local';
            $localdata['params']['fetchDateDiff'] = time() - $localdata['edited'];
            return $r->withStatus(200)->withJson($localdata);
        }else{
            return $r->withStatus(500)->withJson(['status'=>'error','statusText'=>'Error: this entry exists in the dictionary, but the content is corrupted.', 'term' => $term]);
        }

    }

	
})->setName('topioSearchHsuter');


$app->get('/topiosearch/hsuternames[/]', function (Request $q, Response $r, array $args) {
	
	$validate = new Validator($this->db);
	$dictionaryModel = new TopioSearch();
    $blobModel = new Blob($this->db);
    
    $keepAccents = true;
	$term = $validate->toFileName($_GET['term'],$keepAccents);
    unset($keepAccents);
    $term = ucfirst($term);
	

//    $cachefile = ABSDIR.'/cache/topiosearch/'.$term[0].'/topiosearch--hsuternames--'.$term.'.json';
	
        
    $getHsuterNamesWord = $this->db->prepare('SELECT * FROM `api_oppidumweb_public` WHERE url = "topiosearch--hsuternames--'.$term.'" AND edited > DATE_SUB(NOW(), INTERVAL 1 MONTH) LIMIT 1;');
    $getHsuterNamesWord->execute();
    $cachefile = $getHsuterNamesWord->fetch();

	if(empty($cachefile)){
       
        //hsuternames remote
        $secondLetter = strtoupper($term[1]);
        $firstLetter = strtoupper($term[0]);
        $firstLetters = strtoupper($term[0]).strtolower($term[1]);
        
        //firstletter is defined on henrysuter.ch:
        if(in_array($firstLetters,['Aa','Ab','Ac','Ad','Ae','Af','Ag'])){$page = 'A0';}
        elseif(in_array($firstLetters,['Ai','Aj','Al','Am','An','Ao','Ap'])){$page = 'A1';}
        elseif(in_array($firstLetters,['Ar','As'])){$page = 'A2';}
        elseif(in_array($firstLetters,['At','Au','Av','Ay','Az'])){$page = 'A3';}
        
        elseif(in_array($firstLetters,['Ba'])){$page = 'B0';}
        elseif(in_array($firstLetters,['Be'])){$page = 'B1';}
        elseif(in_array($firstLetters,['Bi','Bl'])){$page = 'B2';}
        elseif(in_array($firstLetters,['Bo'])){$page = 'B3';}
        elseif(in_array($firstLetters,['Br','Bu'])){$page = 'B4';}

        elseif(in_array($firstLetters,['Ca','Ce'])){$page = 'C0';}
        elseif(in_array($firstLetters,['Ch'])){$page = 'C1';}
        elseif(in_array($firstLetters,['Ci','Cl'])){$page = 'C2';}
        elseif(in_array($firstLetters,['Co'])){$page = 'C3';}
        elseif(in_array($firstLetters,['Cp','Cr','Cu','Cy'])){$page = 'C4';}
        
        elseif(in_array($firstLetters,['Da','De'])){$page = 'D0';}
        elseif(in_array($firstLetters,['Dg','Di','Dj','Do','Dr','Du','Dy','Dz'])){$page = 'D1';}
        
        elseif(in_array($firstLetters,['Ea','Eb','Ec','Ed'])){$page = 'E0';}
        elseif(in_array($firstLetters,['Ef','Eg','Eh','Ei','El','Em','En','Eo','Ep','Eq','Er'])){$page = 'E1';}
        elseif(in_array($firstLetters,['Es','Et','Eu','Ev','Ex','Ey','Ez'])){$page = 'E2';}
        
        elseif(in_array($firstLetters,['Fa','Fe','Fi'])){$page = 'F0';}
        elseif(in_array($firstLetters,['Fl','Fo','Fr','Fu'])){$page = 'F1';}

        elseif(in_array($firstLetters,['Ga','Ge','Gi'])){$page = 'G0';}
        elseif(in_array($firstLetters,['Gl','Go','Gr','Gu','Gy'])){$page = 'G1';}
        
        elseif(in_array($firstLetter,['H'])){$page = 'H0';}

        elseif(in_array($firstLetter,['I'])){$page = 'I0';}
        
        elseif(in_array($firstLetter,['J'])){$page = 'J0';}

        elseif(in_array($firstLetter,['K'])){$page = 'K0';}

        elseif(in_array($firstLetters,['La'])){$page = 'L0';}
        elseif(in_array($firstLetters,['Le','Lh','Li','Lo','Lu','Ly'])){$page = 'L1';}

        elseif(in_array($firstLetters,['Ma'])){$page = 'M0';}
        elseif(in_array($firstLetters,['Me','Mi'])){$page = 'M1';}
        elseif(in_array($firstLetters,['Mo','Mu','My'])){$page = 'M2';}
        
        elseif(in_array($firstLetter,['N'])){$page = 'N0';}

        elseif(in_array($firstLetter,['O'])){$page = 'O0';}
        
        elseif(in_array($firstLetters,['Pa'])){$page = 'P0';}
        elseif(in_array($firstLetters,['Pe','Pf','Ph'])){$page = 'P1';}
        elseif(in_array($firstLetters,['Pi','Pl'])){$page = 'P2';}
        elseif(in_array($firstLetters,['Po','Pr','Pu','Py'])){$page = 'P3';}
        
        elseif(in_array($firstLetter,['Q'])){$page = 'Q0';}
        
        elseif(in_array($firstLetters,['Ra','Rb','Re','Rh'])){$page = 'R0';}
        elseif(in_array($firstLetters,['Ri','Ro','Ru'])){$page = 'R1';}
        
        elseif(in_array($firstLetters,['Sa'])){$page = 'S0';}
        elseif(in_array($firstLetters,['Sc','Se','Si','So','Sp','St','Su','Sy'])){$page = 'S1';}

        elseif(in_array($firstLetters,['Ta','Tc','Te'])){$page = 'T0';}
        elseif(in_array($firstLetters,['Th','Ti','To'])){$page = 'T1';}
        elseif(in_array($firstLetters,['Tr','Ts','Tu','Ty','Tz'])){$page = 'T2';}

        elseif(in_array($firstLetter,['U'])){$page = 'U0';}
        
        elseif(in_array($firstLetters,['Va'])){$page = 'V0';}
        elseif(in_array($firstLetters,['Ve'])){$page = 'V1';}
        elseif(in_array($firstLetters,['Vi','Vo','Vu','Vy'])){$page = 'V2';}
        
        elseif(in_array($firstLetter,['W'])){$page = 'W0';}
        elseif(in_array($firstLetter,['X'])){$page = 'X0';}
        elseif(in_array($firstLetter,['Y'])){$page = 'Y0';}
        elseif(in_array($firstLetter,['Z'])){$page = 'Z0';}


        $url = 'http://henrysuter.ch/glossaires/topo'.$page.'.html';
            
        //fetch data from website    
        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL, $url);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
        $dictHTML = curl_exec($ch);
        curl_close($ch);     
        
        $termJSON = $dictionaryModel->parseFileHSuter($dictHTML,$term);
        
        if(!$termJSON){
            return $r->withStatus(404)->withJson(['status'=>'error', 'term'=>$term, 'url'=>$url,'statusText'=>'This keyword doesn\'t match with any word in the database']);
        }else{


            $urlForApi = 'topiosearch--hsuternames--';
            
            $termJSON['params']['copyright'] = '&copy; <a href="http://www.henrysuter.ch">henrysuter.ch</a>';
            $termJSON['params']['origin'] = $url;
            $urlForApi .= $termJSON['params']['term'];
            $termJSON['url'] = $urlForApi;

            /*if(!is_dir(ABSDIR.'/cache/topiosearch/'.$termJSON['params']['term'][0])){
                mkdir(ABSDIR.'/cache/topiosearch/'.$termJSON['params']['term'][0]);
                if(!is_dir(ABSDIR.'/cache/topiosearch/'.$termJSON['params']['term'][0])){
                    return $r->withStatus(500)->withJson(['status'=>'error','statusText'=>'Unable to create the cache folder, please check the permissions on the server', 'term' => $term]);
                }
            }*/
            $termJSON['edited'] = date('Y-m-d H:i:s');
            $termJSON['lang'] = "fr";
            $termJSON['parent'] = 0;
            $termJSON['status'] = 1;

            ksort($termJSON);
            ksort($termJSON['params']);

            
            //Save in topio database - Params
            $termJSON['type'] = "topiosearch";
            $termJSON['name'] = $termJSON['url'];
            $termJSON['content'] = $termJSON['params']['term'];

            $insertEntry = $blobModel->addBlob($termJSON); 
            $termJSON['params']['db_insert_callback'] = $insertEntry;
            $termJSON['params']['source'] = "remote";

            

            return $r->withStatus(200)->withJson($termJSON);
        }

    }else{
        
        //hsuternames local
        $localdata = $cachefile;
        if(!!$localdata){
            $localdata['params'] = json_decode($localdata['params'],true);
            $localdata['params']['source'] = 'local';
            $localdata['params']['fetchDateDiff'] = time() - $localdata['edited'];
            return $r->withStatus(200)->withJson($localdata);
        }else{
            return $r->withStatus(500)->withJson(['status'=>'error','statusText'=>'Error: this entry exists in the dictionary, but the content is corrupted.', 'term' => $term]);
        }


    }

        
})->setName('topioSearchHsuterNames');

'''