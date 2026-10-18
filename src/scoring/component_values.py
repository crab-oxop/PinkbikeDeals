"""
Component value database — MSRP reference data for mountain bike parts.

All values in USD (new retail). Used-value multipliers applied separately.
Organized by component slot. Fuzzy matching is done by the extractor.

Coverage: forks, shocks, drivetrains, brakes, wheels, droppers,
tires, handlebars, stems, saddles, pedals, grips.
"""

# =============================================================================
# FORKS — Single crown suspension forks
# =============================================================================
FORK_VALUES = {
    # Fox 2023-2026
    "Fox 38 Factory":           1149,
    "Fox 38 Performance Elite": 929,
    "Fox 38 Performance":       769,
    "Fox 36 Factory":           1099,
    "Fox 36 Performance Elite": 879,
    "Fox 36 Performance":       719,
    "Fox 34 Factory":           999,
    "Fox 34 Performance Elite": 829,
    "Fox 34 Performance":       669,
    "Fox 34 Rhythm":            549,
    "Fox 32 Step-Cast Factory": 999,
    "Fox 32 Step-Cast Performance": 699,
    # RockShox 2023-2026
    "RockShox ZEB Ultimate":    999,
    "RockShox ZEB Select+":     749,
    "RockShox ZEB Select":      599,
    "RockShox ZEB Base":        449,
    "RockShox Lyrik Ultimate":  949,
    "RockShox Lyrik Select+":   699,
    "RockShox Lyrik Select":    549,
    "RockShox Pike Ultimate":   899,
    "RockShox Pike Select+":    649,
    "RockShox Pike Select":     499,
    "RockShox Recon":           399,
    "RockShox 35 Gold":         349,
    "RockShox 30 Gold":         299,
    "RockShox Judy":            249,
    "RockShox Domain":          599,
    "RockShox Boxxer Ultimate": 999,
    "RockShox Boxxer Select":   699,
    # Ohlins
    "Ohlins RXF38 m.2":        1599,
    "Ohlins RXF36 m.2":        1499,
    # DVO
    "DVO Diamond":              899,
    "DVO Beryl":                599,
    # Marzocchi
    "Marzocchi Bomber Z1":      579,
    "Marzocchi Bomber Z2":      399,
    # MRP
    "MRP Bartlett":             999,
    "MRP Ribbon":               849,
    # Manitou
    "Manitou Mezzer Pro":       879,
    "Manitou Mezzer Expert":    649,
    "Manitou Mattoc Pro":       699,
    # EXT
    "EXT Era":                  1899,
    # SR Suntour
    "SR Suntour Zeron":         349,
    "SR Suntour Auron":         299,
    "SR Suntour XCR":           149,
    # Formula
    "Formula Selva S":          999,
    "Formula Selva R":          799,
}

# =============================================================================
# SHOCKS — Rear suspension
# =============================================================================
SHOCK_VALUES = {
    # Fox
    "Fox Float X2 Factory":         659,
    "Fox Float X2 Performance":     479,
    "Fox Float DPX2 Factory":       599,
    "Fox Float DPX2 Performance":   429,
    "Fox Float DPS Factory":        499,
    "Fox Float DPS Performance":    329,
    "Fox DHX2 Factory":             659,
    "Fox Van":                      399,
    # RockShox
    "RockShox Super Deluxe Ultimate": 629,
    "RockShox Super Deluxe Select+":  479,
    "RockShox Super Deluxe Select":   429,
    "RockShox Super Deluxe Coil Ultimate": 599,
    "RockShox Super Deluxe Coil Select+":  449,
    "RockShox Deluxe Select+":      299,
    "RockShox Deluxe Select":       249,
    "RockShox Monarch":             279,
    "RockShox Vivid Ultimate":      649,
    "RockShox Vivid Select+":       479,
    # Ohlins
    "Ohlins TTX22M":               699,
    "Ohlins TTX Air":              649,
    # EXT
    "EXT Storia V3":               799,
    "EXT Storia Lok":              899,
    # Cane Creek
    "Cane Creek DB Kitsuma Air":    499,
    "Cane Creek DB Kitsuma Coil":   449,
    "Cane Creek DB Inline":         399,
    "Cane Creek Double Barrel":     499,
    # PUSH
    "PUSH Elevensix":               999,
    "PUSH Nineone":                 899,
    # Manitou
    "Manitou Mara Pro":             449,
    "Manitou Mara":                 349,
    # X-Fusion
    "X-Fusion Nude":                249,
    "X-Fusion Vector":              299,
    # DVO
    "DVO Topaz":                    449,
    "DVO Jade":                     399,
    # Formula
    "Formula Mod":                  549,
}

