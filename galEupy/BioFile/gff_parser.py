import re
from collections import defaultdict, OrderedDict
import logging
_logger = logging.getLogger("galEupy.BioFile.gff_parser")


def dct_structure():
    return defaultdict(dct_structure)


class ReadGFF3:
    def __init__(self, gff_file):
        self.gff_file = gff_file
        self.pseudo_gene_id_dct = dct_structure()

    def reader(self):
        """
            This function takes gff file as input and return a dictionary of the gff file
        """
        dct = dct_structure()
        gene_id_dct = dct_structure()
        
        read_fh = open(self.gff_file, 'r', encoding="utf-8")
        lookup_list = ['pseudogene', 'gene', 'mRNA', 'tRNA', 'rRNA', 'cds', 'exon', 'transcript']

        for i, line in enumerate(read_fh):
            line = line.rstrip()
            if re.search(r'^#', line):
                continue
            cols = re.split(r'\t', line)
            if len(cols) > 7:
                gff_line_obj = ParseGffLine(cols)
                if any(item.lower() == cols[2].lower() for item in lookup_list):
                    source = cols[0]
                    match_obj = re.search(r'^(\S+) (.*)', cols[0])
                    if match_obj:
                        source = match_obj.group(1)

                    if cols[2].lower() in ['gene', 'pseudogene']:
                        dct = self.process_gene_line(dct, cols)
                        
                    if cols[2].lower() in ['mrna', 'rrna', 'trna']:
                        dct, gene_id_dct = self.process_rna_features(dct, cols, gene_id_dct)
                    if re.search(r'transcript', cols[2], re.I):
                        dct, gene_id_dct = self.process_augustus_transcript_line(dct, cols, gene_id_dct)

                    if re.search(r'cds', cols[2], re.I):
                        super_parent_id, parent_id = gff_line_obj.get_super_parent_id(gene_id_dct, source)
                        location_list = [cols[3], cols[4]]
                        if super_parent_id in dct[source]['pseudogene']:
                            try:
                                dct[source]['pseudogene'][super_parent_id]['mrna'][parent_id]['cds']['location'].append(location_list)
                            except AttributeError:
                                dct[source]['pseudogene'][super_parent_id]['mrna'][parent_id]['cds']['location'] = [location_list]
                        else:
                            try:
                                dct[source]['gene'][super_parent_id]['mrna'][parent_id]['cds']['location'].append(
                                    [cols[3], cols[4]])
                            except AttributeError:
                                dct[source]['gene'][super_parent_id]['mrna'][parent_id]['cds']['location'] = [
                                    [cols[3], cols[4]]]

                    if re.search(r'exon', cols[2], re.I):
                        super_parent_id, parent_id = gff_line_obj.get_super_parent_id(gene_id_dct, source)
                        location_str = [[cols[3], cols[4]]]
                        if super_parent_id is not None and parent_id is not None:
                            rna_type = gff_line_obj.id_to_rna_type(gene_id_dct, source, parent_id)
                            if super_parent_id in self.pseudo_gene_id_dct:
                                try:
                                    dct[source]['pseudogene'][super_parent_id][rna_type][parent_id]['exon']['location'].append(location_str)
                                except AttributeError:
                                    dct[source]['pseudogene'][super_parent_id][rna_type][parent_id]['exon']['location'] = location_str
                            else:
                                try:
                                    dct[source]['gene'][super_parent_id][rna_type][parent_id]['exon']['location'].append(location_str)
                                except AttributeError:
                                    dct[source]['gene'][super_parent_id][rna_type][parent_id]['exon']['location'] = location_str
                                        
        return dct
    
    def process_gene_line(self, dct, cols):
        attribute_dct = parse_single_feature_line(cols[8])

        gff_attribute = GffAttribute()
        if not attribute_dct:
            gene_id = cols[8]
        elif gff_attribute.id in attribute_dct:
            gene_id = attribute_dct[gff_attribute.id]
        else:
            raise Exception('Please check your Gff file')

        source = cols[0]
        match_obj = re.search(r'^(\S+) (.*)', cols[0])
        if match_obj:
            source = match_obj.group(1)

        gene_feature = "gene"
        if cols[2].lower() in ['pseudogene']:
            gene_feature = 'pseudogene'
            self.pseudo_gene_id_dct[gene_id] = gene_feature
            
        location_str = [cols[3], cols[4], cols[6]]
        try:
            dct[source][gene_feature][gene_id]['location'].append(location_str)
        except AttributeError:
            dct[source][gene_feature][gene_id]['location'] = [location_str]

        return dct

    def process_rna_features(self, dct, cols, gene_id_dct):
        contig = cols[0]
        rna_type = cols[2].lower()

        attribute_dct = parse_single_feature_line(cols[8])

        gff_attribute = GffAttribute()
        rna_id = None
        if gff_attribute.id in attribute_dct:
            rna_id = attribute_dct[gff_attribute.id]

        if gff_attribute.parent in attribute_dct and rna_id:
            gene_id = attribute_dct[gff_attribute.parent]
            gene_id_dct[contig][rna_id] = {'ID': gene_id, 'FeatureType':rna_type}

            location_str = [cols[3], cols[4], cols[6]]
            if gene_id in self.pseudo_gene_id_dct:
                try:
                    dct[contig]['pseudogene'][gene_id][rna_type][rna_id]['location'].append(location_str)
                except AttributeError:
                    dct[contig]['pseudogene'][gene_id][rna_type][rna_id]['location'] = [location_str]
                if gff_attribute.product in attribute_dct:
                    dct[contig]['pseudogene'][gene_id][rna_type][rna_id]['product'] = attribute_dct[gff_attribute.product]
            else:
                try:
                    dct[contig]['gene'][gene_id][rna_type][rna_id]['location'].append(location_str)
                except AttributeError:
                    dct[contig]['gene'][gene_id][rna_type][rna_id]['location'] = [location_str]

                    if gff_attribute.product in attribute_dct:
                        dct[contig]['gene'][gene_id][rna_type][rna_id]['product'] = attribute_dct[gff_attribute.product]
        return dct, gene_id_dct
    
    def process_augustus_transcript_line(self, dct, tmp, gene_id_dct):
        attribute_dct = parse_single_feature_line(tmp[8])
        source = tmp[0]
        if not attribute_dct:
            arr = tmp[8].split('.')
            gene_id = arr[0]
            rna_id = tmp[8]
            gene_id_dct[source][tmp[8]] = arr[0]
            try:
                dct[source]['gene'][gene_id]['mrna'][rna_id]['location'].append([tmp[3], tmp[4]])
            except AttributeError:
                dct[source]['gene'][gene_id]['mrna'][rna_id]['location'] = [[tmp[3], tmp[4]]]
        else:
            dct, gene_id_dct = self.process_rna_features(dct, tmp, gene_id_dct)

        return dct, gene_id_dct

    
