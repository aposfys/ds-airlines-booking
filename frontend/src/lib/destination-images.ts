import bcn from '../assets/destinations/bcn.jpg';
import cdg from '../assets/destinations/cdg.jpg';
import fco from '../assets/destinations/fco.jpg';
import fra from '../assets/destinations/fra.jpg';
import lhr from '../assets/destinations/lhr.jpg';
import muc from '../assets/destinations/muc.jpg';

/** Station photography, keyed by the real-world key.
 *
 *  These are small crops lifted from the original design comps, which is the
 *  only place the photography existed — see the README. They are soft at card
 *  size and deliberately sit under a scrim, which is where the design puts
 *  them anyway. Replacing one is a single line here; nothing else knows where
 *  an image came from.
 *
 *  A station with no photograph is not a failure: `imageFor` returns
 *  undefined and the card falls back to the bloom, which is a defined surface
 *  in the token layer rather than an empty box. */
const IMAGES: Readonly<Record<string, string>> = {
  LHR: lhr,
  CDG: cdg,
  FCO: fco,
  BCN: bcn,
  FRA: fra,
  MUC: muc,
};

export const imageFor = (iata: string): string | undefined =>
  IMAGES[iata.toUpperCase()];

/** The published network, in the order the carousel and the cards show it.
 *  Origins are Athens and Thessaloniki; these are the destinations. */
export interface Destination {
  iata: string;
  city: string;
  country: string;
}

export const DESTINATIONS: readonly Destination[] = [
  { iata: 'LHR', city: 'London', country: 'United Kingdom' },
  { iata: 'CDG', city: 'Paris', country: 'France' },
  { iata: 'FCO', city: 'Rome', country: 'Italy' },
  { iata: 'BCN', city: 'Barcelona', country: 'Spain' },
  { iata: 'FRA', city: 'Frankfurt', country: 'Germany' },
  { iata: 'MUC', city: 'Munich', country: 'Germany' },
] as const;
