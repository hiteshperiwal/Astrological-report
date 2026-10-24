from __future__ import annotations
from typing import Any, Dict, Iterable, List, Mapping

# A broad catalogue of commonly implemented Parashari/Jaimini/Tajika-style yoga
# names. Presence rules are intentionally separated from the catalogue because
# traditions differ and many yogas require school-specific conditions.
YOGA_CATALOG = [
 'Vesi Yoga','Vosi Yoga','Ubhayachara Yoga','Nipuna Yoga','Sunapha Yoga','Anapha Yoga','Duradhara Yoga','Kemadruma Yoga',
 'Chandra Mangala Yoga','Adhi Yoga','Ruchaka Yoga','Bhadra Yoga','Hamsa Yoga','Malavya Yoga','Sasa Yoga','Gaja Kesari Yoga',
 'Guru Mangala Yoga','Amala Yoga','Parvata Yoga','Kahala Yoga','Chamara Yoga','Shankha Yoga','Bheri Yoga','Mridanga Yoga',
 'Srinatha Yoga','Matsya Yoga','Koorma Yoga','Khadga Yoga','Kusuma Yoga','Kalanidhi Yoga','Kalpadruma Yoga','Lakshmi Yoga',
 'Saraswati Yoga','Bharati Yoga','Saarada Yoga','Hari Yoga','Brahma Yoga','Vishnu Yoga','Siva Yoga','Trilochana Yoga',
 'Gauri Yoga','Chandika Yoga','Amsaavatara Yoga','Devendra Yoga','Indra Yoga','Ravi Yoga','Bhaskara Yoga','Kulavardhana Yoga',
 'Gandharva Yoga','Go Yoga','Vidyut Yoga','Pushkala Yoga','Makuta Yoga','Jaya Yoga','Harsha Yoga','Sarala Yoga','Vimala Yoga',
 'Rajju Yoga','Musala Yoga','Nala Yoga','Maala Yoga','Sarpa Yoga','Gada Yoga','Sakata Yoga','Sringataka Yoga','Hala Yoga',
 'Vajra Yoga','Yava Yoga','Kamala Yoga','Vapi Yoga','Yoopa Yoga','Sara Yoga','Sakti Yoga','Danda Yoga','Nauka Yoga',
 'Koota Yoga','Chatra Yoga','Chapa Yoga','Ardha Chandra Yoga','Chakra Yoga','Samudra Yoga','Veena Yoga','Daama Yoga',
 'Paasa Yoga','Kedaara Yoga','Soola Yoga','Yuga Yoga','Gola Yoga','Subha Yoga','Asubha Yoga','Budha Aditya Yoga',
 'Dhana Yoga','Raja Yoga','Dharma Karmadhipati Raja Yoga','Viparita Raja Yoga','Neecha Bhanga Raja Yoga','Vasumati Yoga',
 'Guru Chandra Yoga','Chandra Adhi Yoga','Sunapha-Anapha-Duradhara','Pancha Mahapurusha Yoga'
]

YOGA_DESCRIPTIONS={
 'Gaja Kesari Yoga':'Jupiter in a kendra from the Moon; traditional texts associate it with intelligence, reputation and support, subject to affliction and dignity.',
 'Budha Aditya Yoga':'Sun and Mercury association; commonly read for intellect, communication and administrative ability, with combustion and dignity considered.',
 'Chandra Mangala Yoga':'Moon-Mars association; traditionally linked with enterprise and material initiative.',
 'Dhana Yoga':'A broad class of wealth combinations involving 2nd, 5th, 9th and 11th lords/associations.',
 'Raja Yoga':'A broad class of status combinations, commonly involving kendra and trikona lords.',
 'Viparita Raja Yoga':'A reversal-type combination involving lords of the 6th, 8th and 12th placed in specified dusthana relationships.',
 'Neecha Bhanga Raja Yoga':'Cancellation conditions for debilitation; multiple classical rule variants exist.',
}

def catalog_status(detected:Iterable[Mapping[str,Any]])->Dict[str,Any]:
    detected_names={str(x.get('name','')).replace(' — review','').replace(' — screening','') for x in detected}
    rows=[]
    for name in YOGA_CATALOG:
        rows.append({'name':name,'detected':name in detected_names,'description':YOGA_DESCRIPTIONS.get(name,'Catalogue entry; school-specific detection rules may vary.')})
    return {'catalog_size':len(YOGA_CATALOG),'detected_count':sum(x['detected'] for x in rows),'entries':rows}

