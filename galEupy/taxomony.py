import re
import logging
_logger = logging.getLogger("galEupy.taxonomy")


class OrganismName:
    def __init__(self, org_name, org_version=1 ):
        """
        class constructor for the Organism name
        parameters
        -------------
        org_name: str
            Full name of the organism
        org_version: str
            Version string
        """
        # _logger.info(f"Organism: {org_name}, Version: {org_version}")
        self.org_name = org_name
        self.org_version = org_version
        self.org_arr = re.split(r'\s', org_name)
        self.species = "{} {}".format(self.org_arr[0], self.org_arr[1])

    @property
    def prefix(self):
        """
        Returns the organism prefix
        Returns
        --------
        gene_name: str
            Organism name prefix
        """
        org = re.split(r'\s+', self.org_name)
        if len(org) >= 2:
            species = org[0]
            genus = org[1]

            taxonomy_detail = ''
            if len(org) == 4:
                taxonomy_detail = org[2] + org[3]
            elif len(org) == 3:
                taxonomy_detail = org[2]

            taxonomy_detail = re.sub(r'\s+', "", taxonomy_detail)
            organism_prefix = species[:3] + genus[:4] + "_" + taxonomy_detail
            return organism_prefix

    @property
    def org_short_name(self):
        """
        Return short organism name with version number
        Returns
        ----------
        org_name: str
            short organism name with organism version
        """
        if self.prefix.endswith('_'):
            org_name = f'{self.prefix}v{self.org_version}'
        else:
            org_name = f'{self.prefix}_v{self.org_version}' '{}_v{}'
        return org_name


class CommonOrganismInfo(OrganismName):
    def __init__(self, db_sres, org_name, org_version=1):
        OrganismName.__init__(self, org_name, org_version)
        self.db_sres = db_sres

    @property
    def taxonomy_id_sres(self):
        sql_query = f"SELECT ncbi_taxon_ID FROM taxon where TAXON_NAME = '{self.org_name}'"
        data = self.db_sres.query_one(sql_query)
        if data is not None:
            taxonomy_id = data['ncbi_taxon_ID']
            if taxonomy_id is None:
                _logger.error(f"input name: {self.org_name}, Error : Organism Name has issue ")
            return taxonomy_id

    def taxon_entries(self):
        _logger.info(f'Checking similar organism entries with {self.species}')
        sql_query = f"SELECT ncbi_taxon_ID, taxon_name FROM taxon where TAXON_NAME like '{self.species}%'"
        result = self.db_sres.query(sql_query)
        if len(result) > 0:
            result_str = "\n".join(f"{d['ncbi_taxon_ID']}\t{d['taxon_name']}" for d in result)
            _logger.info(f'Entries available:\nncbi_taxon_ID\ttaxon_name\n{result_str}')
        else:
            if len(self.org_arr) > 1 and len(self.org_arr[1]) >= 2:
                short_org_name = f'{self.org_arr[0]} {self.org_arr[1][0:2]}'
                _logger.info(f'There is no entry with species name. Listing organisms with {short_org_name}')

                sql_query = f"SELECT ncbi_taxon_ID, taxon_name FROM taxon where taxon_name like '{short_org_name}%'"
                result = self.db_sres.query(sql_query)
                if len(result) > 0:
                    result_str = "\n".join(f"{d['ncbi_taxon_ID']}\t{d['taxon_name']}" for d in result)
                    _logger.info(f'Entries available: \nncbi_taxon_ID\ttaxon_name\n{result_str}')

                else:
                    _logger.info(f'No record found with: {short_org_name}%')
        return False

    def taxonomy_hierarchy(self):
        query = f"""SELECT ncbi_taxon_ID, parent_ID, taxon_name, taxon_strain, `rank`  FROM taxon 
        where taxon_name = '{self.org_name}'"""

        taxonomy_dct = {}
        result = self.db_sres.query(query)
        for i, value in enumerate(result):
            if value['rank'] in ["species", "subspecies", "strain"]:
                taxonomy_dct['taxon_ID'] = value['ncbi_taxon_ID']
                taxonomy_id, parent_id, name, rank = self.fetch_taxonomy_info_by_id(value['parent_ID'])
                taxonomy_dct[rank] = name
                while taxonomy_id != parent_id:
                    taxonomy_id, parent_id, name, rank = self.fetch_taxonomy_info_by_id(parent_id)
                    taxonomy_dct[rank] = name
            elif value['rank'] == 'no rank':
                taxonomy_id, parent_id, name, rank = self.fetch_taxonomy_info_by_id(value['parent_ID'])
                if rank == 'species':
                    taxonomy_dct['taxon_ID'] = value['ncbi_taxon_ID']
                    taxonomy_dct[rank] = name
                    while taxonomy_id != parent_id:
                        taxonomy_id, parent_id, name, rank = self.fetch_taxonomy_info_by_id(parent_id)
                        taxonomy_dct[rank] = name
                else:
                    _logger.error("Please check the organism name")
            elif value['rank'] != '':
                _logger.error("Please check the organism name")
        return taxonomy_dct

    def fetch_taxonomy_info_by_id(self, taxonomy_id):
        child_query = f"""SELECT ncbi_taxon_ID, parent_ID, taxon_name, taxon_strain, `rank`  FROM taxon WHERE 
        ncbi_taxon_ID = {taxonomy_id}"""
        result = self.db_sres.query(child_query)
        for i, value in enumerate(result):
            return value['ncbi_taxon_ID'], value['parent_ID'], value['taxon_name'], value['rank']

    def find_organism_type(self, taxonomy_dct):
        """
        This function finds organism type i.e. euk/gram+/gram-
        :return euk/gram+/gram-:
        """
        organism_type = 'euk'
        if 'superkingdom' in taxonomy_dct:
            if taxonomy_dct['superkingdom'] == 'Bacteria':
                organism_type = 'gram+'
                query = f"select strain_type from gramstrain where organism like '%{self.org_name}%'"
                result = self.db_sres.query_one(query)
                if result is not None:
                    strain_type = result['strain_type']
                    if strain_type == 'Gram negative':
                        organism_type = 'gram-'
                    else:
                        organism_type = "gram+"
            else:
                organism_type = 'euk'

            return organism_type
        else:
            return organism_type