class GffAttribute:
    product = 'product'
    id = 'id'
    parent = 'parent'


class ParseGffLine:
    def __init__(self, gff_line):
        self.line_cols = gff_line

    @property
    def attribute_dct(self):
        attribute_string = self.line_cols[8]
        attributes = dict()
        for key_value_pair in attribute_string.split(';'):
            if not key_value_pair:
                # empty string due to a trailing ";"
                continue

            if "=" in key_value_pair:
                sub_attributes = key_value_pair.strip().split("=")
                if len(sub_attributes) == 1:
                    attributes[sub_attributes[0].lower()] = None
                elif len(sub_attributes) == 2:
                    attributes[sub_attributes[0].lower()] = sub_attributes[1]
                else:
                    attributes[sub_attributes[0].lower()] = " ".join(sub_attributes[1:])
            elif " " in key_value_pair:
                key_value_pair = key_value_pair.strip()
                key, val = key_value_pair.split(" ", maxsplit=1)
                val = val.strip('"')
                attributes[key.lower()] = val
        return attributes

    def get_super_parent_id(self, gene_id_dct, contig):
        """If its exon: 
            parent is rna
            superparent is gene 
        """
        attribute_dct = self.attribute_dct

        super_parent_id, parent_id = None, None
        if 'parent' in attribute_dct:
            parent_id = attribute_dct['parent']
            if parent_id in gene_id_dct[contig]:
                super_parent_id = gene_id_dct[contig][parent_id]['ID']
        elif 'transcript_id' in attribute_dct:
            parent_id = attribute_dct['transcript_id']
            super_parent_id = attribute_dct['gene_id']

        return super_parent_id, parent_id

    def id_to_rna_type(self, gene_id_dct, contig, rna_id):
        
        rna_type = gene_id_dct[contig][rna_id]['FeatureType']
        return rna_type


def parse_single_feature_line(attribute_string):
    attributes = dict()
    for key_value_pair in attribute_string.split(';'):
        if not key_value_pair:
            # empty string due to a trailing ";"
            continue

        if "=" in key_value_pair:
            sub_attributes = key_value_pair.strip().split("=")
            if len(sub_attributes) == 1:
                attributes[sub_attributes[0].lower()] = None
            elif len(sub_attributes) == 2:
                attributes[sub_attributes[0].lower()] = sub_attributes[1]
            else:
                attributes[sub_attributes[0].lower()] = " ".join(sub_attributes[1:])
        elif " " in key_value_pair:
            key_value_pair = key_value_pair.strip()
            key, val = key_value_pair.split(" ", maxsplit=1)
            val = val.strip('"')
            attributes[key.lower()] = val
    return attributes


def make_custom_order(dct):
    sort_order = ['gene', 'mrna', 'cds', 'exon']

    all_sites_ordered = OrderedDict(OrderedDict(sorted(dct.items(), key=lambda i: sort_order.index(i[0]))))
    return all_sites_ordered


def make_custom_sort(orders):
    orders = [{k: -i for (i, k) in enumerate(reversed(order), 1)} for order in orders]

    def process(stuff):
        if isinstance(stuff, dict):
            l = [(k, process(v)) for (k, v) in stuff.items()]
            keys = set(stuff)
            for order in orders:
                if keys.issuperset(order):
                    return OrderedDict(sorted(l, key=lambda x: order.get(x[0], 0)))
            return OrderedDict(sorted(l))
        if isinstance(stuff, list):
            return [process(x) for x in stuff]
        return stuff
    return process
