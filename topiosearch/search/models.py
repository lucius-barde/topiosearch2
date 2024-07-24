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

        # TODO - crawl topio database
        url = 'https://www.topio.ch/dico.php'
        htmlrequest = requests.get(url) # TODO - show debug data
        htmldata = htmlrequest.text

        html = BeautifulSoup(htmldata, "html.parser")
        content = html.find('div', id = 'contenu')
        table = html.find('table')
        rows = table.find_all('tr')

        topioterms = []
        for index, row in enumerate(rows):
            if index > 2:
                first_td = row.find('td')
                if first_td:
                    topioterm = first_td.get_text()
                    topioterms.append(topioterm)
                    if(topioterm in searchCriteria):
                        name = topioterm

        return {
            "search_criteria":searchCriteria,
            "url":termNoAccentsLower,
            "name": name,
            "type":"",
            "definition":"",
            "example":"",
            "alternative_forms":"",
            "copyright":"",
            "origin":""
        }




'''
Scratchpad - conversion de PHP vers Python

$app->get('/topiosearch/topio[/]', function (Request $q, Response $r, array $args) {

    $validate = new Validator($this->db);
    $blobModel = new Blob($this->db);
    $dictionaryModel = new TopioSearch();

    $keepAccents = true;
    $term = $validate->toFileName($_GET['term'],$keepAccents);
    unset($keepAccents);

    $term = str_replace('_', ' ', $term);
    $term = ucfirst($term);

    $getTopioWord = $this->db->prepare('SELECT * FROM `api_oppidumweb_public` WHERE url = "topiosearch--topio--'.$term.'" AND edited > DATE_SUB(NOW(), INTERVAL 1 MONTH) LIMIT 1;');
    $getTopioWord->execute();
    $cachefile = $getTopioWord->fetch();

    if(empty($cachefile)){
        //topio remote

        $url = 'https://www.topio.ch/dico.php';

        //fetch data from website
        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL, $url);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
        $dictHTML = curl_exec($ch);
        curl_close($ch);

        $termJSON = $dictionaryModel->parseFileTopio($dictHTML,$term);

        if($termJSON['status'] == "error"){
            return $r->withStatus(404)->withJson(['status'=>'error','url'=>$url,'statusText'=>$termJSON['statusText']]);
        }elseif(!$termJSON){
            return $r->withStatus(404)->withJson(['status'=>'error', 'url'=>$url, 'term'=>$term, 'statusText'=>'This keyword doesn\'t match with any word in the database']);
        }else{

            $urlForApi = 'topiosearch--topio--';
            $termJSON['params']['copyright'] = '&copy; <a href="https://www.topio.ch">topio.ch</a>';

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

        //topio local
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

'''