# astrokundali
- version = "0.1.2"
- description = "Flexible astrokundali package with Different house calculation methods and interpretation JSONs"
- authors = name="Mirjan Ali Sha"
- requires-python = ">=3.7"

**Request:**
If anyone would like to collaborate or discuss new features, please send me an email. I will get in touch with you.<br>
If you want access to this project's source code, please do the same. I am planning to make this project fully open source in the near future.
<hr>

# USER OPTIONS
## Ayanāṃśa Options

- **`fagan_bradley`**  
  Fagan–Bradley Ayanāṃśa: a Western sidereal offset fixed at 24°02′31″ (January 1 1950) and widely used in Western sidereal astrology.

- **`lahiri`** *(default)*  
  Lahiri (Chitra‑Paksha/Rohini) Ayanāṃśa: India’s official Vedic ayanāṃśa, zeroed at Spica (Chitra), and by far the most prevalent in Hindu astrology.

- **`deluce`**  
  de Luce Ayanāṃśa: proposed by Robert DeLuce (1877–1964), theoretically set to 1 CE but in practice anchored to ~26°24′47″ (1900) using Newcomb’s precession theory.

- **`raman`**  
  Raman Ayanāṃśa: introduced by B. V. Raman to better align with traditional nakṣatra positions, favored by his school of Vedic astrology.

- **`krishnamurti`**  
  Krishnamurti (KP) Ayanāṃśa: developed by K. S. Krishnamurti for the KP system, emphasizing precise divisional‑chart timing.

- **`sassanian`**  
  Sassanian Ayanāṃśa: reconstructs pre‑Islamic Persian/Sassanian zodiac data (via Al‑Biruni), often used with whole‑sign houses for ancient chart revival.

- **`aldebaran`**  
  Aldebaran Ayanāṃśa: fixes zero at the bright star Aldebaran (15° Taurus), popular in fixed‑star and esoteric charting.

- **`galcenter`**  
  Galcenter Ayanāṃśa: anchors the zodiac at the Milky Way’s center (~5° Sagittarius), used in modern “galactic” sidereal astrology.

## House‑System Options

- **`equal`**  
  Equal Houses: twelve 30° houses measured from the exact Ascendant degree, offering simplicity and uniformity across latitudes.

- **`whole_sign`** *(default)*  
  Whole‑Sign: the sign containing the Ascendant becomes the 1st house, the next sign the 2nd, etc.; the oldest division from Hellenistic to Vedic traditions.

- **`porphyry`**  
  Porphyry: each quadrant (Ascendant→MC, MC→Descendant, etc.) is trisected into three equal parts, creating houses by trisection of angle arcs; described by Vettius Valens in the 2nd CE.

- **`placidus`**  
  Placidus: the most common Western quadrant system, trisecting diurnal/nocturnal arcs between the four angles to set cusps; can fail near polar circles.

- **`koch`**  
  Koch: a time‑based quadrant method dividing right‑ascension arcs equally between angles; popular in research and German circles, defined only within ~66° latitude.

- **`campanus`**  
  Campanus: divides the prime vertical into twelve equal segments, projecting them onto the ecliptic; emphasizes Earth‑centered spatial divisions.

- **`regiomontanus`**  
  Regiomontanus: splits the celestial equator into twelve equal arcs then projects those onto the ecliptic; a medieval Renaissance favorite attributed to Johann Müller.


# Example Usage
<pre>
  pip install astrokundali
  or
  !pip install astrokundali [Notebook]
    </pre>
  **Configure AstroData**
  <pre>
    from astrokundali import AstroData
    data = AstroData(2009,3,30,9,36,0,5,30,19.0760,72.8777,ayanamsa='lahiri')
  </pre>
  **Plot Lagna Chart**
  <pre>
    from astrokundali import plot_lagna_chart
    houses = plot_lagna_chart(data, house_system= 'whole_sign') 
      or 
    houses = plot_lagna_chart(data) 
  </pre>
  **Plot Moon/Chandra Chart**
    <pre>
    from astrokundali import plot_moon_chart
    houses = plot_moon_chart(data, house_system= 'whole_sign') 
      or 
    houses = plot_moon_chart(data) 
  </pre>
  **Plot Navamsa/Navamsha/D9 Chart**
  <pre>
    from astrokundali import plot_navamsa_chart
    houses = plot_navamsa_chart(data, house_system= 'whole_sign') 
      or 
    houses = plot_navamsa_chart(data)
  </pre>
  **Read Astrokundali House Objects**
  <pre>
   from astrokundali import format_houses        
   import json
   readable = format_houses(houses) 
   print(json.dumps(readable, indent=2))
  </pre>
  **Get Planetary Positions and Dispositions**
  <pre>
    from astrokundali import get_dispositions
    import json
    disp = get_dispositions(data, house_system= 'whole_sign')
      or
    disp = get_dispositions(data)
    print(json.dumps(report, ensure_ascii=False, indent=2)) 
  </pre>
  **Get Interpretation Report**
  <pre>
    from astrokundali import generate_report, json_sanitize
    import json
    report  = json_sanitize(generate_report(data, house_system= 'whole_sign'))
      or
    report  = json_sanitize(generate_report(data))
    print(json.dumps(report, ensure_ascii=False, indent=2))
  </pre>
  * to use `json_sanitize` function please install `ftfy` using `pip install ftfy`<br>
  **Marriage Matching**
  <pre>
    from astrokundali import AstroData, match_kundli
    boy = AstroData(1990,1,1,10,0,0,5,30,19.07,72.88)
    girl = AstroData(1992,6,15,16,30,0,5,30,28.61,77.23)
    from pprint import pprint
    pprint(match_kundli(boy, girl))
      or
    from astrokundali import AstroData, match_kundli
    boy = AstroData(1990,1,1,10,0,0,5,30,19.07,72.88,ayanamsa='lahiri')
    girl = AstroData(1992,6,15,16,30,0,5,30,28.61,77.23,ayanamsa='lahiri')
    from pprint import pprint
    pprint(match_kundli(boy, girl, house_system= 'whole_sign')) [Version should be >=0.2.1]
  </pre>
  **Format Match Table in Pandas DataFrame**
  <pre>
    from astrokundali import AstroData, match_kundli
    boy = AstroData(1990,1,1,10,0,0,5,30,19.07,72.88)
    girl = AstroData(1992,6,15,16,30,0,5,30,28.61,77.23)
    astro_match = match_kundli(boy, girl)
    print(astro_match['interpretation'])
    import pandas as pd
    df = pd.DataFrame(astro_match['table'])
    df
  </pre>
  