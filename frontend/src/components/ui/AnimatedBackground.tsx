/** Small drifting bokeh-style particles layered above the aurora wash in
 * index.css (body::before). Mounted once at the app root (see App.tsx) so it
 * keeps animating in place across route changes. Purely decorative: aria
 * hidden, pointer-events disabled, and frozen by the prefers-reduced-motion
 * rule in index.css.
 */
const PARTICLES = [
  { left: "4%", size: 9, color: "var(--color-primary)", duration: 22, delay: -2 },
  { left: "12%", size: 5, color: "var(--color-mango)", duration: 28, delay: -14 },
  { left: "20%", size: 13, color: "var(--color-coral)", duration: 26, delay: -6 },
  { left: "29%", size: 7, color: "var(--color-route-blue)", duration: 19, delay: -10 },
  { left: "38%", size: 11, color: "var(--color-primary)", duration: 32, delay: -18 },
  { left: "47%", size: 6, color: "var(--color-coral)", duration: 24, delay: -4 },
  { left: "56%", size: 15, color: "var(--color-mango)", duration: 30, delay: -22 },
  { left: "64%", size: 8, color: "var(--color-route-blue)", duration: 19, delay: -8 },
  { left: "72%", size: 10, color: "var(--color-primary)", duration: 27, delay: -16 },
  { left: "80%", size: 5, color: "var(--color-coral)", duration: 23, delay: -1 },
  { left: "88%", size: 12, color: "var(--color-mango)", duration: 29, delay: -12 },
  { left: "95%", size: 7, color: "var(--color-route-blue)", duration: 21, delay: -6 },
] as const;

export function AnimatedBackground() {
  return (
    <div aria-hidden="true" className="pointer-events-none fixed inset-0 -z-10 overflow-hidden">
      {PARTICLES.map((particle, index) => (
        <span
          key={index}
          className="particle"
          style={{
            left: particle.left,
            width: particle.size,
            height: particle.size,
            backgroundColor: particle.color,
            boxShadow: `0 0 ${particle.size}px 1px ${particle.color}`,
            animationDuration: `${particle.duration}s`,
            animationDelay: `${particle.delay}s`,
          }}
        />
      ))}
    </div>
  );
}
