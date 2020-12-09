## Transilien (Paris region commuter train) real-time information panel

This is a real-time information panel showing the departure times for trains from a given station in the Paris Transilien commuter train network

![alt text](https://github.com/andreistoian/transilien_info_panel/blob/main/photo1.jpg?raw=true)

It is based on two parts that communicate through serial-over-USB: 
- a software service running on a Raspberry PI connnected to the internet. This is implemented as a python service that gets real-time info from the Transilien Web API with an SQL backend and a schedule refreshing cron job
- a 7-segment LED based display showing a maximum of 4 trains and the current time. This is based on a PIC18F microcontroller and several MAX