class DotsOrganism(OrganismName):
    def __init__(self, db_dots, org_name, org_version=1):
        OrganismName.__init__(self, org_name, org_version)
        self.db_dots = db_dots

    @property
    def taxonomy_hierarchy_dots(self):
        sql_query = f"select * from organism where taxon_name = '{self.org_name}' and strain_number = {self.org_version}"
        taxonomy_dct = {}

        result = self.db_dots.query_one(sql_query)
        if result is not None:
            taxonomy_dct = result
        taxonomy_dct = NoneDict(taxonomy_dct)
        return taxonomy_dct

    def taxonomy_id_dots(self):
        taxonomy_dct = self.taxonomy_hierarchy_dots
        if 'taxon_ID' in taxonomy_dct:
            return taxonomy_dct['taxon_ID']

    def remove_organism_record(self):
        taxonomy_id = self.taxonomy_id_dots()

        if taxonomy_id is None:
            _logger.info(f"Organism details doesn't exist. \n\t\tOrganism name; {self.org_name}, strain_number: {self.org_version}")
        else:
            _logger.info(f"Deleting the organism records: \n\t\tOrganism name; {self.org_name}, strain_number: {self.org_version}")

            sql_query_1 = f"""
            DELETE nl FROM nalocation AS nl
            INNER JOIN nafeatureimp AS nf ON nl.na_feature_ID = nf.na_feature_ID
            INNER JOIN nasequenceimp AS ns ON nf.na_sequence_ID = ns.na_sequence_ID
            WHERE ns.taxon_ID = {taxonomy_id}
            AND ns.strain_number = {self.org_version}
            AND ns.sequence_type_ID != 1
            """
            self.db_dots.insert(sql_query_1)

            sql_query_2 = F"""
            DELETE p FROM protein AS p
            INNER JOIN geneinstance AS gi ON p.gene_instance_ID = gi.gene_instance_ID
            INNER JOIN nafeatureimp AS nf ON gi.na_feature_ID = nf.na_feature_ID
            INNER JOIN nasequenceimp AS ns ON nf.na_sequence_ID = ns.na_sequence_ID
            WHERE ns.taxon_ID = {taxonomy_id} 
            AND ns.strain_number = {self.org_version} 
            AND ns.sequence_type_ID = 6
            """
            self.db_dots.insert(sql_query_2)

            sql_query_3 = F"""
            DELETE gi FROM geneinstance AS gi
            INNER JOIN nafeatureimp AS nf ON gi.na_feature_ID = nf.na_feature_ID
            INNER JOIN nasequenceimp AS ns ON nf.na_sequence_ID = ns.na_sequence_ID
            WHERE ns.taxon_ID = {taxonomy_id} 
            AND ns.strain_number = {self.org_version}
            """
            self.db_dots.insert(sql_query_3)

            sql_query_4 = f"""
            DELETE nf FROM nafeatureimp AS nf
            INNER JOIN nasequenceimp AS ns ON nf.na_sequence_ID = ns.na_sequence_ID
            WHERE ns.taxon_ID = {taxonomy_id}
            AND ns.strain_number = {self.org_version}
            """
            self.db_dots.insert(sql_query_4)

            sql_query_5 = F"""
            DELETE ns FROM nasequenceimp AS ns 
            WHERE ns.taxon_ID = {taxonomy_id} 
            AND ns.strain_number = {self.org_version} 
            AND ns.sequence_type_ID != 1
            """
            self.db_dots.insert(sql_query_5)

            sql_query_6 = F"""
            DELETE ns FROM nasequenceimp AS ns 
            WHERE ns.taxon_ID = {taxonomy_id} 
            AND ns.strain_number = {self.org_version}
            """
            self.db_dots.insert(sql_query_6)

            #Step 5: Delete from organism
            sql_query_7 = F"""
            DELETE org FROM organism AS org 
            WHERE org.taxon_ID = {taxonomy_id} 
            AND org.strain_number = {self.org_version}
            """
            self.db_dots.insert(sql_query_7)

            sql_query_8 = F"""
            DELETE pi FROM proteininstancefeature AS pi 
            WHERE pi.taxonomy_id = {taxonomy_id} 
            AND pi.strain_number = {self.org_version}
            """
            self.db_dots.insert(sql_query_8)




        #     sql_query_1 = F"""DELETE ips FROM interproscan as ips
        # INNER JOIN geneinstance AS gi
        # ON ips.gene_instance_ID = gi.gene_instance_ID
        # INNER JOIN nafeatureimp as nf
        # ON gi.na_feature_ID = nf.na_feature_ID
        # INNER JOIN nasequenceimp as ns 
        # ON nf.na_sequence_ID = ns.na_sequence_ID 
        # WHERE ns.taxon_ID = {taxonomy_id} and ns.org_version = {self.org_version} and ns.sequence_type_ID = 6"""
        #     self.db_dots.insert(sql_query_1)

        #     sql_query_2 = F"""DELETE sp FROM signalp as sp
        # INNER JOIN geneinstance AS gi
        # ON sp.gene_instance_ID = gi.gene_instance_ID
        # INNER JOIN nafeatureimp as nf
        # ON gi.na_feature_ID = nf.na_feature_ID
        # INNER JOIN nasequenceimp as ns 
        # ON nf.na_sequence_ID = ns.na_sequence_ID
        # WHERE ns.taxon_ID = {taxonomy_id} and ns.org_version = {self.org_version} and ns.sequence_type_ID = 6"""
        #     self.db_dots.insert(sql_query_2)

        #     sql_query_3 = F"""DELETE tm FROM tmhmm as tm
        # INNER JOIN geneinstance AS gi
        # ON tm.gene_instance_ID = gi.gene_instance_ID
        # INNER JOIN nafeatureimp as nf
        # ON gi.na_feature_ID = nf.na_feature_ID
        # INNER JOIN nasequenceimp as ns 
        # ON nf.na_sequence_ID = ns.na_sequence_ID 
        # WHERE ns.taxon_ID = {taxonomy_id} and ns.org_version = {self.org_version} and ns.sequence_type_ID = 6"""
        #     self.db_dots.insert(sql_query_3)



    def get_organism_record(self):

        count_dct = {}
        taxonomy_id = self.taxonomy_id_dots()
        if taxonomy_id is None:
            _logger.info(f"Organism details doesn't exist. \nOrganism name; {self.org_name}, strain number: {self.org_version}")
        # else:
        #     sql_query_1 = F"""select count(*) as count FROM interproscan as ips
        # INNER JOIN geneinstance AS gi
        # ON ips.gene_instance_ID = gi.gene_instance_ID
        # INNER JOIN nafeatureimp as nf
        # ON gi.na_feature_ID = nf.na_feature_ID
        # INNER JOIN nasequenceimp as ns 
        # ON nf.na_sequence_ID = ns.na_sequence_ID
        # WHERE ns.taxon_ID = {taxonomy_id} and ns.org_version = {self.org_version} and ns.sequence_type_ID = 6"""
        #     data1 = self.db_dots.query_one(sql_query_1)
        #     count_dct['interproscan'] = data1['count']

        #     sql_query_2 = F"""SELECT COUNT(*) AS count FROM signalp as sp
        # INNER JOIN geneinstance AS gi
        # ON sp.gene_instance_ID = gi.gene_instance_ID
        # INNER JOIN nafeatureimp as nf
        # ON gi.na_feature_ID = nf.na_feature_ID
        # INNER JOIN nasequenceimp as ns 
        # ON nf.na_sequence_ID = ns.na_sequence_ID
        # WHERE ns.taxon_ID = {taxonomy_id} and ns.org_version = {self.org_version} and ns.sequence_type_ID = 6"""
        #     data1 = self.db_dots.query_one(sql_query_2)
        #     count_dct['SignalP'] = data1['count']

        #     sql_query_3 = F"""SELECT COUNT(*) AS count FROM tmhmm as tm
        # INNER JOIN geneinstance AS gi
        # ON tm.gene_instance_ID = gi.gene_instance_ID
        # INNER JOIN nafeatureimp as nf
        # ON gi.na_feature_ID = nf.na_feature_ID
        # INNER JOIN nasequenceimp as ns 
        # ON nf.na_sequence_ID = ns.na_sequence_ID
        # WHERE ns.taxon_ID = {taxonomy_id} and ns.org_version = {self.org_version} and ns.sequence_type_ID = 6"""
        #     data1 = self.db_dots.query_one(sql_query_3)
        #     count_dct['Tmhmm'] = data1['count']

        #     sql_query_4 = F"""SELECT COUNT(*) AS count FROM hmmpfam as hfam
        # INNER JOIN geneinstance AS gi
        # ON hfam.gene_instance_ID = gi.gene_instance_ID
        # INNER JOIN nafeatureimp as nf
        # ON gi.na_feature_ID = nf.na_feature_ID
        # INNER JOIN nasequenceimp as ns 
        # ON nf.na_sequence_ID = ns.na_sequence_ID
        # WHERE ns.taxon_ID = {taxonomy_id} and ns.org_version = {self.org_version} and ns.sequence_type_ID = 6"""
        #     data1 = self.db_dots.query_one(sql_query_4)
        #     count_dct['hmmpfam'] = data1['count']

            # _logger.info(f"""Count of rows for Organism Name: {self.org_name}, Organism Version: {self.org_version}
            #             hmmpfam: {count_dct['hmmpfam']}
            #             signalp: {count_dct['signalp']}
            #             tmhmm: {count_dct['tmhmm']}
            #             interproscan: {count_dct['interproscan']}
            # """)


