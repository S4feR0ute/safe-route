"""Distritos objetivo (Lima Metropolitana + Callao) y su mapeo a ubigeo INEI."""

# Distritos
TARGET_DISTRICTS = [
    # --- LIMA ---
    "Ancón, Lima, Peru",
    "Ate, Lima, Peru",
    "Barranco, Lima, Peru",
    "Breña, Lima, Peru",
    "Carabayllo, Lima, Peru",
    "Chaclacayo, Lima, Peru",
    "Chorrillos, Lima, Peru",
    "Cieneguilla, Lima, Peru",
    "Comas, Lima, Peru",
    "El Agustino, Lima, Peru",
    "Independencia, Lima, Peru",
    "Jesús María, Lima, Peru",
    "La Molina, Lima, Peru",
    "La Victoria, Lima, Peru",
    "Lima District, Lima, Peru",
    "Lince, Lima, Peru",
    "Los Olivos, Lima, Peru",
    "Lurigancho, Lima, Peru",
    "Lurín, Lima, Peru",
    "Magdalena del Mar, Lima, Peru",
    "Miraflores, Lima, Peru",
    "Pachacámac, Lima, Peru",
    "Pucusana, Lima, Peru",
    "Pueblo Libre, Lima, Peru",
    "Puente Piedra, Lima, Peru",
    "Punta Hermosa, Lima, Peru",
    "Punta Negra, Lima, Peru",
    "Rímac, Lima, Peru",
    "San Bartolo, Lima, Peru",
    "San Borja, Lima, Peru",
    "San Isidro, Lima, Peru",
    "San Juan de Lurigancho, Lima, Peru",
    "San Juan de Miraflores, Lima, Peru",
    "San Luis, Lima, Peru",
    "San Martín de Porres, Lima, Peru",
    "San Miguel, Lima, Peru",
    "Santa Anita, Lima, Peru",
    "Santa María del Mar, Lima, Peru",
    "Santa Rosa, Lima, Peru",
    "Santiago de Surco, Lima, Peru",
    "Surquillo, Lima, Peru",
    "Villa El Salvador, Lima, Peru",
    "Villa María del Triunfo, Lima, Peru",

    # --- CALLAO ---
    "Bellavista, Callao, Peru",
    "Callao District, Callao, Peru",
    "Carmen de la Legua Reynoso, Callao, Peru",
    "La Perla, Callao, Peru",
    "La Punta, Callao, Peru",
    "Mi Perú, Callao, Peru",
    "Ventanilla, Callao, Peru"
]

# Mapa de nombre OSM -> código ubigeo INEI
UBIGEO_MAP = {
    # --- LIMA ---
    "Ancón, Lima, Peru":                        "150102",
    "Ate, Lima, Peru":                          "150103",
    "Barranco, Lima, Peru":                     "150104",
    "Breña, Lima, Peru":                        "150105",
    "Carabayllo, Lima, Peru":                   "150106",
    "Chaclacayo, Lima, Peru":                   "150107",
    "Chorrillos, Lima, Peru":                   "150108",
    "Cieneguilla, Lima, Peru":                  "150109",
    "Comas, Lima, Peru":                        "150110",
    "El Agustino, Lima, Peru":                  "150111",
    "Independencia, Lima, Peru":                "150112",
    "Jesús María, Lima, Peru":                  "150113",
    "La Molina, Lima, Peru":                    "150114",
    "La Victoria, Lima, Peru":                  "150115",
    "Lima District, Lima, Peru":                "150101",
    "Lince, Lima, Peru":                        "150116",
    "Los Olivos, Lima, Peru":                   "150117",
    "Lurigancho, Lima, Peru":                   "150118",
    "Lurín, Lima, Peru":                        "150119",
    "Magdalena del Mar, Lima, Peru":            "150120",
    "Miraflores, Lima, Peru":                   "150122",
    "Pachacámac, Lima, Peru":                   "150123",
    "Pucusana, Lima, Peru":                     "150124",
    "Pueblo Libre, Lima, Peru":                 "150121",
    "Puente Piedra, Lima, Peru":                "150125",
    "Punta Hermosa, Lima, Peru":                "150126",
    "Punta Negra, Lima, Peru":                  "150127",
    "Rímac, Lima, Peru":                        "150128",
    "San Bartolo, Lima, Peru":                  "150129",
    "San Borja, Lima, Peru":                    "150130",
    "San Isidro, Lima, Peru":                   "150131",
    "San Juan de Lurigancho, Lima, Peru":       "150132",
    "San Juan de Miraflores, Lima, Peru":       "150133",
    "San Luis, Lima, Peru":                     "150134",
    "San Martín de Porres, Lima, Peru":         "150135",
    "San Miguel, Lima, Peru":                   "150136",
    "Santa Anita, Lima, Peru":                  "150137",
    "Santa María del Mar, Lima, Peru":          "150138",
    "Santa Rosa, Lima, Peru":                   "150139",
    "Santiago de Surco, Lima, Peru":            "150140",
    "Surquillo, Lima, Peru":                    "150141",
    "Villa El Salvador, Lima, Peru":            "150142",
    "Villa María del Triunfo, Lima, Peru":      "150143",

    # --- CALLAO ---
    "Bellavista, Callao, Peru":                 "070102",
    "Callao District, Callao, Peru":            "070101",
    "Carmen de la Legua Reynoso, Callao, Peru": "070103",
    "La Perla, Callao, Peru":                   "070104",
    "La Punta, Callao, Peru":                   "070105",
    "Mi Perú, Callao, Peru":                    "070107",
    "Ventanilla, Callao, Peru":                 "070106",
}

# Nominatim resuelve mal estos nombres en texto libre: "Callao District, Callao, Peru"
# matchea primero el boundary de la provincia/región, y "Lima District, Lima, Peru"
# matchea un lugar homónimo equivocado cerca de Tumbes (a ~1000km de Lima). Ambos
# se corrigen con una query estructurada (city/state/country) que sí resuelve al
# distrito correcto.
GEOCODE_QUERY_OVERRIDES = {
    "Callao District, Callao, Peru": {
        "city": "Callao",
        "state": "Lima Metropolitana",
        "country": "Peru",
    },
    "Lima District, Lima, Peru": {
        "city": "Lima",
        "state": "Lima Metropolitana",
        "country": "Peru",
    },
}
