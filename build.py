#!/usr/bin/env python3
"""Build offline trip PWA data from markdown + PDF sources."""
import base64
import json
import re
import shutil
import time
import urllib.request
from pathlib import Path

import qrcode
import qrcode.image.svg
from PIL import Image

ROOT = Path(__file__).parent.parent
APP = ROOT / "app"
DOCS = APP / "documents"
ASSETS = APP / "assets"
CITIES = ASSETS / "cities"

# Per-day city photos — photo_url is the primary source (Wikipedia Commons)
DAY_MEDIA = {
    "2026-07-06": {
        "city": "Wiesbaden",
        "photo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/Wiesbaden_Kurhaus.JPG/960px-Wiesbaden_Kurhaus.JPG",
        "photo_credit": "Wikimedia — Wiesbaden Kurhaus",
    },
    "2026-07-07": {
        "city": "Wiesbaden → Salzburg",
        "photo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/65/Salzburg_from_Festungsberg.jpg/960px-Salzburg_from_Festungsberg.jpg",
        "photo_credit": "Wikimedia — Salzburg",
    },
    "2026-07-08": {
        "city": "Salzburg",
        "photo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/65/Salzburg_from_Festungsberg.jpg/960px-Salzburg_from_Festungsberg.jpg",
        "photo_credit": "Wikimedia — Salzburg",
    },
    "2026-07-09": {
        "city": "Salzburg",
        "photo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/13/Mozarteum_Salzburg.jpg/960px-Mozarteum_Salzburg.jpg",
        "photo_credit": "Wikimedia — Salzburg",
    },
    "2026-07-10": {
        "city": "Ljubljana",
        "photo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b0/Ljubljana_-_View_from_the_Castle.jpg/960px-Ljubljana_-_View_from_the_Castle.jpg",
        "photo_credit": "Wikimedia — Ljubljana",
    },
    "2026-07-11": {
        "city": "Lake Bled",
        "photo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/06/Bled_747.jpg/960px-Bled_747.jpg",
        "photo_credit": "Wikimedia — Lake Bled",
    },
    "2026-07-12": {
        "city": "Split",
        "photo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9e/Diocletian%27s_Palace_in_Split_%28Croatia%29.jpg/960px-Diocletian%27s_Palace_in_Split_%28Croatia%29.jpg",
        "photo_credit": "Wikimedia — Split",
    },
    "2026-07-13": {
        "city": "Hvar",
        "photo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/55/Hvar_harbour%2C_Croatia.jpg/960px-Hvar_harbour%2C_Croatia.jpg",
        "photo_fallbacks": [
            "https://upload.wikimedia.org/wikipedia/commons/thumb/7/75/Hvar_panorama.jpg/960px-Hvar_panorama.jpg",
        ],
        "photo_credit": "Wikimedia — Hvar harbour",
    },
    "2026-07-14": {
        "city": "Split",
        "photo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/44/Peristyle%2C_Split_2.jpg/960px-Peristyle%2C_Split_2.jpg",
        "photo_credit": "Wikimedia — Split Peristyle",
    },
    "2026-07-15": {
        "city": "Sarajevo",
        "photo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/89/Old_Bazaar%2C_Sarajevo%2C_Bosnia_and_Herzegovina.jpg/960px-Old_Bazaar%2C_Sarajevo%2C_Bosnia_and_Herzegovina.jpg",
        "photo_credit": "Wikimedia — Sarajevo",
    },
    "2026-07-16": {
        "city": "Sarajevo",
        "photo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d7/Vije%C4%87nica_%28Sarajevo%29.jpg/960px-Vije%C4%87nica_%28Sarajevo%29.jpg",
        "photo_credit": "Wikimedia — Sarajevo City Hall",
    },
    "2026-07-17": {
        "city": "Frankfurt",
        "photo_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e9/Frankfurt_%28DerPlainer%29_R%C3%B6merberg.jpg/960px-Frankfurt_%28DerPlainer%29_R%C3%B6merberg.jpg",
        "photo_fallbacks": [
            "https://upload.wikimedia.org/wikipedia/commons/thumb/d/da/Frankfurt_Skyline.jpg/960px-Frankfurt_Skyline.jpg",
            "https://upload.wikimedia.org/wikipedia/commons/thumb/7/73/Frankfurt_am_Main_Skyline_%28cropped%29.jpg/960px-Frankfurt_am_Main_Skyline_%28cropped%29.jpg",
        ],
        "photo_credit": "Wikimedia — Frankfurt Römerberg",
    },
}