# =============================================================================
# DRIVETRAINS — Complete groupsets and individual parts
# =============================================================================
DRIVETRAIN_VALUES = {
    # SRAM Eagle (complete groups)
    "SRAM XX Eagle AXS T-Type":     3600,
    "SRAM XX1 Eagle AXS":           3200,
    "SRAM XX1 Eagle AXS T-Type":    3200,
    "SRAM XO Eagle AXS T-Type":     2200,
    "SRAM XO1 Eagle AXS":           2100,
    "SRAM X0 Eagle AXS T-Type":     2200,
    "SRAM X01 Eagle AXS":           2100,
    "SRAM XO1 Eagle":               1200,
    "SRAM X01 Eagle":               1200,
    "SRAM GX Eagle AXS T-Type":     1200,
    "SRAM GX Eagle AXS":            1100,
    "SRAM GX Eagle":                550,
    "SRAM NX Eagle":                350,
    "SRAM SX Eagle":                250,
    # SRAM individual
    "SRAM X0 Eagle AXS Derailleur": 580,
    "SRAM GX Eagle AXS Derailleur": 330,
    # Shimano (complete groups)
    "Shimano XTR M9100":            2400,
    "Shimano XTR M9200":            2500,
    "Shimano Deore XT M8100":       900,
    "Shimano XT M8100":             900,
    "Shimano XT M8120":             900,
    "Shimano XT Di2":               2000,
    "Shimano XTR Di2":              3000,
    "Shimano SLX M7100":            550,
    "Shimano Deore M6100":          350,
    "Shimano Deore M5100":          280,
    "Shimano Alivio":               180,
    "Shimano CUES":                 300,
    # Shimano individual
    "Shimano XTR Derailleur":       350,
    "Shimano XT Derailleur":        130,
    "Shimano SLX Derailleur":       75,
}

# =============================================================================
# BRAKES — Disc brakes (set of 2)
# =============================================================================
BRAKE_VALUES = {
    # SRAM
    "SRAM Maven Ultimate":          650,
    "SRAM Maven Silver":            430,
    "SRAM Maven Bronze":            280,
    "SRAM Code Ultimate":           650,
    "SRAM Code RSC":                420,
    "SRAM Code R":                  280,
    "SRAM G2 Ultimate":             380,
    "SRAM G2 RSC":                  260,
    "SRAM G2 R":                    180,
    "SRAM Level Ultimate":          400,
    "SRAM Level TLM":               300,
    "SRAM Level T":                 160,
    "SRAM Guide RSC":               350,
    "SRAM Guide R":                 200,
    # Shimano
    "Shimano Saint M820":           500,
    "Shimano XT M8120 4-pot":       320,
    "Shimano XT M8100":             260,
    "Shimano SLX M7120 4-pot":      220,
    "Shimano SLX M7100":            180,
    "Shimano Deore M6120 4-pot":    160,
    "Shimano Deore M6100":          120,
    "Shimano MT520 4-pot":          160,
    "Shimano MT500":                120,
    "Shimano MT420":                100,
    "Shimano MT200":                60,
    # Hope
    "Hope Tech4 V4":                520,
    "Hope Tech4 E4":                440,
    "Hope Tech3 V4":                460,
    "Hope Tech3 E4":                380,
    # Magura
    "Magura MT7":                   480,
    "Magura MT5":                   300,
    "Magura MT Trail":              350,
    # TRP
    "TRP DH-R EVO":                 380,
    "TRP Trail EVO":                340,
    "TRP Quadiem":                  280,
    # Hayes
    "Hayes Dominion A4":            340,
    "Hayes Dominion A2":            240,
    # Tektro
    "Tektro HD-M745":               120,
    "Tektro Orion":                 80,
}

