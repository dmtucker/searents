"""Tests for searents.equity."""


from pathlib import Path

import searents.equity


def test_equity_parser():
    """Verify that the EquityParser can parse a scraped Equity Webpage."""
    parser = searents.equity.EquityParser()
    with Path(__file__).with_name("urbana.html").open() as html_f:
        parser.feed(html_f.read())
    assert parser.units == [
        {
            "building": "1",
            "description": "Studio F",
            "floorplan": "https://media.equityapartments.com/image/upload/"
            "f_auto,q_auto,b_white/4141-FP-00379254-0-1-514",
            "ledger": "29262",
            "price": "$1,788",
            "unit": "437",
        },
        {
            "building": "1",
            "description": "Open 1 Bedroom A",
            "floorplan": "https://media.equityapartments.com/image/upload/"
            "f_auto,q_auto,b_white/4141-FP-00379250-1-1-485",
            "ledger": "29262",
            "price": "$1,733",
            "unit": "312",
        },
        {
            "building": "1",
            "description": "Open 1 Bedroom C",
            "floorplan": "https://media.equityapartments.com/image/upload/"
            "f_auto,q_auto,b_white/4141-FP-00379253-1-1-497",
            "ledger": "29262",
            "price": "$1,886",
            "unit": "415",
        },
        {
            "building": "1",
            "description": "Open 1 Bedroom A",
            "floorplan": "https://media.equityapartments.com/image/upload/"
            "f_auto,q_auto,b_white/4141-FP-00379250-1-1-485",
            "ledger": "29262",
            "price": "$1,922",
            "unit": "512",
        },
        {
            "building": "1",
            "description": "One Bedroom B",
            "floorplan": "https://media.equityapartments.com/image/upload/"
            "f_auto,q_auto,b_white/4141-FP-00379267-1-1-687",
            "ledger": "29262",
            "price": "$2,341",
            "unit": "524",
        },
        {
            "building": "1",
            "description": "One Bedroom E",
            "floorplan": "https://media.equityapartments.com/image/upload/"
            "f_auto,q_auto,b_white/4141-FP-00379271-1-1-719",
            "ledger": "29262",
            "price": "$2,426",
            "unit": "602",
        },
        {
            "building": "1",
            "description": "One Bedroom I",
            "floorplan": "https://media.equityapartments.com/image/upload/"
            "f_auto,q_auto,b_white/4141-FP-00379275-1-1-744",
            "ledger": "29262",
            "price": "$2,435",
            "unit": "339",
        },
        {
            "building": "1",
            "description": "One Bedroom E",
            "floorplan": "https://media.equityapartments.com/image/upload/"
            "f_auto,q_auto,b_white/4141-FP-00379271-1-1-719",
            "ledger": "29262",
            "price": "$2,436",
            "unit": "302",
        },
        {
            "building": "1",
            "description": "One Bedroom M",
            "floorplan": "https://media.equityapartments.com/image/upload/"
            "f_auto,q_auto,b_white/4141-FP-00379279-1-1-766",
            "ledger": "29262",
            "price": "$2,625",
            "unit": "436",
        },
        {
            "building": "1",
            "description": "One Bedroom L",
            "floorplan": "https://media.equityapartments.com/image/upload/"
            "f_auto,q_auto,b_white/4141-FP-00379278-1-1-760",
            "ledger": "29262",
            "price": "$2,670",
            "unit": "320",
        },
        {
            "building": "1",
            "description": "One Bedroom J",
            "floorplan": "https://media.equityapartments.com/image/upload/"
            "f_auto,q_auto,b_white/4141-FP-00379276-1-1-751",
            "ledger": "29262",
            "price": "$2,688",
            "unit": "536",
        },
        {
            "building": "1",
            "description": "One Bedroom S",
            "floorplan": "https://media.equityapartments.com/image/upload/"
            "f_auto,q_auto,b_white/4141-FP-00379287-1-1-870",
            "ledger": "29262",
            "price": "$2,768",
            "unit": "305",
        },
        {
            "building": "1",
            "description": "1 Bedroom U",
            "floorplan": "https://media.equityapartments.com/image/upload/"
            "f_auto,q_auto,b_white/4141-FP-383585-1-1-697",
            "ledger": "29262",
            "price": "$2,791",
            "unit": "629",
        },
        {
            "building": "1",
            "description": "Two Bedroom I",
            "floorplan": "https://media.equityapartments.com/image/upload/"
            "f_auto,q_auto,b_white/4141-FP-00379297-2-2-1131",
            "ledger": "29262",
            "price": "$3,494",
            "unit": "538",
        },
        {
            "building": "1",
            "description": "Two Bedroom M",
            "floorplan": "https://media.equityapartments.com/image/upload/"
            "f_auto,q_auto,b_white/4141-FP-00379301-2-2-1150",
            "ledger": "29262",
            "price": "$3,519",
            "unit": "331",
        },
    ]
