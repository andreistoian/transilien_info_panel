use transilien;

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