# =============================================================================
# WHEELS — Wheelsets (front + rear pair)
# =============================================================================
WHEEL_VALUES = {
    # ENVE
    "ENVE M930":                    2800,
    "ENVE M730":                    2600,
    "ENVE M630":                    2400,
    "ENVE M525":                    2200,
    # Reserve (Santa Cruz)
    "Reserve 30|HD i9":             2400,
    "Reserve 30|HD DT":             1800,
    "Reserve 30 i9":                2200,
    "Reserve 30 DT":                1600,
    "Reserve 37":                   2200,
    "Santa Cruz Reserve":           2000,
    # Industry Nine
    "I9 Hydra Enduro S":            1800,
    "I9 Hydra Enduro":              1600,
    "I9 Hydra Trail S":             1700,
    "I9 Hydra Trail":               1500,
    "Industry Nine Enduro S":       1800,
    "Industry Nine Enduro":         1600,
    "Industry Nine Trail S":        1700,
    "Industry Nine Trail":          1500,
    "I9 1/1 Enduro S":              1500,
    "I9 1/1 Trail S":               1400,
    "I9 101":                       800,
    # DT Swiss
    "DT Swiss EXC 1501":            1400,
    "DT Swiss EX 1700":             750,
    "DT Swiss EX 1501":             1200,
    "DT Swiss E 1900":              500,
    "DT Swiss E 1700":              400,
    "DT Swiss M 1900":              500,
    "DT Swiss M 1700":              400,
    "DT Swiss XM 1700":             500,
    "DT Swiss XMC 1200":            1600,
    "DT Swiss FR 1500":             900,
    "DT Swiss 350":                 700,
    # Race Face
    "Race Face Turbine R":          900,
    "Race Face Turbine":            700,
    "Race Face Aeffect R":          600,
    "Race Face Aeffect":            450,
    "Race Face AR":                 500,
    # Stans / NoTubes
    "Stan's Flow EX3 i9":           1200,
    "Stan's Flow EX3 DT 350":       800,
    "Stan's Flow EX3":              600,
    "Stan's Flow S2":               700,
    "Stan's Arch S2":               650,
    "Stan's Crest S2":              600,
    # Crankbrothers
    "Crankbrothers Synthesis E":    1800,
    "Crankbrothers Synthesis":      1200,
    # WTB
    "WTB KOM i30 DT 350":          800,
    "WTB KOM i30":                  500,
    "WTB ST i30":                   350,
    # Roval (Specialized)
    "Roval Traverse SL":            1800,
    "Roval Traverse":               900,
    "Roval Control SL":             1800,
    "Roval Control":                900,
    # Bontrager (Trek)
    "Bontrager Line Elite":         900,
    "Bontrager Line Comp":          600,
    "Bontrager Line":               400,
    # Sun Ringle / Others
    "Sun Ringle Duroc":             350,
    "Alex Rims":                    250,
    "Mavic":                        500,
    "Mavic Deemax":                 700,
    "Mavic Crossmax":               600,
    "Newmen":                       800,
    # We Are One
    "We Are One Union":             1600,
    "We Are One Convergence":       1400,
    "We Are One Faction":           1200,
    "We Are One Strife":            1000,
    # Hunt
    "Hunt Enduro Wide":             600,
    "Hunt Trail Wide":              500,
}

