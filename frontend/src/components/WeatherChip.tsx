import { CloudSun } from '@phosphor-icons/react';
import type { StationWeather } from '../types';

/** The small temperature badge on a card image.
 *
 *  The icon is decorative and the visible text is a bare number, so the whole
 *  chip carries one accessible label spelling out the condition and the city —
 *  "17 degrees, mainly clear in London" reads; "17°" does not. */
const WeatherChip = ({ weather }: { weather?: StationWeather }) => {
  if (!weather) return null;

  return (
    <span
      className="ds-label v-glass ds-on-photo inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full"
      aria-label={`${weather.temperature_c} degrees, ${weather.condition.toLowerCase()} in ${weather.city}`}
    >
      <CloudSun aria-hidden="true" weight="regular" className="v-icon" />
      <span aria-hidden="true" className="v-num">
        {weather.temperature_c}°
      </span>
    </span>
  );
};

export default WeatherChip;
