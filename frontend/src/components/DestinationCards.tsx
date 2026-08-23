import { DESTINATIONS, imageFor } from '../lib/destination-images';
import type { StationWeather } from '../types';
import WeatherChip from './WeatherChip';

interface Props {
  weather: Map<string, StationWeather>;
  onSelect: (iata: string) => void;
}

/** Popular destinations.
 *
 *  Each card is a button, not a link with a picture in it: choosing one runs a
 *  search. The photograph is decorative (`alt=""`) and the accessible name
 *  describes the action rather than the image — a passenger navigating by
 *  button list wants "Search flights to London", not "London at dusk". */
const DestinationCards = ({ weather, onSelect }: Props) => (
  <section aria-labelledby="destinations-heading" className="mt-12">
    <div className="flex items-baseline justify-between gap-4 mb-5">
      <h2 id="destinations-heading" className="ds-label text-muted">
        Popular destinations
      </h2>
      <p className="ds-label text-faint">ATH · SKG → Europe</p>
    </div>

    <ul className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 list-none p-0 m-0">
      {DESTINATIONS.map((destination) => {
        const image = imageFor(destination.iata);
        return (
          <li key={destination.iata}>
            <button
              type="button"
              onClick={() => onSelect(destination.iata)}
              aria-label={`Search flights to ${destination.city}`}
              className="ds-card-photo relative block w-full overflow-hidden text-left"
              style={{ borderRadius: 'var(--r-lg)', height: 'var(--sp-9)' }}
            >
              {image ? (
                <img
                  src={image}
                  alt=""
                  aria-hidden="true"
                  decoding="async"
                  loading="lazy"
                  sizes="(min-width: 1024px) 16vw, (min-width: 768px) 33vw, 50vw"
                  className="ds-photo"
                />
              ) : (
                /* No photograph for this station — the bloom is a defined
                   surface, so the card is still a card. */
                <span className="ds-photo" style={{ background: 'var(--bloom)' }} />
              )}
              <span className="ds-scrim ds-scrim--card" />

              <span className="absolute top-2 right-2">
                <WeatherChip weather={weather.get(destination.iata)} />
              </span>

              <span className="absolute left-3 bottom-2.5 ds-on-photo">
                <span className="block font-semibold text-sm">{destination.city}</span>
                <span className="block ds-label opacity-80">{destination.iata}</span>
              </span>
            </button>
          </li>
        );
      })}
    </ul>
  </section>
);

export default DestinationCards;
