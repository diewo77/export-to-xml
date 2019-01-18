import datetime
import os
from xml.etree.cElementTree import Element, SubElement, ElementTree
import pyodbc

server = 'tcp:192.168.1.254'
database = 'ES019'
username = 'sa'
password = 'cegid.2008'


def sales_file():
    cnxn = pyodbc.connect(
        'DRIVER={SQL Server};SERVER=' + server + ';DATABASE=' + database + ';UID=' + username + ';PWD=' + password)
    cursor = cnxn.cursor()

    today = datetime.datetime.now().strftime('%Y-%m-%d')
    yesterday = (datetime.date.today() - datetime.timedelta(1)).strftime('%Y-%m-%d')

    cursor.execute("""SELECT GL_NATUREPIECEG, FORMAT(GL_DATEPIECE,'yyyy-MM-dd'), GL_NUMERO AS TransactionId, CC3.CC_LIBELLE as FN4,
        GL_CODEARTICLE, GL_TIERS, T_LIBELLE, ART.GA_CODEBARRE AS CODEBARRE,
        CAST(GL_QTEFACT AS INT ) As QuantitySold, 
        CAST(ROUND(GL_PRHT*1.20,-1) AS INT ) as ItemPriceCalculatedNetAmount, 
        CAST((GL_TOTALTTC - 700) AS INT ) AS ItemPriceInformationInclTAXAmount, 
        CAST(((GL_PUTTC*gl_qtefact) - 700) AS INT ) AS NormalSalesPrice,
        GL_REMISELIGNE, GL_DEVISE, 
        FORMAT(GP_HEURECREATION,'yyyy-MM-dd-HH-mm-ss') as SalesTime
        FROM GCLIGNEARTDIM
        LEFT OUTER JOIN ETABLISS ET1 ON GL_ETABLISSEMENT=ET1.ET_ETABLISSEMENT
        LEFT OUTER JOIN ARTICLECOMPL AC on GL_ARTICLE = GA2_ARTICLE
        LEFT OUTER JOIN ARTICLE ART on GL_ARTICLE = GA_ARTICLE
        LEFT OUTER JOIN CHOIXCOD CC3 ON AC.GA2_FAMILLENIV4=CC3.CC_CODE AND CC3.CC_TYPE='FN4'
        WHERE (GL_DATEPIECE = '20190103' AND (GL_NATUREPIECEG = 'FFO') AND ((GL_TYPELIGNE <> 'COM' AND GL_TYPELIGNE <> 'TOT'))
        AND (GL_ETABLISSEMENT='008') AND (T_NATUREAUXI = 'CLI') AND GP_TICKETANNULE<>'X')
        ORDER BY GL_ETABLISSEMENT ,GL_CAISSE ,GL_NUMLIGNE""")
    rows = cursor.fetchall()

    in_sales_report_nonbspos = Element("InSalesReportNonbspos",
                                       {'xmlns': 'http://Bestseller.BizTalk.Object.InSalesReport.CustomXml.Schemas'})
    #
    # #header
    header = SubElement(in_sales_report_nonbspos, "Header")
    SubElement(header, "DocumentIdentification").text = "AA11223344"
    SubElement(header, "DocumentType").text = "SalesDataReport"
    header_date = SubElement(header, "Date")
    SubElement(header_date, "DocumentDate").text = str(today)
    SubElement(header_date, "SalesReportPeriodStartDate").text = str(yesterday)
    SubElement(header_date, "SalesReportPeriodEndDate").text = str(yesterday)
    # ##Parties
    header_parties = SubElement(header, "Parties")
    # ###BuyerParty
    parties_buyer_party = SubElement(header_parties, "BuyerParty")
    SubElement(parties_buyer_party, "Name").text = "EuropaSport"
    buyer_party_party_identification_detail = SubElement(parties_buyer_party, "PartyIdentificationDetail")
    SubElement(buyer_party_party_identification_detail, "GlobalLocationNumber").text = "1234567890123"
    # ###SupplierParty
    parties_supplier_party = SubElement(header_parties, "SupplierParty")
    SubElement(parties_supplier_party, "Name").text = "Bestseller A/S"
    supplier_party_party_identification_detail = SubElement(parties_supplier_party, "PartyIdentificationDetail")
    SubElement(supplier_party_party_identification_detail, "GlobalLocationNumber").text = "5790000425921"

    # #sales_locations
    sales_locations = SubElement(in_sales_report_nonbspos, "SalesLocations")
    sales_location = SubElement(sales_locations, "SalesLocation")
    seller_party = SubElement(sales_location, "SellerParty")
    SubElement(seller_party, "Name").text = "El Senia - Oran"
    party_identification_detail = SubElement(seller_party, "PartyIdentificationDetail")
    SubElement(party_identification_detail, "GlobalLocationNumber").text = "1234567890123"

    sales_location_date = SubElement(sales_location, "Date")
    SubElement(sales_location_date, "SalesDate").text = str(yesterday)

    sales_report_lines = SubElement(sales_location, "SalesReportLines")

    cntr = 1
    # Ligne de vente a envoyer en boucle
    for row in rows:
        sales_report_line = SubElement(sales_report_lines, "SalesReportLine")
        SubElement(sales_report_line, "LineNumber").text = str(cntr)
        SubElement(sales_report_line, "TransactionId").text = str(row.TransactionId)
        SubElement(sales_report_line, "TransactionType").text = "Normal"
        SubElement(sales_report_line, "SalesTime").text = row.SalesTime
        sales_person = SubElement(sales_report_line, "SalesPerson")
        SubElement(sales_person, "Name").text = row.T_LIBELLE
        SubElement(sales_person, "Identifier").text = row.GL_TIERS
        item = SubElement(sales_report_line, "Item")
        SubElement(item, "ItemGlobalTradeItemNumber").text = str(row.CODEBARRE)
        SubElement(item, "ItemDescription").text = row.FN4
        quantity = SubElement(sales_report_line, "Quantity")
        SubElement(quantity, "QuantitySold").text = str(row.QuantitySold)
        price_detail = SubElement(sales_report_line, "PriceDetail")
        SubElement(price_detail, "ItemPriceCalculatedNetAmount").text = str(row.ItemPriceCalculatedNetAmount)
        SubElement(price_detail, "ItemPriceCalculatedNetCurrency").text = row.GL_DEVISE
        SubElement(price_detail, "ItemPriceInformationInclTAXAmount").text = str(row.ItemPriceInformationInclTAXAmount)
        SubElement(price_detail, "ItemPriceInformationInclTAXCurrency").text = row.GL_DEVISE
        SubElement(price_detail, "TaxRate1").text = "19"
        SubElement(price_detail, "TaxRate2").text = "0"
        SubElement(price_detail, "NormalSalesPrice").text = str(row.NormalSalesPrice)
        SubElement(price_detail, "NormalSalesCurrency").text = row.GL_DEVISE
        cntr += 1

    tree = ElementTree(in_sales_report_nonbspos)
    today = datetime.datetime.now()
    file_name = "sales_" + today.strftime("%d_%m_%Y_%H%M%S") + ".xml"
    print(file_name)
    fullname = os.path.join('sales', file_name)
    tree.write(fullname, encoding='UTF-8', xml_declaration=True)


