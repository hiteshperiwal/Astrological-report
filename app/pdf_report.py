from __future__ import annotations
from io import BytesIO
from typing import Any, Dict
from xml.sax.saxutils import escape as _xml_escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.graphics.shapes import Drawing, Line, String, Rect


def _xml(value: Any) -> str:
    """Escape dynamic text before it is embedded in ReportLab Paragraph markup."""
    return _xml_escape(str(value if value is not None else ""))

def _chart_drawing(v: Dict[str, Any], title: str, width: float = 245, height: float = 190) -> Drawing:
    d=Drawing(width,height); d.add(Rect(2,2,width-4,height-4,strokeColor=colors.HexColor('#8b6b3e'),fillColor=colors.HexColor('#fffaf0')))
    cx,cy=width/2,height/2
    # North Indian fixed-house geometry. Planet placement is derived only from the
    # computed house field; signs rotate from the divisional Lagna.
    pts=[(cx,3),(width-3,cy),(cx,height-3),(3,cy)]
    for a,b in zip(pts,pts[1:]+pts[:1]): d.add(Line(a[0],a[1],b[0],b[1],strokeColor=colors.HexColor('#8b6b3e'),strokeWidth=1))
    d.add(Line(3,3,width-3,height-3,strokeColor=colors.HexColor('#8b6b3e'),strokeWidth=.7)); d.add(Line(width-3,3,3,height-3,strokeColor=colors.HexColor('#8b6b3e'),strokeWidth=.7))
    d.add(String(cx,height-10,title,fontSize=8.5,fontName='Helvetica-Bold',textAnchor='middle',fillColor=colors.HexColor('#5b3a21')))
    # Same house centers as the web North-Indian renderer, scaled to the PDF chart.
    raw_pos={1:(200,72),2:(92,42),3:(43,132),4:(94,200),5:(43,286),6:(92,352),7:(200,328),8:(308,352),9:(357,286),10:(306,200),11:(357,132),12:(308,42)}
    pos={h:(x/400*width, height-y/400*height) for h,(x,y) in raw_pos.items()}
    from .engine import SIGNS
    for hnum in range(1,13):
        x,y=pos[hnum]; sign=(int(v.get('lagna_sign_index',0))+hnum-1)%12
        d.add(String(x,y+10,f'H{hnum}',fontSize=5.5,fillColor=colors.HexColor('#9b7a45'),textAnchor='middle'))
        d.add(String(x,y+1,SIGNS[sign],fontSize=6.2,fontName='Helvetica-Bold',fillColor=colors.HexColor('#372718'),textAnchor='middle'))
        planets=[p for p,pd in v.get('planets',{}).items() if pd.get('house')==hnum]
        for i,pname in enumerate(planets[:4]): d.add(String(x,y-9-i*7,pname,fontSize=5.3,fontName='Helvetica-Bold',fillColor=colors.HexColor('#7b2348'),textAnchor='middle'))
    return d


def _table(data, widths):
    t=Table(data,repeatRows=1,colWidths=widths)
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#e9eef7')),('GRID',(0,0),(-1,-1),.35,colors.HexColor('#aeb8c4')),('FONTSIZE',(0,0),(-1,-1),7),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),4),('RIGHTPADDING',(0,0),(-1,-1),4)]))
    return t


