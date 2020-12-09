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