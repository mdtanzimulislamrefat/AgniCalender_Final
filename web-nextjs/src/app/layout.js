import Link from 'next/link';
import './globals.css';

export const metadata = {
  title: 'AgniCalendar — Harmonized Burning Activity Calendar for Bangladesh',
  description:
    'NASA Space Apps Challenge 2026, Harmonization of MODIS and VIIRS Hot Spots. 244,308 raw FIRMS detections harmonized into 117,602 fire events for Bangladesh, 2003–2024. No login required.',
  openGraph: {
    title: 'AgniCalendar — One fire calendar, not three sensor counts',
    description:
      '244,308 raw NASA FIRMS detections → 117,602 harmonized fire events for Bangladesh, 2003–2024. Peak month April 2023: 4,746 events.',
    type: 'website',
  },
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>
        <div className="topbar">
          <div className="wrap">
            <Link className="brand" href="/">
              AgniCalendar <span>🔥 Bangladesh</span>
            </Link>
            <nav aria-label="Main navigation">
              <Link href="/">Dashboard</Link>
              <Link href="/critical">Critical periods</Link>
              <Link href="/method">Method &amp; limitations</Link>
            </nav>
          </div>
        </div>
        {children}
        <footer>
          <div className="wrap">
            AgniCalendar — NASA Space Apps Challenge 2026, “Harmonization of MODIS and
            VIIRS Hot Spots”. Data: NASA FIRMS yearly country files for Bangladesh
            (MODIS 2003–2024, VIIRS S-NPP 2013–2024, VIIRS NOAA-20 2019–2024).
            This project uses NASA open data and is not affiliated with or endorsed
            by NASA. No NASA logo is used. Code:{' '}
            <a href="https://github.com/mdtanzimulislamrefat/AgniCalender">
              github.com/mdtanzimulislamrefat/AgniCalender
            </a>
          </div>
        </footer>
      </body>
    </html>
  );
}
