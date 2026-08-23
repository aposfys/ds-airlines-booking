import { useEffect, useState } from 'react';
import api from '../api';
import type { StationWeather } from '../types';

/** Conditions for the given stations, keyed by IATA.
 *
 *  Weather is decoration on top of a booking product, so this hook has no
 *  error state and exposes none: if the call fails, the map stays empty and
 *  every consumer draws nothing. The API is built the same way — it returns
 *  200 with whatever it could gather — so a forecast provider having a bad
 *  afternoon costs this dashboard some chips, not a render. */
export const useWeather = (codes: readonly string[]): Map<string, StationWeather> => {
  const [weather, setWeather] = useState<Map<string, StationWeather>>(new Map());
  const key = [...codes].sort().join(',');

  useEffect(() => {
    if (!key) return;
    let cancelled = false;

    api
      .get<{ stations: StationWeather[] }>('/weather', {
        params: { iata: key.split(',') },
        paramsSerializer: { indexes: null },
      })
      .then(({ data }) => {
        if (cancelled) return;
        setWeather(new Map(data.stations.map((s) => [s.iata_code, s])));
      })
      .catch(() => {
        /* Deliberately silent — see above. */
      });

    return () => {
      cancelled = true;
    };
  }, [key]);

  return weather;
};
