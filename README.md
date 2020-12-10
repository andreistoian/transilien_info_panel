## Transilien (Paris region commuter train) real-time information panel

This is a real-time information panel showing the departure times for trains from a given station in the Paris Transilien commuter train network

![alt text](https://github.com/andreistoian/transilien_info_panel/blob/main/photo1.jpg?raw=true)

It is based on two parts that communicate through serial-over-USB: 
- a software service running on a Raspberry PI connnected to the internet. This is implemented as a python service that gets real-time info from the Transilien Web API with an SQL backend and a schedule refreshing cron job
- a 7-segment LED based display showing a maximum of 4 trains and the current time. This is based on a PIC18F microcontroller and 3 MAX7219 7 segment drivers. These are used to show the information on 4 4x7 segment common cathode displays and 4x single 7 segment displays. 

## Functions

- The display shows the 4 next trains from your station the destination
- Trains that are cancelled are shown with blinking 'SuPP' (useful to known what happened to the train you were expecting)
- The train name (A, B, C, D, E) is shown which is very useful for stations where multiple trains pass on different platforms
- Destinations can be one hop or two hops (change trains once). For two hops it is possible to program the exchange time, filtering out train combinations where the exchange time would be too short
- Two destinations can be programmed (toggle with the panel switch). 
- Time can be advanced to show trains schedules in the future (in 15 min increments)
- Error message is shown when no connection to Raspberry Pi

## Schematic

![alt text](https://github.com/andreistoian/transilien_info_panel/blob/main/transilien_small.jpg?raw=true)

## Bill of Materials

- 12 Capacitors
  - 1	C1	470n	
  - 2	C2-C3	22pf	
  - 1	C4	100n	
  - 2	C5-C6	220n	
  - 3	C7,¬C10,¬C12 10uF		
  - 3	C8-C9,¬C11 100n	

- 9 Resistors
  - 7	R1-R4,¬R6,¬R8,¬R11 10k		
  - 1	R5	220		
  - 1	R7	1k		

- 4 Integrated Circuits
  - 3	U1,¬U4-U5 MAX7219		
  - 1	U3	PIC18F4550		

- 1 Diode
  - 1	D2	LED-RED		5V

- 16 Miscellaneous
  - 1	J1	Simple Header through-hole (used for programming the PIC)
  - 1	J2	Through-hole USB connector
  - 1	LED1	HDSP-B0XG		
  - 1	LED2	GNQ-4041AX		
  - 2 panel mounted push buttons
  - 1 through-hole push button (for reset)
  - 1 panel mounted single pole switch		
  - 1	X1	CRYSTAL		8 MHz


## Erratum

- The USB connector is wired wrong (need to invert the two D- and D+ pins)
- There are two missing connections on the diagram and the PCB, these can be fixed with small wires. 


