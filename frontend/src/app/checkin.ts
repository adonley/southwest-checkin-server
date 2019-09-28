/*
  {
    "confirmation": "PXPXFQ",
    "email": "",
    "firstName": "Andrew",
    "flightInfo":
      [
        {
          "arrivalTime": "22:20",
          "boundType": "DEPARTING",
          "checkedIn": false,
          "departureAirport": "San Jose, CA",
          "destinationAirport": "Las Vegas, NV",
          "failed": false,
          "nextDayArrival": false,
          "numberOfPeople": 2,
          "results": [],
          "takeoff": "2019-10-24-21:05",
          "travelTime": "1h 15m",
          "utcDay": 1571961600,
          "utcDepartureTimestamp": 1571976300
        },
        {
          "arrivalTime": "08:00",
          "boundType": "RETURNING",
          "checkedIn": false,
          "departureAirport": "Las Vegas, NV",
          "destinationAirport": "San Jose, CA",
          "failed": false, "nextDayArrival": false,
          "numberOfPeople": 2,
          "results": [],
          "takeoff": "2019-10-28-06:40",
          "travelTime": "1h 20m",
          "utcDay": 1572220800,
          "utcDepartureTimestamp": 1572270000
        }
      ],
    "lastName": "Donley",
    "phone": ""
  }
*/

interface Checkin {
  confirmation: string;
  firstName: string;
  lastName: string;
  phone: string;
  email: string;
  flightInfo: FlightInfo[];
}

interface FlightInfo {
  "arrivalTime": string;
  "boundType": string; // RETURNING
  "checkedIn": boolean;
  "departureAirport": string;
  "destinationAirport": string;
  "failed": boolean;
  "nextDayArrival": boolean;
  "numberOfPeople": number;
  "results": FlightResult[];
  "takeoff": string;
  "travelTime": string;
  "utcDay": number;
  "utcDepartureTimestamp": number;
}

interface FlightResult {

}
