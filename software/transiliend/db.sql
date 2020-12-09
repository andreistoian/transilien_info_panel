-- --------------------------------------------------------
-- Host:                         127.0.0.1
-- Server version:               5.7.9-log - MySQL Community Server (GPL)
-- Server OS:                    Win64
-- HeidiSQL Version:             9.3.0.4984
-- --------------------------------------------------------

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET NAMES utf8mb4 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;

-- Dumping database structure for transilien
DROP DATABASE IF EXISTS `transilien`;
CREATE DATABASE IF NOT EXISTS `transilien` /*!40100 DEFAULT CHARACTER SET utf8 */;
USE `transilien`;


-- Dumping structure for table transilien.calendar
CREATE TABLE IF NOT EXISTS `calendar` (
  `service_id` int(11) DEFAULT NULL,
  `monday` tinyint(4) DEFAULT NULL,
  `tuesday` tinyint(4) DEFAULT NULL,
  `wednesday` tinyint(4) DEFAULT NULL,
  `thursday` tinyint(4) DEFAULT NULL,
  `friday` tinyint(4) DEFAULT NULL,
  `saturday` tinyint(4) DEFAULT NULL,
  `sunday` tinyint(4) DEFAULT NULL,
  `start_date` datetime DEFAULT NULL,
  `end_date` datetime DEFAULT NULL,
  KEY `Index 2` (`start_date`),
  KEY `Index 3` (`end_date`),
  KEY `Index 4` (`monday`),
  KEY `Index 5` (`tuesday`),
  KEY `Index 6` (`wednesday`),
  KEY `Index 1` (`service_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- Data exporting was unselected.


-- Dumping structure for table transilien.calendar_dates
CREATE TABLE IF NOT EXISTS `calendar_dates` (
  `service_id` int(11) NOT NULL,
  `date` date DEFAULT NULL,
  `exception_type` int(11) DEFAULT NULL,
  KEY `Index 1` (`service_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- Dumping structure for table transilien.routes
DROP TABLE IF EXISTS `routes`;
CREATE TABLE IF NOT EXISTS `routes` (
  `route_id` char(16) NOT NULL,
  `agency_id` varchar(128) DEFAULT NULL,
  `route_short_name` varchar(4) DEFAULT NULL,
  `route_long_name` varchar(255) DEFAULT NULL,
  `route_desc` varchar(255) DEFAULT NULL,
  `route_type` int(11) DEFAULT NULL,
  `route_url` varchar(255) DEFAULT NULL,
  `route_color` char(6) DEFAULT NULL,
  `route_text_color` char(6) DEFAULT NULL,
  PRIMARY KEY (`route_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- Data exporting was unselected.


-- Dumping structure for table transilien.route_direction
DROP TABLE IF EXISTS `route_direction`;
CREATE TABLE IF NOT EXISTS `route_direction` (
  `route_id` varchar(50) DEFAULT NULL,
  `banlieue_dir` int(11) DEFAULT NULL,
  KEY `Index 1` (`route_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- Data exporting was unselected.


-- Dumping structure for table transilien.stops
DROP TABLE IF EXISTS `stops`;
CREATE TABLE IF NOT EXISTS `stops` (
  `stop_id` varchar(128) NOT NULL,
  `stop_name` varchar(255) DEFAULT NULL,
  `stop_desc` varchar(255) DEFAULT NULL,
  `stop_lat` decimal(10,8) DEFAULT NULL,
  `stop_lon` decimal(10,8) DEFAULT NULL,
  `zone_id` varchar(128) DEFAULT NULL,
  `stop_url` varchar(255) DEFAULT NULL,
  `location_type` int(11) DEFAULT NULL,
  `parent_station` varchar(128) DEFAULT NULL,
  PRIMARY KEY (`stop_id`),
  KEY `Index 2` (`stop_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- Data exporting was unselected.


-- Dumping structure for table transilien.stop_times
DROP TABLE IF EXISTS `stop_times`;
CREATE TABLE IF NOT EXISTS `stop_times` (
  `trip_id` char(32) NOT NULL,
  `arrival_time` time DEFAULT NULL,
  `departure_time` time DEFAULT NULL,
  `stop_id` varchar(128) NOT NULL,
  `stop_sequence` int(11) DEFAULT NULL,
  `stop_headsign` char(8) DEFAULT NULL,
  `pickup_type` int(11) DEFAULT NULL,
  `drop_off_type` int(11) DEFAULT NULL,
  PRIMARY KEY (`trip_id`,`stop_id`),
  KEY `Index 1` (`stop_id`),
  KEY `Index 2` (`trip_id`),
  KEY `Index 3` (`departure_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;

-- Data exporting was unselected.

-- Dumping structure for table transilien.trips
DROP TABLE IF EXISTS `trips`;
CREATE TABLE IF NOT EXISTS `trips` (
  `route_id` char(16) DEFAULT NULL,
  `service_id` int(11) NOT NULL,
  `trip_id` char(32) NOT NULL,
  `trip_headsign` char(8) NOT NULL,
  `direction_id` int(11) DEFAULT NULL,
  `block_id` varchar(50) DEFAULT NULL,
  PRIMARY KEY (`trip_id`),
  KEY `Index 1` (`route_id`),
  KEY `Index 3` (`service_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8;
 
drop procedure if exists train_times_for_day_2stations;
DELIMITER //

CREATE PROCEDURE `train_times_for_day_2stations`(IN `_d` DATETIME, IN `_station_name` TEXT, IN `_station_name2` TEXT)
begin

select R.route_short_name, T.trip_headsign, TRIPS_2_STOPS.departure_time FROM

(SELECT T1.trip_id, T1.departure_time FROM 

(select ST2.trip_id, ST2.stop_id, ST2.departure_time
from	stop_times ST2
	inner join stops S2 ON ST2.stop_id = S2.stop_id
WHERE
 ST2.stop_id IN (SELECT stop_id FROM stops WHERE stop_name =_station_name2 AND location_type=0)) T2

inner join 

(select ST.trip_id, ST.stop_id, ST.departure_time
from	stop_times ST 
   inner join stops S ON ST.stop_id = S.stop_id
WHERE
	 ST.stop_id IN (SELECT stop_id FROM stops WHERE stop_name =_station_name AND location_type=0)) T1
	 
	  ON T1.trip_id = T2.trip_id
		where 
		T1.departure_time > TIME(_d)
		AND
		T1.departure_time < T2.departure_time
	  
	  ) TRIPS_2_STOPS

inner join trips T on T.trip_id = TRIPS_2_STOPS.trip_id
inner join routes R ON T.route_id=R.route_id

where TRIPS_2_STOPS.trip_id in 

(SELECT T.trip_id
from
trips T
inner join	calendar C on T.service_id=C.service_id
left join calendar_dates CD ON CD.service_id = T.service_id AND CD.date = DATE(_d)
where
( ((C.start_date <= _d AND C.end_date >= _d AND CD.date IS NULL)

AND ( (C.monday=1 AND (WEEKDAY(_d)=0))
OR (C.tuesday=1 AND (WEEKDAY(_d)=1))
OR (C.wednesday=1	AND (WEEKDAY(_d)=2))
OR (C.thursday=1 AND (WEEKDAY(_d)=3))
OR (C.friday=1 AND (WEEKDAY(_d)=4))
OR (C.saturday=1 AND (WEEKDAY(_d)=5))
OR (C.sunday=1 AND (WEEKDAY(_d)=6)))
)
OR (CD.date = DATE(_d) AND CD.exception_type <> 2))
) 

ORDER BY TRIPS_2_STOPS.departure_time;
end//

DELIMITER ; 
drop procedure if exists query_train_id;
DELIMITER //
CREATE PROCEDURE `query_train_id`(IN train_number_web VARCHAR(255), IN train_headsign_web VARCHAR(255), OUT route_short_name CHAR(1))
begin
	select distinct r.route_short_name 
	INTO route_short_name 
	from trips t inner join routes r on t.route_id=r.route_id 
	where ((trip_id like CONCAT('DUASN', REPLACE(train_number_web, '\'', ''), '%')) OR (trip_id like CONCAT('DUA', REPLACE(train_number_web, '\'', ''), '%'))) AND trip_headsign=train_headsign_web;
end//
DELIMITER ; 
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