# =============================================================================
# DROPPER POSTS
# =============================================================================
DROPPER_VALUES = {
    # RockShox
    "RockShox Reverb AXS":         550,
    "RockShox Reverb AXS XPLR":    480,
    "RockShox Reverb Stealth":      350,
    # Fox
    "Fox Transfer Factory":         459,
    "Fox Transfer Performance":     299,
    "Fox Transfer SL":              499,
    # OneUp
    "OneUp Dropper V3":             220,
    "OneUp Dropper V2":             200,
    "OneUp Dropper":                200,
    # PNW
    "PNW Rainier Gen3":             199,
    "PNW Rainier":                  189,
    "PNW Loam":                     169,
    "PNW Bachelor":                 139,
    "PNW Coast":                    219,
    # BikeYoke
    "BikeYoke Revive":              299,
    "BikeYoke Divine":              269,
    "BikeYoke Sagma":               139,
    # SDG
    "SDG Tellis":                   199,
    # Brand-X
    "Brand-X Ascend":               120,
    # KS / Kind Shock
    "KS Lev":                       180,
    "KS LEV Integra":               230,
    "KS Rage-i":                    160,
    "Kind Shock LEV":               230,
    # TranzX
    "TranzX":                       100,
    # Crankbrothers
    "Crankbrothers Highline":       200,
    # Specialized
    "Specialized Command Post":     280,
    # Thomson
    "Thomson Covert":               350,
    # 9point8
    "9point8 Fall Line":            350,
}

# =============================================================================
# TIRES (per tire — most bikes have 2)
# =============================================================================
TIRE_VALUES = {
    # Maxxis
    "Maxxis Assegai":               80,
    "Maxxis Minion DHF":            70,
    "Maxxis Minion DHR II":         70,
    "Maxxis Minion DHR2":           70,
    "Maxxis Dissector":             70,
    "Maxxis Aggressor":             65,
    "Maxxis High Roller II":        70,
    "Maxxis Shorty":                80,
    "Maxxis Rekon":                 65,
    "Maxxis Ardent":                55,
    "Maxxis Forekaster":            60,
    # Specialized
    "Specialized Butcher":          75,
    "Specialized Eliminator":       75,
    "Specialized Cannibal":         80,
    "Specialized Slaughter":        70,
    "Specialized Purgatory":        65,
    "Specialized Ground Control":   55,
    # Continental
    "Continental Kryptotal":        85,
    "Continental Der Baron":        75,
    "Continental Trail King":       65,
    "Continental Mountain King":    55,
    # Schwalbe
    "Schwalbe Magic Mary":          80,
    "Schwalbe Hans Dampf":          75,
    "Schwalbe Nobby Nic":           60,
    "Schwalbe Big Betty":           70,
    # Vittoria
    "Vittoria Mazza":               80,
    "Vittoria Martello":            75,
    "Vittoria Syerra":              85,
    # Michelin
    "Michelin DH22":                70,
    "Michelin DH34":                70,
    "Michelin Wild Enduro":         70,
    # Pirelli
    "Pirelli Scorpion":             75,
    # WTB
    "WTB Verdict":                  65,
    "WTB Judge":                    65,
    "WTB Vigilante":                60,
    "WTB Trail Boss":               55,
    # Teravail
    "Teravail Kessel":              60,
    "Teravail Ehline":              60,
}

# =============================================================================
# HANDLEBARS
# =============================================================================
HANDLEBAR_VALUES = {
    # Deity
    "Deity Skywire":                100,
    "Deity Speedway":               85,
    "Deity Blacklabel":             120,
    "Deity CZ38":                   55,
    # Race Face
    "Race Face Next R":             180,
    "Race Face Next SL":            250,
    "Race Face Sixc":               160,
    "Race Face Atlas":              70,
    "Race Face Turbine R":          80,
    "Race Face Chester":            40,
    # Renthal
    "Renthal Fatbar":               90,
    "Renthal Fatbar Lite":          130,
    "Renthal Fatbar Carbon":        180,
    # OneUp
    "OneUp Carbon Bar":             130,
    "OneUp Aluminium Bar":          50,
    # Chromag
    "Chromag Fubars":               90,
    "Chromag BZA":                  150,
    "Chromag Cutlass":              70,
    # Spank
    "Spank Spike Race":             60,
    "Spank Vibrocore":              80,
    # Burgtec
    "Burgtec Ride Wide":            100,
    # Nukeproof
    "Nukeproof Horizon":            60,
    # Specialized
    "S-Works Carbon Bar":           200,
    # Bontrager
    "Bontrager Line Pro":           100,
    "Bontrager Line":               50,
    # Enve
    "ENVE M7":                      250,
    "ENVE M9":                      300,
}