# Extended catalogue for research/reference. Detection remains deliberately separate
# because many named yogas have multiple definitions across Parashari, Jaimini and regional schools.
YOGA_CATALOG.extend([
    'Akhanda Samrajya Yoga','Mahabhagya Yoga','Lakshana Yoga','Parivartana Yoga','Dainya Parivartana Yoga','Khala Parivartana Yoga','Maha Parivartana Yoga',
    'Shubha Kartari Yoga','Papa Kartari Yoga','Lakshmi Narayana Yoga','Dharma Adhipati Yoga','Karma Adhipati Yoga','Dhana Adhipati Yoga',
    'Vesi-Vosi-Ubhayachara Yoga','Sunapha-Anapha Yoga','Chatussagara Yoga','Deva Yoga','Arishta Yoga','Balarishta Yoga','Daridra Yoga',
    'Alpayu Yoga','Madhyayu Yoga','Purnayu Yoga','Akhanda Lakshmi Yoga','Soubhagya Yoga','Kalanidhi Mahapurusha Yoga','Mahendra Yoga',
    'Kusuma Yoga','Sreenatha Yoga','Saraswati Mahapurusha Yoga','Vasumati Yoga','Chatussagara Raja Yoga','Sakata Yoga','Kemadruma Bhanga Yoga',
    'Adhi Raja Yoga','Rajju Naabhasa Yoga','Musala Naabhasa Yoga','Nala Naabhasa Yoga','Maala Naabhasa Yoga','Sarpa Naabhasa Yoga',
    'Gada Naabhasa Yoga','Shakata Naabhasa Yoga','Sringataka Naabhasa Yoga','Hala Naabhasa Yoga','Vajra Naabhasa Yoga','Yava Naabhasa Yoga',
    'Kamala Naabhasa Yoga','Vapi Naabhasa Yoga','Yoopa Naabhasa Yoga','Sara Naabhasa Yoga','Sakti Naabhasa Yoga','Danda Naabhasa Yoga',
    'Nauka Naabhasa Yoga','Koota Naabhasa Yoga','Chatra Naabhasa Yoga','Chapa Naabhasa Yoga','Ardha Chandra Naabhasa Yoga','Chakra Naabhasa Yoga',
    'Samudra Naabhasa Yoga','Veena Naabhasa Yoga','Daama Naabhasa Yoga','Paasa Naabhasa Yoga','Kedara Naabhasa Yoga','Soola Naabhasa Yoga',
    'Yuga Naabhasa Yoga','Gola Naabhasa Yoga','Shubha Naabhasa Yoga','Ashubha Naabhasa Yoga','Vargottama Yoga','Pushkara Navamsha Yoga',
    'Pushkara Bhaga Yoga','Neecha Bhanga Parivartana','Viparita Raja Harsha','Viparita Raja Sarala','Viparita Raja Vimala',
    'Dharma Karmadhipati Yoga','Raja Sambandha Yoga','Raja Lakshana Yoga','Kendra Trikona Raja Yoga','Lakshmi Raja Yoga','Dhana Lakshmi Yoga',
    'Gauri Yoga','Bharati Yoga','Saarada Yoga','Kalanidhi Yoga','Devendra Yoga','Indra Yoga','Bhaskara Yoga','Kulavardhana Yoga',
    'Gandharva Yoga','Go Yoga','Vidyut Yoga','Pushkala Yoga','Makuta Yoga','Jaya Yoga','Harsha Yoga','Sarala Yoga','Vimala Yoga',
    'Amsavatara Yoga','Hari Yoga','Brahma Yoga','Vishnu Yoga','Siva Yoga','Trilochana Yoga','Chandika Yoga','Gouri Yoga',
    'Guru Chandra Adhi Yoga','Chandra Adhi Raja Yoga','Amala Raja Yoga','Parvata Raja Yoga','Kahala Raja Yoga','Chamra Raja Yoga',
    'Shankha Raja Yoga','Bheri Raja Yoga','Mridanga Raja Yoga','Matsya Raja Yoga','Koorma Raja Yoga','Khadga Raja Yoga','Kusuma Raja Yoga',
    'Kalpadruma Raja Yoga','Brahma Raja Yoga','Vishnu Raja Yoga','Siva Raja Yoga','Amsa Raja Yoga','Indra Raja Yoga','Devendra Raja Yoga',
])
YOGA_CATALOG=list(dict.fromkeys(YOGA_CATALOG))

DOSHA_CATALOG=[
    'Manglik / Kuja Dosha','Kala Sarpa Dosha','Grahan Dosha','Guru Chandal Dosha','Shrapit Dosha','Ganda Moola Dosha','Kalathra Dosha',
    'Vish / Punarphoo Dosha','Kemadruma Dosha','Daridra Dosha','Balarishta Dosha','Pitru Dosha','Nadi Dosha','Bhakoot Dosha','Gana Dosha',
    'Rajju Dosha','Vedha Dosha','Graha Yuddha Affliction','Combustion Affliction','Gandanta','Papakartari','Shakatabhanga Review',
    'Dagdha Rashi','Mrityu Bhaga','Tithi Kshaya','Tithi Vriddhi','Navamsha Sandhi','Rashi Sandhi','Karakamsa Affliction','Upapada Affliction',
]

def dosha_catalog_status(detected):
    names={str(x.get('name','')) for x in detected}
    return {'catalog_size':len(DOSHA_CATALOG),'detected_count':sum(n in names for n in DOSHA_CATALOG),
            'entries':[{'name':n,'detected':n in names,'description':'Reference catalogue; detection is school-dependent and requires chart-specific cancellation/mitigation rules.'} for n in DOSHA_CATALOG]}
