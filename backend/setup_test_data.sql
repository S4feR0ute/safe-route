-- TC1: alto riesgo
INSERT INTO district_crime_stats (district_ubigeo, district_name, total_incidents_count, violent_incidents_count, weighted_crime_rate) VALUES
('999901', 'Distrito Sintetico Alto Riesgo', 100, 80, 0.90);

INSERT INTO street_nodes (node_id, geometry, lat, lon) VALUES
(9000001, ST_SetSRID(ST_MakePoint(0, 0), 4326), 0, 0),
(9000002, ST_SetSRID(ST_MakePoint(0, 0.001), 4326), 0.001, 0);

INSERT INTO street_segments (id, osm_way_id, geometry, name, length_m, highway_type, oneway, source_node_id, target_node_id, district_ubigeo) VALUES
(9000001, 9000001, ST_SetSRID(ST_MakeLine(ST_MakePoint(0,0), ST_MakePoint(0,0.001)), 4326), 'Calle Sintetica TC1', 111.0, 'path', false, 9000001, 9000002, '999901');

-- TC2: bajo riesgo, comisaria cerca, 2 camaras
INSERT INTO district_crime_stats (district_ubigeo, district_name, total_incidents_count, violent_incidents_count, weighted_crime_rate) VALUES
('999902', 'Distrito Sintetico Bajo Riesgo', 100, 5, 0.10);

INSERT INTO street_nodes (node_id, geometry, lat, lon) VALUES
(9000003, ST_SetSRID(ST_MakePoint(0, 0.01), 4326), 0.01, 0),
(9000004, ST_SetSRID(ST_MakePoint(0, 0.011), 4326), 0.011, 0);

INSERT INTO street_segments (id, osm_way_id, geometry, name, length_m, highway_type, oneway, source_node_id, target_node_id, district_ubigeo) VALUES
(9000002, 9000002, ST_SetSRID(ST_MakeLine(ST_MakePoint(0,0.01), ST_MakePoint(0,0.011)), 4326), 'Calle Sintetica TC2', 111.0, 'primary', false, 9000003, 9000004, '999902');

INSERT INTO urban_pois (osm_id, poi_type, name, geometry) VALUES
('test_police_tc2', 'police_station', 'Comisaria Test TC2', ST_SetSRID(ST_MakePoint(0, 0.0105), 4326)),
('test_camera_tc2_1', 'surveillance_camera', 'Camara Test TC2-1', ST_SetSRID(ST_MakePoint(0, 0.0102), 4326)),
('test_camera_tc2_2', 'surveillance_camera', 'Camara Test TC2-2', ST_SetSRID(ST_MakePoint(0, 0.0108), 4326));

-- TC3: distrito sin datos de criminalidad
INSERT INTO street_nodes (node_id, geometry, lat, lon) VALUES
(9000005, ST_SetSRID(ST_MakePoint(0, 0.02), 4326), 0.02, 0),
(9000006, ST_SetSRID(ST_MakePoint(0, 0.021), 4326), 0.021, 0);

INSERT INTO street_segments (id, osm_way_id, geometry, name, length_m, highway_type, oneway, source_node_id, target_node_id, district_ubigeo) VALUES
(9000003, 9000003, ST_SetSRID(ST_MakeLine(ST_MakePoint(0,0.02), ST_MakePoint(0,0.021)), 4326), 'Calle Sintetica TC3', 111.0, 'residential', false, 9000005, 9000006, '999903');

-- TC4: comisaria a distancia intermedia (~450m)
INSERT INTO street_nodes (node_id, geometry, lat, lon) VALUES
(9000007, ST_SetSRID(ST_MakePoint(0, 0.03), 4326), 0.03, 0),
(9000008, ST_SetSRID(ST_MakePoint(0, 0.031), 4326), 0.031, 0);

INSERT INTO street_segments (id, osm_way_id, geometry, name, length_m, highway_type, oneway, source_node_id, target_node_id, district_ubigeo) VALUES
(9000004, 9000004, ST_SetSRID(ST_MakeLine(ST_MakePoint(0,0.03), ST_MakePoint(0,0.031)), 4326), 'Calle Sintetica TC4', 111.0, 'residential', false, 9000007, 9000008, '999904');

INSERT INTO urban_pois (osm_id, poi_type, name, geometry) VALUES
('test_police_tc4', 'police_station', 'Comisaria Test TC4', ST_SetSRID(ST_MakePoint(0, 0.025958), 4326));

-- TC5: exactamente 1 camara cercana
INSERT INTO street_nodes (node_id, geometry, lat, lon) VALUES
(9000009, ST_SetSRID(ST_MakePoint(0, 0.04), 4326), 0.04, 0),
(9000010, ST_SetSRID(ST_MakePoint(0, 0.041), 4326), 0.041, 0);

INSERT INTO street_segments (id, osm_way_id, geometry, name, length_m, highway_type, oneway, source_node_id, target_node_id, district_ubigeo) VALUES
(9000005, 9000005, ST_SetSRID(ST_MakeLine(ST_MakePoint(0,0.04), ST_MakePoint(0,0.041)), 4326), 'Calle Sintetica TC5', 111.0, 'residential', false, 9000009, 9000010, '999905');

INSERT INTO urban_pois (osm_id, poi_type, name, geometry) VALUES
('test_camera_tc5', 'surveillance_camera', 'Camara Test TC5', ST_SetSRID(ST_MakePoint(0, 0.0405), 4326));
