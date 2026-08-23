import { CloudSun } from '@phosphor-icons/react';
import { DESTINATIONS } from '../lib/destination-images';
import type { StationWeather } from '../types';

/** Conditions at every destination, with the next three days.
 *
 *  Renders nothing at all when no station answered — an empty row of skeleton
 *  cards would claim the provider is about to reply, and it may not be. */
const WeatherStrip = ({ weather }: { weather: Map<string, StationWeather> }) => {
  const stations = DESTINATIONS.map((d) => weather.get(d.iata)).filter(
    (s): s is StationWeather => s !== undefined,
  );

  if (stations.length === 0) return null;

  return (
    <section aria-labelledby="weather-heading" className="mt-12">
      <div className="flex items-baseline justify-between gap-4 mb-5">
        <div>
          <h2 id="weather-heading" className="ds-label text-muted">
            Weather at your destinations
          </h2>
          <p className="ds-label text-faint">Live conditions and the next three days</p>
        </div>
        <p className="ds-label text-accent">Live</p>
      </div>

      <ul className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4 list-none p-0 m-0">
        {stations.map((station) => (
          <li key={station.iata_code} className="v-glass p-4">
            <div className="flex items-baseline justify-between gap-2">
              <span className="text-strong font-semibold text-sm">{station.city}</span>
              <span className="ds-label text-faint v-num">{station.iata_code}</span>
            </div>

            <p
              className="flex items-center gap-2 mt-3"
              aria-label={`${station.temperature_c} degrees, ${station.condition.toLowerCase()}, wind ${station.wind_kph} kilometres per hour`}
            >
              <CloudSun
                aria-hidden="true"
                weight="regular"
                className="v-icon text-accent"
                style={{ fontSize: '1.6em' }}
              />
              <span aria-hidden="true">
                <span className="v-num text-2xl text-strong">{station.temperature_c}°</span>
                <span className="block ds-label text-muted">{station.condition}</span>
              </span>
            </p>

            <p aria-hidden="true" className="ds-label text-faint mt-2">
              {station.wind_kph} km/h wind
            </p>

            {station.forecast.length > 0 && (
              <ul className="grid grid-cols-3 gap-2 mt-4 pt-3 border-t border-hairline list-none p-0">
                {station.forecast.map((day) => (
                  <li key={day.date} className="text-center">
                    <span className="ds-label text-faint block">
                      {new Date(day.date).toLocaleDateString('en-GB', { weekday: 'short' })}
                    </span>
                    <span
                      className="v-num text-2xs text-muted block mt-1"
                      aria-label={`${day.condition}, high ${day.high_c}, low ${day.low_c}`}
                    >
                      {day.high_c}°/{day.low_c}°
                    </span>
                  </li>
                ))}
              </ul>
            )}
          </li>
        ))}
      </ul>
    </section>
  );
};

export default WeatherStrip;