# Hand-curated enrichments keyed by item id (folder/filename without ext)
ENRICH = {
    "06_July/Best Western Booking.com": {
        "id": "hotel-wiesbaden",
        "summary": "Check in — Best Western Hotel Wiesbaden",
        "address": "Mainzer Str. 74, 65189 Wiesbaden, Germany",
        "phone": "+49 611 17079150",
        "links": [
            {"label": "Manage on Booking.com", "url": "https://www.booking.com/"},
            {"label": "Google Maps", "url": "https://maps.google.com/?q=Mainzer+Str.+74+65189+Wiesbaden+Germany"},
        ],
        "tips": [
            "Check-in from 15:00, check-out until 11:00.",
            "Public parking on site ~€15/day.",
            "Emergency in Germany: dial 112.",
        ],
        "qr_data": "6504.681.227|PIN:8454",
        "lat": 50.0710,
        "lon": 8.2493,
    },
    "08_July/Salzburg Booking.com": {
        "id": "hotel-salzburg",
        "summary": "Check in — Motel One Salzburg-Süd",
        "address": "Alpenstraße 92-94, 5020 Salzburg, Austria",
        "phone": "+43 662 835020",
        "links": [
            {"label": "Manage on Booking.com", "url": "https://www.booking.com/"},
            {"label": "Google Maps", "url": "https://maps.google.com/?q=Motel+One+Salzburg-Süd+Alpenstraße+92+Salzburg"},
        ],
        "tips": ["Check-in from 15:00, check-out until 12:00.", "Parking nearby ~€11/day."],
        "qr_data": "5941.541.530|PIN:8175",
        "lat": 47.7947,
        "lon": 13.0663,
    },
    "08_July/Salt Mines Tour": {
        "id": "activity-salt-mines",
        "summary": "Salzwelten Salt Mines Tour @ 15:20",
        "address": "Ramsaustraße 3, 5422 Bad Dürrnberg, Austria",
        "phone": "+43 6132 200 8511",
        "email": "info@salzwelten.at",
        "links": [
            {"label": "Salzwelten website", "url": "https://www.salzwelten.at/en/"},
            {"label": "Google Maps", "url": "https://maps.google.com/?q=Salzwelten+Salzburg+Bad+Dürrnberg"},
        ],
        "tips": [
            "Arrive ~15 minutes before 15:20 admission time.",
            "Temperature in mine ~10°C — bring warm clothes and sturdy shoes.",
            "Tour ~90 min, ~1 km walking.",
        ],
        "qr_data": "SBG2661789",
    },
    "09_July/Eagles Nest": {
        "id": "activity-eagles-nest",
        "summary": "Eagle's Nest Historical Tour @ 11:15",
        "address": "Salzbergstraße 45, 83471 Berchtesgaden, Germany",
        "phone": "+49 151 21190598",
        "links": [
            {
                "label": "GetYourGuide voucher",
                "url": "https://www.getyourguide.com/voucher?booking=GYG9963K9N6A",
            },
            {"label": "Meeting point on Maps", "url": "https://maps.google.com/?q=Salzbergstraße+45+83471+Berchtesgaden"},
        ],
        "tips": [
            "Arrive 15 min early at Eagle's Nest bus departure point.",
            "Look for guide with 'Discover Eagle's Nest' sign.",
            "Cancel before 11:15 AM on July 8 for full refund.",
        ],
        "qr_data": "GYG9963K9N6A|PIN:LUSmZXQ+",
    },
    "09_July/Mozart Concert": {
        "id": "activity-mozart",
        "summary": "Mozart Fortress Concert & Dinner @ 18:30",
        "address": "Festungsgasse 4, 5020 Salzburg, Austria",
        "phone": "+43 662 825858",
        "links": [
            {
                "label": "GetYourGuide voucher",
                "url": "https://www.getyourguide.com/voucher?booking=GYGN6B4WGQ89",
            },
            {"label": "FestungsBahn on Maps", "url": "https://maps.google.com/?q=Festungsgasse+4+5020+Salzburg"},
        ],
        "tips": [
            "Arrive 30 min early at FestungsBahn funicular valley station.",
            "Use the funicular — do NOT walk up or down!",
            "Voucher includes free funicular ride.",
        ],
        "qr_data": "GYGN6B4WGQ89|PIN:qH&Dh/HS",
    },
    "10_July/Salzburg to Ljubljana": {
        "id": "transport-salzburg-ljubljana",
        "summary": "Train 08:07 → 12:27 (ÖBB RJ 551 + D 313)",
        "address": "Salzburg Hbf → Ljubljana",
        "links": [
            {"label": "ÖBB My tickets", "url": "https://tickets.oebb.at/en/"},
            {"label": "ÖBB journey info", "url": "https://www.oebb.at/en/"},
            {"label": "Salzburg Hbf on Maps", "url": "https://maps.google.com/?q=Salzburg+Hbf"},
            {"label": "Ljubljana station on Maps", "url": "https://maps.google.com/?q=Ljubljana+train+station"},
        ],
        "tips": [
            "Platform 9 at Salzburg Hbf. 1st class, seats 21 & 23 (car 26).",
            "Print ticket for cross-border segment (A4 white paper).",
            "Bring photo ID. No exchange/refund.",
            "Joy ticket: 2595 9041 9044 4129 · Jeffery: 2556 8765 0723 8395",
        ],
        "qr_data": "0707233885467696",
        "passengers": ["Joy Peterson", "Jeffery Peterson"],
    },
    "10_July/Ljubljana Hotel": {
        "id": "hotel-ljubljana-airbnb",
        "summary": "Check in — Airbnb Comfy Studio Ljubljana",
        "address": "Cerkova ulica 14, 1000 Ljubljana, Slovenia",
        "links": [
            {
                "label": "Airbnb reservation",
                "url": "https://www.airbnb.com/trips/v1/reservation-details/ro/RESERVATION2_CHECKIN/HMENEBDYT9",
            },
            {"label": "Google Maps", "url": "https://maps.google.com/?q=Cerkova+ulica+14+Ljubljana"},
        ],
        "tips": [
            "Self check-in with lockbox. Check-in from 17:00, out by 11:00.",
            "Host: Tine. WiFi details sent 48h before check-in.",
            "Cancel before 5 PM July 3 for partial refund.",
        ],
        "qr_data": "HMENEBDYT9",
    },
    "10_July/Ljubljana Castle": {
        "id": "activity-ljubljana-castle",
        "summary": "Ljubljana Castle — funicular, exhibitions & tower",
        "address": "Grajska planota 1, 1000 Ljubljana, Slovenia",
        "links": [
            {"label": "Google Maps", "url": "https://maps.google.com/?q=Ljubljana+Castle"},
        ],
        "tips": [
            "Includes funicular return, history exhibition, viewing tower, puppet museum.",
            "2 tickets purchased (€20.70 each).",
        ],
    },
    "11_July/Ljubljana to Bled": {
        "id": "transport-ljubljana-bled-joy",
        "summary": "Bus Ljubljana → Bled @ 07:15 (Joy)",
        "address": "Ljubljana bus station → Bled bus station",
        "phone": "+386 40121900",
        "links": [
            {"label": "Nomago My tickets", "url": "https://www.nomago.si/en"},
            {"label": "Nomago FAQ", "url": "https://www.nomago.hr/en/bus-tickets-online/faq"},
            {"label": "Ljubljana bus station", "url": "https://maps.google.com/?q=Ljubljana+bus+station"},
        ],
        "tips": ["Arrive 15 min early. Show ticket on phone or print.", "Shuttle/van — may not have Nomago branding."],
        "qr_data": "1828870186",
        "passengers": ["Joy Peterson"],
    },
    "11_July/Ljubljana to Bled 2": {
        "id": "transport-ljubljana-bled-jeff",
        "summary": "Bus Ljubljana → Bled @ 07:15 (Jeffery)",
        "address": "Ljubljana bus station → Bled bus station",
        "phone": "+386 40121900",
        "links": [
            {"label": "Nomago My tickets", "url": "https://www.nomago.si/en"},
            {"label": "Nomago FAQ", "url": "https://www.nomago.hr/en/bus-tickets-online/faq"},
        ],
        "tips": ["Arrive 15 min early. Platform 4."],
        "qr_data": "1809719252",
        "passengers": ["Jeffery Peterson"],
    },
    "11_July/Ebike Tour of Vintgar Gorge": {
        "id": "activity-vintgar",
        "summary": "E-Bike Vintgar Gorge Tour @ 09:00",
        "address": "Ljubljanska cesta 20, 4260 Bled, Slovenia",
        "phone": "+386 41 746 397",
        "links": [
            {
                "label": "GetYourGuide voucher",
                "url": "https://www.getyourguide.com/voucher?booking=GYG2Q9K6Z32G",
            },
            {"label": "pr1motours on Maps", "url": "https://maps.google.com/?q=Ljubljanska+cesta+20+Bled"},
        ],
        "tips": [
            "Arrive on time — Vintgar entry time is fixed.",
            "Min height 150 cm for e-bike. Hike in gorge 2–3 hours.",
            "No parking at tour office.",
        ],
        "qr_data": "GYG2Q9K6Z32G|PIN:ETUhxt7B",
    },
    "11_July/Bled to Ljubljana": {
        "id": "transport-bled-airport-joy",
        "summary": "Shuttle Bled → Ljubljana Airport @ 08:00 (Joy) ⚠️ verify time",
        "address": "Bled bus station → Ljubljana Jože Pučnik Airport (LJU)",
        "phone": "+386 40121900",
        "links": [
            {"label": "Nomago My tickets", "url": "https://www.nomago.si/en"},
            {"label": "Nomago support", "url": "mailto:intercity@nomago.eu"},
        ],
        "tips": [
            "⚠️ This 08:00 departure conflicts with the 09:00 Bled tour — verify or rebook.",
            "Arrive 15 min early.",
        ],
        "qr_data": "1853148948",
        "passengers": ["Joy Peterson"],
        "warning": True,
    },
    "11_July/Bled to Ljubljana 2": {
        "id": "transport-bled-airport-jeff",
        "summary": "Shuttle Bled → Ljubljana Airport @ 08:00 (Jeffery) ⚠️ verify time",
        "address": "Bled bus station → Ljubljana Jože Pučnik Airport (LJU)",
        "phone": "+386 40121900",
        "links": [
            {"label": "Nomago My tickets", "url": "https://www.nomago.si/en"},
        ],
        "tips": ["⚠️ Conflicts with Bled day trip schedule — verify or rebook."],
        "qr_data": "1797295136",
        "passengers": ["Jeffery Peterson"],
        "warning": True,
    },
    "12_July/Ljubljana to Zagreb": {
        "id": "transport-ljubljana-zagreb",
        "summary": "FlixBus @ 08:25 → 10:25",
        "address": "Trg Osvobodilne fronte 4, 1000 Ljubljana → Avenija Marina Držića 4, Zagreb",
        "links": [
            {"label": "FlixBus My booking", "url": "https://shop.flixbus.com/rebooking/login"},
            {"label": "Track trip", "url": "https://www.flixbus.com/track/order/3362291273"},
            {"label": "Departure station", "url": "https://maps.google.com/?q=Ljubljana+bus+station+Trg+Osvobodilne+fronte+4"},
        ],
        "tips": ["Route N952, Gate 29 & 30. Arrive 15 min early.", "Carry valid passport/ID."],
        "qr_data": "3362291273",
        "passengers": ["Joy Peterson", "Jeffery Peterson"],
    },
    "12_July/Zagreb to Split": {
        "id": "transport-zagreb-split",
        "summary": "Flight OU380 @ 14:40 → 15:25",
        "address": "Zagreb (ZAG) → Split (SPU)",
        "links": [
            {"label": "Croatia Airlines", "url": "https://www.croatiaairlines.com/"},
            {"label": "Check-in (OU380)", "url": "https://www.croatiaairlines.com/us-en/check-in"},
            {"label": "Zagreb Airport", "url": "https://maps.google.com/?q=Zagreb+Airport"},
            {"label": "Split Airport", "url": "https://maps.google.com/?q=Split+Airport"},
        ],
        "tips": [
            "Check-in reference: 77UU4C",
            "Joy e-ticket: 831-9541938486 · Jeffery: 831-9541938485",
            "Hand baggage only, 8 kg max.",
        ],
        "qr_data": "77UU4C",
        "passengers": ["Joy Peterson", "Jeffery Peterson"],
    },
    "12_July/Split Hotel": {
        "id": "hotel-split-airbnb",
        "summary": "Check in — Luxury Room Mareta (old town Split)",
        "address": "Riva, old town Split, Croatia",
        "phone": "+385 (contact via Airbnb)",
        "links": [
            {"label": "Airbnb messages", "url": "https://www.airbnb.com/guest/messages"},
            {"label": "Boat excursions (host partner)", "url": "https://seayou.com/?ttafid=39685"},
            {"label": "Split old town", "url": "https://maps.google.com/?q=Split+Riva+Croatia"},
        ],
        "tips": [
            "Host: Josko. Check-in 14:00, check-out 10:00.",
            "Contact host for airport transfer suggestions.",
        ],
    },
    "13_July/Catamaran Booking": {
        "id": "transport-ferry-hvar",
        "summary": "Ferry Split → Hvar 07:30, return 19:00",
        "address": "Split (Gat Svetog Petra) ↔ Hvar",
        "links": [
            {"label": "Ferryhopper My bookings", "url": "https://www.ferryhopper.com/en/my-bookings"},
            {"label": "Jadrolinija", "url": "https://www.jadrolinija.hr/en"},
            {"label": "Split ferry port", "url": "https://maps.google.com/?q=Gat+Svetog+Petra+Split"},
        ],
        "tips": [
            "Out: Jadrolinija 07:30 → 08:35 (reservation 439629162).",
            "Return: Kapetan Luka 19:00 → 20:00 (reservation 59xYqoMahEc).",
            "Arrive at port 1 hour early. Board with e-ticket.",
        ],
        "qr_data": "FH56MC2224FB",
        "passengers": ["Joy Peterson", "Jeffery Peterson"],
    },
    "13_July/Speedboat Tour": {
        "id": "activity-speedboat",
        "summary": "Blue Cave & 5 Islands Speedboat @ 10:30 (Hvar)",
        "address": "Fabrika 26, 21450 Hvar, Croatia",
        "phone": "+385 91 762 5227",
        "links": [
            {
                "label": "GetYourGuide voucher",
                "url": "https://www.getyourguide.com/voucher?booking=GYGX7NFB26ZA",
            },
            {"label": "Gajeta Agency on Maps", "url": "https://maps.google.com/?q=Fabrika+26+Hvar"},
        ],
        "tips": [
            "Be at Gajeta Agency office by 10:15.",
            "Bring swimwear, towel, sunscreen, cash.",
        ],
        "qr_data": "GYGX7NFB26ZA|PIN:tFkdBjLC",
    },
    "14_July/Walking Tour Split": {
        "id": "activity-split-walk",
        "summary": "Split Walking Tour @ 10:30",
        "address": "Golden Gate, Diocletian's Palace, Split",
        "phone": "+385 99 821 5383",
        "email": "desk@splitwalkingtour.com",
        "links": [
            {"label": "Meeting point on Maps", "url": "https://maps.google.com/?q=Golden+Gate+Split+Diocletian+Palace"},
            {"label": "WhatsApp host", "url": "https://wa.me/385998215383"},
        ],
        "tips": [
            "Arrive 5 min early. Look for guide with blue umbrella.",
            "€30 still to pay on arrival (€40.50 total, €10.50 prepaid).",
        ],
        "qr_data": "R169-260617-2",
        "passengers": ["Joy Peterson"],
    },
    "15_July/Split to Sarajevo": {
        "id": "transport-split-sarajevo",
        "summary": "Bus @ 13:30 → 18:45",
        "address": "Obala Kneza Domagoja 12, Split → Put života 2, Sarajevo",
        "links": [
            {"label": "Bookaway My booking", "url": "https://www.bookaway.com/"},
            {"label": "Globtour", "url": "https://www.globtour.com/"},
            {"label": "Split bus terminal", "url": "https://maps.google.com/?q=Obala+Kneza+Domagoja+12+Split"},
        ],
        "tips": [
            "Report 30 min before departure. Non-refundable.",
            "Bring ID. Operator: Globtour / Croatia Bus.",
            "Also: CRB-11137407, TPL-11138289",
        ],
        "qr_data": "BW5232109",
        "passengers": ["Joy Peterson", "Jeffery Peterson"],
    },
    "15_July/Sarajevo Hotel": {
        "id": "hotel-sarajevo",
        "summary": "Check in — Hotel Old Sarajevo",
        "address": "Bravadžiluk 38, 71000 Sarajevo, Bosnia & Herzegovina",
        "phone": "+387 33 573 555",
        "links": [
            {"label": "Manage on Booking.com", "url": "https://www.booking.com/"},
            {"label": "Google Maps", "url": "https://maps.google.com/?q=Hotel+Old+Sarajevo+Bravadžiluk+38"},
        ],
        "tips": [
            "Check-in 14:00–23:00, out by 11:00. Stairs only to room.",
            "Free cancellation until July 13.",
            "Photo ID + credit card required at check-in.",
        ],
        "qr_data": "5144.122.456|PIN:6419",
    },
    "16_July/Sarajevo Walking Tour": {
        "id": "activity-sarajevo-walk",
        "summary": "Free Walking Tour — Meet Bosnia",
        "address": "Gazi Husrev-begova 75, Sarajevo",
        "links": [
            {"label": "Meeting point on Maps", "url": "https://goo.gl/maps/1BBVAS1rjJ7XiSc56"},
            {"label": "What to see in Sarajevo", "url": "https://meetbosnia.com/what-to-see-in-sarajevo-amazing-local-guide/"},
        ],
        "tips": [
            "Free tour — tip your guide!",
            "Highlights: Baščaršija, Latin Bridge, City Hall, synagogue & more.",
        ],
    },
    "17_July/Sarajevo to Frankfurt": {
        "id": "transport-sarajevo-frankfurt",
        "summary": "Flight LH 1547 @ 06:25 → 08:20",
        "address": "Sarajevo (SJJ) → Frankfurt (FRA) Terminal 1",
        "links": [
            {"label": "Lufthansa My bookings", "url": "https://www.lufthansa.com/us/en/my-bookings"},
            {"label": "Lufthansa check-in", "url": "https://www.lufthansa.com/us/en/online-check-in"},
            {"label": "SJJ Airport", "url": "https://maps.google.com/?q=Sarajevo+International+Airport"},
            {"label": "Frankfurt Airport", "url": "https://maps.google.com/?q=Frankfurt+Airport+Terminal+1"},
        ],
        "tips": [
            "Booking ref: 782HJV. Economy Light, 1 carry-on each (8 kg).",
            "Joy Miles & More: 992003814611897",
            "Arrive at airport well before 06:25 — international flight.",
        ],
        "qr_data": "782HJV",
        "passengers": ["Joy Peterson", "Jeffery Peterson"],
        "lat": 43.8246,
        "lon": 18.3315,
    },
    "08_July/Wiesbaden to Salzburg": {
        "id": "transport-wiesbaden-salzburg",
        "pdf_key": "08_July/Wiesbaden to Salzburg Ticket",
        "summary": "Train 07:37 → 13:59 (RE 24507 + ICE 117)",
        "address": "Wiesbaden Hbf → Salzburg Hbf",
        "links": [
            {"label": "DB My bookings", "url": "https://int.bahn.de/en/buchung/kundenkonto/ihrkonto"},
            {
                "label": "This journey on bahn.de",
                "url": "https://int.bahn.de/en/buchung/fahrplan/suche#sts=true&so=Wiesbaden%20Hbf&zo=Salzburg%20Hbf&kl=1&hd=2026-07-08T07:37:00",
            },
            {"label": "Wiesbaden Hbf on Maps", "url": "https://maps.google.com/?q=Wiesbaden+Hbf"},
            {"label": "Salzburg Hbf on Maps", "url": "https://maps.google.com/?q=Salzburg+Hbf"},
        ],
        "tips": [
            "Order ref: 357186782360 · €211.78 Super Sparpreis, 1st class, 2 adults.",
            "07:37 RB75 (24507) Wiesbaden → Darmstadt 08:21 · 08:30 ICE 117 Darmstadt → Salzburg 13:59.",
            "ICE seats: car 27, seats 75 & 76 (Handybereich). Reservation ref 804520281374.",
            "Show this ticket PDF + photo ID on board. Invoice PDF is also in Documents.",
            "Checkout Best Western by 11:00; Motel One Salzburg check-in from 15:00.",
        ],
        "qr_data": "357186782360",
        "passengers": ["Joy Peterson", "Jeffery Peterson"],
        "lat": 50.0715,
        "lon": 8.2423,
    },
}

