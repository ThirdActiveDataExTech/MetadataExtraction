import zipfile
import xml.etree.ElementTree as ET
import re
import pandas as pd

TARGET_HEADERS = ['관리번호', '기술분류', '중점분야', '기획유형', '과제명', '연구비용', '연구기간', '']

def parse_content(header, content):
    """Parses content based on header."""
    if header == '관리번호':
        match = re.search(r'\d{4}-\d{3}', content)
        return match.group() if match else None
    elif header in ['중점분야', '기획유형']:
        return ', '.join([field.split('(')[0] for field in content.split(', ') if '√' in field])
    elif header in ['기술분류', '과제명', '연구비용', '연구기간']:
        return content
    return None

def process_table(root: ET.Element):
    hp_tag = "http://www.hancom.co.kr/hwpml/2011/paragraph"
    table_headers = root.findall(".//{" + hp_tag + "}tbl")
    records = []

    for table in table_headers:
        record = {header: None for header in TARGET_HEADERS}
        rows = table.findall(".//{" + hp_tag + "}tr")

        for row in rows:
            cells = row.findall(".//{" + hp_tag + "}t")
            if cells and cells[0].text in TARGET_HEADERS:
                header = cells[0].text
                content = ' '.join([cell.text or '' for cell in cells[1:]])
                parsed_content = parse_content(header, content)
                record[header] = parsed_content

        if record['관리번호'] is not None:
            records.append(record)

    return records

def explore_xml_structure(file_path):
    all_records = []

    try:
        with zipfile.ZipFile(file_path, 'r') as zip_ref:
            for file_name in zip_ref.namelist():
                if file_name.startswith('Contents/section') and file_name.endswith('.xml'):
                    xml_content = zip_ref.read(file_name)
                    root = ET.fromstring(xml_content)
                    all_records.extend(process_table(root))

    except Exception as e:
        print(f"An error occurred: {e}")

    data = []
    for record in all_records:
        for header in TARGET_HEADERS:
            data.append({
                "항목": header,
                "추출값": record.get(header),
                "예측값": record.get(header)
            })

    df = pd.DataFrame(data, columns=["항목", "추출값", "예측값"])

    total = len(df)
    correct = df.apply(lambda row: row['추출값'] == row['예측값'] and pd.notna(row['추출값']), axis=1).sum()
    accuracy = (correct / total) * 100 if total > 0 else 0

    df.to_csv('results.csv', index=False)

    print(df)
    print(f"\n정답률: {accuracy:.2f}%")

# File path
file_path = ''

# Explore the XML structure
explore_xml_structure(file_path)
