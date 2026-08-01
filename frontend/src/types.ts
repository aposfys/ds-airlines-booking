export interface User {
  id: string;
  username: string;
  full_name: string;
  passport_number: string | null;
  email: string;
  is_admin: boolean;
  is_active: boolean;
}

/** A fare class priced for a specific flight.
 *  Decimal fields arrive as strings — Pydantic serialises them that way to
 *  avoid the float rounding that money must not be subject to. */
export interface FareOption {
  fare_class_code: string;
  name: string;
  price_eur: string;
  seats_available: number;
  cabin_bag_included: boolean;
  checked_bag_included: boolean;
  changeable: boolean;
  refundable: boolean;
}

export interface Flight {
  id: string;
  flight_number: string;
  origin_iata: string;
  origin_city: string;
  destination_iata: string;
  destination_city: string;
  departure_date: string;
  scheduled_departure: string;
  scheduled_arrival: string;
  duration_minutes: number;
  aircraft_type: string;
  seats_available: number;
  fares: FareOption[];
}

export interface Booking {
  id: string;
  booking_reference: string;
  status: string;
  flight_number: string;
  origin_iata: string;
  destination_iata: string;
  scheduled_departure: string;
  fare_class_code: string;
  passenger_full_name: string;
  seat_numbers: string[];
  card_last4: string;
  amount_eur: string;
  created_at: string;
}