TRAVEL_SERVICES = [
    {
        "name": "Deutsche Bahn",
        "url": "https://int.bahn.de/en/buchung/kundenkonto/ihrkonto",
        "note": "Order 357186782360 · Peterson",
    },
    {
        "name": "ÖBB",
        "url": "https://tickets.oebb.at/en/",
        "note": "Booking 0707 2338 8546 7696",
    },
    {
        "name": "Nomago",
        "url": "https://www.nomago.si/en",
        "note": "Joy 1828870186 · Jeffery 1809719252",
    },
    {
        "name": "FlixBus",
        "url": "https://shop.flixbus.com/rebooking/login",
        "note": "Booking 3362291273 · Peterson",
    },
    {
        "name": "Croatia Airlines",
        "url": "https://www.croatiaairlines.com/en-us/plan-and-book/check-in",
        "note": "Ref 77UU4C · OU380",
    },
    {
        "name": "Ferryhopper",
        "url": "https://www.ferryhopper.com/en/my-bookings",
        "note": "Ref FH56MC2224FB",
    },
    {
        "name": "Bookaway",
        "url": "https://www.bookaway.com/",
        "note": "Ref BW5232109",
    },
    {
        "name": "Lufthansa",
        "url": "https://www.lufthansa.com/us/en/my-bookings",
        "note": "Ref 782HJV · Peterson",
    },
    {
        "name": "Booking.com",
        "url": "https://secure.booking.com/myreservations.html",
        "note": "Wiesbaden, Salzburg, Sarajevo",
    },
    {
        "name": "Airbnb",
        "url": "https://www.airbnb.com/trips/v1",
        "note": "Ljubljana HMENEBDYT9 · Split",
    },
]

