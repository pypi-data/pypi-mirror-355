import csv
import json


def wkt_linestring_z_to_coordinates(wkt):
	# Remove o "LINESTRING Z (" e ")"
	coords_text = wkt.replace("LINESTRING Z (", "").replace(")", "")
	# Divide por vírgula
	points = coords_text.split(", ")
	# Extrai longitude e latitude (ignora a coordenada Z)
	coordinates = [[float(lon), float(lat)] for lon, lat, *_ in (p.split() for p in points)]
	return coordinates


# Lê o CSV e gera GeoJSON
features = []
with open("dados.csv", "r", encoding="utf-8") as f:
	reader = csv.DictReader(f)
	for row in reader:
		coords = wkt_linestring_z_to_coordinates(row["geometria_linha"])
		feature = {"type": "Feature", "geometry": {"type": "LineString", "coordinates": coords}, "properties": {"id": row["id"]}}
		features.append(feature)

geojson_data = {"type": "FeatureCollection", "features": features}

# Salva como arquivo GeoJSON
with open("saida.geojson", "w", encoding="utf-8") as f:
	json.dump(geojson_data, f, ensure_ascii=False, indent=2)
