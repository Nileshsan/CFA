import requests

TALLY_URL = "http://localhost:9000"
xml = """
<ENVELOPE>
    <HEADER>
        <TALLYREQUEST>Export Data</TALLYREQUEST>
    </HEADER>
    <BODY>
        <EXPORTDATA>
            <REQUESTDESC>
                <REPORTNAME>List of Accounts</REPORTNAME>
                <STATICVARIABLES>
                    <ACCOUNTTYPE>Ledger</ACCOUNTTYPE>
                    <SVEXPORTFORMAT>XML</SVEXPORTFORMAT>
                </STATICVARIABLES>
            </REQUESTDESC>
        </EXPORTDATA>
    </BODY>
</ENVELOPE>
"""

response = requests.post(TALLY_URL, data=xml, timeout=30)
print("Status:", response.status_code)
print("Response:", response.text[:500])