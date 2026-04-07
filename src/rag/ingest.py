from pypdf import PdfReader
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from models import WarrantyPolicy, WarrantyCoverage
import json

llm = ChatGroq(
    model="llama-3.3-70b-versatile", 
    api_key="YOUR_API_KEY",
    temperature=0
)

prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a warranty policy analyzer.
Extract warranty information and return ONLY valid JSON.
No extra text, just JSON.

JSON format:
{{
    "policy_name": "string",
    "covered_items": [
        {{
            "item": "string",
            "duration_months": number,
            "covered": true/false,
            "max_amount": number or null
        }}
    ],
    "excluded_items": ["string1", "string2"],
    "requires_receipt": true/false,
    "repair_days": number
}}"""),
    ("human", "Extract warranty info from this:\n\n{policy_text}")
])

chain = prompt | llm

#  Function 1 - Read PDF
def extract_text_from_pdf(pdf_path: str) -> str:
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

#  Function 2 - Parse warranty
def parse_warranty(text: str) -> WarrantyPolicy:
    response = chain.invoke({"policy_text": text})

    content = response.content.strip()
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()

    data = json.loads(content)
    return WarrantyPolicy(**data)

#  Function 3 - Main function
def ingest_warranty(pdf_path: str) -> WarrantyPolicy:
    print(f"Reading PDF: {pdf_path}")
    text = extract_text_from_pdf(pdf_path)

    print("Extracting warranty info...")
    policy = parse_warranty(text)

    print(f" Policy extracted: {policy.policy_name}")
    return policy