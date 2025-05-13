import logging
# Assuming .dbtable_utility exists in the same package or a relative path
from .dbtable_utility import TableUtility


_logger = logging.getLogger("galEupy.process_tables")

class TableProcessUtility(TableUtility):
    """
    Utility class for processing GFF data and interacting with database tables.
    Inherits from TableUtility.
    """
    def __init__(self, db_dots, upload_dir, organism, taxonomy_id, version):
        """
        Initializes TableProcessUtility, calling the parent constructor.
        """

        super().__init__(db_dots, upload_dir, organism, taxonomy_id, version)

    def process_gff_gene_data(self, scaffold, gene_id, gene_dct, scaffold_na_sequence_id):
        """
        Processes a single gene's data from a GFF structure.
        """
        gene_name = self.prefix + gene_id
        gene_data = GeneInfo(gene_name, gene_dct)

        # Process the gene feature itself
        self.na_sequenceimp_gene(
            self.NaSequenceId, scaffold, scaffold_na_sequence_id, gene_data
        )
        data_type = 'gene'
        self.na_featureimp(
            self.NaFeatureId, self.NaSequenceId, data_type, gene_name, "NULL"
        )

        self.na_location(
            self.na_location_Id,
            self.NaFeatureId,
            gene_data.gene_start,
            gene_data.gene_end,
            gene_data.strand
        )
        gene_na_feature_id = self.NaFeatureId  # Store parent ID for children
        self.NaFeatureId += 1
        self.na_location_Id += 1

        # Process associated RNA features
        if 'trna' in gene_dct:
            for rna_id, rna_dct in gene_dct['trna'].items():
                self.process_other_rna_data(
                    rna_id, rna_dct, 'tRNA', gene_na_feature_id, gene_data
                )

        if 'rrna' in gene_dct:
            for rna_id, rna_dct in gene_dct['rrna'].items():
                self.process_other_rna_data(
                    rna_id, rna_dct, 'rRNA', gene_na_feature_id, gene_data
                )

        if 'mrna' in gene_dct:
            for rna_id, rna_dct in gene_dct['mrna'].items():
                data_type = 'mRNA'
                self.na_featureimp(
                    self.NaFeatureId, self.NaSequenceId, data_type, rna_id, gene_na_feature_id
                )
                rna_data = RnaInfo(rna_dct)
                self.na_location(
                    self.na_location_Id, self.NaFeatureId, rna_data.start, rna_data.end, gene_data.strand
                )

                annotation = rna_dct.get('product', 'Hypothetical Protein')
                self.gene_instance(self.GeneInstanceId, self.NaFeatureId, annotation)

                cds_id = None
                protein_id = None
                # Capture the NaFeatureId for this mRNA *before* processing its children (CDS/exon)
                # and *before* incrementing for the next mRNA.
                rna_na_feature_id = self.NaFeatureId

                if 'cds' in rna_dct:
                    # Check if 'cds' is a list of CDS dictionaries (common in multi-segment CDS)
                    cds_list = rna_dct['cds'] if isinstance(rna_dct['cds'], list) else [rna_dct['cds']]
                    for cds_info in cds_list:
                        cds_id = cds_info.get('ID', f'cds_for_{rna_id}')
                        protein_id = cds_info.get('protein_id', None)
                        self.process_cds_exon_gff_data(
                            feature_name='cds',
                            feature_dct=cds_info,
                            feature_id_name=cds_id,
                            gene_strand=gene_data.strand,
                            parent_na_feature_id=rna_na_feature_id
                        )
                # if 'cds' in rna_dct:
                #     cds_info = rna_dct['cds']
                #     # Use a more specific default if ID is missing
                #     cds_id = cds_info.get('ID', f'cds_for_{rna_id}')
                #     protein_id = cds_info.get('protein_id', None) # Often links to protein feature

                    self.process_cds_exon_gff_data(
                        feature_name='cds',
                        feature_dct=cds_info,
                        feature_id_name=cds_id, # Pass the specific ID for CDS
                        gene_strand=gene_data.strand,
                        parent_na_feature_id=rna_na_feature_id # Link CDS to mRNA
                    )

                protein_sequence = rna_dct.get('protein_sequence', "")
                # Ensure protein_id from CDS attributes is used if available
                # Assuming self.protein links the protein sequence to the gene instance/mRNA
                self.protein(
                    self.ProteinId,
                    gene_name,
                    annotation,
                    self.GeneInstanceId,
                    protein_sequence
                )
                # _logger.info(f'the protein id is {self.ProteinId} and the gene name is {gene_name}')
                if 'exon' in rna_dct:
                    # Exons usually share an identifier, often related to the parent mRNA/CDS
                    # Using cds_id here might be correct if exons are grouped by CDS ID,
                    # otherwise, might need a different approach based on GFF structure.

                    exon_info = rna_dct['exon']
                    # Use a more specific default if ID is missing
                    exon_id = exon_info.get('ID', f'exon_for_{rna_id}')
                    #protein_id = cds_info.get('protein_id', None) # Often links to protein feature

                    self.process_cds_exon_gff_data(
                        feature_name='exon',
                        feature_dct=exon_info,
                        feature_id_name=exon_id, # Pass the specific ID for CDS
                        gene_strand=gene_data.strand,
                        parent_na_feature_id=rna_na_feature_id # Link CDS to mRNA
                    )

                    # exon_id_name = f'exon_for_{rna_id}' # Example placeholder if no specific exon ID
                    # self.process_cds_exon_gff_data(
                    #     feature_name='exon',
                    #     feature_dct=rna_dct['exon'],
                    #     feature_id_name=exon_id_name, # Pass appropriate ID for Exon
                    #     gene_strand=gene_data.strand,
                    #     parent_na_feature_id=rna_na_feature_id # Link exon to mRNA
                    # )

                # Increment IDs for the *next* mRNA feature (or other top-level feature)
                # The CDS/exon processing increments IDs internally for each part.
                self.NaFeatureId += 1
                self.na_location_Id += 1
                self.GeneInstanceId += 1
                self.ProteinId += 1


    def process_other_rna_data(self, rna_id, rna_dct, data_type, gene_na_feature_id, gene_data):
        """
        Processes non-mRNA RNA types (tRNA, rRNA).
        """
        rna_data = RnaInfo(rna_dct)
        # Consider if na_featureimp_rna is different from na_featureimp
        self.na_featureimp( # Assuming na_featureimp_rna was a typo or specific implementation needed
            self.NaFeatureId, self.NaSequenceId, data_type, rna_id, gene_na_feature_id
        )
        self.na_location(
            self.na_location_Id, self.NaFeatureId, rna_data.start, rna_data.end, gene_data.strand
        )
        self.NaFeatureId += 1
        self.na_location_Id += 1

    def process_cds_exon_gff_data(self, feature_name, feature_dct, feature_id_name, gene_strand, parent_na_feature_id):
        """
        Processes features with multiple location segments (CDS/exons) as single features with multiple locations
        """
        # Create single NA_FEATURE entry for this CDS/exon
        self.na_featureimp(
            self.NaFeatureId,
            self.NaSequenceId,
            feature_name,
            feature_id_name,
            parent_na_feature_id
        )

        # Process all location segments for this feature
        locations = feature_dct.get('location', [])
        if not isinstance(locations, list):
            _logger.warning(f"Expected list for locations in {feature_name} {feature_id_name}, found {type(locations)}. Skipping.")
            return

        valid_segment_count = 0
        for loc_entry in locations:
            if not isinstance(loc_entry, (list, tuple)) or len(loc_entry) != 2:
                _logger.warning(f"Invalid location format in {feature_name} {feature_id_name}: {loc_entry}. Skipping segment.")
                continue

            feature_start, feature_end = loc_entry

            # CREATE LOCATION ENTRY (NO COORDINATE VALIDATION)
            self.na_location(
                self.na_location_Id,
                self.NaFeatureId,  # Use the same feature ID for all segments
                feature_start,
                feature_end,
                gene_strand
            )
            self.na_location_Id += 1
            valid_segment_count += 1

        if valid_segment_count == 0:
            _logger.error(f"No valid locations found for {feature_name} {feature_id_name}. Feature not created.")
            return  # Roll back feature creation by not incrementing NaFeatureId
        else:
            _logger.debug(f"Created {feature_name} {feature_id_name} with {valid_segment_count} segments")

        # Only increment feature ID after processing all segments
        self.NaFeatureId += 1


    def process_repeat_data(self, feature, feature_dct, scaffold_na_sequence_id):
        """
        Processes repeat features.
        """
        data_type = feature # e.g., 'repeat_region', 'tandem_repeat'
        location_key = 'location'
        if location_key in feature_dct:
            locations = feature_dct[location_key]
            if not isinstance(locations, list):
                _logger.warning(f"Expected list for locations in {feature}, found {type(locations)}. Skipping.")
                return

            for loc_entry in locations:
                if not isinstance(loc_entry, (list, tuple)) or not (1 <= len(loc_entry) <= 2):
                     _logger.warning(f"Invalid location format in {feature}: {loc_entry}. Skipping.")
                     continue

                feature_start = loc_entry[0]
                feature_end = loc_entry[1] if len(loc_entry) == 2 else loc_entry[0]

                # Determine strand based on GFF conventions (usually '+' or '-')
                # The original logic `strand = 1 if feature_start > feature_end else 0`
                # seems incorrect for standard GFF where start <= end.
                # Assuming strand info might be elsewhere in feature_dct or defaults to forward (0).
                # Fetching strand properly would require knowing the structure of feature_dct.
                # Using a default of 0 (forward/unknown) for now.
                strand = feature_dct.get('strand', 0) # Assuming 0 for '+' or unknown, 1 for '-'

                # Repeats often don't have a parent feature in the same way genes/mRNAs do.
                # Using "NULL" or a specific repeat ID if available.
                # Passing scaffold_na_sequence_id as the sequence context.
                self.na_featureimp(
                     self.NaFeatureId, scaffold_na_sequence_id, data_type, data_type, "NULL" # Or a specific repeat ID
                )
                self.na_location(
                    self.na_location_Id, self.NaFeatureId, feature_start, feature_end, strand
                )
                self.NaFeatureId += 1
                self.na_location_Id += 1

