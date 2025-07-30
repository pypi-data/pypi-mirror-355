from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Dict, Optional
import xml.etree.ElementTree as ET
import os
import logging
import traceback

# Configure logging
logger = logging.getLogger(__name__)

from typing import List, Dict, Optional, Union
from pydantic import BaseModel, Field, RootModel

class Summary(BaseModel):
    report_name: str
    published_datasource: int
    embedded_datasource: int
    calculations: int
    dashboards: int
    sheets: int
    parameters: int
    tables: int
    hours: Optional[int] = None

class Sheet(BaseModel):
    worksheet_name: str
    chart: List[str]

class Calculation(RootModel):
    root: Dict[str, str]

class DatasourceInfo(BaseModel):
    datasource_name: str
    filters: List[str]
    row_level_identifier: str

class Details(BaseModel):
    report_name: str
    dashboards: List[str]
    sheets: List[Sheet]
    charts: List[str]
    tables: List[str]
    published_data_sources: List[str]
    embedded_data_sources: List[str]
    connections: List[str]
    calculations: List[Calculation]
    live_extract: Dict[str, str]
    actions: List[str]
    parameters: List[str]
    filters: List[str]
    joins: List[str]
    datasource_info: List[DatasourceInfo]

class TableauWorkbookAnalysis(BaseModel):
    summary: Summary
    details: Details

class TableauWorkbookResponse(RootModel):
    root: List[TableauWorkbookAnalysis] 

class TableauParserError(Exception):
    """Base exception for Tableau parser errors"""
    pass

class FileNotFoundError(TableauParserError):
    """Raised when the Tableau workbook file is not found"""
    pass

class InvalidFileError(TableauParserError):
    """Raised when the file is not a valid Tableau workbook"""
    pass

class ParsingError(TableauParserError):
    """Raised when there's an error parsing the Tableau workbook"""
    pass

class TableauParser(ABC):
    """Abstract base class for parsing Tableau workbook components"""
    @abstractmethod
    def parse(self, root: ET.Element) -> Dict:
        pass

class SummaryParser(TableauParser):
    """Parser for workbook summary information"""
    def parse(self, root: ET.Element) -> Dict:
        datasource_set = set()
        published_datasource_set = set()
        total_calculations = 0
        total_sheets = 0
        total_parameters = 0
        total_tables = 0
        tables_set = set()  # To track unique tables

        # Parse datasources
        for datasource in root.findall('./datasources/datasource'):
            caption = datasource.get('caption')
            if caption:
                datasource_set.add(caption)
                
                # Count unique calculations
                for column in datasource.findall('.//column'):  # Changed to search all nested columns
                    # Count if it's a calculated field (has calculation element)
                    if column.find('.//calculation') is not None and column.get('caption'):
                        total_calculations += 1

            # Count parameters
            if caption is None and datasource.get('name') == "Parameters":
                total_parameters = len(datasource.findall('./column'))

            # Check for published datasources
            connection = datasource.find('connection')
            if connection is not None and connection.get('class') == 'sqlproxy':
                published_datasource_set.add(caption)

        # Count dimensions and tables
        for datasource in root.findall('./datasources/datasource'):
            skip_table = False
            
            for relation in datasource.findall('.//relation'):
                table = relation.get('table')
                if table:
                    if table != "[Extract].[Extract]":
                        # Clean table name and add to set
                        clean_table = table.strip('[]').split('.')[-1]
                        if clean_table and clean_table not in ["Extract", "sqlproxy"]:
                            tables_set.add(clean_table)
                    else:
                        skip_table = True

        total_dashboards = len(root.findall('./dashboards/dashboard'))
        total_sheets = len(root.findall('./worksheets/worksheet'))
        total_tables = len(tables_set)  # Use the count of unique tables

        return {
            "report_name": os.path.basename(root.get('_filename', '')),
            "published_datasource": len(published_datasource_set),
            "embedded_datasource": len(datasource_set) - len(published_datasource_set),
            "calculations": total_calculations,
            "dashboards": total_dashboards,
            "sheets": total_sheets,
            "parameters": total_parameters,
            "tables": total_tables,
            "hours": None
        }