PHRASES = [
    {
        "lang": "German",
        "region": "Germany & Austria",
        "lines": [
            {
                "en": "One ticket to …, please",
                "local": "Eine Fahrkarte nach …, bitte",
                "pron": "EYE-neh FAR-kar-teh nakh …, BIT-teh",
            },
            {
                "en": "Which platform?",
                "local": "Von welchem Gleis?",
                "pron": "fon VEL-khem GLYS",
            },
            {
                "en": "Is this seat taken?",
                "local": "Ist dieser Platz frei?",
                "pron": "ist DEE-zer plats FRY",
            },
            {
                "en": "Where is the hotel?",
                "local": "Wo ist das Hotel?",
                "pron": "voh ist dahs hoh-TEL",
            },
            {
                "en": "The bill, please",
                "local": "Die Rechnung, bitte",
                "pron": "dee REKH-noong, BIT-teh",
            },
            {"en": "Help!", "local": "Hilfe!", "pron": "HIL-feh"},
            {
                "en": "I don't speak German",
                "local": "Ich spreche kein Deutsch",
                "pron": "ikh SHPRE-kheh kine DOYTSH",
            },
            {"en": "Thank you", "local": "Danke", "pron": "DAHN-keh"},
        ],
    },
    {
        "lang": "Slovenian",
        "region": "Slovenia",
        "lines": [
            {
                "en": "One ticket to …, please",
                "local": "Eno vozovnico do …, prosim",
                "pron": "EH-noh voh-zohv-NEE-tsoh doh …, PRO-seem",
            },
            {
                "en": "Which platform?",
                "local": "Kateri peron?",
                "pron": "kah-TEH-ree peh-ROHN",
            },
            {
                "en": "Where is the bus station?",
                "local": "Kje je avtobusna postaja?",
                "pron": "kyeh yeh av-toh-BOOS-nah poh-STAH-yah",
            },
            {
                "en": "How much does it cost?",
                "local": "Koliko stane?",
                "pron": "koh-LEE-koh STAH-neh",
            },
            {"en": "Thank you", "local": "Hvala", "pron": "HVAH-lah"},
            {"en": "Good morning", "local": "Dober dan", "pron": "DOH-behr dahn"},
        ],
    },
    {
        "lang": "Croatian",
        "region": "Croatia",
        "lines": [
            {
                "en": "One ticket to …, please",
                "local": "Jednu kartu do …, molim",
                "pron": "YED-noo KAR-too doh …, MOH-leem",
            },
            {
                "en": "Where is the ferry?",
                "local": "Gdje je trajekt?",
                "pron": "gdyeh yeh TRAH-yekt",
            },
            {
                "en": "Which gate?",
                "local": "Koji je ulaz?",
                "pron": "KOH-yee yeh OO-lahz",
            },
            {
                "en": "How much?",
                "local": "Koliko košta?",
                "pron": "KOH-lee-koh KOH-shtah",
            },
            {"en": "Thank you", "local": "Hvala", "pron": "HVAH-lah"},
            {"en": "Good morning", "local": "Dobar dan", "pron": "DOH-bar dahn"},
        ],
    },
    {
        "lang": "Bosnian",
        "region": "Bosnia & Herzegovina",
        "lines": [
            {
                "en": "Where is the bus station?",
                "local": "Gdje je autobuska stanica?",
                "pron": "gdyeh yeh ow-toh-BOOS-kah STAH-nee-tsah",
            },
            {
                "en": "How much?",
                "local": "Koliko košta?",
                "pron": "KOH-lee-koh KOH-shtah",
            },
            {"en": "Thank you", "local": "Hvala", "pron": "HVAH-lah"},
            {"en": "Good morning", "local": "Dobro jutro", "pron": "DOH-broh YOO-troh"},
            {"en": "Excuse me", "local": "Izvinite", "pron": "eez-vee-NEE-teh"},
        ],
    },
]

