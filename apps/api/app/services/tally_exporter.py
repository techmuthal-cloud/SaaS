from decimal import Decimal
from typing import List, Dict, Any

class TallyExporterService:
    """
    Generates TallyPrime XML DayBook / Journal Vouchers.
    Maps marketplace disbursements, commissions, and shipping expenses directly into Tally.
    """

    @classmethod
    def generate_daybook_xml(cls, workspace_id: str, db: Any) -> str:
        from app.models.entities import Workspace, SettlementTransaction
        ws = db.query(Workspace).filter(Workspace.id == workspace_id).first()
        workspace_name = ws.name if ws else "SellerFlow Company"
        txns = db.query(SettlementTransaction).filter(SettlementTransaction.workspace_id == workspace_id).all()
        return cls.generate_tally_xml(workspace_name=workspace_name, settlement_txns=txns)

    @classmethod
    def generate_tally_xml(
        cls,
        workspace_name: str,
        settlement_txns: List[Any],
        date_str: str = "20261101"
    ) -> str:
        gross_sales = Decimal("0.0")
        commissions = Decimal("0.0")
        shipping_fees = Decimal("0.0")
        refunds = Decimal("0.0")
        net_bank = Decimal("0.0")

        for t in settlement_txns:
            amt = t.amount or Decimal("0.0")
            ttype = (t.transaction_type or "").lower()
            if "order" in ttype and amt > 0:
                gross_sales += amt
            elif "commission" in ttype or amt < 0 and "commission" in ttype:
                commissions += abs(amt)
            elif "shipping" in ttype or "pick" in ttype:
                shipping_fees += abs(amt)
            elif "refund" in ttype:
                refunds += abs(amt)
            net_bank += amt

        xml_lines = [
            '<ENVELOPE>',
            '  <HEADER>',
            '    <TALLYREQUEST>Import Data</TALLYREQUEST>',
            '  </HEADER>',
            '  <BODY>',
            '    <IMPORTDATA>',
            '      <REQUESTDESC>',
            '        <REPORTNAME>Vouchers</REPORTNAME>',
            '        <STATICVARIABLES>',
            f'          <SVCURRENTCOMPANY>{workspace_name}</SVCURRENTCOMPANY>',
            '        </STATICVARIABLES>',
            '      </REQUESTDESC>',
            '      <REQUESTDATA>',
            '        <TALLYMESSAGE xmlns:UDF="TallyUDF">',
            '          <VOUCHER VCHTYPE="Journal" ACTION="Create">',
            f'            <DATE>{date_str}</DATE>',
            '            <NARRATION>Marketplace Settlement Disbursement Reconciliation via SellerFlow AI</NARRATION>',
            '            <VOUCHERTYPENAME>Journal</VOUCHERTYPENAME>',
            '            <ALLLEDGERENTRIES.LIST>',
            '              <LEDGERNAME>Bank Account</LEDGERNAME>',
            '              <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>',
            f'              <AMOUNT>-{net_bank:.2f}</AMOUNT>',
            '            </ALLLEDGERENTRIES.LIST>',
            '            <ALLLEDGERENTRIES.LIST>',
            '              <LEDGERNAME>Marketplace Commission Expense</LEDGERNAME>',
            '              <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>',
            f'              <AMOUNT>-{commissions:.2f}</AMOUNT>',
            '            </ALLLEDGERENTRIES.LIST>',
            '            <ALLLEDGERENTRIES.LIST>',
            '              <LEDGERNAME>Shipping and Delivery Expense</LEDGERNAME>',
            '              <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>',
            f'              <AMOUNT>-{shipping_fees:.2f}</AMOUNT>',
            '            </ALLLEDGERENTRIES.LIST>',
            '            <ALLLEDGERENTRIES.LIST>',
            '              <LEDGERNAME>Marketplace Gross Sales</LEDGERNAME>',
            '              <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>',
            f'              <AMOUNT>{gross_sales:.2f}</AMOUNT>',
            '            </ALLLEDGERENTRIES.LIST>',
            '          </VOUCHER>',
            '        </TALLYMESSAGE>',
            '      </REQUESTDATA>',
            '    </IMPORTDATA>',
            '  </BODY>',
            '</ENVELOPE>'
        ]

        return "\n".join(xml_lines)
