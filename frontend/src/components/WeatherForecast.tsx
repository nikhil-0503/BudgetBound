import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { CloudSun, RefreshCw, Wind, Droplets, Sunrise, Sunset } from 'lucide-react';
import api from '../services/api';

type Forecast = {
  location_name?: string;
  timezone?: string;
  current: Record<string, number | string | null>;
  daily: Record<string, (number | string | null)[]>;
  units: { current?: Record<string, string>; daily?: Record<string, string> };
};

const descriptions: Record<number, string> = {
  0: 'Clear sky', 1: 'Mainly clear', 2: 'Partly cloudy', 3: 'Overcast', 45: 'Fog', 48: 'Rime fog',
  51: 'Light drizzle', 53: 'Drizzle', 55: 'Heavy drizzle', 61: 'Light rain', 63: 'Rain', 65: 'Heavy rain',
  71: 'Light snow', 73: 'Snow', 75: 'Heavy snow', 80: 'Rain showers', 81: 'Rain showers', 82: 'Heavy showers',
  95: 'Thunderstorm', 96: 'Thunderstorm with hail', 99: 'Thunderstorm with hail',
};

export function WeatherForecast({ latitude, longitude, location, days = 7 }: { latitude?: number | null; longitude?: number | null; location?: string; days?: number }) {
  const valid = Number.isFinite(latitude) && Number.isFinite(longitude);
  const query = useQuery<Forecast>({
    queryKey: ['weather-forecast', latitude, longitude, days],
    enabled: Boolean(valid), staleTime: 20 * 60 * 1000, retry: 1,
    queryFn: async () => (await api.get('/api/weather/forecast', { params: { latitude, longitude, days, location_name: location } })).data,
  });

  if (!valid) return <section className="rounded-2xl border border-paper-200 dark:border-paper-700 p-5 text-sm text-paper-500"><CloudSun className="mb-2" aria-hidden="true" />Select a destination with map coordinates to see a live forecast.</section>;
  if (query.isLoading) return <section aria-label="Loading weather forecast" className="animate-pulse rounded-2xl border border-paper-200 dark:border-paper-700 p-5"><div className="mb-4 h-5 w-48 rounded bg-paper-200 dark:bg-paper-700"/><div className="h-24 rounded bg-paper-100 dark:bg-paper-800"/></section>;
  if (query.isError) return <section role="alert" className="rounded-2xl border border-rose-300 p-5 text-sm text-paper-700 dark:text-paper-200">Weather forecast could not be loaded. <button onClick={() => query.refetch()} className="ml-2 inline-flex items-center gap-1 font-bold text-marigold-600"><RefreshCw size={14}/>Retry</button></section>;
  const forecast = query.data!;
  const current = forecast.current;
  const dates = forecast.daily.time as string[];
  const beyond = days > dates.length;
  return <section className="rounded-2xl border border-paper-200 bg-white p-5 shadow-sm dark:border-paper-700 dark:bg-paper-900" aria-label={`Weather forecast for ${location || 'destination'}`}>
    <div className="mb-4 flex flex-wrap items-start justify-between gap-3"><div><p className="text-xs font-bold uppercase tracking-wider text-marigold-600">Local forecast · {forecast.timezone || 'local time'}</p><h3 className="mt-1 text-lg font-black text-paper-900 dark:text-white">{location || 'Trip weather'}</h3><p className="text-xs text-paper-500">Forecast dates shown in the destination’s local timezone</p></div><div className="text-right"><span className="text-3xl font-black text-paper-900 dark:text-white">{current.temperature_2m ?? '—'}°C</span><p className="text-sm text-paper-500">Feels like {current.apparent_temperature ?? '—'}°C</p><p className="text-xs text-paper-500">Current conditions</p></div></div>
    <div className="mb-4 flex flex-wrap gap-x-5 gap-y-2 text-xs text-paper-600 dark:text-paper-300"><span className="inline-flex items-center gap-1"><Droplets size={14}/>{current.relative_humidity_2m ?? '—'}% humidity</span><span className="inline-flex items-center gap-1"><Wind size={14}/>{current.wind_speed_10m ?? '—'} {forecast.units.current?.wind_speed_10m || 'km/h'}</span><span>Rain {current.precipitation ?? '—'} mm</span></div>
    <div className="grid grid-cols-2 gap-2 sm:grid-cols-3 lg:grid-cols-4">{dates.map((date, i) => { const code = Number(forecast.daily.weather_code?.[i]); return <article key={date} className="rounded-xl bg-paper-50 p-3 dark:bg-paper-800"><p className="text-xs font-bold text-paper-500">{new Date(`${date}T12:00:00`).toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric', timeZone: 'UTC' })}</p><p className="my-2 text-sm" aria-label={descriptions[code] || 'Weather conditions'}>{descriptions[code] || 'Conditions unavailable'}</p><p className="text-sm font-bold text-paper-900 dark:text-white">{forecast.daily.temperature_2m_min?.[i] ?? '—'}° / {forecast.daily.temperature_2m_max?.[i] ?? '—'}°C</p><p className="mt-1 text-xs text-paper-500">Rain {forecast.daily.precipitation_probability_max?.[i] ?? '—'}%</p><p className="mt-2 flex flex-wrap gap-x-2 text-[10px] text-paper-500"><span className="inline-flex items-center gap-1"><Sunrise size={11}/>{String(forecast.daily.sunrise?.[i] || '').slice(11, 16) || '—'}</span><span className="inline-flex items-center gap-1"><Sunset size={11}/>{String(forecast.daily.sunset?.[i] || '').slice(11, 16) || '—'}</span></p></article>; })}</div>
    {beyond && <p className="mt-3 text-sm text-amber-700 dark:text-amber-300">A reliable daily forecast is not yet available for all trip dates beyond the displayed forecast horizon.</p>}
    <p className="mt-4 text-xs text-paper-500">Forecast data is subject to change. Weather data by <a className="underline" href="https://open-meteo.com/" target="_blank" rel="noreferrer">Open-Meteo.com</a></p>
  </section>;
}