DAYS = [
    ("2026-07-06", "Monday, July 6", "Wiesbaden, Germany", ["06_July/Best Western Booking.com"]),
    ("2026-07-07", "Tuesday, July 7", "Wiesbaden (depart tomorrow)", []),
    (
        "2026-07-08",
        "Wednesday, July 8",
        "Salzburg, Austria",
        ["08_July/Wiesbaden to Salzburg", "08_July/Salzburg Booking.com", "08_July/Salt Mines Tour"],
    ),
    (
        "2026-07-09",
        "Thursday, July 9",
        "Salzburg, Austria",
        ["09_July/Eagles Nest", "09_July/Mozart Concert"],
    ),
    (
        "2026-07-10",
        "Friday, July 10",
        "Salzburg → Ljubljana, Slovenia",
        [
            "10_July/Salzburg to Ljubljana",
            "10_July/Ljubljana Hotel",
            "10_July/Ljubljana Castle",
        ],
    ),
    (
        "2026-07-11",
        "Saturday, July 11",
        "Ljubljana & Lake Bled, Slovenia",
        [
            "11_July/Ljubljana to Bled",
            "11_July/Ljubljana to Bled 2",
            "11_July/Ebike Tour of Vintgar Gorge",
            "11_July/Bled to Ljubljana",
            "11_July/Bled to Ljubljana 2",
        ],
    ),
    (
        "2026-07-12",
        "Sunday, July 12",
        "Ljubljana → Split, Croatia",
        [
            "12_July/Ljubljana to Zagreb",
            "12_July/Zagreb to Split",
            "12_July/Split Hotel",
        ],
    ),
    (
        "2026-07-13",
        "Monday, July 13",
        "Split & Hvar, Croatia",
        ["13_July/Catamaran Booking", "13_July/Speedboat Tour"],
    ),
    ("2026-07-14", "Tuesday, July 14", "Split, Croatia", ["14_July/Walking Tour Split"]),
    (
        "2026-07-15",
        "Wednesday, July 15",
        "Split → Sarajevo",
        ["15_July/Split to Sarajevo", "15_July/Sarajevo Hotel"],
    ),
    (
        "2026-07-16",
        "Thursday, July 16",
        "Sarajevo, Bosnia & Herzegovina",
        ["16_July/Sarajevo Walking Tour"],
    ),
    (
        "2026-07-17",
        "Friday, July 17",
        "Sarajevo → Frankfurt, Germany",
        ["17_July/Sarajevo to Frankfurt"],
    ),
]


