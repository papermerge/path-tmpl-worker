
def test_get_doc(make_receipt):
    doc = make_receipt(
        title="invoice.pdf",
        path_template="/home/Receipts/{{document.id}}.pdf"
    )

    assert doc.title == "invoice.pdf"
    assert doc.document_type.path_template == "/home/Receipts/{{document.id}}.pdf"
    