class Taxonomy(CommonOrganismInfo, DotsOrganism):
    def __init__(self, db_connection, org_name, strain, assembly_version, org_version=1):
        CommonOrganismInfo.__init__(self, db_connection, org_name, org_version)
        DotsOrganism.__init__(self, db_connection, org_name, org_version)
        self.strain = strain  # Stored as an instance attribute
        self.assembly_version = assembly_version

    def update_organism_table(self):
        _logger.info(f"Updating the organism table. \nOrganism name: {self.org_name}\nstrain number: {self.org_version}")

        taxonomy_dct = self.taxonomy_hierarchy()
        taxonomy_dct = NoneDict(taxonomy_dct)
        taxonomy_id = taxonomy_dct['taxon_ID']
        genus = taxonomy_dct['genus']
        order = taxonomy_dct['order']
        phylum = taxonomy_dct['phylum']
        class_name = taxonomy_dct['class']
        # subclass = taxonomy_dct['subclass']
        family = taxonomy_dct['family']
        super_kingdom = taxonomy_dct['superkingdom']

        query = f'''INSERT INTO organism(taxon_ID, taxon_name, species, strain, assembly_version, phylum, family, genus, orders, class, 
        superkingdom, strain_number) VALUES ({taxonomy_id}, '{self.org_name}', '{self.species}', '{self.strain}', '{self.assembly_version}', '{phylum}',
        '{family}', '{genus}', '{order}', '{class_name}', '{super_kingdom}', '{self.org_version}')'''
        self.db_dots.insert(query)
        _logger.info(" Organism Table update complete")
        return taxonomy_dct

    @property
    def organism_existence(self):
        _logger.debug("checking the organism existence in organism table")
        if not self.org_name:
            _logger.info("Error: Organism Name does not exist")
            return True
        else:
            _logger.info(f'Organism: {self.org_name} strain number: {self.org_version}')
            taxonomy_id = self.taxonomy_id_sres
            if taxonomy_id:
                sql_query = f"select * from organism where taxon_ID = {taxonomy_id} and strain_number = {self.org_version}"
                row_count = self.db_dots.rowcount(sql_query)
                if row_count == 1:
                    _logger.info("Info: Organism Name and same strain number already exists")
                    return True
                else:
                    _logger.info("New Organism")
                    return False
            else:
                _logger.info("Error: Please check the organism name")
                return True

    def organism_name_check(self):
        sql_query = f"select * from organism where taxon_ID = {self.taxonomy_id} and strain_number = {self.org_version}"

    @property
    def organism_type(self):
        organism_type = self.find_organism_type(self.taxonomy_hierarchy_dots)
        return organism_type


class NoneDict(dict):
    def __getitem__(self, key):
        return dict.get(self, key)
