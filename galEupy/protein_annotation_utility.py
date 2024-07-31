import logging
from pathlib import Path
from .dbtable_utility import TableStatusID
import re
import csv
# from .BioFile.interproscan_parser import ParseInterproResult
from .directory_utility import ProteinAnnotationFiles
# import time
import threading
from concurrent.futures import ThreadPoolExecutor

_logger = logging.getLogger("galEupy.protein_annotation_utility")


_logger = logging.getLogger("galEupy.protein_annotation_utility")

class TranscriptMap:
    def __init__(self, db_dots, taxonomy_id, org_version):
        self.db_dots = db_dots
        self.taxonomy_id = taxonomy_id
        self.org_version = org_version
        self._transcript_map_dct = self.build_transcript_map_dct()

    def build_transcript_map_dct(self):
        sql_query = f"""select p.name as 'name1',naf.name as 'name2', gi.gene_instance_id from 
        protein p, geneinstance gi, nafeatureimp naf, nasequenceimp na where 
        gi.gene_instance_ID = p.gene_instance_ID and
        naf.na_feature_ID = gi.na_feature_ID and
        naf.feature_type='mRNA' and
        na.na_sequence_id = naf.na_sequence_id and 
        na.taxon_id = {self.taxonomy_id} and
        na.sequence_version = {self.org_version}"""

        transcript_name_dct = {}

        result = self.db_dots.query(sql_query)
        for value in result:
            name1 = value['name1']
            name2 = value['name2']
            gene_instance_id = value['gene_instance_id']

            modified_gene_name = self.modify_transcript_name(name1)
            transcript_name_dct[modified_gene_name] = gene_instance_id
            transcript_name_dct[name2] = gene_instance_id

        return transcript_name_dct

    @staticmethod
    def modify_transcript_name(gene_name):
        match_obj = re.search(r'\S+_(\S+)', gene_name, re.M | re.I)
        modified_transcript_name = match_obj.group(1) if match_obj else gene_name
        return f'{modified_transcript_name}.t1'

    def find_transcript_entry(self, transcript_name):
        protein_instance_id = self._transcript_map_dct.get(transcript_name)
        if not protein_instance_id:
            _logger.error(f'{transcript_name} name is not matching with the database entry')
        return protein_instance_id

class BaseProteinAnnotations(ProteinAnnotationFiles, TableStatusID):
    def __init__(self, db_conn, path_config, org_config, random_str):
        ProteinAnnotationFiles.__init__(self, path_config.upload_dir, random_str)
        TableStatusID.__init__(self, db_conn)
        self.db_conn = db_conn
        self.org_config = org_config
        self.path_config = path_config
        self.random_str = random_str

    @property
    def protein_file(self):
        protein_path = Path(self.path_config.upload_dir).joinpath(self.random_str + '.aa')
        _logger.debug(f"protein_path: {protein_path}")
        return protein_path

    def create_protein_file(self, taxonomy_id, org_version):
        _logger.debug("Creating protein file to store the protein information")

        query = f"""select nf.feature_type, nf.name, p.description, p.gene_instance_id, p.sequence from 
        nasequenceimp ns, nafeatureimp nf, geneinstance gi, protein p where ns.taxon_id = {taxonomy_id}
        and ns.sequence_version = {org_version} and ns.sequence_type_id = 6 and nf.na_sequence_id = ns.na_sequence_id
        and nf.feature_type = 'mRNA' and gi.na_feature_id = nf.na_feature_id and  
        p.gene_instance_id = gi.gene_instance_id"""

        result = self.db_dots.query(query)
        with open(self.protein_file, 'w') as fh:
            for value in result:
                header_text = f">{value['name']};gi='{value['gene_instance_id']}'\n{value['sequence']}\n"
                fh.write(header_text)

    @property
    def table_status_dct(self):
        table_info_dct = self.get_protein_feature_table_status()
        return table_info_dct

