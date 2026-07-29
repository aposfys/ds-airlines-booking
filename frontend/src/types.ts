export interface Flight {
  unique_code: string;
  departure: string;
  destination: string;
  date: string;
  time: string;
  cost: number;
  duration: string;
  availability: number;
}

export interface Booking {
  _id: string;
  flight_code: string;
  full_name: string;
  passport_num: string;
  card_last4: string;
  departure: string;
  destination: string;
  flight_date: string;
  cost: number;
}
