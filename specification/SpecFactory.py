__author__ = 'slash'
from exceptions import ValueError
import hashlib
import re
from sqlalchemy.orm.exc import NoResultFound
from model_cloudcalc import Base, Gpl, Gpl_line, Category, Specification
from resourseProducts import ResourseFactory, price, remove_tags
from specFileProcessors import xlsSheetProcessor, xlsxSheetProcessor
from sqlalchemy import and_


class SpecFactory():
    ''' Process specification file, load it into DB and made other actions on it
    '''
    # Column categories
    CAT_NUM = 1
    CAT_PN = 2
    CAT_NAME = 3
    CAT_QUANTITY = 4
    CAT_PRICE = 5

    # headers & categories matchnig
    column_headers = ['#',
                      'Part Number',
                      'Part Description',
                      'Quantity',
                      'Unit List Price',
                      'Qty',
                      'Description',
                      'Item Name',
                      'ListPrice',
                      'Line Number',
                      'Description',
                      'List Price']
    column_categories = [CAT_NUM,
                         CAT_PN,
                         CAT_NAME,
                         CAT_QUANTITY,
                         CAT_PRICE,
                         CAT_QUANTITY,
                         CAT_NAME,
                         CAT_PN,
                         CAT_PRICE,
                         CAT_NUM,
                         CAT_NAME,
                         CAT_PRICE]
    column_footers = ['Total List Price', 'Product/Subscription Total', 'Configset Total', 'Estimate Total']

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
                result[self.column_categories[index]] = col
        print "Category mapping: ", result
        return result

    ## ---------------- Private methods end ---------

    ## ------ Public method
    def __init__(self, filename, specName=None, hash=None):
        self.filename = filename
        if (specName == None or specName ==''):
            tmp = filename[filename.rfind('/')+1:]    # use name of the file as a Spec name
            self.name =re.search('.*?_(.+)(?=.xlsx*?)', tmp).group(1)
        else:
            self.name = remove_tags(specName)
        type = filename[filename.rfind('.')+1:]
        try:
            if (hash == None):
                f = open(filename)
                data = f.read()
                self.file_hash = hashlib.sha1(data).hexdigest()
                f.close()
            else:
                self.file_hash = hash
            if (type == 'xls'):
                self.book = xlsSheetProcessor(filename)
            elif (type == 'xlsx'):
                self.book = xlsxSheetProcessor(filename)
            else:
                raise ('Unsupported spec file type: ', type)
            #self.book = xlrd.open_workbook(filename)
            #self.sheetnames = self.book.sheet_names()
            self.sheet = self.book.sheet_by_index(0)
        except Exception as e:
            raise ValueError('Can\'t open file:(%s) %s'%(e, filename))
        tmp = self.get_spec_range(self.sheet)
        if (tmp == None):
            raise ValueError('File doesn\'t contain specification on the first sheet')
        (self.header, self.footer) = tmp
        self.mapping = self.makeCategoryToColumnsMapping(self.sheet, self.header)
        #if (len(self.mapping) != len(self.column_categories)):
        if (not self.CAT_PN in self.mapping):
            raise ValueError('Can\'t match PN header in file')
        if (not self.CAT_NAME in self.mapping):
            raise ValueError('Can\'t match description header in file')
        if (not self.CAT_QUANTITY in self.mapping):
            raise ValueError('Can\'t match quantity header in file')
        return

    def extractSpec(self, sheet, header, footer, column_mapping):
        ''' Exctract one sheet to list of dictionaries
        :param sheet:
        :param header:
        :param footer:
        :param column_mapping:
        :return:
        '''
        result=[]
        for row in range(header+1, footer):
            line = {}
            #num_field = sheet.cell(row, column_mapping[self.CAT_PN]).ctype
            # If number field type doesn't contain value - skip line
            if (sheet.isCellEmpty(row, column_mapping[self.CAT_PN])):      # 0 - XL_CELL_EMPTY, 6 - XL_CELL_BLANK
                continue
            for cat in self.mapping:
                value = sheet.cell(row,column_mapping[cat]).value
                line[cat] = value
            if (self.CAT_PRICE in self.mapping):
                tmp = price(line[self.CAT_PRICE])
                #print "Price = ", tmp, type(tmp)
                line[self.CAT_PRICE] = tmp
            result.append(line)
        return result

    ## -------- Public method
    def uploadSpecToDatabase(self, session, user_id, spec=None):
        ''' Upload specification to database session
        :return: hash for specification file
        '''
        # get tokenized specification from file
        tokenizedSpec = self.extractSpec(self.sheet, self.header, self.footer, self.mapping)
        print 'Tokenize spec and ready to add it'
        self.spec_hash = hashlib.sha1(self.file_hash + str(user_id)).hexdigest()
        try:
            spec = session.query(Specification).filter(Specification.hash == self.spec_hash).one()
            print "already found"
        except:
            try:
                spec = Specification(self.filename, self.name, tokenizedSpec, self.spec_hash, user_id=user_id)
                session.add(spec)
                session.commit()
                print 'added'
            except Exception as e:
                print "Some exception: ", e.message

        print 'return hash: ', spec.hash
        return spec.hash

    ## -------- Public method
    @staticmethod
    def getSpecFromDatabase(session, hash):
        ''' Function retrieve tokenized specification from database
        :param session: DB session
        :param hash: Spec hash
        :return:
        '''
        #print "retrieve specification from database"
        try:
            spec = session.query(Specification).filter(Specification.hash == hash).one()
        except:
            print '      >>>>> can\'t load spec from DB'
            raise NoResultFound('Specification with hash: \'%s\' isn\'t exist'%hash)
        #print "   >>>> Success!!!"
        return spec.tokenized

    @staticmethod
    def getSpecName(session, hash):
        try:
            spec = session.query(Specification).filter(Specification.hash == hash).one()
        except:
            raise NoResultFound('Specification with hash: \'%s\' isn\'t exist'%hash)
        return spec.name
    ## ----------------------- Method to work with specification line -----
    ## -----------------

    @staticmethod
    def identifyResourse(line):
        ''' function scan specification and return resource type
        :param line: line dictionary from specification
        :return: tuple of resourse and filter
        '''
        for res in ResourseFactory.product_filters:
            for filter in ResourseFactory.product_filters[res]:
                if (line[SpecFactory.CAT_PN].startswith(filter)):
                    return (res, filter)
        return None

    @staticmethod
    def getResourseFromLine(line):
        '''
        :param line: dictionary, one line from specification file
        :return: dict { 'RESOURCE_TYPE' : value, ...} or None
        '''
        tmp = SpecFactory.identifyResourse(line)
        if (tmp):
            (type, filter) = tmp
            res = ResourseFactory.extractValues(type, line[SpecFactory.CAT_NAME], line[SpecFactory.CAT_QUANTITY])
            warn = ResourseFactory.checkIsBundle(line[SpecFactory.CAT_PN])
            if (warn != None):
                res.update(warn)   # If partnumber registered as bundle - add 'WARNING' TAG
            if (res):
                return res
        return None

    ## -------- Public method

    @staticmethod
    def calculateSpecResources(session, hash):
        ''' The function calculate spec resources and return "reach" format of specification
        :return: dict { 'stat' : dict {resource statistics}
                        'spec' : [ dict {line: resource, isRecogized, resourceType, resourceType, resourceValue}]
                                    - array of lines with resources
                }
        '''
        result = []
        return_data = {}
        stat= {ResourseFactory.PROD_CPU : 0,
               ResourseFactory.PROD_MEM : 0,
               ResourseFactory.PROD_HDD : 0,
               ResourseFactory.PROD_SSD : 0
               }
        total_price = 0
        spec = SpecFactory.getSpecFromDatabase(session, hash)        # load specification
        if (spec == None):
            raise NoResultFound("Specification 'hash' found but it's empty")%hash
        # We got specification, let's process it
        for line in spec:
            final_line = line                       # copy all paramemters to final line
            res = SpecFactory.getResourseFromLine(line)
            if (res):
                final_line['isRecognized']  = True      # add resource data to final line
                final_line.update(res)
                if (res.has_key('WARNING')):      # pop warning
                    return_data['WARNING'] = True
                    res.pop('WARNING', None)
                for key in res:
                    #print "DEBUG calculateSpecResources: res[key] = '%s', type: %s", res[key], type(res[key])
                    stat[key] += int(res[key])               # summarize statistics
            result.append(final_line)
            if (line[SpecFactory.CAT_PN] !=''):
                #print "Line: ", line, type(line[SpecFactory.CAT_PRICE])
                p = price(line[SpecFactory.CAT_PRICE])

                #print "item= ", int(line[SpecFactory.CAT_QUANTITY]) * line[SpecFactory.CAT_PRICE]
                total_price +=  int(line[SpecFactory.CAT_QUANTITY]) * line[SpecFactory.CAT_PRICE]
        #print "Price: ", total_price
        name = SpecFactory.getSpecName(session, hash)

        return_data.update({'stat' : stat, 'spec': result, 'price' : total_price, 'name' :name})
        return return_data


