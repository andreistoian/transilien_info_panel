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
