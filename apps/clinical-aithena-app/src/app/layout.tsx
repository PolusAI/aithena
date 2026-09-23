import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import Script from "next/script";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "GARDIAN",
  description: "GARD Intelligent Association Network - Linking individuals with rare diseases to clinical trials",
};

// This inline script is critical to prevent flash of incorrect theme
const themeInitScript = `
(function() {
  try {
    const theme = localStorage.getItem('theme') || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
    document.documentElement.classList.toggle('dark', theme === 'dark');
    document.documentElement.style.colorScheme = theme;
  } catch (e) {}
})();
`;

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <script dangerouslySetInnerHTML={{ __html: themeInitScript }} />
        {/* Additional theme handling */}
        <Script id="theme-manager" strategy="afterInteractive">
          {`
            (function() {
                try {
                    function getThemePreference() {
                        if (typeof localStorage !== 'undefined' && localStorage.getItem('theme')) {
                            return localStorage.getItem('theme');
                        }
                        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
                    }
                    
                    const theme = getThemePreference();
                    
                    if (!localStorage.getItem('theme')) {
                        localStorage.setItem('theme', theme);
                    }
                    
                    window.addEventListener('storage', function() {
                        const updatedTheme = localStorage.getItem('theme');
                        if (updatedTheme === 'dark') {
                            document.documentElement.classList.add('dark');
                            document.documentElement.style.colorScheme = 'dark';
                        } else {
                            document.documentElement.classList.remove('dark');
                            document.documentElement.style.colorScheme = 'light';
                        }
                    });
                    
                    window.addEventListener('themechange', function(e) {
                        const newTheme = e.detail?.theme;
                        if (newTheme === 'dark') {
                            document.documentElement.classList.add('dark');
                            document.documentElement.style.colorScheme = 'dark';
                        } else if (newTheme === 'light') {
                            document.documentElement.classList.remove('dark');
                            document.documentElement.style.colorScheme = 'light';
                        }
                    });
                } catch (e) {
                    console.error('Error in theme manager:', e);
                }
            })();
          `}
        </Script>
      </head>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased bg-[var(--color-background)] text-[var(--color-foreground)]`}
      >
        {children}
      </body>
    </html>
  );
}