def build_pdf(chart: Dict[str, Any], narrative: Dict[str, Any]) -> bytes:
    out=BytesIO(); doc=SimpleDocTemplate(out,pagesize=A4,leftMargin=13*mm,rightMargin=13*mm,topMargin=12*mm,bottomMargin=12*mm)
    styles=getSampleStyleSheet(); styles.add(ParagraphStyle(name='Small2',parent=styles['BodyText'],fontSize=7.5,leading=10)); styles.add(ParagraphStyle(name='Tiny',parent=styles['BodyText'],fontSize=6.5,leading=8))
    m=chart['meta']; story=[Paragraph('JYOTISH LAB 0.9.8 — COMPLETE VEDIC ASTROLOGY REPORT',styles['Title']),Paragraph(f"<b>{_xml(m.get('name','Native'))}</b> · {_xml(m.get('birth_local',''))} · {_xml(m.get('place',''))} · {_xml(m.get('timezone',''))}",styles['BodyText']),Paragraph('Astronomical layer: Swiss Ephemeris · Sidereal Lahiri / Chitra Paksha · Whole-sign houses.',styles['Small2']),Spacer(1,8)]
    story.append(Paragraph('1. Kundali overview',styles['Heading2']))
    story.append(Table([[ _chart_drawing(chart,'D1 / Rashi'), _chart_drawing(chart['divisional_charts']['D9'],'D9 / Navamsa') ]],colWidths=[88*mm,88*mm]))
    story.append(Spacer(1,8)); story.append(Paragraph('Core Nakshatra',styles['Heading3']))
    for x in chart['nakshatra_analysis']['reading']: story.append(Paragraph('• '+_xml(x),styles['Small2']))
    story.append(PageBreak())
    story.append(Paragraph('2. Graha and Nakshatra matrix',styles['Heading2']))
    data=[['Graha','Sign','House','Degree','Nakshatra','Pada','Dignity','Retro','Combust']]
    for p,d in chart['planets'].items(): data.append([p,d['sign'],str(d['house']),f"{d['degree_in_sign']:.2f}",d['nakshatra']['name'],str(d['nakshatra']['pada']),d['dignity'],'Yes' if d['retrograde'] else 'No','Yes' if d['combust'] else 'No'])
    story.append(_table(data,[18*mm,23*mm,12*mm,16*mm,35*mm,11*mm,23*mm,13*mm,15*mm]))
    story.append(Spacer(1,8)); story.append(Paragraph('Nakshatra detail',styles['Heading3']))
    nm=chart['nakshatra_analysis']['moon']; story.append(Paragraph(f"Moon: <b>{_xml(nm['name'])} Pada {_xml(nm['pada'])}</b> · deity {_xml(nm['deity'])} · shakti {_xml(nm['shakti'])} · gana {_xml(nm['gana'])} · yoni {_xml(nm['yoni'])} · nadi {_xml(nm['nadi'])} · Vimshottari lord {_xml(nm['vimshottari_lord'])}",styles['Small2']))
    story.append(PageBreak())
    story.append(Paragraph('3. Divisional chart catalogue',styles['Heading2']))
    rows=[['Varga','Name','Lagna','Primary traditional lens']]
    lens={'D2':'wealth/resources','D3':'siblings/courage','D4':'property/fortune','D7':'children/creative lineage','D9':'dharma/marriage and inner strength','D10':'career/status','D12':'parents/ancestry','D16':'vehicles/comforts','D20':'spiritual practice','D24':'education','D27':'strength/vitality','D30':'adversity/misfortune','D40':'maternal merit','D45':'paternal merit','D60':'fine karmic differentiation'}
    for k,v in chart['divisional_charts'].items(): rows.append([k,v['name'],v.get('lagna_sign',''),lens.get(k,'specialized divisional lens')])
    story.append(_table(rows,[15*mm,40*mm,30*mm,85*mm])); story.append(Spacer(1,7))
    # Compact visual atlas: 4 charts per page
    for i,(k,v) in enumerate(chart['divisional_charts'].items()):
        if i%4==0: story.append(PageBreak()); story.append(Paragraph('Varga visual atlas',styles['Heading3']))
        if i%2==0: row_draw=[]
        row_draw.append(_chart_drawing(v,f"{k} {v['name']}",82*mm,63*mm))
        if i%2==1: story.append(Table([row_draw],colWidths=[85*mm,85*mm]))
    story.append(PageBreak())
    story.append(Paragraph('4. Vimshottari Dasha — adjacent Mahadasha context',styles['Heading2']))
    dctx=narrative.get('interpretations',{}).get('dasha_context',{}) or {}
    selected=dctx.get('selected_mahadashas',[]) or []
    story.append(Paragraph('Timing scope: previous two Mahadashas + current Mahadasha + next three Mahadashas. Sub-period tables below are generated separately so the timing hierarchy remains readable.',styles['Small2']))
    mrows=[['Phase','Lord','Start','End']]
    prev_n=len(dctx.get('previous_mahadashas',[]) or [])
    for i,x in enumerate(selected):
        phase='Previous' if i<prev_n else ('Current' if dctx.get('current_mahadasha',{}).get('start')==x.get('start') else 'Next')
        mrows.append([phase,str(x.get('lord','')),str(x.get('start',''))[:10],str(x.get('end',''))[:10]])
    if len(mrows)>1: story.append(_table(mrows,[30*mm,35*mm,45*mm,45*mm]))

    order=[('Ketu',7),('Venus',20),('Sun',6),('Moon',10),('Mars',7),('Rahu',18),('Jupiter',16),('Saturn',19),('Mercury',17)]
    def add_dasha_level(title, level, widths, limit=5000):
        from datetime import datetime as _dt, timedelta as _td
        rows=[['Parent Mahadasha','Lord','Start','End']]; count=0
        def emit(start_iso,end_iso,lord,depth,parent_label):
            nonlocal count
            if count>=limit: return
            st=_dt.fromisoformat(start_iso); en=_dt.fromisoformat(end_iso); total=(en-st).total_seconds(); cur=st
            for k,(child_lord,years) in enumerate(order):
                if count>=limit: return
                child_end=en if k==8 else cur+_td(seconds=total*years/120.0)
                if depth==level:
                    rows.append([str(parent_label),str(child_lord),str(cur)[:10],str(child_end)[:10]])
                    count+=1
                elif depth<level:
                    emit(cur.isoformat(),child_end.isoformat(),child_lord,depth+1,child_lord)
                cur=child_end
        for top in selected:
            emit(top.get('start'),top.get('end'),top.get('lord'),2,top.get('lord'))
            if count>=limit: break
        story.append(PageBreak()); story.append(Paragraph(title,styles['Heading2']))
        if len(rows)>1: story.append(_table(rows,widths))
        else: story.append(Paragraph('No periods available in the selected Mahadasha scope.',styles['Small2']))

    add_dasha_level('5. Antardasha Timings',2,[34*mm,24*mm,34*mm,34*mm])
    add_dasha_level('6. Pratyantar Dasha Timings',3,[30*mm,20*mm,30*mm,30*mm])
    add_dasha_level('7. Sookshma Dasha Timings',4,[27*mm,18*mm,27*mm,27*mm])
    add_dasha_level('8. Prana Dasha Timings',5,[24*mm,16*mm,24*mm,24*mm])
    story.append(PageBreak())
    story.append(Paragraph('9. Yogas, Doshas and strength',styles['Heading2']))
    for y in chart.get('yogas',[]):
        story.append(Paragraph(f"<b>{_xml(y['name'])}</b> — {_xml(y['basis'])} — {_xml(y['strength'])}",styles['Small2']))
        fw=y.get('fruitification',{}).get('windows',[])[:4]
        if fw: story.append(Paragraph(_xml('Fruitification windows: '+', '.join(f"{w['start']}–{w['end']} ({w['dasha_lord']})" for w in fw)),styles['Tiny']))
    story.append(Spacer(1,5));
    for d in chart.get('doshas',[]): story.append(Paragraph(f"<b>{_xml(d['name'])}</b> — {_xml(d['status'])} — {_xml(d['severity'])} — {_xml(d['basis'])}",styles['Small2']))
    story.append(Spacer(1,8));
    rows=[['Planet','Strength','Dignity','House','Combust']]
    for p,d in chart['planet_strengths']['planets'].items(): rows.append([p+(' (R)' if d['components']['retrograde'] else ''),str(d['score']),d['components']['dignity'],str(d['components']['house']),'Yes' if d['components']['combust'] else 'No'])
    story.append(_table(rows,[28*mm,22*mm,35*mm,20*mm,20*mm,22*mm])); story.append(PageBreak())
    story.append(Paragraph('10. Forecast and planning windows',styles['Heading2']))
    f=chart['forecast']; story.append(Paragraph(f"Horizon: {f['start']} → {f['end']} · {f['amount']} {f['unit']} · {f['granularity']} sampling.",styles['Small2']))
    perf=chart.get('performance',{}); rows=[['Domain','Peak date','Index','Dasha']]
    for domain,items in perf.get('peaks',{}).items():
        if items: rows.append([domain.replace('_',' ').title(),items[0]['date'],str(items[0]['score']),items[0]['dasha']])
    story.append(_table(rows,[45*mm,35*mm,25*mm,30*mm])); story.append(Spacer(1,7))
    story.append(Paragraph('Planning interpretation',styles['Heading3']))
    for domain,v in chart.get('recommendations',{}).items():
        if domain=='start_new': continue
        story.append(Paragraph(f"<b>{_xml(v['label'])}</b>: {_xml(v.get('interpretive_note','Deterministic Jyotish activation index derived from the configured timing layers.'))}",styles['Small2']))
    story.append(PageBreak())
    story.append(Paragraph('11. Predictive astrology',styles['Heading2']))
    pred= narrative.get('predictions',{}) or {}
    story.append(Paragraph(f"Selected horizon: {_xml(pred.get('horizon',{}).get('start',''))} → {_xml(pred.get('horizon',{}).get('end',''))} · {_xml(pred.get('granularity',''))}. The prediction layer combines the calculated Vimshottari hierarchy, slow-planet transits, transit Nakshatra/Pada, Ashtakavarga, alternative Dashas, Sudarshana, Tajaka and exact astronomical events.",styles['Small2']))
    prows=[['Date','Focus','Dasha','Jupiter H','Saturn H','SAV J/S']]
    for x in (pred.get('predictions') or [])[:180]:
        prows.append([str(x.get('date','')),', '.join(x.get('focus',[])[:2]),str(x.get('dasha','')),str(x.get('transit_houses',{}).get('Jupiter','—')),str(x.get('transit_houses',{}).get('Saturn','—')),f"{x.get('ashtakavarga',{}).get('jupiter_sav','—')}/{x.get('ashtakavarga',{}).get('saturn_sav','—')}"])
    if len(prows)>1: story.append(_table(prows,[24*mm,42*mm,45*mm,18*mm,18*mm,22*mm]))
    story.append(Spacer(1,7)); story.append(Paragraph('Prediction interpretations',styles['Heading3']))
    for x in (pred.get('predictions') or [])[:80]: story.append(Paragraph(f"<b>{_xml(x.get('date',''))}</b> — {_xml(x.get('interpretation',''))}",styles['Small2']))
    story.append(PageBreak())
    story.append(Paragraph('12. Advanced Jyotish',styles['Heading2']))
    kar=[['Role','Planet','Degree']]+[[x['role'],x['planet'],str(x['degree_in_sign'])] for x in chart['chara_karakas']['karakas']]; story.append(_table(kar,[50*mm,45*mm,30*mm])); story.append(Spacer(1,8))
    ar=[['Pada','House','Sign','Lord']]+[[k,str(v['house']),v['sign'],v['lord']] for k,v in chart['arudha_padas'].items()]; story.append(_table(ar,[25*mm,25*mm,40*mm,35*mm])); story.append(Spacer(1,8))
    story.append(PageBreak())
    story.append(Paragraph('13. Strength screens and timing systems',styles['Heading2']))
    story.append(Paragraph('Shadbala below is a six-component screening estimate, not a complete canonical calculation. Interpret component totals as approximate.',styles['Small2']))
    sb=[['Planet','Sthana','Dig','Kala','Cheshta','Naisargika','Drik','Rupas','%']]
    for p,d in chart.get('shadbala',{}).get('planets',{}).items(): sb.append([p,str(d['sthana']),str(d['dig']),str(d['kala']),str(d['cheshta']),str(d['naisargika']),str(d['drik']),str(d['rupas']),str(d['strength_pct'])])
    story.append(_table(sb,[20*mm,18*mm,16*mm,18*mm,18*mm,22*mm,18*mm,18*mm,15*mm])); story.append(Spacer(1,7))
    av=chart.get('ashtakavarga_classical',{}); story.append(Paragraph('Ashtakavarga — BAV/SAV with BPHS/PVR-style reductions',styles['Heading3']))
    avrows=[['Planet']+[str(i+1) for i in range(12)]]
    for p,v in av.get('bav',{}).items(): avrows.append([p]+[str(x) for x in v])
    avrows.append(['SAV']+[str(x) for x in av.get('sav',[])])
    story.append(_table(avrows,[22*mm]+[11*mm]*12)); story.append(Spacer(1,5))
    story.append(Paragraph(f"Aggregate Shodhya Pinda totals (sum across seven grahas): Rasi {av.get('shodhya_pinda',{}).get('rasi_pinda','')} · Shodhya {av.get('shodhya_pinda',{}).get('reduced_pinda','')}",styles['Small2']))
    pinda=av.get('shodhya_pinda',{}).get('per_planet',{})
    if pinda:
        p_rows=[['Graha','Rasi Pinda','Graha Pinda','Shodhya Pinda']]+[[p,str(v['rasi_pinda']),str(v['graha_pinda']),str(v['shodhya_pinda'])] for p,v in pinda.items()]
        story.append(_table(p_rows,[35*mm,35*mm,35*mm,40*mm]))
    story.append(PageBreak())
    story.append(Paragraph('14. Alternative Dasha and Tajaka layers',styles['Heading2']))
    for key in ('chara_dasha','ashtottari','yogini','narayana','kalachakra'):
        layer=chart.get('advanced_timing',{}).get(key,{})
        story.append(Paragraph(f"<b>{_xml(layer.get('system',key))}</b> — {_xml(layer.get('method',''))}",styles['Small2']))
        rows=[['Lord/Sign','Start','End']]
        for x in layer.get('periods',[])[:24]: rows.append([str(x.get('lord',x.get('sign',''))),str(x.get('start',''))[:10],str(x.get('end',''))[:10]])
        story.append(_table(rows,[45*mm,40*mm,40*mm])); story.append(Spacer(1,5))
    story.append(Paragraph('Tajaka / Varshaphala annual returns',styles['Heading3']))
    tr=[['Year','Solar return','Lagna','Muntha','Year lord']]
    for x in chart.get('tajaka',{}).get('years',[])[:10]: tr.append([str(x.get('year','')),str(x.get('solar_return',''))[:19],str(x.get('lagna_sign','')),str(x.get('muntha_sign','')),str(x.get('year_lord',''))])
    story.append(_table(tr,[20*mm,48*mm,30*mm,30*mm,25*mm])); story.append(PageBreak())
    story.append(Paragraph('15. Exact astronomical events',styles['Heading2']))
    er=[['Type','Planet','Station','From','To','Datetime']]
    for x in chart.get('exact_astronomical_events',{}).get('events',[])[:160]: er.append([x.get('type',''),x.get('planet',''),x.get('station',''),x.get('from_sign',''),x.get('to_sign',''),str(x.get('datetime',''))[:25]])
    story.append(_table(er,[25*mm,25*mm,25*mm,25*mm,25*mm,55*mm])); story.append(Spacer(1,7))
    story.append(Paragraph('Eclipses',styles['Heading3']))
    ee=[['Type','Maximum','Flags']]+[[x.get('type',''),str(x.get('maximum','')),str(x.get('flags',''))] for x in chart.get('eclipses',{}).get('events',[])[:40]]
    story.append(_table(ee,[45*mm,70*mm,30*mm])); story.append(PageBreak())
    story.append(Paragraph('16. Numerology',styles['Heading2']))
    num=chart.get('numerology',{}); core=num.get('core',{})
    nrows=[['Number','Value','Meaning / lens'],['Life Path',str(core.get('life_path','')),str(core.get('life_path_theme',''))],['Birthday',str(core.get('birthday','')),'birth-day signature'],['Expression',str(core.get('destiny_expression','')),'name / destiny'],['Soul Urge',str(core.get('soul_urge','')),'inner motivation'],['Personality',str(core.get('personality','')),'outward style'],['Maturity',str(core.get('maturity','')),'long-term synthesis'],['Chaldean Name',str(core.get('chaldean_name','')),'name cross-check']]
    story.append(_table(nrows,[38*mm,28*mm,85*mm])); story.append(Spacer(1,7))
    story.append(Paragraph('Pinnacles and challenges',styles['Heading3']))
    pc=[['Pinnacle','Number','Challenge','Number']]
    for k,v in num.get('pinnacles',{}).items(): pc.append([k,str(v),k,str(num.get('challenges',{}).get(k,''))])
    story.append(_table(pc,[35*mm,25*mm,35*mm,25*mm])); story.append(Spacer(1,7))
    story.append(Paragraph('Personal years',styles['Heading3']))
    py=[['Year','Number','Theme']]+[[str(x['year']),str(x['number']),x['theme']] for x in num.get('personal_years',[])[:30]]
    story.append(_table(py,[25*mm,25*mm,70*mm]))
    story.append(Spacer(1,8)); story.append(Paragraph('17. AI interpretation',styles['Heading2']))
    ai=chart.get('ai_interpretation',{})
    if ai.get('status')=='generated':
        story.append(Paragraph(_xml(ai.get('text','')),styles['Small2']))
    else:
        story.append(Paragraph(_xml(ai.get('message','AI interpretation is not configured in the backend.')),styles['Small2']))
    story.append(Spacer(1,8)); story.append(Paragraph('Report disclaimer',styles['Heading3'])); story.append(Paragraph('Interpretations are presented within the Jyotish systems and calculation methods selected in this report. Timing statements are reading windows derived from the supplied chart, dasha and transit layers.',styles['Small2']))
    doc.build(story); return out.getvalue()