def parse_frontmatter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    fm_text = text[3:end].strip()
    body = text[end + 4 :].lstrip("\n")
    meta = {}
    for line in fm_text.splitlines():
        if ":" not in line:
            continue
        key, val = line.split(":", 1)
        key, val = key.strip(), val.strip().strip('"')
        if key == "tags":
            continue
        meta[key] = val
    return meta, body


def make_qr_svg(data: str) -> str:
    factory = qrcode.image.svg.SvgPathImage
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=4, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(image_factory=factory)
    import io

    buf = io.BytesIO()
    img.save(buf)
    return buf.getvalue().decode("utf-8")


def clean_body(body: str) -> str:
    body = re.sub(r"^# .+\n\n", "", body)
    body = re.sub(r"^## Page \d+\n\n", "", body, flags=re.MULTILINE)
    body = re.sub(r"\n---\n", "\n\n", body)
    body = re.sub(r"about:blank \d+/\d+", "", body)
    body = re.sub(r"https?://[^\s]+ \d+/\d+", "", body)
    body = re.sub(r"\n{3,}", "\n\n", body)
    return body.strip()[:4000]


def build_item(key: str, fm: dict, body: str, enrich: dict) -> dict:
    pdf_key = enrich.get("pdf_key", key)
    pdf_src = ROOT / f"{pdf_key}.pdf"
    pdf_rel = f"documents/{pdf_key}.pdf".replace("\\", "/")

    item = {
        "id": enrich.get("id", key.replace("/", "-").replace(" ", "-").lower()),
        "key": key,
        "title": fm.get("title") or Path(key).stem,
        "type": fm.get("type", "other"),
        "date": fm.get("date", ""),
        "end_date": fm.get("end_date", ""),
        "time": fm.get("time", ""),
        "end_time": fm.get("end_time", ""),
        "location": fm.get("location") or enrich.get("address", ""),
        "provider": fm.get("provider", ""),
        "confirmation": fm.get("confirmation", ""),
        "pin": fm.get("pin", ""),
        "guests": fm.get("guests", ""),
        "price": fm.get("price", ""),
        "duration": fm.get("duration", ""),
        "check_in": fm.get("check_in", ""),
        "check_out": fm.get("check_out", ""),
        "summary": enrich.get("summary", fm.get("title", "")),
        "address": enrich.get("address", ""),
        "phone": enrich.get("phone", ""),
        "email": enrich.get("email", ""),
        "links": enrich.get("links", []),
        "tips": enrich.get("tips", []),
        "passengers": enrich.get("passengers", []),
        "warning": enrich.get("warning", False),
        "details": fm.get("details", ""),
        "body": clean_body(body),
        "pdf": pdf_rel if pdf_src.exists() else None,
    }

    qr_data = enrich.get("qr_data") or item["confirmation"]
    if qr_data:
        item["qr_data"] = qr_data
        item["qr_svg"] = make_qr_svg(qr_data)

    return item


