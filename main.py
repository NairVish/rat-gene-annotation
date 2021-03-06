import csv
import time
import requests
import argparse
from sys import exit
from typing import List, Optional, Tuple, Any
from bs4 import BeautifulSoup


def get_ensembl_data(transcript_id: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    gene_name, gene_desc, gene_type, strand = None, None, None, None
    transcript_id = transcript_id.split(".")[0]

    FETCH_URL = f"https://rest.ensembl.org/lookup/id/{transcript_id}"
    r = requests.get(FETCH_URL, headers={ "Content-Type" : "application/json"})
    
    try:
        parent_id = r.json()["Parent"]
    except KeyError:
        return gene_name, gene_desc, gene_type, strand

    FETCH_URL = f"https://rest.ensembl.org/lookup/id/{parent_id}"
    r = requests.get(FETCH_URL, headers={ "Content-Type" : "application/json"})
    j = r.json()

    try:
        gene_name = j["display_name"]
        gene_desc = j["description"]
        gene_type = j["biotype"]
        strand = j["strand"]
    except KeyError as e:
        pass

    return gene_name, gene_desc, gene_type, strand


def get_genbank_data(transcript_id: str) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    gene_name, gene_desc, gene_type, strand = None, None, None, None
    ID_FETCH_URL = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?dbfrom=nuccore&db=gene&term={transcript_id}&retmode=json&api_key={args.api_key}"
    id_json = requests.get(ID_FETCH_URL).json()

    try:
        gid = id_json["esearchresult"]["idlist"][0]
    except (KeyError, IndexError):
        return gene_name, gene_desc, gene_type, strand

    time.sleep(0.04)  # rate limit

    GENE_FETCH_URL = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=gene&id={gid}&retmode=xml&api_key={args.api_key}"
    gene_fetch_results = requests.get(GENE_FETCH_URL).text

    soup = BeautifulSoup(gene_fetch_results, features='xml')

    try:
        gene_name = soup.findAll("Gene-ref_locus")[0].get_text()
        gene_desc = soup.findAll("Gene-ref_desc")[0].get_text()
        gene_type = soup.findAll("Entrezgene_type")[0]["value"]
        strand = soup.findAll("Na-strand")[0]["value"]
    except (KeyError, IndexError) as e:
        pass

    return gene_name, gene_desc, gene_type, strand


def get_data_using_row(row: List[Any]) -> Tuple[Optional[bool], str, List[Any]]:
    try:
        if " of " in row[12]:
            row[11] = row[11] + row[12]
            del row[12]

        transcript_id = row[18]

        func = get_ensembl_data if transcript_id.startswith("ENST") else get_genbank_data
        gene_name, gene_desc, gene_type, strand = func(transcript_id)

        time.sleep(0.04) # rate limit

        row += [gene_name, gene_desc, strand, gene_type]
        return (True, gene_name, row)
    except KeyboardInterrupt:
        return (None, "", row)
    except Exception as e:
        # row.append(f"No result.")
        return (False, "", row)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--input', action='store', type=str, required=True)
    parser.add_argument('-o', '--output', action='store', type=str, required=True)
    parser.add_argument('-k', '--api_key', action='store', type=str, required=True)
    parser.add_argument('-c', '--max_count', action='store', type=int, default=-1)
    parser.add_argument('-s', '--start', action='store', type=int, default=-1)

    args = parser.parse_args()

    # read input file and get header
    input_csv_file = open(args.input, 'r')
    input_csv_data_reader = csv.reader(input_csv_file, delimiter=",")
    csv_header = next(input_csv_data_reader)  + ["Gene name", "Gene description", "Strand", "Gene type"]

    # get output file ready
    output_csv_file = open(args.output, "w", newline='')
    output_csv_data_writer = csv.writer(output_csv_file, delimiter=',')
    output_csv_data_writer.writerow(csv_header)

    rows = []
    curr_count = 0

    for row in input_csv_data_reader:
        curr_count += 1
        if args.start != -1 and curr_count < args.start:
            print(f"Skipping row #{curr_count}.")
            continue

        (ret_status, gene_name, ret_row) = get_data_using_row(row)
        
        if ret_status == False:
            print(f"Processing FAILED for #{curr_count}.")
        elif ret_status is None:
            print("KeyboardInterrupt called.")
            exit(0)
        else: # ret_status == True
            print(f"Processing (#{curr_count}) -- {row[18]} / {gene_name}")
            
        output_csv_data_writer.writerow(ret_row)
        # output_csv_file.flush()
        
        if args.max_count != -1 and curr_count >= args.max_count:
            break
    
    # close the input and output files
    input_csv_file.close()
    output_csv_file.close()
