import { useEffect, useRef } from 'react';

const SLIDES = [
  {
    src: 'https://lh3.googleusercontent.com/aida-public/AB6AXuCX6BVvRsANsoARaoKpwdjynnsgmODbMDvYxQqUexEnEMSs2KLwqUEWFlHg1y3qvXELQkP5MAHre4ayC_nWS8L8rTGqMA7U9Ev5T51_HB0NBJ621KPRk5Yz24o8cDoWpzv3w3yYNr46wUkAM3BsIK1CGb5KyWg9Cbeno4gJUZy9cWlJJu4Lk-LrkT3_1Z5MCx_FiVvOiPUahBk7Cbqsg8vFZE0yv12PXAabHAgc0rqLMkGJvqvtu3ykx96_aagA16zEQGTKoIjkVnv_',
    alt: 'Student studying',
  },
  {
    src: 'https://lh3.googleusercontent.com/aida-public/AB6AXuBOwvW2TYWTTp_2UEAZMaW9h7gcdYqTZY5LIZFQ_w32fOypIsZXp2VA0KnsLreAQQn-oOlh5As0tKGWE6O0HuyfCchxWznJL1i2uXAkr_8M-D_u0-XkNj13tAmi6GKyY-DWF2rpppgpTa9i-Y77Sa4aF6unvi2KtdrWNPzEUyRlCddhC4qVLaTYRqp26XM0pzdon_DPEbtppmjP5_qPaSrbgRkyvqIUYZuRkQAk3AqYU0_v7oQfzHfnybp3APLsHHgEBsRCWRgM95Jb',
    alt: 'Minimalist workspace',
  },
];

function HeroSlideshow() {
  const currentIndexRef = useRef(0);
  const imgRefs = useRef([]);

  useEffect(() => {
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReducedMotion || imgRefs.current.length <= 1) return;

    const interval = setInterval(() => {
      const imgs = imgRefs.current;
      imgs[currentIndexRef.current].classList.replace('active', 'inactive');
      currentIndexRef.current = (currentIndexRef.current + 1) % imgs.length;
      imgs[currentIndexRef.current].classList.replace('inactive', 'active');
    }, 5000);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className="hero-slideshow" id="hero-slideshow">
      {SLIDES.map((slide, index) => (
        <img
          key={index}
          ref={(el) => (imgRefs.current[index] = el)}
          src={slide.src}
          alt={slide.alt}
          className={index === 0 ? 'active' : 'inactive'}
        />
      ))}
      <div className="hero-overlay" />
    </div>
  );
}

export default HeroSlideshow;