def copy_pdfs():
    DOCS.mkdir(parents=True, exist_ok=True)
    copied = []
    for pdf in sorted(ROOT.rglob("*.pdf")):
        if "app" in pdf.parts:
            continue
        rel = pdf.relative_to(ROOT)
        dest = DOCS / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(pdf, dest)
        copied.append(str(rel).replace("\\", "/"))
    return copied


def download_file(url: str, dest: Path) -> bool:
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "EuropeTripApp/1.0 (https://github.com/jdp71/Europe_Trip; offline trip planner)"
            },
        )
        with urllib.request.urlopen(req, timeout=45) as resp:
            data = resp.read()
        if len(data) < 500 and (b"<html" in data[:300].lower() or b"Blocked" in data):
            print(f"WARN bad response from {url}")
            return False
        dest.write_bytes(data)
        return True
    except Exception as exc:
        print(f"WARN download failed {url}: {exc}")
        return False


def is_valid_image(path: Path) -> bool:
    if not path.exists() or path.stat().st_size < 500:
        return False
    head = path.read_bytes()[:8]
    return head.startswith(b"\x89PNG") or head.startswith(b"\xff\xd8")


def prepare_photo(path: Path, max_width: int = 960) -> None:
    if not is_valid_image(path):
        return
    try:
        img = Image.open(path).convert("RGB")
        if img.width > max_width:
            ratio = max_width / img.width
            img = img.resize((max_width, int(img.height * ratio)), Image.Resampling.LANCZOS)
        img.save(path, "JPEG", quality=85, optimize=True)
    except Exception as exc:
        print(f"WARN photo resize failed {path}: {exc}")


