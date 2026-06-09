import { useEffect, useRef } from 'react';

function Navbar() {
  const navRef = useRef(null);

  useEffect(() => {
    const handleScroll = () => {
      if (!navRef.current) return;
      if (window.scrollY > 50) {
        navRef.current.classList.add('scrolled');
      } else {
        navRef.current.classList.remove('scrolled');
      }
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  return (
    <nav ref={navRef} className="navbar">
      <a href="/" className="nav-brand">
        <div className="nav-icon">
          <span className="material-symbols-outlined">menu_book</span>
        </div>
        <span className="nav-title">학습 플래너</span>
      </a>
    </nav>
  );
}

export default Navbar;