class ProteinAnnotations(BaseProteinAnnotations, TranscriptMap):
    def __init__(self, db_conn, path_config, org_config, random_str, taxonomy_id, org_version):
        BaseProteinAnnotations.__init__(self, db_conn, path_config, org_config, random_str)
        TranscriptMap.__init__(self, db_conn, taxonomy_id, org_version)
        self.taxonomy_id = taxonomy_id  # Ensure these lines are present
        self.org_version = org_version

    def parse_eggnog_result(self, parsed_file):
        _logger.info("Parsing EGGNOG data: Initiated")
        _logger.info(f"taxonomy id is {self.taxonomy_id}")
        
        eggnog_row_id = self.table_status_dct['protein_instance_feature_ID']
        field_list = ['Description', 'COG_category', 'GOs', 'EC', 'KEGG_ko', 'KEGG_Pathway',
                    'KEGG_Module', 'KEGG_Reaction', 'KEGG_rclass', 'BRITE', 'KEGG_TC', 'PFAMs']
        
        with open(parsed_file, 'r') as file:
            reader = csv.reader(file, delimiter='\t')
            header_indices = {}
            buffer = []

            for idx, row in enumerate(reader):
                if row[0].startswith('##'):
                    continue
                if row[0].startswith('#'):
                    header = row
                    header_indices = {name: index for index, name in enumerate(header) if name in field_list}
                    for field_name in field_list:
                        if field_name not in header_indices:
                            _logger.error(f"{field_name} doesn't exist")
                    continue

                if header_indices:
                    protein_instance_id = self.find_transcript_entry(row[0])
                    feature_name = "EGGNOG"
                    subclass_dct = {}

                    desc = row[header_indices.get('Description', '')]
                    cog_cat = row[header_indices.get('COG_category', '')]
                    gos = row[header_indices.get('GOs', '')]
                    kegg_ko = row[header_indices.get('KEGG_ko', '')]
                    pfams = row[header_indices.get('PFAMs', '')]

                    if desc != '-':
                        subclass_dct['COG'] = [desc, cog_cat] + [None] * 10
                    if gos != '-':
                        subclass_dct['GO'] = [None, None, gos] + [None] * 9
                    if kegg_ko != '-':
                        kegg_values = [row[header_indices.get(key, '')] if row[header_indices.get(key, '')] != '-' else None for key in field_list[3:]]
                        subclass_dct['KEGG'] = [None, None, None] + kegg_values
                    if pfams != '-':
                        subclass_dct['Pfam'] = [None] * 11 + [pfams]

                    for subclass_view, data_list in subclass_dct.items():
                        eggnog_row_id += 1
                        mapping_list = [eggnog_row_id, protein_instance_id, feature_name, subclass_view, self.taxonomy_id, self.org_version]
                        columns_data = mapping_list + data_list
                        buffer.append("\t".join(map(str, columns_data)) + '\n')

        with open(self.eggnog, 'w') as eggnog_write_fh:
            eggnog_write_fh.write("".join(buffer))

        _logger.info("Parsing EGGNOG data: Complete")


    def upload_eggnog_data(self):
        
        _logger.info(f"Parsing EGGNOG data: Initiated with taxonomy_id={self.taxonomy_id}, org_version={self.org_version}")
        _logger.info(f"Uploading EGGNOG data from {self.eggnog}")
        column_list = ['protein_instance_feature_ID', 'protein_instance_ID', 'feature_name', 'subclass_view', 'taxonomy_id', 'org_version',
                    'domain_name', 'prediction_id', 'go_id',
                    'text1', 'text2', 'text3', 'text4', 'text5', 'text6', 'text7', 'text8', 'text9']

        query = f"""LOAD DATA LOCAL INFILE '{self.eggnog}' INTO TABLE proteininstancefeature FIELDS 
        TERMINATED BY '\t' OPTIONALLY ENCLOSED BY '"' LINES 
        TERMINATED BY '\n' ({",".join(column_list) })"""

        self.db_conn.insert(query)