# Separate utility classes
# Use two blank lines before class definitions
class RnaInfo:
    """
    Simple class to hold basic RNA location info.
    """
    def __init__(self, rna_dct):
        # Add error handling for missing or malformed 'location'
        location_list = []
        try:
            # Expecting location like [[start, end, strand?]] or [[start, end], [start, end]]
            # Taking the first segment for overall start/end
            location_list = rna_dct['location'][0]
            self.start = int(location_list[0])
            self.end = int(location_list[1])
        except (KeyError, IndexError, TypeError, ValueError) as e:
            _logger.error(f"Could not parse RNA location from {rna_dct.get('location')}: {e}")
            # Set defaults or raise exception
            self.start = -1
            self.end = -1


class GeneInfo:
    """
    Simple class to hold basic Gene info (sequence, location, strand).
    """
    def __init__(self, gene_name, gene_dct):
        self.gene_name = gene_name
        # Add error handling for missing keys
        self.gene_sequence = gene_dct.get('gene_sequence', '') # Default to empty string if missing
        if not self.gene_sequence:
             _logger.warning(f"Gene {gene_name} has missing 'gene_sequence'")

        try:
            #  location is like [[start, end, strand]]
            location_info = gene_dct['location'][0]
            self.gene_start = int(location_info[0])
            self.gene_end = int(location_info[1])
            strand_char = location_info[2]
            # Convert strand representation: 1 for '-' (reverse), 0 for '+' (forward) or other
            self.strand = 1 if strand_char == '-' else 0
        except (KeyError, IndexError, TypeError, ValueError) as e:
            _logger.error(f"Could not parse gene location/strand for {gene_name} from {gene_dct.get('location')}: {e}")
            # Set defaults or raise a more specific error
            self.gene_start = -1
            self.gene_end = -1
            self.strand = 0 # Default to forward/unknown