# =============================================================================
# STEMS
# =============================================================================
STEM_VALUES = {
    "Deity Copperhead":             70,
    "Deity Cavity":                 60,
    "Race Face Turbine R":          60,
    "Race Face Atlas":              50,
    "Race Face Aeffect":            40,
    "Chromag HiFi":                 80,
    "Chromag Ranger":               60,
    "Renthal Apex":                 70,
    "OneUp EDC Stem":               65,
    "Burgtec Enduro MK3":          70,
    "Spank Spike":                  50,
    "Hope AM":                      65,
    "Specialized Trail":            40,
    "Bontrager Line Pro":           65,
    "ENVE M7":                      120,
    "ENVE M9":                      160,
}

# =============================================================================
# SADDLES
# =============================================================================
SADDLE_VALUES = {
    "WTB Volt":                     55,
    "WTB Silverado":                55,
    "WTB Deva":                     55,
    "SDG Bel-Air":                  65,
    "SDG Fly":                      45,
    "Deity Speedtrap":              55,
    "Ergon SM":                     60,
    "Ergon SME3":                   80,
    "Specialized Bridge":           50,
    "Specialized Power":            120,
    "Specialized Phenom":           90,
    "Specialized Romin":            100,
    "Fizik Alpaca":                 60,
    "Fizik Terra":                  100,
    "Chromag Trailmaster":          65,
    "Chromag Overture":             65,
    "Fabric Scoop":                 50,
    "SQLab 611":                    100,
}

# =============================================================================
# PEDALS
# =============================================================================
PEDAL_VALUES = {
    # Flat
    "Deity T-Mac":                  100,
    "Deity Deftrap":                65,
    "Deity TMAC":                   100,
    "OneUp Comp":                   80,
    "OneUp Aluminium":              60,
    "Race Face Atlas":              70,
    "Race Face Chester":            45,
    "Crankbrothers Stamp 7":        120,
    "Crankbrothers Stamp 3":        60,
    "Crankbrothers Stamp 2":        50,
    "Crankbrothers Stamp 1":        35,
    "Spank Spike":                  40,
    "Nukeproof Horizon Pro":        80,
    "Burgtec Penthouse MK5":        120,
    "Chromag Dagga":                90,
    "Chromag Scarab":               60,
    # Clipless
    "Shimano Saint PD-M828":        120,
    "Shimano XT PD-M8120":          100,
    "Shimano XT PD-M8100":          80,
    "Crankbrothers Mallet E LS":    170,
    "Crankbrothers Mallet DH":      170,
    "Crankbrothers Candy":          80,
    "Crankbrothers Eggbeater":      70,
    "HT T1":                        160,
    "HT X2":                        130,
}

# =============================================================================
# CRANKS (crankset only, without chainring)
# =============================================================================
CRANK_VALUES = {
    "SRAM XX1 Eagle AXS Cranks":    400,
    "SRAM X01 Eagle AXS Cranks":    300,
    "SRAM X0 Eagle Cranks":         280,
    "SRAM GX Eagle Cranks":         150,
    "SRAM NX Eagle Cranks":         80,
    "SRAM Descendant":              120,
    "Race Face Next R Cranks":      350,
    "Race Face Next SL Cranks":     500,
    "Race Face Turbine Cranks":     200,
    "Race Face Aeffect Cranks":     100,
    "Race Face Atlas Cranks":       120,
    "Race Face Chester Cranks":     50,
    "Shimano XTR Cranks":           300,
    "Shimano XT Cranks":            150,
    "Shimano SLX Cranks":           90,
    "Shimano Deore Cranks":         55,
    "Hope EVO Cranks":              350,
    "Praxis":                       120,
    "e*thirteen TRS+":              250,
    "e*thirteen LG1":               200,
    "Truvativ Descendant":          120,
}

