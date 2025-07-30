import mimetypes, traceback
from openai import OpenAI
import json
import os
import pandas as pd
import fitz  # PyMuPDF
from docx import Document
import pdfplumber
import docx2txt
import html
from weasyprint import HTML
import weaviate
from weaviate.gql.get import HybridFusion
import re
import loggerutility as logger
import commonutility as common

# from .OpenAIDataExtractor import OpenAIDataExtractor
# from .GenerateExtractTemplate import GenerateExtractTemplate

class Document_Automated_Training:

    alphaValue = 0.54

    def identify_complexity_layout_structure(self, extracted_text, openai_api_key):

        prompt = f"""
            From the following text which is extracted from a customer purchase order. Analyze the layout and answer following specific questions
            -What is the complexity percentage of the layout simplest is 0 most complex is 100(complexity_perc)?
            Note: Basis of complexity should be if the data is organized in a simple, structured and easy to extract to structured format
            -Is the line items grouped by Division(division_grouping)?
            -Is there a summary line at the end of Items of a division(is_division_summary)?
            -Is the layout containing multiple data sets in the same row next to each other(is_layout_columnar)?
            -How many sets are there in a row(no_datasets_in_row)?
            -Is there multiple orders in the same document (multiple_order)?
            -Return the distinct division list in the order(division_list).
            -Is the document an unstructured email. There is no organized data in any pattern(unstructured_email)?
            Return the data in json format with tag specified against the question with answer as true, false or number

            Text:
            \"\"\"
            {extracted_text}
            \"\"\"
            """
        
        message = [{
            "role": "user",
            "content": prompt
        }]

        client = OpenAI(api_key=openai_api_key)
        completion = client.chat.completions.create(
                        model='gpt-4.1',
                        messages=message,
                        temperature=0
                    )
        result =  completion.choices[0].message.content 
        try:
            # reply = json.loads(result.choices[0].message.content.replace("\n```", "").replace("```", "").replace("json","").replace("JSON","").replace("csv","").replace("CSV",""))
            match = re.search(r'```json\s*(.*?)\s*```', result, re.DOTALL)
            data = {}
            if match:
                json_str = match.group(1).strip()
                json_str = json_str.replace("\n```", "").replace("```", "").replace("json","").replace("JSON","").replace("csv","").replace("CSV","")
                data = json.loads(json_str)
            return data
        except Exception as e:
            return {"error": "Failed to parse response", "message": str(e), "raw_response": result}

    def identify_customer_keywords(self, extracted_text, openai_api_key):
        prompt = f"""
            Following is an extracted text from a purchase order document issued by a customer to supply goods. 
            Identify unique keywords from the data. The keyword should be such that it would be always present 
            in this type of document received. All keywords together should be unique enough to ensure that a 
            code can identify the customer using regex. Typical keywords can be name of customer, part of address 
            such as city, GST No, customer telephone number. Just return maximum 4 in csv string

            Text:
            \"\"\"
            {extracted_text}
            \"\"\"
        """

        message = [{
            "role": "user",
            "content": prompt
        }]

        client = OpenAI(api_key=openai_api_key)
        completion = client.chat.completions.create(
                        model='gpt-4.1',
                        messages=message,
                        temperature=0
                    )
        result =  completion.choices[0].message.content 
        return result
    
    def identify_customer_code(self, cust_name, openai_api_key, schemaName_Updated, server_url):
        finalResultJson = {}
        client = weaviate.Client(server_url,additional_headers={"X-OpenAI-Api-Key": openai_api_key})
        logger.log(f'Connection is establish : {client.is_ready()}')

        schemaClasslist = [i['class'] for i in client.schema.get()["classes"]]  
        inputQuery  = cust_name.upper().replace("N/A","").replace("."," ").replace(","," ").replace("-"," ").replace("_"," ")
        if schemaName_Updated in schemaClasslist:
            response    = (
                client.query
                .get(schemaName_Updated, ["description", "answer", "city"]) 
                .with_hybrid(
                                alpha       =  self.alphaValue ,
                                query       =  inputQuery.strip() ,
                                fusion_type =  HybridFusion.RELATIVE_SCORE
                            )
                .with_additional('score')
                .with_limit(10)
                .do()
                )
            logger.log(f"Input ::: {cust_name}")
            if response != {}:
                response_List = response['data']['Get'][schemaName_Updated] 
                finalResultJson = {"cust_code": response_List[0]['answer'] , "cust_name": response_List[0]['description'] , "city": response_List[0]['city'] } if len(response_List) > 0 else {}

                for index in range(len(response_List)):
                    cust_name           = response_List[index]['description']
                    cust_name           = cust_name.upper().replace("N/A","").replace("."," ").replace(","," ").replace("-"," ").replace("_"," ")
                    cust_code           = response_List[index]['answer']
                    city                = response_List[index]['city']

                    descr_replaced      = cust_name.replace(" ", "") 
                    inputQuery_replaced = inputQuery.replace(" ", "")

                    if descr_replaced == inputQuery_replaced:
                        logger.log(f"\n Input::: '{inputQuery_replaced}' MATCHEDD with description ::: '{descr_replaced}' \n")
                        finalResultJson    =  {"cust_code": cust_code, "cust_name": cust_name, "city": city } 
                        break
                    else:
                        logger.log(f"\n Input '{inputQuery_replaced}' not matched with returned response description '{descr_replaced}'\n ")    
            return finalResultJson
    
    def identify_line_example(self, extracted_text, openai_api_key):
        message = [{
            "role": "user",
            "content": "Can you give me a list of brands?",
            "role": "assistant",
            "content": "Following are sample brand list (select from table)",
            "role": "user",
            "content": f"""From the following text which is extracted from a customer purchase order. Extract only distinct patterns of line item raw data. Distinct should be identified based on the way line item data is organized. For each distinct line item extract raw data, Line No, Sku Name, Packing (Ordering unit), Order Quantity, Free Quantity or Percentage(if specified), From SKU Name also identify Product Name, Delivery method (Tablet, Capsules, Injection, Powder, Syrup), Product Strength, Pack Size Return only the data in json format with following tag name sample_id, raw_data, line_no, sku_name, ordering_unit, quantity, free_quantity, free_percent, product_name, strength, pack_size, delivery_method.
                Text:
                \"\"\"
                {extracted_text}
                \"\"\"
            """
        }]

        client = OpenAI(api_key=openai_api_key)
        completion = client.chat.completions.create(
                        model='gpt-4.1',
                        messages=message,
                        temperature=0
                    )
        result =  completion.choices[0].message.content
        try:
            # reply = json.loads(result.choices[0].message.content.replace("\n```", "").replace("```", "").replace("json","").replace("JSON","").replace("csv","").replace("CSV",""))
            match = re.search(r'```json\s*(.*?)\s*```', result, re.DOTALL)
            data = {}
            if match:
                json_str = match.group(1).strip()
                json_str = json_str.replace("\n```", "").replace("```", "").replace("json","").replace("JSON","").replace("csv","").replace("CSV","")
                data = json.loads(json_str)
            return data
        except Exception as e:
            return {"error": "Failed to parse response", "message": str(e), "raw_response": result}

    def get_main_page_line(self, json_data):
        if 'ai_proc_variables' in json_data:
            ai_proc_vars_str = json_data['ai_proc_variables']
            try:
                ai_proc_vars = json.loads(ai_proc_vars_str)  # convert to dict
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON in 'ai_proc_variables': {e}")

            if 'Details' in ai_proc_vars:
                for i in ai_proc_vars['Details']:
                    if 'displayName' in i and i['displayName'] == 'Main Page':
                        return i['defaultValue']
        return None
    
    def get_Split_Text(self, main_page_line, phrase):
        sentences = re.split(r'(?<=[.])\s+', main_page_line)

        target_sentence = ""
        for sentence in sentences:
            if phrase in sentence:
                target_sentence = sentence.strip()
                break

        if target_sentence:
            part1 = main_page_line.split(target_sentence)[0].strip()
            part2 = target_sentence
            part3 = main_page_line.split(target_sentence)[1].strip()
        else:
            part1 = main_page_line
            part2 = ""
            part3 = ""

        return part1, part2, part3

    def generate_main_page_instruction(self, ocr_data, open_ai_key, json_data):
        try:
            doc_type = ""
            main_page_line = ""
            result_dict = {}

            model_name = "AIT"
            # main_page_line = self.get_main_page_line(json_data)

            if 'doc_type' in json_data.keys():
                doc_type = json_data['doc_type']
            logger.log(f"\ngenerate_main_page_instruction doc_type ::: {doc_type}")

            if doc_type == "Orders":
                main_page_line = f"""/* Following is the data of the order document. GLAXO is seller of this document, not the purchaser. Some of products Ordering Unit and Size is same. It has a header and multiple line items. SKU are grouped by Division which is to be ignored. Line items are in tabular format. */ <DOCUMENT_DATA> Extract complete information from above document. Include columns Order Number, Order Date, Delivery Date and Purchaser from header part strictly in json format. Where as each detail items extract Sr. No(Heading Sr#), SKU Name, Ordering Unit, Quantity, Product Name, Delivery Method, Product Strength, Size strictly in csv format with headings. Put all column values in quotes:"""    
            elif doc_type == "Order Excel":
                main_page_line = f"""/* Following is the data of the order document. GLAXO is seller of this document, not the purchaser. Some of products Ordering Unit and Size is same. It has a header and multiple line items. SKU are grouped by Division which is to be ignored. Line items are in tabular format. */ <DOCUMENT_DATA> Extract complete information from above document. Include columns Order Number, Order Date, Delivery Date and Purchaser from header part strictly in json format. Where as each detail items extract Sr. No(Heading Sr#), SKU Name, Ordering Unit, Quantity, Product Name, Delivery Method, Product Strength, Size strictly in csv format with headings. Put all column values in quotes:"""
            elif doc_type == "Order Email":
                main_page_line = f"""/* Following is the data of the order document. GLAXO is seller of this document, not the purchaser. Some of products Ordering Unit and Size is same. It has a header and multiple line items. SKU are grouped by Division which is to be ignored. Line items are in tabular format. */ <DOCUMENT_DATA> Extract complete information from above document. Include columns Order Number, Order Date, Delivery Date and Purchaser from header part strictly in json format. Where as each detail items extract Sr. No(Heading Sr#), SKU Name, Ordering Unit, Quantity, Product Name, Delivery Method, Product Strength, Size strictly in csv format with headings. Put all column values in quotes:"""             

            logger.log(f"\nmain_page_line ::: {main_page_line}")
            if ocr_data:
                res = self.identify_complexity_layout_structure(ocr_data, open_ai_key)
                logger.log(f"\ncomplexity_layout_structure ::: {res}")

                if 'complexity_perc' in res:
                    if res['complexity_perc'] > 80:
                        model_name = "AIT4O" 
                logger.log(f"\nmodel_name ::: {model_name}")

                if 'division_grouping' in res and 'division_list' in res:
                    if res['division_grouping'] == True and len(res['division_list']) > 0:
                        logger.log(f"Inside 1st condition.....")
                        division_names = ', '.join(res.get('division_list', []))
                        phrase = "SKU are grouped"
                        start_part, middle_part, end_part = self.get_Split_Text(main_page_line, phrase)
                        main_page_line = f"{start_part} SKUs are grouped by Division and at the end of Division there is a line showing total of Division, Division Names are {division_names}. {end_part}"
                    elif res['is_division_summary'] == False:
                        logger.log(f"Inside 2nd condition.....")
                        phrase = "SKU are grouped"
                        start_part, middle_part, end_part = self.get_Split_Text(main_page_line, phrase)
                        main_page_line = f"{start_part} SKU are grouped by Division, Division Names are GSK-DERMA ACE, GSK-FORTIOR, GLAXO INGINIUM. {end_part}"

                if 'free_quantity_column' in res:
                    if res['free_quantity_column'] == True:
                        logger.log(f"Inside 3rd condition... Add line for free quantity...")
                        phrase = "Line items are in"
                        start_part, middle_part, end_part = self.get_Split_Text(main_page_line, phrase)
                        main_page_line = f"{start_part} {middle_part} FREE can be a fixed value or percentage. {end_part.replace('Quantity', 'Quantity, FREE')}"

                if 'unstructured_email' in res:
                    if res['unstructured_email'] == True:
                        logger.log(f"Inside 4rd condition... Unstructured Email...")
                        main_page_line = f"/* Following is data of email received from a customer of Glaxo, which needs to be extracted and converted to structured format. GLAXO is the seller of this document, not the purchaser. It has a header and multiple line items. Quantity is always specified against each line item, whereas Strength and Size can be optional. SKU can be grouped by Division which is to be ignored. */    /* Ordering units can be placed in standard packing of items or any other units such as box or case pack.  When an ordering-unit is present, output it **exactly as written in the source (line-item), including capitalisation and punctuation**; do not expand, translate, or normalise it.   **Always use the ordering-unit that already appears in the line-item. Only if the ordering unit is not specified, derive it using the following table.**  */ /* Derive-Unit table (tablet or cap or capsule = STRIPS, syrup or cream or ointment = NOS, injection or  inj = VIALS) */  /* If the quantity is specified as numeric value1 + numeric value2 calculate quantity by adding both the values. In this case the 1st numeric value is the chargeable quantity and the 2nd value is the free quantity. When the free quantity is specified as a percentage, do not perform the calculation, just consider  the chargeable value as the quantity.*/  <DOCUMENT_DATA> Extract complete information from above document. Include columns Order Number, Order Date, Delivery Date and Purchaser from header part strictly in json format. Whereas for each detail items extract Sr. No(Heading Sr#), SKU Name, Ordering Unit, Quantity, Product Name, Delivery Method, Product Strength, Size strictly in csv format with headings. Put all column values in quotes:"

                logger.log(f"\nmain_page_line ::: {main_page_line}")

                result_dict = {
                    "default_value" : main_page_line,
                    "modelname" : model_name
                }

            return result_dict      
        except Exception as error:
            raise str(error)  

    def generate_line_example(self, ocr_data, open_ai_key):
        try:
            line_example_json_data = self.identify_line_example(ocr_data, open_ai_key)
            logger.log(f"\nline_example_json_data length ::{len(line_example_json_data)}")

            line_examples = []
            for item in line_example_json_data:
                line_no = item.get('line_no')
                sku_name = item.get('sku_name')
                pack_size = item.get('pack_size')
                quantity = item.get('quantity')
                ordering_unit = item.get('ordering_unit')
                product_name = item.get('product_name')
                delivery_method = item.get('delivery_method')
                strength = item.get('strength')
                quantity = str(quantity).replace(",","") if quantity else None

                first_parts = [
                    f"In Line Item {line_no}" if line_no else "",
                    sku_name if sku_name else "",
                    pack_size if pack_size else "",
                    quantity if quantity else "",
                    ordering_unit if ordering_unit else ""
                ]
                first_sentence = ", ".join(filter(None, first_parts)) + "."

                kv_map = {
                    "Line Number": line_no,
                    "SKU Name": sku_name,
                    "Ordering Unit": ordering_unit,
                    "Quantity": quantity,
                    "Product Name": product_name,
                    "Delivery Method": delivery_method,
                    "Product Strength": strength
                }

                second_sentence = ", ".join(
                    [f"{key} is {value}" for key, value in kv_map.items() if value not in [None, ""]]
                ) + "."

                line_examples.append(f"{first_sentence} {second_sentence}")

            final_line_example = "Example of Line Item organisation are as following. " + " ".join(line_examples)
            logger.log(f"\nfinal_line_example ::: {final_line_example}")

            result_dict = {
                "default_value" : final_line_example,
            }

            return result_dict        
        except Exception as error:
            raise str(error)  