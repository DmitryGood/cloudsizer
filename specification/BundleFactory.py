__author__ = 'slash'
from specFileProcessors import xlsSheetProcessor, xlsxSheetProcessor
from resourseProducts import remove_tags, price, ResourseFactory
from exceptions import ValueError


class BundleFactory():

    # Column categories
    CAT_LEVEL1 = 1
    CAT_LEVEL2 = 2
    CAT_PN = 3
    CAT_NAME = 4
    CAT_PRICE = 5
    CAT_QUANTITY = 6
    CAT_PARAMETERS = 7
    CAT_VALUES = 8

    # possible values for column headers
    column_headers = ['Level1',
                      'Level2',
                      'Part Number',
                      'Description',
                      'Unit List Price',
                      'Qty',
                      'PARAMETERS',
                      'VALUES']

    # category mapping
    column_categories = [CAT_LEVEL1,
                         CAT_LEVEL2,
                         CAT_PN,
                         CAT_NAME,
                         CAT_PRICE,
                         CAT_QUANTITY,
                         CAT_PARAMETERS,
                         CAT_VALUES]

    # Word to recongnize footer
    column_footers = ['END']

    ## ---------------- Private methods -------------
    # return header and footer as tuple
    def get_spec_range(self, sheet):
        header = 0
        footer = 0
        ncols = sheet.max_col()
        nrows = sheet.max_row()
        for row in range(0,nrows):
            #cells = sheet.row(row)
            for col in range(0, ncols):
                c = sheet.cell(row, col)
                if (c.value in self.column_headers):
                    header = row
                    break
                if (c.value in self.column_footers):
                    footer = row
                    break
        print "Spec starts from %s, ends on %s"%(header, footer)
        if (header < footer):
            return (header, footer)
        return None

    # Match categories to column numbers
    def makeCategoryToColumnsMapping(self, sheet, header):
        '''
        :param sheet: sheet
        :param header: hesder for the sheet
        :return: category to column matching
        '''
        ncols = sheet.max_col()
        result={}
        for col in range(0, ncols):
            cell = sheet.cell(header, col)
            if cell.value in self.column_headers:
                index = self.column_headers.index(cell.value)
                if not result.has_key(self.column_categories[index]):
                    result[self.column_categories[index]] = col
        #print "Category mapping: ", result
        return result

    ## ---------------- Private methods end ---------

    ## ------ Public method
    def __init__(self, filename, specTag=None):
        self.bundle = None
        self.filename = filename
        if (specTag == None or specTag ==''):

            self.tag ='def'         # just some kind of default tag
        else:
            self.tag = remove_tags(specTag)       # remove special symbols
        type = filename[filename.rfind('.')+1:]     # get file extension
        try:
            if (type == 'xls'):
                self.book = xlsSheetProcessor(filename)
            elif (type == 'xlsx'):
                self.book = xlsxSheetProcessor(filename)
            else:
                raise ('Unsupported spec file type: ', type)
            self.sheet = self.book.sheet_by_index(0)            # load first stylesheet
        except Exception as e:
            raise ValueError('Can\'t open file:(%s) %s'%(e, filename))
        tmp = self.get_spec_range(self.sheet)
        if (tmp == None):
            raise ValueError('File doesn\'t contain specification on the first sheet')
        (self.header, self.footer) = tmp
        self.mapping = self.makeCategoryToColumnsMapping(self.sheet, self.header)
        if (not self.CAT_LEVEL1 in self.mapping):
            raise ValueError('Can\'t match Level1 header in file')
        if (not self.CAT_LEVEL2 in self.mapping):
            raise ValueError('Can\'t match Level2 header in file')
        if (not self.CAT_PN in self.mapping):
            raise ValueError('Can\'t match PN header in file')
        if (not self.CAT_NAME in self.mapping):
            raise ValueError('Can\'t match description header in file')
        if (not self.CAT_QUANTITY in self.mapping):
            raise ValueError('Can\'t match quantity header in file')
        if (not self.CAT_PARAMETERS in self.mapping):
            raise ValueError('Can\'t match Parameters header in file')
        if (not self.CAT_VALUES in self.mapping):
            raise ValueError('Can\'t match parameter values header in file')
        return

    def extractSpec(self, sheet, begin, column_mapping):
        ''' Exctract part of the bundle sheet to list of dictionaries (Spec representation)
            Extract made starting from <begin> line till the first empty line
        :param sheet:    Sheet
        :param begin:   The line to start with
        :               There are no end line - part ends when empty line appears
        :param column_mapping: map (see above)
        :return:
        '''
        result=[]
        row = begin
        while (not sheet.isCellEmpty(row, column_mapping[self.CAT_PN])):
            line = {}
            for cat in [self.CAT_PN, self.CAT_NAME, self.CAT_PRICE, self.CAT_QUANTITY]:
                value = sheet.cell(row,column_mapping[cat]).value
                line[cat] = value
            tmp = price(line[self.CAT_PRICE])
            line[self.CAT_PRICE] = tmp
            result.append(line)
            row +=1
        return (row, result)

    def lookForPart(self, start, level1, level2):
        row = start
        found = False
        while (row < self.footer):
            lvl1=self.sheet.cell(row, self.mapping[self.CAT_LEVEL1]).value;
            lvl2=self.sheet.cell(row, self.mapping[self.CAT_LEVEL2]).value;
            if (lvl1 and lvl2 and lvl1.startswith(level1) and lvl2.startswith(level2)):
                found = True
                break
            row += 1            # go next line
        if found:
            return row
        return None

    def extractParameters(self, start, end):
        # Extract parameters from string range to dictionary
        # make all parameters lower case
        row=start
        parameters = {}
        while (row < end):
            par = self.sheet.cell(row, self.mapping[self.CAT_PARAMETERS]).value
            val = self.sheet.cell(row, self.mapping[self.CAT_VALUES]).value
            if (par == ""):
                break
            parameters[str(par).lower()] = val
            row +=1
        if (bool(parameters)):
            return parameters
        return None

    def normalizeSpec(self, spec, divider):
        result=[]
        for line in spec:
            r = line
            r[self.CAT_QUANTITY] = line[self.CAT_QUANTITY] / divider
            result.append(r)
        return result

    def getSpecPrice(self, spec):
        result = 0
        for line in spec:
            total = line[self.CAT_PRICE] * line[self.CAT_QUANTITY]
            result +=total
        return result

    def getConfigParameters(self, par, prefix):
        # loop over parameter list and return those which have prefix in the name as a separate dictionary
        result = {}
        for entry in par:
            if (entry.startswith(prefix)):
                sub_par = entry[len(prefix):]
                result[sub_par] = par[entry]
        return result

    def extractBundleTest(self):
        row = self.header
        baseLine = self.lookForPart(self.header, 'BASE', 'BASE')
        if (not baseLine):
            raise ValueError('Can\'t find BASE section')
        (row, baseSpec) = self.extractSpec(self.sheet, baseLine, self.mapping)
        # If now in base spec we have specification

        optionLine = self.lookForPart(row, 'OPTION1', 'BASE')
        if (not optionLine):
            raise ValueError('Can\'t find OPTION section')

        (row, optionSpec) = self.extractSpec(self.sheet, optionLine, self.mapping)
        # row now contains end line of OPTION section
        option_parameters = self.extractParameters(optionLine, row)
        if (not option_parameters):
            raise ValueError('Can\'t find OPTION parameters')

        normOptionSpec = self.normalizeSpec(optionSpec,option_parameters['servers'])
        print "Normalized spec: ", normOptionSpec, " TOTAL: ", self.getSpecPrice(normOptionSpec)

        conf_param = self.getConfigParameters(option_parameters, "config_")
        print "Config parameters: ", conf_param

        addonLine = self.lookForPart(row, 'OPTION_ADDON', 'MEMORY')
        if (not addonLine):
            raise ValueError('Can\'t find ADDON section')
        (row, addonSpec) = self.extractSpec(self.sheet, addonLine, self.mapping)
        # row now contains end line of ADDON section
        addon_parameters = self.extractParameters(addonLine, row)
        if (not option_parameters):
            raise ValueError('Can\'t find ADDON parameters')
        print "Addon parameter: ", addon_parameters['limit']

        return { 'base' : baseSpec, 'option' : optionSpec, 'addon' : addonSpec, 'parameters': (option_parameters, addon_parameters)}

    def extractBundle(self):
        # Extract bundle from sheet
        row = self.header

        # Identify base part and extract spec
        baseLine = self.lookForPart(self.header, 'BASE', 'BASE')
        if (not baseLine):
            raise ValueError('Can\'t find BASE section')
        (row, baseSpec) = self.extractSpec(self.sheet, baseLine, self.mapping)
        # row now show to end of base specification
        # Now in baseSpec we have specification

        optionLine = self.lookForPart(row, 'OPTION1', 'BASE')
        if (not optionLine):
            raise ValueError('Can\'t find OPTION section')

        (row, optionSpec) = self.extractSpec(self.sheet, optionLine, self.mapping)
        # row now contains end line of OPTION section
        # in optionSpec we now have specification
        # get spec paramemters
        option_parameters = self.extractParameters(optionLine, row)
        if (not option_parameters):
            raise ValueError('Can\'t find OPTION parameters')
        # normalize OPTION specification
        normOptionSpec = self.normalizeSpec(optionSpec,option_parameters['servers'])
        ###print "Normalized spec: ", normOptionSpec, " TOTAL: ", self.getSpecPrice(normOptionSpec)

        # get configuration parameters
        conf_param = self.getConfigParameters(option_parameters, "config_")
        ###print "Config parameters: ", conf_param
        cpu_param = self.getConfigParameters(option_parameters, "cpu_")

        # look for ADDON section
        addonLine = self.lookForPart(row, 'OPTION_ADDON', 'MEMORY')
        if (not addonLine):
            raise ValueError('Can\'t find ADDON section')
        (row, addonSpec) = self.extractSpec(self.sheet, addonLine, self.mapping)
        # row now contains end line of ADDON section
        # addonSpec now contains spec
        # look for addon parameters
        addon_parameters = self.extractParameters(addonLine, row)
        if (not option_parameters):
            raise ValueError('Can\'t find ADDON parameters')
        #####print "Addon parameter: ", addon_parameters['limit']
        # lets create the final object
        addon_size = 32
        #addon_line = addonSpec[0]
        #addon_size = ResourseFactory.extractMEMv10(addon_line[self.CAT_NAME], addon_line[self.CAT_QUANTITY])


        result={}  # Final resultion object

        # Add BASE part
        result['BASE'] = {
            'spec' : baseSpec,
            'price' : self.getSpecPrice(baseSpec)
        }

        # Add OPTION part
        result['OPTION'] = {
            'spec' : normOptionSpec,
            'price' : self.getSpecPrice(normOptionSpec),
            'min' : int(option_parameters['servers_min']),
            'max' : int(option_parameters['servers_max']),
            'config' : conf_param,
            'cpu' : cpu_param
        }


        result['ADDON'] = {
            'name' : 'MEMORY',
            'spec' : addonSpec,
            'cost': self.getSpecPrice(addonSpec),
            'limit' : int(addon_parameters['limit']),
            'size' : int(addon_size)
        }

        self.bundle = result        ## Save bundle object for future use

        return True

    def extract_for_web(self):
        bundle_option = self.bundle['OPTION']
        result = {}
        for i in range(bundle_option['min'], bundle_option['max']+1):
            #print "Server: ----", i
            option_param= {'price': 0, 'core': 0}
            config = bundle_option['config']
            price = self.bundle['BASE']['price'] + bundle_option['price'] * i
            new_conf = {}
            for e in config:
                new_conf[e] = config[e] * i
            cores = int(new_conf['cpu'])
            result[cores] = {
                'servers' : i,
                'price' : price,
                'config' : new_conf,
                'memoryLimit' : self.bundle['ADDON']['limit'] * i,
                'memorySize' : self.bundle['ADDON']['size'],
                'memoryCost' : self.bundle['ADDON']['cost']
            }

            if bundle_option.has_key('cpu'):
                result[cores]['cpu'] = bundle_option['cpu']
            #print "------------" + '\n'
        return result

    @staticmethod
    def compare_is_conf1_less(conf_1, conf_2):
        return (conf_1['price'] < conf_2['price'])

    @staticmethod
    def combine_bundles_config(bundles_list):
        result = {}
        # iterate configurations list
        for bun in bundles_list:
            # iterate configurations
            conf = bun.extract_for_web()
            for key in conf:
                if not result.has_key(key):             # If key hasn't been in result - put it
                    result[key] = conf[key]
                else:                                   # If the same key is in result - decide which one will remain
                    print "**** Key conflict", key
                    if BundleFactory.compare_is_conf1_less(conf[key], result[key]):       # if new is less - put it, else remain existing
                        print "----- >>>> Relace key"
                        result[key] = conf[key]
        return result
