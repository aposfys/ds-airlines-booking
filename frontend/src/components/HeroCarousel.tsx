import { useCallback, useEffect, useRef, useState } from 'react';
import { ArrowRight, CaretLeft, CaretRight } from '@phosphor-icons/react';
import { DESTINATIONS, imageFor } from '../lib/destination-images';

const ADVANCE_MS = 6000;

/** Does the visitor want motion at all? Read live rather than once, so a
 *  change in system settings takes effect without a reload. */
const usePrefersReducedMotion = (): boolean => {
  const [reduced, setReduced] = useState(
    () =>
      typeof window !== 'undefined' &&
      typeof window.matchMedia === 'function' &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches,
  );

  useEffect(() => {
    if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') return;
    const query = window.matchMedia('(prefers-reduced-motion: reduce)');
    const onChange = () => setReduced(query.matches);
    query.addEventListener('change', onChange);
    return () => query.removeEventListener('change', onChange);
  }, []);

  return reduced;
};

/** The hero: a photographic backdrop the glass search bar sits on, and a
 *  featured route underneath it.
 *
 *  The image is blurred and scaled well past its native size on purpose. The
 *  source crops are small, and `.v-glass` needs something with structure
 *  behind it to refract — flat paper gives it nothing to do.
 *
 *  Auto-advance stops entirely under prefers-reduced-motion, and the strip is
 *  aria-live so a screen reader hears the route change without the carousel
 *  stealing focus. */
const HeroCarousel = ({
  children,
  onSearchRoute,
}: {
  children: React.ReactNode;
  onSearchRoute: (iata: string) => void;
}) => {
  const [index, setIndex] = useState(0);
  const reducedMotion = usePrefersReducedMotion();
  const paused = useRef(false);

  const go = useCallback((next: number) => {
    setIndex((next + DESTINATIONS.length) % DESTINATIONS.length);
  }, []);

  useEffect(() => {
    if (reducedMotion) return;
    const timer = setInterval(() => {
      if (!paused.current) setIndex((i) => (i + 1) % DESTINATIONS.length);
    }, ADVANCE_MS);
    return () => clearInterval(timer);
  }, [reducedMotion]);

  const active = DESTINATIONS[index];
  const image = imageFor(active.iata);

  return (
    <header
      className="relative overflow-hidden"
      onMouseEnter={() => (paused.current = true)}
      onMouseLeave={() => (paused.current = false)}
    >
      {image ? (
        <img
          key={active.iata}
          src={image}
          alt=""
          aria-hidden="true"
          /* The first slide is the largest thing above the fold. */
          fetchPriority={index === 0 ? 'high' : 'low'}
          decoding={index === 0 ? 'sync' : 'async'}
          loading={index === 0 ? 'eager' : 'lazy'}
          sizes="100vw"
          className="ds-photo"
          style={{ filter: 'blur(18px)', transform: 'scale(1.15)' }}
        />
      ) : (
        <span className="ds-photo" style={{ background: 'var(--bloom)' }} />
      )}
      <span className="ds-scrim ds-scrim--hero" />

      <div className="relative max-w-7xl mx-auto px-6 py-16">{children}</div>

      {/* Featured route */}
      <div className="relative max-w-7xl mx-auto px-6 pb-10">
        <div className="v-glass v-glass-frame flex flex-wrap items-center gap-4 px-5 py-3">
          <p className="ds-eyebrow">Daily from Athens</p>

          <p className="ds-on-photo flex items-center gap-3 text-sm" aria-live="polite">
            <span className="v-num font-semibold">ATH → {active.iata}</span>
            <span className="opacity-80">
              {active.city}, {active.country}
            </span>
          </p>

          <button
            type="button"
            onClick={() => onSearchRoute(active.iata)}
            className="ds-action ds-action--primary"
          >
            Search this route
            <ArrowRight aria-hidden="true" weight="regular" className="v-icon" />
          </button>

          <div className="flex items-center gap-1 ml-auto">
            <button
              type="button"
              className="ds-icon-button"
              onClick={() => go(index - 1)}
              aria-label="Previous destination"
            >
              <CaretLeft aria-hidden="true" weight="regular" className="v-icon" />
            </button>

            <ul className="flex list-none p-0 m-0" aria-label="Featured destinations">
              {DESTINATIONS.map((destination, i) => (
                <li key={destination.iata}>
                  <button
                    type="button"
                    className="ds-dot"
                    aria-current={i === index}
                    aria-label={`Show ${destination.city}`}
                    onClick={() => go(i)}
                  />
                </li>
              ))}
            </ul>

            <button
              type="button"
              className="ds-icon-button"
              onClick={() => go(index + 1)}
              aria-label="Next destination"
            >
              <CaretRight aria-hidden="true" weight="regular" className="v-icon" />
            </button>
          </div>
        </div>
      </div>
    </header>
  );
};

export default HeroCarousel;