def fetch_day_photo(media: dict, date: str, dest: Path) -> str:
    credit = media.get("photo_credit", "")
    if dest.exists() and is_valid_image(dest):
        prepare_photo(dest)
        return credit

    urls = [media.get("photo_url")] + list(media.get("photo_fallbacks", []))
    for url in urls:
        if not url:
            continue
        for attempt in range(3):
            if download_file(url, dest) and is_valid_image(dest):
                prepare_photo(dest)
                return credit
            time.sleep(1 + attempt)
    return credit


def image_to_data_url(path: Path) -> str | None:
    if not is_valid_image(path):
        return None
    suffix = path.suffix.lower()
    mime = "image/jpeg" if suffix in (".jpg", ".jpeg") else "image/png"
    encoded = base64.standard_b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def fetch_day_assets() -> dict[str, dict]:
    CITIES.mkdir(parents=True, exist_ok=True)
    result: dict[str, dict] = {}

    for date, media in DAY_MEDIA.items():
        photo_path = CITIES / f"{date}.jpg"
        credit = fetch_day_photo(media, date, photo_path)
        photo_ok = is_valid_image(photo_path)

        result[date] = {
            "city": media["city"],
            "photo": f"assets/cities/{date}.jpg" if photo_ok else None,
            "photo_credit": credit,
        }
        time.sleep(0.3)

    return result


def write_precache(pdfs: list[str], asset_files: list[str], build_id: str) -> None:
    urls = [
        "./",
        "./index.html",
        "./manifest.json",
        "./css/app.css",
        "./js/app.js",
        "./sw.js",
        "./precache.json",
        "./trip-data.json",
        "./vendor/pdf.min.js",
        "./vendor/pdf.worker.min.js",
        "./icons/icon-192.png",
        "./icons/icon-512.png",
    ]
    for pdf in pdfs:
        urls.append(f"./documents/{pdf}")
    for asset in asset_files:
        urls.append(f"./{asset}")

    manifest = {"version": build_id, "urls": urls}
    (APP / "precache.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")


def main():
    items = {}
    for key, enrich in ENRICH.items():
        md_path = ROOT / f"{key}.md"
        if not md_path.exists():
            print(f"WARN missing: {md_path}")
            continue
        text = md_path.read_text(encoding="utf-8", errors="replace")
        fm, body = parse_frontmatter(text)
        item = build_item(key, fm, body, enrich)
        items[item["id"]] = item

    pdfs = copy_pdfs()
    day_assets = fetch_day_assets()

    days = []
    for date, label, location, keys in DAYS:
        day_items = []
        for k in keys:
            e = ENRICH.get(k, {})
            iid = e.get("id", k.replace("/", "-").replace(" ", "-").lower())
            if iid in items:
                day_items.append(iid)
        day = {"date": date, "label": label, "location": location, "items": day_items}
        if date in day_assets:
            day.update(day_assets[date])
        days.append(day)

    asset_files = []
    if ASSETS.exists():
        for f in ASSETS.rglob("*"):
            if f.is_file():
                asset_files.append(str(f.relative_to(APP)).replace("\\", "/"))

    data = {
        "trip": {
            "title": "Europe Trip 2026",
            "subtitle": "Joy & Jeffery Peterson",
            "start": "2026-07-06",
            "end": "2026-07-17",
            "route": "Germany → Austria → Slovenia → Croatia → Bosnia → Germany",
            "travelers": ["Joy Peterson", "Jeffery Peterson"],
        },
        "days": days,
        "items": items,
        "travel_services": TRAVEL_SERVICES,
        "phrases": PHRASES,
        "pdfs": pdfs,
        "assets": asset_files,
        "built": __import__("datetime").datetime.now().isoformat(timespec="seconds"),
    }

    out = APP / "trip-data.json"
    APP.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    build_id = __import__("datetime").datetime.now().strftime("%Y%m%d%H%M")
    write_precache(pdfs, asset_files, build_id)

    print(
        f"Built {out} — {len(items)} items, {len(pdfs)} PDFs, "
        f"{len(days)} days, {len(asset_files)} assets, cache {build_id}"
    )


if __name__ == "__main__":
    main()