def inventory_file():
    cnxn = pyodbc.connect(
        'DRIVER={SQL Server};SERVER=' + server + ';DATABASE=' + database + ';UID=' + username + ';PWD=' + password)
    cursor = cnxn.cursor()

    today = datetime.datetime.now().strftime('%Y-%m-%d')
    yesterday = (datetime.date.today() - datetime.timedelta(1)).strftime('%Y-%m-%d')

    cursor.execute("""SELECT ART.GA_CODEBARRE AS 'ItemGlobalTradeItemNumber', CAST(SUM(GQ_PHYSIQUE) AS INT ) AS 'QuantityStock', 
                    MAX(CC3.CC_LIBELLE) as 'ItemDescription'
                    FROM   DISPO 
                    LEFT OUTER JOIN ARTICLECOMPL AC on GQ_ARTICLE = GA2_ARTICLE
                    LEFT OUTER JOIN ARTICLE ART on GQ_ARTICLE = GA_ARTICLE
                    LEFT OUTER JOIN CHOIXCOD CC3 ON AC.GA2_FAMILLENIV4=CC3.CC_CODE AND CC3.CC_TYPE='FN4'
                    WHERE (((ART.GA_STATUTART='UNI' or ART.GA_STATUTART='DIM')) AND (GQ_DEPOT='008')
                    AND (GQ_PHYSIQUE > 0) AND GQ_CLOTURE<>'X' AND GA_FERME<>'X')
                    GROUP BY ART.GA_CODEBARRE
                    """)
    rows = cursor.fetchall()

    bs_in_inventory_report = Element("BSInInventoryReport",
                                     {
                                         'xmlns': 'http://Bestseller.BizTalk.Object.InInventoryReport.BSInInventoryReport10.Schemas',
                                         'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
                                         'xsi:schemaLocation': 'http://Bestseller.BizTalk.Object.InInventoryReport.BSInInventoryReport10.Schemas BSInventoryReport_10_XML.xsd'
                                     })
    #
    # #header
    header = SubElement(bs_in_inventory_report, "Header")
    SubElement(header, "DocumentIdentification").text = "AA11223344"
    SubElement(header, "DocumentType").text = "OnStock"
    header_date = SubElement(header, "Date")
    SubElement(header_date, "DocumentDate").text = str(today)
    SubElement(header_date, "InventoryReportDate").text = str(yesterday)
    # ##Parties
    header_parties = SubElement(header, "Parties")
    # ###BuyerParty
    parties_buyer_party = SubElement(header_parties, "BuyerParty")
    SubElement(parties_buyer_party, "Name").text = "EuropaSport"
    buyer_party_party_identification_detail = SubElement(parties_buyer_party, "PartyIdentificationDetail")
    SubElement(buyer_party_party_identification_detail, "GlobalLocationNumber").text = "1234567890123"
    # ###SupplierParty
    parties_supplier_party = SubElement(header_parties, "SupplierParty")
    SubElement(parties_supplier_party, "Name").text = "Bestseller A/S"
    supplier_party_party_identification_detail = SubElement(parties_supplier_party, "PartyIdentificationDetail")
    SubElement(supplier_party_party_identification_detail, "GlobalLocationNumber").text = "5790000425921"

    inventory_report_locations = SubElement(bs_in_inventory_report, "InventoryReportLocations")

    inventory_report_location = SubElement(inventory_report_locations, "InventoryReportLocation")
    inventory_reporting_party = SubElement(inventory_report_location, "InventoryReportingParty")
    SubElement(inventory_reporting_party, "Name").text = "EuropaSport"
    party_identification_detail = SubElement(inventory_reporting_party, "PartyIdentificationDetail")
    SubElement(party_identification_detail, "GlobalLocationNumber").text = "3838514999599"

    inventory_report_lines = SubElement(inventory_report_location, "InventoryReportLines")
    ## Loop

    cntr = 1
    # Ligne de vente a envoyer en boucle
    for row in rows:

        inventory_report_line = SubElement(inventory_report_lines, "InventoryReportLine")
        SubElement(inventory_report_line, "LineNumber").text = str(cntr)

        inventory_report_line_item = SubElement(inventory_report_line, "Item")
        SubElement(inventory_report_line_item, "ItemGlobalTradeItemNumber").text = str(row.ItemGlobalTradeItemNumber)
        SubElement(inventory_report_line_item, "ItemDescription").text = str(row.ItemDescription)

        inventory_report_line_quantity = SubElement(inventory_report_line, "Quantity")
        SubElement(inventory_report_line_quantity, "QuantityStock").text = str(row.QuantityStock)
        SubElement(inventory_report_line_quantity, "MeasurementUnitCode").text = "PCE"
        cntr += 1

    tree = ElementTree(bs_in_inventory_report)
    today = datetime.datetime.now()
    file_name = "inventory_" + today.strftime("%d_%m_%Y_%H%M%S") + ".xml"
    print(file_name)
    fullname = os.path.join('inventory', file_name)
    tree.write(fullname, encoding='UTF-8', xml_declaration=True)


# TODO Make the file upload to an FTP Server
# TODO I will keep a copy of the file locally
# TODO Make the scripts executes every day
inventory_file()