def build_mundane_pdf(result: Dict[str, Any]) -> bytes:
    analysis=result['analysis']; historical=result['historical']; forecast=result['forecast']
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER
    import io
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='MuniSmall2', parent=styles['BodyText'], fontSize=7.2, leading=9))
    buf=io.BytesIO(); doc=SimpleDocTemplate(buf,pagesize=A4,rightMargin=28,leftMargin=28,topMargin=28,bottomMargin=28)
    story=[Paragraph('JYOTISH LAB — MUNDANE HISTORICAL ANALOGUE REPORT',styles['Title']),
           Paragraph(f"<b>{_xml(analysis.get('country',''))}</b> · canonical chart: {_xml(analysis.get('event',{}).get('event_name',''))} · {_xml(analysis.get('event',{}).get('local_date',''))}",styles['BodyText']),
           Paragraph('This module reports what happened during historically similar astrological configurations. It does not convert a present or future configuration into an independently invented national event prediction.',styles['MuniSmall2']),Spacer(1,8)]
    lag=analysis.get('lagna',{})
    story.append(Paragraph(f"<b>Country Lagna:</b> {lag.get('sign','—')} · {lag.get('longitude','—')}° sidereal",styles['BodyText']))
    rows=[['Planet','Sign','Degree','Retrograde']]
    for p,d in analysis.get('positions',{}).items(): rows.append([p+(' (R)' if d.get('retrograde') else ''),d.get('sign',''),f"{d.get('degree_in_sign',0):.2f}°",''])
    t=Table(rows,colWidths=[75,80,70,70]); t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#202946')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('GRID',(0,0),(-1,-1),.3,colors.grey),('FONTSIZE',(0,0),(-1,-1),7.5),('VALIGN',(0,0),(-1,-1),'TOP')]))
    story += [Spacer(1,6),t,Spacer(1,10),Paragraph('Historical matching method',styles['Heading2']),Paragraph('Matches use planetary sign overlap, planetary house-from-Lagna structure, major aspects and Lagna relationship. Same-country matches and cross-country matches are both retained because countries with similar chart properties can show similar historical manifestations within this rule system.',styles['MuniSmall2'])]
    rows=[['Country','Event','Date','Type','Similarity','Matched factors']]
    for x in (historical.get('results') or [])[:150]: rows.append([x.get('event',{}).get('country',''),x.get('event',{}).get('event_name',''),x.get('event',{}).get('local_date',''),x.get('event',{}).get('event_type',''),str(x.get('score','')),', '.join(x.get('matches',[])[:4])])
    t=Table(rows,colWidths=[62,130,58,58,48,145],repeatRows=1); t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#202946')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('GRID',(0,0),(-1,-1),.25,colors.grey),('FONTSIZE',(0,0),(-1,-1),6.4),('VALIGN',(0,0),(-1,-1),'TOP')]))
    story += [Spacer(1,8),Paragraph('1. Historical analogues',styles['Heading2']),t]
    story.append(Paragraph('2. Current and future signatures — past manifestations only',styles['Heading2']))
    for label,block in [('Near term',forecast.get('near_term',{})),('Long term',forecast.get('long_term',{}))]:
        story.append(Paragraph(label,styles['Heading3']))
        rows=[['Date','Signature score','Triggers','Past events with similar signature']]
        for x in (block.get('monthly') or [])[:120]:
            analog=x.get('global_historical_analogues') or []
            past='; '.join(f"{a.get('date','')} — {a.get('country','')}: {a.get('event','')}" for a in analog[:5])
            rows.append([x.get('date',''),str(x.get('activation','')),', '.join(x.get('triggers',[])[:4]),past])
        t=Table(rows,colWidths=[52,55,105,289],repeatRows=1); t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#202946')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('GRID',(0,0),(-1,-1),.25,colors.grey),('FONTSIZE',(0,0),(-1,-1),6.1),('VALIGN',(0,0),(-1,-1),'TOP')]))
        story += [t,Spacer(1,8)]
    ex=forecast.get('exact_astronomical_events',{})
    story.append(Paragraph('3. Exact astronomical calendar',styles['Heading2']))
    rows=[['Type','Planet','Station','From','To','Datetime']]
    for x in (ex.get('events') or [])[:180]: rows.append([x.get('type',''),x.get('planet',''),x.get('station',''),x.get('from_sign',''),x.get('to_sign',''),str(x.get('datetime',''))[:25]])
    t=Table(rows,colWidths=[58,58,58,62,62,115],repeatRows=1); t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#202946')),('TEXTCOLOR',(0,0),(-1,0),colors.white),('GRID',(0,0),(-1,-1),.25,colors.grey),('FONTSIZE',(0,0),(-1,-1),6.3)])); story += [t]
    doc.build(story); return buf.getvalue()

