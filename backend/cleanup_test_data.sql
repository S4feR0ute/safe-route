DELETE FROM risk_scores WHERE segment_id IN (9000001,9000002,9000003,9000004,9000005);
DELETE FROM street_segments WHERE id IN (9000001,9000002,9000003,9000004,9000005);
DELETE FROM street_nodes WHERE node_id IN (9000001,9000002,9000003,9000004,9000005,9000006,9000007,9000008,9000009,9000010);
DELETE FROM district_crime_stats WHERE district_ubigeo IN ('999901','999902');
DELETE FROM urban_pois WHERE osm_id IN ('test_police_tc2','test_camera_tc2_1','test_camera_tc2_2','test_police_tc4','test_camera_tc5');