class DetailsParser(TableauParser):
    """Parser for workbook detailed information"""
    def parse(self, root: ET.Element) -> Dict:
        calculations = self._parse_calculations(root)
        # Ensure each calculation is a dictionary
        formatted_calculations = []
        for calc in calculations:
            if isinstance(calc, str):
                # If it's a string, convert it to a dictionary with empty formula
                formatted_calculations.append({calc: ""})
            elif isinstance(calc, dict):
                formatted_calculations.append(calc)
            else:
                # Skip invalid calculations
                continue

        return {
            "report_name": os.path.basename(root.get('_filename', '')),
            "dashboards": self._parse_dashboards(root),
            "sheets": self._parse_sheets(root),
            "charts": self._parse_charts(root),
            "tables": self._parse_tables(root),
            "published_data_sources": self._parse_published_datasources(root),
            "embedded_data_sources": self._parse_embedded_datasources(root),
            "connections": self._parse_connections(root),
            "calculations": formatted_calculations,
            "live_extract": self._parse_live_extract(root),
            "actions": self._parse_actions(root),
            "parameters": self._parse_parameters(root),
            "filters": self._parse_filters(root),
            "joins": self._parse_joins(root),
            "datasource_info": self._parse_datasource_info(root)
        }

    def _parse_dashboards(self, root: ET.Element) -> List[str]:
        return [d.get("name") for d in root.findall(".//dashboards/dashboard") 
                if d.get("type") != "storyboard" and d.get("name") is not None]

    def _parse_sheets(self, root: ET.Element) -> List[Dict]:
        sheets = []
        for worksheet in root.findall(".//worksheets/worksheet"):
            temp_charts = []
            for chart in worksheet.findall(".//mark"):
                chart_class = chart.get("class", "")
                if chart_class:
                    chart_class = chart_class.replace("Automatic", "Tableau Default")
                    temp_charts.append(chart_class)
            
            worksheet_name = worksheet.get("name")
            if worksheet_name:
                sheets.append({
                    "worksheet_name": worksheet_name,
                    "chart": temp_charts
                })
        return sheets

    def _parse_charts(self, root: ET.Element) -> List[str]:
        charts = []
        for chart in root.findall(".//mark"):
            chart_class = chart.get("class", "")
            if chart_class:
                chart_class = chart_class.replace("Automatic", "Tableau Default")
                charts.append(chart_class)
        return list(set(charts))

    def _parse_tables(self, root: ET.Element) -> List[str]:
        tables = set()
        for relation in root.findall(".//relation"):
            table = relation.get("name")
            if table and table not in ["Extract", "sqlproxy"]:
                tables.add(table)
        return list(tables)

    def _parse_published_datasources(self, root: ET.Element) -> List[str]:
        return [d.get("caption") for d in root.findall("./datasources/datasource")
                if d.get("caption") and "sqlproxy" in (d.get("name") or "")]

    def _parse_embedded_datasources(self, root: ET.Element) -> List[str]:
        return [d.get("caption") for d in root.findall("./datasources/datasource")
                if d.get("caption") and "sqlproxy" not in (d.get("name") or "")]

    def _parse_connections(self, root: ET.Element) -> List[str]:
        connections = set()
        for connection in root.findall(".//named-connection/connection"):
            conn_class = connection.get("class")
            if conn_class:
                connections.add(conn_class)
        return list(connections)

    def _parse_calculations(self, root: ET.Element) -> List[Dict]:
        calculations = []
        seen_calculations = set()  # To track unique calculations
        name_caption_mapping = {}

        # First pass: build name-caption mapping
        for column in root.findall(".//column"):
            name = column.get("name")
            caption = column.get("caption")
            if name and caption:
                name_caption_mapping[name] = caption    

        # Second pass: process calculations
        for datasource in root.findall(".//datasource"):
            for column in datasource.findall(".//column"):
                if column.get("name") != "Parameters":
                    formula_element = column.find(".//calculation")
                    if formula_element is not None:
                        formula = formula_element.get("formula", "")
                        name = column.get("caption")
                        
                        # Include calculation even if formula is empty
                        if name:  # Only require name to be present
                            # Replace IDs with names in formula if formula exists
                            if formula:
                                for formula_id, caption in name_caption_mapping.items():
                                    if formula_id and formula_id in formula:
                                        formula = formula.replace(
                                            formula_id,
                                            f'[{caption}]' if caption else formula_id
                                        )
                            
                            # Create a unique key for this calculation
                            calc_key = f"{name}:{formula}"
                            
                            # Only add if we haven't seen this calculation before
                            if calc_key not in seen_calculations:
                                seen_calculations.add(calc_key)
                                # Create a dictionary with the calculation name as key and formula as value
                                calculations.append({name: formula})
        
        return calculations

    def _parse_live_extract(self, root: ET.Element) -> Dict[str, str]:
        live_extract = {}
        for datasource in root.findall("./datasources/datasource"):
            caption = datasource.get("caption")
            if caption:
                properties = datasource.findall(".//properties")
                property_list = []
                for p in properties:
                    relation = p.find("relation")
                    if relation is not None:
                        name = relation.get("name")
                        if name:
                            property_list.append(name)
                
                if "Extract" in property_list:
                    live_extract[caption] = "Extract"
                else:
                    live_extract[caption] = "Live"
        return live_extract

    def _parse_actions(self, root: ET.Element) -> List[str]:
        return [action.get("caption") for action in root.findall("./actions/action")
                if action.get("caption") is not None]

    def _parse_parameters(self, root: ET.Element) -> List[str]:
        parameters = []
        for datasource in root.findall("./datasources/datasource"):
            if datasource.get("name") == "Parameters":
                for col in datasource.findall("./column"):
                    caption = col.get("caption")
                    if caption:
                        parameters.append(caption)
        return parameters

    def _parse_filters(self, root: ET.Element) -> List[str]:
        filters = set()
        for filter_elem in root.findall(".//view/filter"):
            column = filter_elem.get("column", "")
            if column and "none:" in column:
                try:
                    filter_name = column.split("none:")[1].split(":")[0].split("]")[0]
                    if filter_name:
                        filters.add(filter_name)
                except IndexError:
                    continue
        return list(filters)

    def _parse_joins(self, root: ET.Element) -> List[str]:
        joins = []
        seen_joins = set()

        for datasource in root.findall(".//datasource"):
            logical_table_name = datasource.get("caption")
            if not logical_table_name:
                continue
            
            for relation in datasource.findall(".//relation[@join]"):
                join_type = relation.get("join")
                if not join_type:
                    continue

                clause = relation.find(".//clause[@type='join']")
                if clause is not None:
                    expressions = clause.findall(".//expression[@op='=']/expression")
                    if len(expressions) == 2:
                        left_op = expressions[0].get("op", "")
                        right_op = expressions[1].get("op", "")
                        
                        if left_op and right_op:
                            try:
                                left_table = left_op.strip("[]").split("].[")[0]
                                right_table = right_op.strip("[]").split("].[")[0]
                                left_col = left_op.strip("[]").split("].[")[1]
                                right_col = right_op.strip("[]").split("].[")[1]
                                
                                join_key = (logical_table_name, left_table, right_table, 
                                          left_col, right_col, join_type)
                                
                                if join_key not in seen_joins:
                                    seen_joins.add(join_key)
                                    
                                    # Clean table names
                                    left_table = left_table.replace(".csv", "")
                                    right_table = right_table.replace(".csv", "")
                                    
                                    # Create a string representation of the join
                                    join_str = f"{logical_table_name}: {left_table} {join_type} JOIN {right_table} ON {left_table}.{left_col} = {right_table}.{right_col}"
                                    joins.append(join_str)
                            except (IndexError, AttributeError):
                                continue
        return joins

    def _parse_datasource_info(self, root: ET.Element) -> List[Dict]:
        datasource_info = []
        
        for datasource in root.findall("./datasources/datasource"):
            datasource_name = datasource.get("caption")
            if datasource_name:
                # Parse filters
                datasource_filters = []
                for filter_tag in datasource.findall(".//filter"):
                    filter_name = filter_tag.get("column")
                    if not filter_name:
                        continue

                    filter_details = []
                    for groupfilter in filter_tag.findall(".//groupfilter"):
                        if groupfilter.get("function") == "member":
                            member_detail = groupfilter.get("member")
                            if member_detail:
                                filter_details.append(member_detail)
                    
                    datasource_filters.append({
                        "filter_name": filter_name,
                        "details": filter_details
                    })
                
                # Check for row level identifier
                has_row_level_identifier = "No"
                for group in datasource.findall(".//group"):
                    if group.get("name"):
                        has_row_level_identifier = "Yes"
                        break
                
                datasource_info.append({
                    "datasource_name": datasource_name,
                    "filters": datasource_filters,
                    "row_level_identifier": has_row_level_identifier
                })
        
        return datasource_info

