import csv
import time
import requests
import argparse
from sys import exit
from typing import List, Optional, Tuple, Any
from bs4 import BeautifulSoup

def get_data_using_row(row: List[Any]) -> Tuple[Optional[bool], str, List[Any]]:
    try:
        if " of " in row[12]:
            row[11] = row[11] + row[12]
            del row[12]

        transcript_id = row[18]
        if transcript_id.startswith("ENST"):
            transcript_id = transcript_id.split(".")[0]
            FETCH_URL = f"https://rest.ensembl.org/lookup/id/{transcript_id}"
            r = requests.get(FETCH_URL, headers={ "Content-Type" : "application/json"})
            parent_id = r.json()["Parent"]

            FETCH_URL = f"https://rest.ensembl.org/lookup/id/{parent_id}"
            r = requests.get(FETCH_URL, headers={ "Content-Type" : "application/json"})
            j = r.json()

            gene_name = j["display_name"]
            gene_desc = j["description"]
            gene_type = j["biotype"]
            strand = j["strand"]

        else: # transcript_id.startswith("NM_"):
            ID_FETCH_URL = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?dbfrom=nuccore&db=gene&term={transcript_id}&retmode=json&api_key={args.api_key}"
            id_json = requests.get(ID_FETCH_URL).json()
            # print(id_json)
            gid = id_json["esearchresult"]["idlist"][0]

            time.sleep(0.04)  # rate limit

            GENE_FETCH_URL = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=gene&id={gid}&retmode=xml&api_key={API_KEY}"
            gene_fetch_results = requests.get(GENE_FETCH_URL).text

            soup = BeautifulSoup(gene_fetch_results, features='xml')

            gene_name = soup.findAll("Gene-ref_locus")[0].get_text()
            gene_desc = soup.findAll("Gene-ref_desc")[0].get_text()
            gene_type = soup.findAll("Entrezgene_type")[0]["value"]
            strand = soup.findAll("Na-strand")[0]["value"]

        time.sleep(0.04)
        
        row.append(gene_name)
        row.append(gene_desc)
        row.append(strand)
        row.append(gene_type)
        return (True, gene_name, row)
    except KeyboardInterrupt:
        return (None, "", row)
    except Exception as e:
        row.append(f"No result ({e.__class__.__name__}).")
        return (False, "", row)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', action='store', type=str, required=True)
    parser.add_argument('-o', '--output', action='store', type=str, required=True)
    parser.add_argument('-k', '--api_key', action='store', type=str, required=True)
    parser.add_argument('-c', '--max_count', action='store', type=int, default=-1)

    args = parser.parse_args()

    # read file and skip header
    csv_file = open(args.input, 'r')
    csv_data_reader = csv.reader(csv_file, delimiter=",")
    csv_header = next(csv_data_reader)

    rows = []
    curr_count = 0
    header_complete = False

    for row in csv_data_reader:
        if not header_complete:
            csv_header = csv_header + ["Gene name", "Gene description", "Strand", "Gene type"]
            header_complete = True
        
        (ret_status, gene_name, ret_row) = get_data_using_row(row)
        curr_count += 1
        
        if ret_status == False:
            print(f"Processing FAILED for #{curr_count}.")
            # rows.append(ret_row)
        elif ret_status is None:
            print("KeyboardInterrupt called.")
            exit(0)
        else: # ret_status == True
            print(f"Processing (#{curr_count}) -- {row[18]} / {gene_name}")
            rows.append(ret_row)
        
        if args.max_count != -1 and curr_count >= args.max_count:
            break
    
    # close the input file
    csv_file.close()

    # write everything into the output file
    with open(args.output, "w+") as output_csv_file:
        csv_writer = csv.writer(output_csv_file, delimiter=',')
        csv_writer.writerow(csv_header)
        csv_writer.writerows(rows)
