INSERT INTO `route_direction` (`route_id`, `banlieue_dir`) VALUES
	('DUA810801041', 0),
	('DUA810802061', 0),
	('DUA800803071', 0),
	('DUA800804081', 0),
	('DUA800805091', 0),
	('DUA800853021', 1),
	('DUA800854041', 0),
	('DUA800853022', 0),
	('DUA800854042', 0),
	('DUA800852051', 0),
	('DUA800850011', 0),
	('DUA800851081', 0),
	('DUA800855048', 0);
		
LOAD DATA LOW_PRIORITY LOCAL INFILE 'schedule/calendar_dates.txt' REPLACE INTO TABLE `transilien`.`calendar_dates` FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' ESCAPED BY '"' LINES TERMINATED BY '\r\n' IGNORE 1 LINES (`service_id`, `date`, `exception_type`);
LOAD DATA LOW_PRIORITY LOCAL INFILE 'schedule/calendar.txt' REPLACE INTO TABLE `transilien`.`calendar` FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' ESCAPED BY '"' LINES TERMINATED BY '\r\n' IGNORE 1 LINES (`service_id`,	`monday`,	`tuesday`,	`wednesday` ,	`thursday` ,	`friday` ,	`saturday` ,	`sunday` ,	`start_date` ,	`end_date`);
LOAD DATA LOW_PRIORITY LOCAL INFILE 'schedule/routes.txt' REPLACE INTO TABLE `transilien`.`routes` FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' ESCAPED BY '"' LINES TERMINATED BY '\r\n' IGNORE 1 LINES (`route_id`,`agency_id`,`route_short_name`,`route_long_name`,`route_desc`,`route_type`,`route_url`,`route_color`,`route_text_color`);
LOAD DATA LOW_PRIORITY LOCAL INFILE 'schedule/stop_times.txt' REPLACE INTO TABLE `transilien`.`stop_times` FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' ESCAPED BY '"' LINES TERMINATED BY '\r\n' IGNORE 1 LINES (`trip_id`,`arrival_time`,`departure_time`,`stop_id`,`stop_sequence`,`stop_headsign`,`pickup_type`,`drop_off_type`);
LOAD DATA LOW_PRIORITY LOCAL INFILE 'schedule/stops.txt' REPLACE INTO TABLE `transilien`.`stops` FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' ESCAPED BY '"' LINES TERMINATED BY '\r\n' IGNORE 1 LINES (`stop_id`,`stop_name`,`stop_desc`,`stop_lat`,`stop_lon`,`zone_id`,`stop_url`,`location_type`,`parent_station`);
LOAD DATA LOW_PRIORITY LOCAL INFILE 'schedule/trips.txt' REPLACE INTO TABLE `transilien`.`trips` FIELDS TERMINATED BY ',' OPTIONALLY ENCLOSED BY '"' ESCAPED BY '"' LINES TERMINATED BY '\r\n' IGNORE 1 LINES (`route_id`,`service_id`,`trip_id`,`trip_headsign`,`direction_id`,`block_id`);