class TableauWorkbookAnalyzer:
    """Main class for analyzing Tableau workbooks"""
    def __init__(self):
        self.summary_parser = SummaryParser()
        self.details_parser = DetailsParser()

    def analyze(self, file_path: str) -> TableauWorkbookResponse:
        """Analyze a Tableau workbook file and return the analysis results"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Tableau workbook file not found: {file_path}")

        if not file_path.endswith('.twb'):
            raise InvalidFileError(f"Invalid file type: {file_path}. Only .twb files are supported.")

        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            root.set('_filename', file_path)
            
            # Parse summary and details
            try:
                summary_data = self.summary_parser.parse(root)
            except Exception as e:
                logger.error(f"Error parsing summary: {str(e)}\n{traceback.format_exc()}")
                raise ParsingError(f"Error parsing summary: {str(e)}")

            try:
                details_data = self.details_parser.parse(root)
            except Exception as e:
                logger.error(f"Error parsing details: {str(e)}\n{traceback.format_exc()}")
                raise ParsingError(f"Error parsing details: {str(e)}")

            # Create Pydantic models
            try:
                summary = Summary(**summary_data)
                details = Details(**details_data)
            except Exception as e:
                logger.error(f"Error creating Pydantic models: {str(e)}\n{traceback.format_exc()}")
                raise ParsingError(f"Error creating Pydantic models: {str(e)}")
            
            # Create workbook analysis
            workbook_analysis = TableauWorkbookAnalysis(
                summary=summary,
                details=details
            )
            
            # Return response
            return TableauWorkbookResponse(root=[workbook_analysis])

        except ET.ParseError as e:
            logger.error(f"XML parsing error: {str(e)}\n{traceback.format_exc()}")
            raise InvalidFileError(f"Invalid Tableau workbook file: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}\n{traceback.format_exc()}")
            raise TableauParserError(f"Unexpected error: {str(e)}")

def analyze_tableau_workbook(file_path: str) -> TableauWorkbookResponse:
    """Convenience function to analyze a Tableau workbook"""
    try:
        analyzer = TableauWorkbookAnalyzer()
        return analyzer.analyze(file_path)
    except TableauParserError as e:
        # Re-raise Tableau parser specific errors
        raise
    except Exception as e:
        # Wrap unexpected errors
        logger.error(f"Unexpected error in analyze_tableau_workbook: {str(e)}\n{traceback.format_exc()}")
        raise TableauParserError(f"Unexpected error: {str(e)}") 