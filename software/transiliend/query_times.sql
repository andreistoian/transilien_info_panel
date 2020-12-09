DROP PROCEDURE IF EXISTS train_times_for_date_2;
--_direction: 0-banlieue
-- 	        : 1-paris

CREATE PROCEDURE `train_times_for_date_2`(_d DATETIME, _station_name TEXT,_direction INT)

select ST.departure_time, T.trip_id, T.trip_headsign, T.direction_id, R.route_short_name,RD.banlieue_dir
from stop_times ST 		
		inner join trips T on ST.trip_id = T.trip_id inner join routes R ON T.route_id=R.route_id
		inner join calendar C on T.service_id=C.service_id
		left join calendar_dates CD ON CD.service_id = T.service_id AND CD.date = DATE(_d)
		inner join route_direction RD ON T.route_id = RD.route_id
WHERE 		ST.stop_id = (SELECT stop_id FROM stops WHERE stop_name =_station_name AND location_type=0)
		AND ST.departure_time > _d 
		AND C.start_date <= _d AND C.end_date >= _d
		AND R.route_type=2
		AND ( _direction = 1 AND T.direction_id = (!RD.banlieue_dir)
					OR 
				(_direction = 0 AND T.direction_id = RD.banlieue_dir))
		AND ( (C.monday=1 AND (WEEKDAY(_d)=0))
		OR (C.tuesday=1 AND (WEEKDAY(_d)=1))
		OR (C.wednesday=1	AND (WEEKDAY(_d)=2))
		OR (C.thursday=1 AND (WEEKDAY(_d)=3))
		OR (C.friday=1 AND (WEEKDAY(_d)=4))
		OR (C.saturday=1 AND (WEEKDAY(_d)=5))
		OR (C.sunday=1 AND (WEEKDAY(_d)=6)))
		AND (CD.date IS NULL OR (CD.date = DATE(_d) AND CD.exception_type <> 2)) 		
ORDER BY departure_time
LIMIT 15