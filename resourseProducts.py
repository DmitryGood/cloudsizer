__author__ = 'slash'
import re


def price(inpstr):
    if (isinstance(inpstr, float)):
        return inpstr
    if (isinstance(inpstr, str) or isinstance(inpstr, unicode)):
        tmp=re.sub('[^0-9]*', '', inpstr.split('.')[0])
        if (tmp != ''):
            return int(tmp)
        else:
            return 0
    return inpstr

TAG_RE = re.compile(r'<[^>]+>')   # constant function

def remove_tags(text):
    return TAG_RE.sub('', text)

class ResourseFactory():
    # product categories
    PROD_CPU = 'CPU'
    PROD_MEM = 'MEM'
    PROD_HDD = 'HDD'
    PROD_SSD = 'SSD'
    PROD_BUNDL = 'BUND'


    # filter for product categories
    product_filters = {
        PROD_CPU : ['A01-','N20-X0', 'UCS-CPU-E3', 'UCS-CPU-E5', 'UCS-CPU-E7', 'UCS-CPUE5', 'UCSCPU'],
        PROD_MEM : ['A02-','N01-M3', 'UCS-ML', 'UCS-MR', 'UCS-MU', 'UCS-SPL-M', 'UCS-SPM-M16', 'UCS-SPM-M32'],
        PROD_HDD : ['A03-','R200-D', 'UCS-EZ-300', 'UCS-EZ7-300GB', 'UCS-HD', 'UCS-SP-1P2T', 'UCS-SPL-1P2T', 'UCS-SPL-D1P2T', 'UCSHDD'],
        PROD_SSD : ['N20-D0','UCS-C3X60', 'UCS-SD', 'UCSSD', 'UCSSSD'],
        PROD_BUNDL : ['C880-2T', 'C880-6T', 'UCS-CX-B', 'UCS-EZ7-B', 'UCS-SA', 'UCS-SL-CPA',
                  'UCS-SM', 'UCS-SP-B', 'UCS-SP-C',
                  'UCS-SP7-SRB200', 'UCS-SP7SRB200', 'UCS-SPL-B', 'UCS-SPL-C', 'UCS-SPM-B', 'UCS-SPM-C',
                  'UCS-SPR-C', 'UCS-SR-B', 'UCS-VDI-C', 'UCSB-EZ-UC-', 'UCSCDBUNC2', 'UCSEZ', 'UCSME-',
                  'UCSSP', 'UCUCS-EZ-B', 'UCUCS-EZ-C', 'UCUCSEZ-C', 'UCSC-C3X60-','UCSC-C3260', 'UCS-SP6-', 'UCS-SP-ENVP']
    }

    # ----------------- Static data end ------------

    product_data_extractors = {
        PROD_CPU : {
            'UCS-CPU-E5' : None

        },
        PROD_MEM : {
            'UCS-ML' : None,
            'UCS-MR' : None
        }
    }

    ## ------------- Parsers -----------
    ## --------

    @staticmethod
    def extractCPUv10(name, quantity):
        ''' CPU cores extractor, valid for Russia GPL from 18.01.2016
        :param name: name string
        :param quantity: quantity field
        :return:
        '''
        num = 0
        par = re.search('([0-9]+)[cC]', name)               # parse first type of lines
        if (par):                                           # success
            #print "   --1- par:%s  ___ line: %s"%(par.group(1), name)
            num = int(par.group(1))
        else:                                               # fail - try more
            par = re.search('([0-9]+) (?=cores)', name)     # parse second type of lines
            if par:
                #print "   --2- par:%s  ___ line: %s"%(par.group(1), name)
                num = int(par.group(1))
        return {ResourseFactory.PROD_CPU : num * int(quantity)}

    @staticmethod
    def extractMEMv10(name, quantity, pn=''):
        ''' MEM GBs extractor, valid for Russia GPL from 18.01.2016
        :param name: name string
        :param quantity: quantity field
        :return:
        '''
        num = 0
        par = re.search('(2)\s*?[Xx]\s*?([0-9]+)\s*?(?=GB)', name)               # parse first type of lines 2 X 32GB
        if (par):                                           # success
            #print "   --1- par:%s  ___ line: %s"%(par.group(2), name)
            num = int(par.group(1))*int(par.group(1))
        else:                                               # fail - try more
            par = re.search('([0-9]+)(?=GB)', name)               # parse second type of lines 16GB
            if (par):                                           # success
                #print "   --2- par:%s  ___ line: %s"%(par.group(1), name)
                num = int(par.group(1))
            else:
                #print "<<<< %s _________ line: %s"%(pn,name)
                pass
        if (num !=0):
            return {ResourseFactory.PROD_MEM : num * int(quantity)}
        else:
            return 0

    @staticmethod
    def extractHDDv10(name, quantity, pn=''):
        ''' HDD GBs extractor, valid for Russia GPL from 18.01.2016
        :param name: name string
        :param quantity: quantity field
        :return:
        '''
        num = 0
        par = re.search('[^0-9]*?([0-9]+)\s*?GB.*(?=HDD)', name)               # parse first type of lines 400 GB ___ HDD
        if (par):                                           # success
            #print "   --1- par:%s  ___ line: %s"%(par.group(1), name)
            num = int(par.group(1))
        else:                                               # fail - try more
            par = re.search('[^0-9]*?([0-9.]+)\s*?TB.*(?=HDD)', name)               # parse second type of lines 1.2 TB ____ HDD
            if (par):                                           # success
                #print "   --2- par:%s  ___ line: %s"%(par.group(1), name)
                group = par.group(1).split('.')
                if (len(group) == 2):
                    num = int(group[0])*1000 + int(group[1]) * 100
                    #print "   --3- par:%s  ___ line: %s"%(num, name)
                elif (len(group) == 1):
                    num = int(group[0]) * 1000
                    #print "   --4- par:%s  ___ line: %s"%(num, name)
                else:
                    #print "<<<< %s _________ line: %s"%(pn,name)
                    pass
        if (num !=0):
            return {ResourseFactory.PROD_HDD : num * int(quantity)}
        else:
            return 0

    @staticmethod
    def extractSSDv10(name, quantity, pn=''):
        ''' HDD GBs extractor, valid for Russia GPL from 18.01.2016
        :param name: name string
        :param quantity: quantity field
        :return:
        '''
        num = 0
        par = re.search('([0-9]+)\s*?GB.*(?=SSD)', name)               # parse first type of lines 400 GB ___ HDD
        if (par):                                           # success
            #print "   --1- par:%s  ___ line: %s"%(par.group(1), name)
            num = int(par.group(1))
        else:                                               # fail - try more
            par = re.search('[^0-9]*?([0-9.]+)\s*?TB.*(?=SSD)', name)               # parse second type of lines 1.2 TB ____ HDD
            if (par):                                           # success
                #print "   --2- par:%s  ___ line: %s"%(par.group(1), name)
                group = par.group(1).split('.')
                if (len(group) == 2):
                    num = int(group[0])*1000 + int(group[1]) * 100
                    #print "   --2- par:%s  ___ line: %s"%(num, name)
                elif (len(group) == 1):
                    num = int(group[0]) * 1000
                    #print "   --3- par:%s  ___ line: %s"%(num, name)
            else:
                par = re.search('[^0-9]*?([0-9.]+)\s*?GB.*(?=SD)', name)
                if (par):
                    num = int(par.group(1))
                    #print "   --4- par:%s  ___ line: %s"%(num, name)
                else:
                    par = re.search('([0-9]+)\s*?G.*(?=SSD)', name)
                    if (par):
                        num = int(par.group(1))
                        #print "   --5- par:%s  ___ line: %s"%(num, name)
                    else:
                        print "<<<< %s _________ line: %s"%(pn,name)
                        pass
        if (num !=0):
            return {ResourseFactory.PROD_SSD : num * int(quantity)}
        else:
            return 0

    @staticmethod
    def extractBUNDLv10(name, quantity, pn=''):
        ''' Bundl info extractor, valid for Russia GPL from 18.01.2016
        :param name: name string
        :param quantity: quantity field
        :return:
        '''
        num = 0
        par = re.search(',\s*?([0-9]+)x([0-9]+)\s*?(?=GB)', name)               # parse first type of lines 400 GB ___ HDD
        if (par):                                           # success
            #print "   --1- par:%s x %s ___ line: %s"%(par.group(1), par.group(2), name)
            num = int(par.group(1))*int(par.group(2))
        else:                                               # fail - try more
            par = re.search(',\s*?([0-9]+)x([0-9]+)x([0-9]+)\s*?GB', name)               # parse second type of lines 1.2 TB ____ HDD
            if (par):
                num = int(par.group(1))*int(par.group(2))*int(par.group(3))                                       # success
                #print "   --2- par:%s x %s x %s ___ line: %s"%(par.group(1), par.group(2), par.group(3), name)
            else:
                par = re.search(',\s*?([0-9]+)\s*?GB', name)
                if (par):
                    num = int(par.group(1))
                    #print "   --3- par:%s  ___ line: %s"%(num, name)
                else:
                    par = re.search(',\s*?([0-9]+)\s*?G', name)
                    if (par):
                        num = int(par.group(1))
                        #print "   --4- par:%s  ___ line: %s"%(num, name)
                    else:
                        #print "<<<< %s _________ line: %s"%(pn,name)
                        pass
        if (num !=0):
            return {ResourseFactory.PROD_MEM : num * int(quantity), 'WARNING': True}
        else:
            return {'WARNING': True}


    @staticmethod
    def dummyExtractor(name, quantity, pn=''):
        '''  Dummy extractor
        :param name:
        :param quantity:
        :param pn:
        :return:
        '''
        return 0

    @staticmethod
    def extractValues(type, name, quantity):
        if type == ResourseFactory.PROD_CPU:
            return ResourseFactory.extractCPUv10(name, quantity)
        if type == ResourseFactory.PROD_MEM:
            return ResourseFactory.extractMEMv10(name, quantity)
        if type == ResourseFactory.PROD_HDD:
            return ResourseFactory.extractHDDv10(name, quantity)
        if type == ResourseFactory.PROD_SSD:
            return ResourseFactory.extractSSDv10(name, quantity)
        if type == ResourseFactory.PROD_BUNDL:
            return ResourseFactory.extractBUNDLv10(name, quantity)
        return None

    @staticmethod
    def checkIsBundle(line_pn):
        '''
        :param line_pn: partnumber
        :return: dict {'WARNING' : True} if PN in bundle, else - false

        '''
        #print "Got: %s parameter, iterate over: %s"%(line_pn, ResourseFactory.product_filters[ResourseFactory.PROD_BUNDL])
        for filter in ResourseFactory.product_filters[ResourseFactory.PROD_BUNDL]:
            if line_pn.startswith(filter):
                return {'WARNING': True}        # return tag if part of bundle except - None
        return None