# =============================================================================
# FRAME VALUE ESTIMATES — Base frame values by brand tier and year
# =============================================================================
FRAME_BRAND_TIERS = {
    "premium": {
        "brands": ["Santa Cruz", "Yeti", "Ibis", "Evil", "Forbidden",
                    "Pivot", "Revel", "We Are One", "Specialized S-Works",
                    "RAAW", "Starling", "Kavenz", "Nicolai", "Unno"],
        "base_value": 3500,  # Avg new carbon frame MSRP
    },
    "high": {
        "brands": ["Specialized", "Trek", "Giant", "Norco", "Rocky Mountain",
                    "Transition", "Devinci", "Intense", "Commencal",
                    "Canyon", "Propain", "Mondraker", "Scott", "Cannondale",
                    "Kona", "Knolly"],
        "base_value": 2500,
    },
    "mid": {
        "brands": ["YT", "Nukeproof", "Orbea", "Marin", "Merida",
                    "Polygon", "Vitus", "Whyte", "NS Bikes", "Banshee",
                    "Salsa", "Chromag", "Bird", "Cotic"],
        "base_value": 1800,
    },
    "budget": {
        "brands": ["Diamondback", "Mongoose", "GT", "Fuji", "Haro",
                    "Jamis", "Felt", "Kestrel"],
        "base_value": 1000,
    },
}

# Material multiplier for frame value
FRAME_MATERIAL_MULT = {
    "Carbon Fiber": 1.0,
    "Carbon":       1.0,
    "Aluminum":     0.55,
    "Aluminium":    0.55,
    "Alloy":        0.55,
    "Steel":        0.50,
    "Chromoly":     0.55,
    "Titanium":     1.15,
}

# =============================================================================
# COMPONENT TIER CLASSIFICATION — For quality scoring (not value)
# =============================================================================
COMPONENT_TIERS = {
    "fork": {
        "premium": ["Fox 38 Factory", "Fox 36 Factory", "RockShox ZEB Ultimate",
                     "RockShox Lyrik Ultimate", "Ohlins RXF38", "Ohlins RXF36",
                     "EXT Era", "MRP Bartlett"],
        "mid":     ["Fox 38 Performance Elite", "Fox 36 Performance Elite",
                     "RockShox ZEB Select+", "RockShox Lyrik Select+",
                     "RockShox Pike Ultimate", "Fox 34 Factory",
                     "DVO Diamond", "Manitou Mezzer Pro", "Formula Selva S"],
        "entry":   ["Fox 38 Performance", "Fox 36 Performance",
                     "RockShox ZEB Select", "RockShox Lyrik Select",
                     "RockShox Pike Select+", "Marzocchi Bomber Z1",
                     "Fox 34 Performance", "Manitou Mezzer Expert"],
        "budget":  ["RockShox Recon", "RockShox 35 Gold", "Marzocchi Bomber Z2",
                     "SR Suntour Zeron", "RockShox Pike Select",
                     "Fox 34 Rhythm", "SR Suntour Auron"],
    },
    "shock": {
        "premium": ["Fox Float X2 Factory", "RockShox Super Deluxe Ultimate",
                     "Ohlins TTX", "EXT Storia", "PUSH Elevensix",
                     "RockShox Vivid Ultimate", "Fox DHX2 Factory"],
        "mid":     ["Fox Float X2 Performance", "Fox DPX2 Factory",
                     "RockShox Super Deluxe Select+", "RockShox Vivid Select+",
                     "Cane Creek Kitsuma", "PUSH Nineone"],
        "entry":   ["Fox DPX2 Performance", "RockShox Deluxe Select+",
                     "RockShox Super Deluxe Select", "Fox Float DPS Factory",
                     "Manitou Mara Pro", "DVO Topaz"],
        "budget":  ["RockShox Deluxe Select", "Fox Float DPS Performance",
                     "X-Fusion", "RockShox Monarch", "Manitou Mara"],
    },
    "drivetrain": {
        "premium": ["SRAM XX1 Eagle AXS", "SRAM XO1 Eagle AXS", "SRAM X01 Eagle AXS",
                     "SRAM XX Eagle AXS T-Type", "SRAM XO Eagle AXS T-Type",
                     "SRAM X0 Eagle AXS T-Type", "Shimano XTR", "Shimano XTR Di2",
                     "Shimano XT Di2"],
        "mid":     ["SRAM XO1 Eagle", "SRAM X01 Eagle", "SRAM GX Eagle AXS",
                     "SRAM GX Eagle AXS T-Type", "Shimano XT", "Shimano Deore XT"],
        "entry":   ["SRAM GX Eagle", "Shimano SLX", "Shimano CUES"],
        "budget":  ["SRAM NX Eagle", "SRAM SX Eagle", "Shimano Deore",
                     "Shimano Alivio"],
    },
    "brakes": {
        "premium": ["SRAM Code Ultimate", "SRAM Maven Ultimate", "Shimano Saint",
                     "Hope Tech4 V4", "Magura MT7", "TRP DH-R EVO"],
        "mid":     ["SRAM Code RSC", "SRAM Maven Silver", "Shimano XT 4-pot",
                     "Shimano XT M8120", "Hope Tech4 E4", "Magura MT5",
                     "Hayes Dominion A4", "TRP Trail EVO"],
        "entry":   ["SRAM Code R", "SRAM Maven Bronze", "SRAM G2 RSC",
                     "Shimano SLX 4-pot", "Shimano SLX M7120",
                     "Shimano Deore 4-pot", "Shimano MT520",
                     "Magura MT Trail", "Hayes Dominion A2"],
        "budget":  ["SRAM G2 R", "SRAM Level T", "Shimano Deore M6100",
                     "Shimano MT500", "Shimano MT200", "Tektro"],
    },
    "wheels": {
        "premium": ["ENVE M730", "ENVE M930", "ENVE M630", "Reserve i9",
                     "I9 Hydra", "Industry Nine Hydra", "DT Swiss EXC 1501",
                     "We Are One", "Crankbrothers Synthesis E",
                     "Roval Traverse SL", "DT Swiss EX 1501"],
        "mid":     ["DT Swiss EX 1700", "Race Face Turbine R", "I9 1/1",
                     "Stan's Flow i9", "Reserve DT", "Bontrager Line Elite",
                     "Roval Traverse", "DT Swiss M 1700", "Newmen",
                     "Crankbrothers Synthesis", "Hunt Enduro Wide"],
        "entry":   ["DT Swiss E 1900", "Race Face Aeffect R", "Stan's Flow EX3",
                     "WTB KOM i30", "Bontrager Line Comp", "DT Swiss M 1900",
                     "Race Face Aeffect", "Hunt Trail Wide"],
        "budget":  ["WTB ST i30", "Alex Rims", "Sun Ringle Duroc",
                     "Bontrager Line", "DT Swiss E 1700"],
    },
}

# Tier score multipliers
TIER_SCORES = {
    "premium": 95,
    "mid":     70,
    "entry":   45,
    "budget":  20,
    "unknown": 40,
}

# =============================================================================
# MASTER LOOKUP — All component categories
# =============================================================================
ALL_COMPONENT_VALUES = {
    "fork":         FORK_VALUES,
    "shock":        SHOCK_VALUES,
    "drivetrain":   DRIVETRAIN_VALUES,
    "brakes":       BRAKE_VALUES,
    "wheels":       WHEEL_VALUES,
    "dropper":      DROPPER_VALUES,
    "tires":        TIRE_VALUES,
    "handlebars":   HANDLEBAR_VALUES,
    "stem":         STEM_VALUES,
    "saddle":       SADDLE_VALUES,
    "pedals":       PEDAL_VALUES,
    "cranks":       CRANK_VALUES,
}

# Weight of each slot toward total build value (for missing-component estimation)
SLOT_VALUE_WEIGHTS = {
    "fork":         0.20,
    "shock":        0.12,
    "drivetrain":   0.22,
    "brakes":       0.08,
    "wheels":       0.20,
    "dropper":      0.04,
    "tires":        0.03,
    "handlebars":   0.03,
    "stem":         0.01,
    "saddle":       0.01,
    "pedals":       0.02,
    "cranks":       0.04,
}
